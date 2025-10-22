"""
Raspberry Pi - Maestro BLE Solo Brazo (Central)
Proyecto Microprocesadores - Sistema de Sensores Corporales

Este script actúa como MAESTRO BLE que:
- Escanea y se conecta únicamente al Arduino Nano 33 BLE Sense del BRAZO
- Recolecta datos solo del sensor del brazo
- Procesa y almacena los datos del brazo
- Envía a Firebase o base de datos
"""

import asyncio
import json
import time
import argparse
import sys
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
        
    def add_sensor_reading_to_person(self, person_firebase_id, arm_data):
        """Agrega una nueva lectura del sensor al historial de la persona"""
        try:
            if not person_firebase_id:
                logger.error("❌ No se puede agregar: person_firebase_id es None")
                return False, None
                
            # Crear registro de lectura del sensor
            sensor_reading = {
                'timestamp': datetime.now().isoformat(),
                'raspberry_timestamp': arm_data.get('timestamp'),
                'arduino_timestamp': arm_data.get('brazo', {}).get('arduino_timestamp', 0),
                'device_id': arm_data.get('brazo', {}).get('device_id', 'brazo_sensor'),
                'sensor_type': 'brazo',
                'accelerometer': {
                    'x': arm_data.get('brazo', {}).get('accelerometer_x', 0),
                    'y': arm_data.get('brazo', {}).get('accelerometer_y', 0),
                    'z': arm_data.get('brazo', {}).get('accelerometer_z', 0)
                },
                'gyroscope': {
                    'x': arm_data.get('brazo', {}).get('gyroscope_x', 0),
                    'y': arm_data.get('brazo', {}).get('gyroscope_y', 0),
                    'z': arm_data.get('brazo', {}).get('gyroscope_z', 0)
                }
            }
            
            # URL para agregar al array de lecturas de sensor
            url = f"{self.firebase_url}/persons/{person_firebase_id}/sensor_readings.json"
            
            logger.info(f"➕ Agregando lectura del sensor en: {url}")
            
            # POST agrega un nuevo elemento al array
            response = requests.post(url, json=sensor_reading, timeout=10)
            
            if response.status_code == 200:
                # Actualizar timestamp de última actividad
                last_activity_url = f"{self.firebase_url}/persons/{person_firebase_id}/last_sensor_update.json"
                requests.put(last_activity_url, json=datetime.now().isoformat(), timeout=5)
                
                logger.info(f"✅ Nueva lectura agregada al historial de: {person_firebase_id}")
                return True, person_firebase_id
            else:
                logger.error(f"❌ Error HTTP {response.status_code}: {response.text}")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ Error agregando lectura: {e}")
            return False, None
    
    def send_person_data(self, person_info):
        """Envía información de persona a Firebase"""
        try:
            person_data = {
                **person_info,
                'timestamp': datetime.now().isoformat(),
                'raspberry_id': 'raspberry_pi_brazo_001'
            }
            
            url = f"{self.firebase_url}/persons_brazo.json"
            response = requests.post(url, json=person_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Persona registrada en Firebase (brazo). ID: {result['name']}")
                return True, result['name']
            else:
                logger.error(f"❌ Error registrando persona: {response.status_code}")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ Error registrando persona: {e}")
            return False, None

class BLEArmSensorMaster:
    def __init__(self, scan_timeout=15, firebase_interval=3, debug=False):
        # UUIDs del servicio y característica del BRAZO
        self.ARM_SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"
        self.ARM_CHAR_UUID = "12654321-1321-1321-1321-1ba987654321"
        
        # Cliente BLE del brazo
        self.arm_client = None
        
        # Datos del sensor del brazo
        self.arm_data = {}
        
        # Parámetros configurables
        self.scan_timeout = scan_timeout
        self.firebase_interval = firebase_interval
        self.debug_mode = debug
        
        # Configurar nivel de logging según debug
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.info("🐛 Modo debug activado")
        
        # Control de conexión
        self.arm_connected = False
        self.running = True
        
        # Firebase Manager
        self.firebase = FirebaseManager(FIREBASE_URL)
        
        # Control de envío a Firebase
        self.last_firebase_send = 0
        self.data_count = 0
        self.arm_readings_count = 0  # Contador de lecturas guardadas
        
        # Persona activa del monitor
        self.active_person = None
        
    async def scan_for_arm_device(self, timeout=None):
        """Escanea dispositivos BLE para encontrar el Arduino del brazo"""
        timeout = timeout or self.scan_timeout
        logger.info(f"🔍 Escaneando dispositivo del BRAZO por {timeout}s...")
        
        arm_device = None
        
        devices = await BleakScanner.discover(timeout=timeout)
        
        for device in devices:
            logger.info(f"Encontrado: {device.name} - {device.address}")
            
            # Identificar por nombre exacto correlacionado
            if device.name:
                # Sensor del BRAZO
                if device.name == "Arduino_Brazo_Sensor":
                    arm_device = device
                    logger.info(f"✅ Sensor BRAZO encontrado: {device.address}")
                    break
                # Búsqueda alternativa por palabras clave
                elif "Arduino" in device.name:
                    if "brazo" in device.name.lower() or "arm" in device.name.lower():
                        arm_device = device
                        logger.info(f"✅ Sensor BRAZO (alternativo) encontrado: {device.address}")
                        break
            
            # También buscar por servicios conocidos (si están disponibles)
            try:
                if hasattr(device, 'metadata') and device.metadata and 'uuids' in device.metadata:
                    uuids = device.metadata['uuids']
                    if self.ARM_SERVICE_UUID in uuids:
                        arm_device = device
                        logger.info(f"✅ Sensor BRAZO (por UUID): {device.address}")
                        break
            except (AttributeError, TypeError):
                # Versión de bleak sin metadata, continuar con búsqueda por nombre
                pass
        
        return arm_device
    
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
    
    def transform_arduino_data(self, raw_data):
        """Transforma datos del formato Arduino al formato esperado por React"""
        try:
            transformed = {
                "device_id": raw_data.get("dev", "unknown"),
                "sensor_type": raw_data.get("sensor", "brazo"),
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
            self.process_arm_data()
            
        except Exception as e:
            logger.error(f"❌ Error procesando datos BRAZO: {e}")
    
    def process_arm_data(self):
        """Procesa datos del sensor del brazo"""
        if self.arm_data:
            arm_reading = {
                "timestamp": datetime.now().isoformat(),
                "brazo": self.arm_data
            }
            
            # Agregar información de la persona activa si está disponible
            if self.active_person:
                arm_reading.update({
                    "nombre": self.active_person.get('nombre'),
                    "persona_id": self.active_person.get('id'),
                    "edad": self.active_person.get('edad'),
                    "genero": self.active_person.get('genero')
                })
            
            self.data_count += 1
            
            if self.active_person:
                logger.info(f"🎯 Datos Brazo #{self.data_count} para {self.active_person.get('nombre')}")
            else:
                logger.info(f"🎯 Datos Brazo #{self.data_count} (sin persona asignada)")
            
            # Enviar a Firebase según intervalo
            current_time = time.time()
            if current_time - self.last_firebase_send >= self.firebase_interval:
                self.send_to_firebase(arm_reading)
                self.last_firebase_send = current_time
    
    def send_to_firebase(self, arm_reading):
        """Actualiza los datos del sensor del brazo en la persona activa"""
        def firebase_sender():
            try:
                if self.active_person and self.active_person.get('firebase_id'):
                    # Agregar nueva lectura del sensor al historial de la persona
                    success, person_id = self.firebase.add_sensor_reading_to_person(
                        self.active_person.get('firebase_id'), 
                        arm_reading
                    )
                    if success:
                        logger.info(f"� Firebase: Nueva lectura del brazo agregada a {self.active_person.get('nombre')}")
                        # Incrementar contador de lecturas
                        if hasattr(self, 'arm_readings_count'):
                            self.arm_readings_count += 1
                        else:
                            self.arm_readings_count = 1
                    else:
                        logger.warning(f"⚠️ Firebase: Error agregando lectura del brazo para {self.active_person.get('nombre')}")
                else:
                    logger.warning("⚠️ No hay persona activa seleccionada. Datos no guardados.")
                    logger.info("💡 Selecciona una persona en el monitor web para guardar los datos del sensor")
            except Exception as e:
                logger.error(f"❌ Firebase: Error inesperado - {e}")
        
        # Ejecutar en hilo separado para no bloquear BLE
        firebase_thread = threading.Thread(target=firebase_sender, daemon=True)
        firebase_thread.start()
    
    def get_active_person(self):
        """Obtiene la persona activa desde Firebase con su ID"""
        try:
            # Intentar obtener la última persona seleccionada desde el monitor
            url = f"{self.firebase.firebase_url}/persons.json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                persons_data = response.json()
                if persons_data:
                    # Obtener todas las personas con sus IDs
                    persons_with_ids = []
                    for firebase_id, person_data in persons_data.items():
                        person_data['firebase_id'] = firebase_id  # Agregar el ID de Firebase
                        persons_with_ids.append(person_data)
                    
                    # Ordenar por timestamp para obtener la más reciente
                    persons_with_ids.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                    
                    if persons_with_ids:
                        active_person = persons_with_ids[0]  # La más reciente
                        logger.info(f"👤 Persona activa encontrada: {active_person.get('nombre', 'Sin nombre')} (ID: {active_person.get('firebase_id')})")
                        return active_person
                    
            logger.warning("⚠️ No se encontró ninguna persona registrada")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error obteniendo persona activa: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado obteniendo persona: {e}")
            return None

    def get_person_readings_count(self, person_firebase_id):
        """Obtiene el número de lecturas guardadas para una persona"""
        try:
            url = f"{self.firebase.firebase_url}/persons/{person_firebase_id}/sensor_readings.json"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                readings = response.json()
                if readings:
                    return len(readings)
            return 0
        except:
            return 0

    def update_person_session(self, person_data):
        """Actualiza la sesión de la persona activa con información del brazo"""
        if not person_data or not person_data.get('firebase_id'):
            return
            
        try:
            # Solo los campos de sesión que queremos actualizar
            session_update = {
                'brazo_session_start': datetime.now().isoformat(),
                'device_brazo_connected': True,
                'raspberry_brazo_id': 'raspberry_pi_brazo_001',
                'last_brazo_connection': datetime.now().isoformat(),
                'sensor_mode': 'brazo_activo'
            }
            
            logger.info(f"📝 Actualizando sesión del brazo para: {person_data.get('nombre', 'Usuario')}")
            
            # URL para actualizar la persona existente específica
            url = f"{self.firebase.firebase_url}/persons/{person_data.get('firebase_id')}.json"
            
            # Usar PATCH para solo actualizar los campos de sesión
            response = requests.patch(url, json=session_update, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Sesión del brazo actualizada exitosamente")
            else:
                logger.warning(f"⚠️ Error actualizando sesión del brazo: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error actualizando sesión: {e}")
    
    def show_statistics(self):
        """Muestra estadísticas del sistema"""
        logger.info("📊 ESTADÍSTICAS DEL SISTEMA (SOLO BRAZO)")
        logger.info(f"   📈 Datos recibidos: {self.data_count}")
        logger.info(f"   🔗 Brazo conectado: {'✅' if self.arm_connected else '❌'}")
        if self.active_person:
            logger.info(f"   👤 Persona activa: {self.active_person.get('nombre')} (ID: {self.active_person.get('firebase_id')})")
            readings_count = getattr(self, 'arm_readings_count', 0)
            logger.info(f"   📊 Lecturas guardadas: {readings_count}")
        else:
            logger.info(f"   👤 Persona activa: Sin seleccionar")
        logger.info(f"   🔥 Último envío Firebase: {int(time.time() - self.last_firebase_send)}s atrás")
        logger.info(f"   ⏱️  Intervalo Firebase: {self.firebase_interval}s")
        logger.info("─" * 50)
    
    async def monitor_connection(self):
        """Monitor para reconectar el dispositivo del brazo si se desconecta"""
        person_check_counter = 0
        
        while self.running:
            try:
                # Verificar conexión del brazo
                if self.arm_client and not self.arm_client.is_connected:
                    logger.warning("⚠️ Brazo desconectado, reintentando...")
                    self.arm_connected = False
                    # Aquí podrías implementar lógica de reconexión automática
                
                # Refrescar persona activa cada 30 segundos (10 ciclos x 3 segundos)
                person_check_counter += 1
                if person_check_counter >= 10:
                    logger.info("🔄 Verificando si cambió la persona seleccionada...")
                    new_active_person = self.get_active_person()
                    
                    # Comparar IDs de Firebase para detectar cambios
                    current_firebase_id = self.active_person.get('firebase_id') if self.active_person else None
                    new_firebase_id = new_active_person.get('firebase_id') if new_active_person else None
                    
                    if new_firebase_id and new_firebase_id != current_firebase_id:
                        old_name = self.active_person.get('nombre') if self.active_person else 'Ninguna'
                        new_name = new_active_person.get('nombre')
                        logger.info(f"👤 Cambiando persona activa: {old_name} → {new_name}")
                        self.active_person = new_active_person
                        self.update_person_session(self.active_person)
                    elif not new_active_person and self.active_person:
                        logger.warning("⚠️ No se encontró persona activa, manteniendo la anterior")
                    
                    person_check_counter = 0
                
                # Esperar antes de la próxima verificación
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"Error en monitor: {e}")
                await asyncio.sleep(3)
    
    async def disconnect(self):
        """Desconecta el dispositivo del brazo"""
        logger.info("🔌 Desconectando dispositivo del brazo...")
        
        if self.arm_client and self.arm_client.is_connected:
            await self.arm_client.disconnect()
            logger.info("✅ Brazo desconectado")
    
    async def run(self):
        """Función principal del maestro BLE para brazo"""
        logger.info("🚀 Iniciando Maestro BLE (SOLO BRAZO)...")
        
        try:
            # 1. Escanear dispositivo del brazo
            arm_device = await self.scan_for_arm_device()
            
            if not arm_device:
                logger.error("❌ No se encontró sensor del BRAZO")
                return
            
            # 2. Conectar dispositivo del brazo
            arm_connected = await self.connect_to_arm(arm_device)
            
            if not arm_connected:
                logger.error("❌ No se pudo conectar al sensor del brazo")
                return
            
            logger.info("🎉 Sensor del brazo conectado exitosamente!")
            
            # 3. Obtener persona activa del monitor
            self.active_person = self.get_active_person()
            if self.active_person:
                logger.info(f"👤 Usando persona: {self.active_person.get('nombre')} ({self.active_person.get('edad')} años)")
                self.update_person_session(self.active_person)
            else:
                logger.warning("⚠️ No hay persona seleccionada en el monitor. Los datos se guardarán sin asociar a una persona específica.")
            
            # 4. Iniciar monitoreo
            monitor_task = asyncio.create_task(self.monitor_connection())
            
            # 5. Mantener el programa corriendo
            logger.info("📡 Recolectando datos del brazo... Presiona Ctrl+C para salir")
            logger.info(f"🔥 Enviando a Firebase cada {self.firebase_interval} segundos")
            if self.active_person:
                logger.info(f"👤 Datos asociados a: {self.active_person.get('nombre')}")
            else:
                logger.info("⚠️ Datos no asociados a persona específica - Selecciona una persona en el monitor web")
            
            start_time = time.time()
            while self.running:
                # Mostrar estadísticas cada 20 segundos
                if int(time.time() - start_time) % 20 == 0 and int(time.time() - start_time) > 0:
                    self.show_statistics()
                
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Deteniendo maestro BLE del brazo...")
            self.running = False
            
        finally:
            await self.disconnect()


def parse_arguments():
    """Parsear argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Maestro BLE Solo Brazo - Conectar sensor del brazo",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--scan_timeout', 
        type=int, 
        default=15,
        help='Tiempo de escaneo BLE en segundos'
    )
    
    parser.add_argument(
        '--firebase_interval', 
        type=int, 
        default=3,
        help='Intervalo de envío a Firebase en segundos'
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Activar modo debug'
    )
    
    return parser.parse_args()

async def main():
    """Función principal"""
    # Parsear argumentos de línea de comandos
    args = parse_arguments()
    
    logger.info("🔵 Modo: SOLO SENSOR DEL BRAZO")
    logger.info(f"⚙️ Configuración:")
    logger.info(f"   - Timeout escaneo: {args.scan_timeout}s")
    logger.info(f"   - Intervalo Firebase: {args.firebase_interval}s")
    logger.info(f"   - Debug: {'Activado' if args.debug else 'Desactivado'}")
    
    # Crear maestro con parámetros
    master = BLEArmSensorMaster(
        scan_timeout=args.scan_timeout,
        firebase_interval=args.firebase_interval,
        debug=args.debug
    )
    
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
    
    # Ejecutar maestro del brazo
    asyncio.run(main())