"""
Raspberry Pi - Maestro BLE (Central)
Proyecto Microprocesadores - Sistema de Sensores Corporales

Este script actúa como MAESTRO BLE que:
- Escanea y se conecta a múltiples Arduino Nano 33 BLE Sense (periféricos)
- Recolecta datos de sensores de brazo y pie simultáneamente
- Procesa y almacena los datos combinados
- Envía a Firebase o base de datos
"""

import asyncio
import json
import time
from datetime import datetime
from bleak import BleakClient, BleakScanner
import logging
import requests
import threading

# Configuración logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración Firebase
FIREBASE_URL = "https://proyecto-posturas-microp-default-rtdb.firebaseio.com"

class FirebaseManager:
    def __init__(self, firebase_url):
        self.firebase_url = firebase_url
        
    def send_sensor_data(self, combined_data, person_id=None):
        """Envía datos combinados de sensores a Firebase"""
        try:
            # Si hay un person_id, agregar a su historial
            if person_id:
                return self.add_combined_reading_to_person(person_id, combined_data)
            
            # Si no hay person_id, usar el método original (tabla general)
            firebase_data = {
                'timestamp': combined_data.get('timestamp'),
                'raspberry_id': 'raspberry_pi_maestro_001',
                'brazo': combined_data.get('brazo', {}),
                'pie': combined_data.get('pie', {}),
                'session_id': f"session_{int(time.time())}"
            }
            
            # URL para enviar datos de sensores (tabla general)
            url = f"{self.firebase_url}/sensor_readings.json"
            
            # Enviar datos
            response = requests.post(url, json=firebase_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Datos enviados a Firebase (tabla general). ID: {result['name']}")
                return True, result['name']
            else:
                logger.error(f"❌ Error Firebase: {response.status_code} - {response.text}")
                return False, None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error de conexión Firebase: {e}")
            return False, None
        except Exception as e:
            logger.error(f"❌ Error inesperado Firebase: {e}")
            return False, None

    def add_combined_reading_to_person(self, person_firebase_id, combined_data):
        """Agrega una lectura combinada (brazo + pie) al historial de la persona"""
        try:
            if not person_firebase_id:
                logger.error("❌ No se puede agregar: person_firebase_id es None")
                return False, None
                
            # Crear registro de lectura combinada
            combined_reading = {
                'timestamp': datetime.now().isoformat(),
                'raspberry_timestamp': combined_data.get('timestamp'),
                'session_id': f"session_{int(time.time())}",
                'sensor_type': 'combined',  # brazo + pie
                'brazo': {
                    'device_id': combined_data.get('brazo', {}).get('device_id', 'brazo_sensor'),
                    'arduino_timestamp': combined_data.get('brazo', {}).get('arduino_timestamp', 0),
                    'accelerometer': {
                        'x': combined_data.get('brazo', {}).get('accelerometer_x', 0),
                        'y': combined_data.get('brazo', {}).get('accelerometer_y', 0),
                        'z': combined_data.get('brazo', {}).get('accelerometer_z', 0)
                    },
                    'gyroscope': {
                        'x': combined_data.get('brazo', {}).get('gyroscope_x', 0),
                        'y': combined_data.get('brazo', {}).get('gyroscope_y', 0),
                        'z': combined_data.get('brazo', {}).get('gyroscope_z', 0)
                    }
                },
                'pie': {
                    'device_id': combined_data.get('pie', {}).get('device_id', 'pie_sensor'),
                    'arduino_timestamp': combined_data.get('pie', {}).get('arduino_timestamp', 0),
                    'accelerometer': {
                        'x': combined_data.get('pie', {}).get('accelerometer_x', 0),
                        'y': combined_data.get('pie', {}).get('accelerometer_y', 0),
                        'z': combined_data.get('pie', {}).get('accelerometer_z', 0)
                    },
                    'gyroscope': {
                        'x': combined_data.get('pie', {}).get('gyroscope_x', 0),
                        'y': combined_data.get('pie', {}).get('gyroscope_y', 0),
                        'z': combined_data.get('pie', {}).get('gyroscope_z', 0)
                    }
                }
            }
            
            # URL para agregar al array de lecturas de sensor
            url = f"{self.firebase_url}/persons/{person_firebase_id}/sensor_readings.json"
            
            logger.info(f"➕ Agregando lectura combinada en: {url}")
            
            # POST agrega un nuevo elemento al array
            response = requests.post(url, json=combined_reading, timeout=10)
            
            if response.status_code == 200:
                # Actualizar timestamp de última actividad
                last_activity_url = f"{self.firebase_url}/persons/{person_firebase_id}/last_sensor_update.json"
                requests.put(last_activity_url, json=datetime.now().isoformat(), timeout=5)
                
                logger.info(f"✅ Nueva lectura combinada agregada al historial de: {person_firebase_id}")
                return True, person_firebase_id
            else:
                logger.error(f"❌ Error HTTP {response.status_code}: {response.text}")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ Error agregando lectura combinada: {e}")
            return False, None
    
    def send_person_data(self, person_info):
        """Envía información de persona a Firebase con estructura para historial de sensores"""
        try:
            person_data = {
                **person_info,
                'timestamp': datetime.now().isoformat(),
                'raspberry_id': 'raspberry_pi_maestro_001',
                'sensor_readings': {},  # Inicializar array vacío para historial de sensores
                'last_sensor_update': None,  # Timestamp de última actualización del sensor
                'total_readings_count': 0,  # Contador total de lecturas
                'session_active': False  # Estado de sesión
            }
            
            url = f"{self.firebase_url}/persons.json"
            response = requests.post(url, json=person_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Persona registrada con estructura de sensores. ID: {result['name']}")
                return True, result['name']
            else:
                logger.error(f"❌ Error registrando persona: {response.status_code}")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ Error registrando persona: {e}")
            return False, None

    def get_active_person(self):
        """Obtiene la persona activa desde Firebase"""
        try:
            response = requests.get(f"{self.firebase_url}/persons.json", timeout=10)
            
            if response.status_code == 200:
                persons_data = response.json()
                if persons_data:
                    logger.info(f"📋 Encontradas {len(persons_data)} personas en Firebase")
                    
                    # Buscar persona activa
                    for firebase_id, person_data in persons_data.items():
                        if person_data.get('es_activa', False):
                            logger.info(f"✅ Persona activa: {person_data.get('nombre')} [ID: {firebase_id}]")
                            person_data['firebase_id'] = firebase_id
                            return person_data
                    
                    # Si no hay activa, usar la primera
                    first_id, first_person = next(iter(persons_data.items()))
                    first_person['firebase_id'] = first_id
                    logger.warning(f"⚠️ No hay persona activa, usando: {first_person.get('nombre')} [ID: {first_id}]")
                    return first_person
                else:
                    logger.error("❌ No hay personas registradas en Firebase")
                    return None
            else:
                logger.error(f"❌ Error HTTP {response.status_code} obteniendo personas")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo persona activa: {e}")
            return None

class BLESensorMaster:
    def __init__(self):
        # UUIDs de servicios y características (deben coincidir con Arduino)
        self.ARM_SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"
        self.ARM_CHAR_UUID = "12654321-1321-1321-1321-1ba987654321"
        
        self.FOOT_SERVICE_UUID = "22345678-2234-2234-2234-223456789abc"  
        self.FOOT_CHAR_UUID = "22654321-2321-2321-2321-2ba987654321"
        
        # Clientes BLE
        self.arm_client = None
        self.foot_client = None
        
        # Datos de sensores
        self.arm_data = {}
        self.foot_data = {}
        self.combined_data = {}
        
        # Control de conexiones
        self.arm_connected = False
        self.foot_connected = False
        self.running = True
        
        # Firebase Manager
        self.firebase = FirebaseManager(FIREBASE_URL)
        
        # Persona activa del monitor
        self.active_person = None
        self.combined_readings_count = 0  # Contador de lecturas combinadas guardadas
        
        # Control de envío a Firebase
        self.last_firebase_send = 0
        self.firebase_interval = 5  # Enviar a Firebase cada 5 segundos
        self.data_count = 0
        
    async def scan_devices(self, timeout=10):
        """Escanea dispositivos BLE para encontrar los Arduino"""
        logger.info(f"🔍 Escaneando dispositivos BLE por {timeout}s...")
        
        arm_device = None
        foot_device = None
        
        devices = await BleakScanner.discover(timeout=timeout)
        
        for device in devices:
            logger.info(f"Encontrado: {device.name} - {device.address}")
            
            # Identificar por nombre exacto correlacionado
            if device.name:
                # Sensor del BRAZO
                if device.name == "Arduino_Brazo_Sensor":
                    arm_device = device
                    logger.info(f"✅ Sensor BRAZO encontrado: {device.address}")
                # Sensor del PIE  
                elif device.name == "Arduino_Pie_Sensor":
                    foot_device = device  
                    logger.info(f"✅ Sensor PIE encontrado: {device.address}")
                # Búsqueda alternativa por palabras clave
                elif "Arduino" in device.name:
                    if "brazo" in device.name.lower() or "arm" in device.name.lower():
                        arm_device = device
                        logger.info(f"✅ Sensor BRAZO (alternativo) encontrado: {device.address}")
                    elif "pie" in device.name.lower() or "foot" in device.name.lower():
                        foot_device = device  
                        logger.info(f"✅ Sensor PIE (alternativo) encontrado: {device.address}")
            
            # También buscar por servicios conocidos (si están disponibles)
            try:
                if hasattr(device, 'metadata') and device.metadata and 'uuids' in device.metadata:
                    uuids = device.metadata['uuids']
                    if self.ARM_SERVICE_UUID in uuids:
                        arm_device = device
                        logger.info(f"✅ Sensor BRAZO (por UUID): {device.address}")
                    elif self.FOOT_SERVICE_UUID in uuids:
                        foot_device = device
                        logger.info(f"✅ Sensor PIE (por UUID): {device.address}")
            except (AttributeError, TypeError):
                # Versión de bleak sin metadata, continuar con búsqueda por nombre
                pass
        
        return arm_device, foot_device
    
    async def connect_to_arm(self, device):
        """Conecta al sensor del brazo"""
        try:
            logger.info(f"🔗 Conectando al sensor BRAZO: {device.address}")
            
            self.arm_client = BleakClient(device.address)
            await self.arm_client.connect()
            
            if self.arm_client.is_connected:
                logger.info("✅ Conectado al sensor BRAZO")
                self.arm_connected = True
                
                # Activar notificaciones
                await self.arm_client.start_notify(
                    self.ARM_CHAR_UUID, 
                    self.arm_notification_handler
                )
                logger.info("🔔 Notificaciones BRAZO activadas")
                return True
            else:
                logger.error("❌ Falló conexión al sensor BRAZO")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error conectando al BRAZO: {e}")
            return False
    
    async def connect_to_foot(self, device):
        """Conecta al sensor del pie"""
        try:
            logger.info(f"🔗 Conectando al sensor PIE: {device.address}")
            
            self.foot_client = BleakClient(device.address)
            await self.foot_client.connect()
            
            if self.foot_client.is_connected:
                logger.info("✅ Conectado al sensor PIE")
                self.foot_connected = True
                
                # Activar notificaciones  
                await self.foot_client.start_notify(
                    self.FOOT_CHAR_UUID,
                    self.foot_notification_handler
                )
                logger.info("🔔 Notificaciones PIE activadas")
                return True
            else:
                logger.error("❌ Falló conexión al sensor PIE")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error conectando al PIE: {e}")
            return False
    
    def transform_arduino_data(self, raw_data):
        """Transforma datos del formato Arduino al formato esperado por React"""
        try:
            transformed = {
                "device_id": raw_data.get("dev", "unknown"),
                "sensor_type": raw_data.get("sensor", "unknown"),
                "arduino_timestamp": raw_data.get("ts", 0)
            }
            
            # Transformar datos del acelerómetro
            if "acc" in raw_data:
                acc = raw_data["acc"]
                transformed["accelerometer_x"] = acc.get("x", 0)
                transformed["accelerometer_y"] = acc.get("y", 0)
                transformed["accelerometer_z"] = acc.get("z", 0)
            # Formato alternativo (nombres cortos)
            elif "ax" in raw_data:
                transformed["accelerometer_x"] = raw_data.get("ax", 0)
                transformed["accelerometer_y"] = raw_data.get("ay", 0)
                transformed["accelerometer_z"] = raw_data.get("az", 0)
                transformed["arduino_timestamp"] = raw_data.get("ts", 0)
            
            # Transformar datos del giroscopio
            if "gyr" in raw_data:
                gyr = raw_data["gyr"]
                transformed["gyroscope_x"] = gyr.get("x", 0)
                transformed["gyroscope_y"] = gyr.get("y", 0)
                transformed["gyroscope_z"] = gyr.get("z", 0)
            # Formato alternativo (nombres cortos)
            elif "gx" in raw_data:
                transformed["gyroscope_x"] = raw_data.get("gx", 0)
                transformed["gyroscope_y"] = raw_data.get("gy", 0)
                transformed["gyroscope_z"] = raw_data.get("gz", 0)
            
            return transformed
            
        except Exception as e:
            logger.error(f"❌ Error transformando datos: {e}")
            return raw_data  # Retornar datos originales en caso de error

    def arm_notification_handler(self, sender, data):
        """Maneja datos recibidos del sensor del brazo"""
        try:
            json_data = data.decode('utf-8')
            raw_arm_data = json.loads(json_data)
            self.arm_data = self.transform_arduino_data(raw_arm_data)
            logger.info(f"📱 Datos BRAZO (original): {raw_arm_data}")
            logger.info(f"📱 Datos BRAZO (transformado): {self.arm_data}")
            self.process_combined_data()
            
        except Exception as e:
            logger.error(f"❌ Error procesando datos BRAZO: {e}")
    
    def foot_notification_handler(self, sender, data):
        """Maneja datos recibidos del sensor del pie"""
        try:
            json_data = data.decode('utf-8')
            raw_foot_data = json.loads(json_data)
            self.foot_data = self.transform_arduino_data(raw_foot_data)
            logger.info(f"🦶 Datos PIE (original): {raw_foot_data}")
            logger.info(f"🦶 Datos PIE (transformado): {self.foot_data}")
            self.process_combined_data()
            
        except Exception as e:
            logger.error(f"❌ Error procesando datos PIE: {e}")
    
    def process_combined_data(self):
        """Combina datos de ambos sensores y procesa"""
        if self.arm_data and self.foot_data:
            self.combined_data = {
                "timestamp": datetime.now().isoformat(),
                "brazo": self.arm_data,
                "pie": self.foot_data
            }
            
            self.data_count += 1
            logger.info(f"🎯 Datos Combinados #{self.data_count}: {self.combined_data}")
            
            # Enviar a Firebase según intervalo
            current_time = time.time()
            if current_time - self.last_firebase_send >= self.firebase_interval:
                self.send_to_firebase()
                self.last_firebase_send = current_time
    
    def send_to_firebase(self):
        """Envía los datos combinados a Firebase en un hilo separado"""
        def firebase_sender():
            try:
                success, firebase_id = self.firebase.send_sensor_data(self.combined_data)
                if success:
                    logger.info(f"🔥 Firebase: Datos enviados exitosamente (ID: {firebase_id})")
                else:
                    logger.warning("⚠️ Firebase: Error enviando datos")
            except Exception as e:
                logger.error(f"❌ Firebase: Error inesperado - {e}")
        
        # Ejecutar en hilo separado para no bloquear BLE
        firebase_thread = threading.Thread(target=firebase_sender, daemon=True)
        firebase_thread.start()
    
    def register_person(self, person_info):
        """Registra información de una persona en Firebase"""
        def person_sender():
            try:
                success, person_id = self.firebase.send_person_data(person_info)
                if success:
                    logger.info(f"👤 Firebase: Persona registrada (ID: {person_id})")
                else:
                    logger.warning("⚠️ Firebase: Error registrando persona")
            except Exception as e:
                logger.error(f"❌ Firebase: Error registrando persona - {e}")
        
        firebase_thread = threading.Thread(target=person_sender, daemon=True)
        firebase_thread.start()
    
    def register_initial_person(self):
        """Registra información inicial de la persona (ejemplo)"""
        person_info = {
            "nombre": "Usuario de Prueba",
            "genero": "No especificado",
            "edad": 25,
            "session_start": datetime.now().isoformat(),
            "device_brazo": "Arduino_Brazo_Sensor",
            "device_pie": "Arduino_Pie_Sensor",
            "status": "sesion_activa"
        }
        
        logger.info("👤 Registrando persona en Firebase...")
        self.register_person(person_info)
    
    def show_statistics(self):
        """Muestra estadísticas del sistema"""
        logger.info("📊 ESTADÍSTICAS DEL SISTEMA")
        logger.info(f"   📈 Datos recibidos: {self.data_count}")
        logger.info(f"   🔗 Brazo conectado: {'✅' if self.arm_connected else '❌'}")
        logger.info(f"   🦶 Pie conectado: {'✅' if self.foot_connected else '❌'}")
        logger.info(f"   🔥 Último envío Firebase: {int(time.time() - self.last_firebase_send)}s atrás")
        logger.info("─" * 50)
    
    async def monitor_connections(self):
        """Monitor para reconectar dispositivos desconectados"""
        while self.running:
            try:
                # Verificar conexión del brazo
                if self.arm_client and not self.arm_client.is_connected:
                    logger.warning("⚠️ Brazo desconectado, reintentando...")
                    self.arm_connected = False
                
                # Verificar conexión del pie  
                if self.foot_client and not self.foot_client.is_connected:
                    logger.warning("⚠️ Pie desconectado, reintentando...")
                    self.foot_connected = False
                
                # Esperar antes de la próxima verificación
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error en monitor: {e}")
                await asyncio.sleep(5)
    
    async def disconnect(self):
        """Desconecta todos los dispositivos"""
        logger.info("🔌 Desconectando dispositivos...")
        
        if self.arm_client and self.arm_client.is_connected:
            await self.arm_client.disconnect()
            logger.info("✅ Brazo desconectado")
        
        if self.foot_client and self.foot_client.is_connected:
            await self.foot_client.disconnect()
            logger.info("✅ Pie desconectado")
    
    async def run(self):
        """Función principal del maestro BLE"""
        logger.info("🚀 Iniciando Maestro BLE...")
        
        try:
            # 1. Escanear dispositivos
            arm_device, foot_device = await self.scan_devices()
            
            if not arm_device:
                logger.error("❌ No se encontró sensor del BRAZO")
                return
                
            if not foot_device:
                logger.error("❌ No se encontró sensor del PIE")  
                return
            
            # 2. Conectar dispositivos
            arm_connected = await self.connect_to_arm(arm_device)
            foot_connected = await self.connect_to_foot(foot_device)
            
            if not (arm_connected and foot_connected):
                logger.error("❌ No se pudieron conectar todos los dispositivos")
                return
            
            logger.info("🎉 Todos los sensores conectados exitosamente!")
            
            # 3. Obtener persona activa del monitor
            self.active_person = self.firebase.get_active_person()
            if self.active_person:
                logger.info(f"👤 Usando persona: {self.active_person.get('nombre')} ({self.active_person.get('edad')} años)")
            else:
                logger.warning("⚠️ No hay persona seleccionada en el monitor.")
                logger.info("💡 Registrando persona inicial...")
                self.register_initial_person()
            
            # 4. Iniciar monitoreo
            monitor_task = asyncio.create_task(self.monitor_connections())
            
            # 5. Mantener el programa corriendo
            logger.info("📡 Recolectando datos... Presiona Ctrl+C para salir")
            logger.info(f"🔥 Enviando a Firebase cada {self.firebase_interval} segundos")
            if self.active_person:
                logger.info(f"👤 Datos asociados a: {self.active_person.get('nombre')}")
            else:
                logger.info("⚠️ Datos no asociados a persona específica")
            
            start_time = time.time()
            while self.running:
                # Mostrar estadísticas cada 30 segundos
                if int(time.time() - start_time) % 30 == 0 and int(time.time() - start_time) > 0:
                    self.show_statistics()
                
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Deteniendo maestro BLE...")
            self.running = False
            
        finally:
            await self.disconnect()


async def main():
    """Función principal"""
    master = BLESensorMaster()
    await master.run()


if __name__ == "__main__":
    # Verificar dependencias
    try:
        import bleak
        try:
            logger.info(f"✅ Bleak version: {bleak.__version__}")
        except AttributeError:
            logger.info("✅ Bleak instalado (versión no disponible)")
    except ImportError:
        logger.error("❌ Instala bleak: pip install bleak")
        exit(1)
    
    # Ejecutar maestro
    asyncio.run(main())