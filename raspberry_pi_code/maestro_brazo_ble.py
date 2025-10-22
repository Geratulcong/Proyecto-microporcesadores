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
        
    def send_arm_sensor_data(self, arm_data):
        """Envía datos del sensor del brazo a Firebase"""
        try:
            # Preparar datos para Firebase
            firebase_data = {
                'timestamp': arm_data.get('timestamp'),
                'raspberry_id': 'raspberry_pi_brazo_001',
                'brazo': arm_data.get('brazo', {}),
                'session_id': f"session_brazo_{int(time.time())}"
            }
            
            # URL para enviar datos de sensores del brazo
            url = f"{self.firebase_url}/sensor_brazo_readings.json"
            
            # Enviar datos
            response = requests.post(url, json=firebase_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Datos del brazo enviados a Firebase. ID: {result['name']}")
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
            
            self.data_count += 1
            logger.info(f"🎯 Datos Brazo #{self.data_count}: {arm_reading}")
            
            # Enviar a Firebase según intervalo
            current_time = time.time()
            if current_time - self.last_firebase_send >= self.firebase_interval:
                self.send_to_firebase(arm_reading)
                self.last_firebase_send = current_time
    
    def send_to_firebase(self, arm_reading):
        """Envía los datos del brazo a Firebase en un hilo separado"""
        def firebase_sender():
            try:
                success, firebase_id = self.firebase.send_arm_sensor_data(arm_reading)
                if success:
                    logger.info(f"🔥 Firebase: Datos del brazo enviados exitosamente (ID: {firebase_id})")
                else:
                    logger.warning("⚠️ Firebase: Error enviando datos del brazo")
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
            "nombre": "Usuario Sensor Brazo",
            "genero": "No especificado",
            "edad": 25,
            "session_start": datetime.now().isoformat(),
            "device_brazo": "Arduino_Brazo_Sensor",
            "device_pie": "N/A - Solo brazo",
            "status": "sesion_activa_brazo_solo",
            "sensor_mode": "brazo_unicamente"
        }
        
        logger.info("👤 Registrando persona (solo brazo) en Firebase...")
        self.register_person(person_info)
    
    def show_statistics(self):
        """Muestra estadísticas del sistema"""
        logger.info("📊 ESTADÍSTICAS DEL SISTEMA (SOLO BRAZO)")
        logger.info(f"   📈 Datos recibidos: {self.data_count}")
        logger.info(f"   🔗 Brazo conectado: {'✅' if self.arm_connected else '❌'}")
        logger.info(f"   🔥 Último envío Firebase: {int(time.time() - self.last_firebase_send)}s atrás")
        logger.info(f"   ⏱️  Intervalo Firebase: {self.firebase_interval}s")
        logger.info("─" * 50)
    
    async def monitor_connection(self):
        """Monitor para reconectar el dispositivo del brazo si se desconecta"""
        while self.running:
            try:
                # Verificar conexión del brazo
                if self.arm_client and not self.arm_client.is_connected:
                    logger.warning("⚠️ Brazo desconectado, reintentando...")
                    self.arm_connected = False
                    # Aquí podrías implementar lógica de reconexión automática
                
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
            
            # 3. Registrar persona (opcional)
            self.register_initial_person()
            
            # 4. Iniciar monitoreo
            monitor_task = asyncio.create_task(self.monitor_connection())
            
            # 5. Mantener el programa corriendo
            logger.info("📡 Recolectando datos del brazo... Presiona Ctrl+C para salir")
            logger.info(f"🔥 Enviando a Firebase cada {self.firebase_interval} segundos")
            
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