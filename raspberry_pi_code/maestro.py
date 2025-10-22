"""
Raspberry Pi - Maestro BLE Dual Independiente (Central)
Proyecto Microprocesadores - Sistema de Sensores Corporales

Este script actúa como MAESTRO BLE que:
- Escanea y se conecta a sensores del BRAZO y/o PIE
- Funciona independientemente: cada sensor puede conectarse por separado
- Recolecta datos de ambos sensores cuando están disponibles
- Procesa y almacena los datos de forma unificada
- Envía a Firebase con estructura combinada
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
        
    def add_sensor_reading_to_person(self, person_firebase_id, sensor_data):
        """Agrega una nueva lectura del sensor al historial de la persona"""
        try:
            if not person_firebase_id:
                logger.error("No se puede agregar: person_firebase_id es None")
                return False, None
                
            # Crear registro de lectura del sensor (puede ser brazo, pie o combinado)
            sensor_reading = {
                'timestamp': datetime.now().isoformat(),
                'raspberry_timestamp': sensor_data.get('timestamp'),
                'sensor_type': sensor_data.get('sensor_type', 'unknown')
            }
            
            # Agregar datos del brazo si están disponibles
            if 'brazo' in sensor_data:
                brazo_data = sensor_data['brazo']
                sensor_reading['brazo'] = {
                    'device_id': brazo_data.get('device_id', 'brazo_sensor'),
                    'arduino_timestamp': brazo_data.get('arduino_timestamp', 0),
                    'accelerometer': {
                        'x': brazo_data.get('accelerometer_x', 0),
                        'y': brazo_data.get('accelerometer_y', 0),
                        'z': brazo_data.get('accelerometer_z', 0)
                    },
                    'gyroscope': {
                        'x': brazo_data.get('gyroscope_x', 0),
                        'y': brazo_data.get('gyroscope_y', 0),
                        'z': brazo_data.get('gyroscope_z', 0)
                    }
                }
            
            # Agregar datos del pie si están disponibles
            if 'pie' in sensor_data:
                pie_data = sensor_data['pie']
                sensor_reading['pie'] = {
                    'device_id': pie_data.get('device_id', 'pie_sensor'),
                    'arduino_timestamp': pie_data.get('arduino_timestamp', 0),
                    'accelerometer': {
                        'x': pie_data.get('accelerometer_x', 0),
                        'y': pie_data.get('accelerometer_y', 0),
                        'z': pie_data.get('accelerometer_z', 0)
                    },
                    'gyroscope': {
                        'x': pie_data.get('gyroscope_x', 0),
                        'y': pie_data.get('gyroscope_y', 0),
                        'z': pie_data.get('gyroscope_z', 0)
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

class BLEDualSensorMaster:
    def __init__(self, scan_timeout=15, firebase_interval=0.3, debug=False, person_id=None, person_name=None):
        # UUIDs del servicio y característica del BRAZO
        self.ARM_SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"
        self.ARM_CHAR_UUID = "12654321-1321-1321-1321-1ba987654321"
        
        # UUIDs del servicio y característica del PIE
        self.FOOT_SERVICE_UUID = "22345678-2234-2234-2234-223456789abc"
        self.FOOT_CHAR_UUID = "22654321-2321-2321-2321-2ba987654321"
        
        # Clientes BLE
        self.arm_client = None
        self.foot_client = None
        
        # Datos de los sensores
        self.arm_data = {}
        self.foot_data = {}
        
        # Parámetros configurables
        self.scan_timeout = scan_timeout
        self.firebase_interval = firebase_interval
        self.debug_mode = debug
        self.person_id = person_id
        self.person_name = person_name
        
        # Configurar nivel de logging según debug
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.info("🐛 Modo debug activado")
        
        # Control de conexión independiente
        self.arm_connected = False
        self.foot_connected = False
        self.running = True
        
        # Firebase Manager
        self.firebase = FirebaseManager(FIREBASE_URL)
        
        # Control de envío a Firebase
        self.last_firebase_send = 0
        self.data_count = 0
        self.arm_readings_count = 0
        self.foot_readings_count = 0
        self.combined_readings_count = 0
        
        # Persona activa del monitor
        if person_id and person_name:
            self.active_person = {
                'firebase_id': person_id,
                'nombre': person_name
            }
            logger.info(f"👤 Persona configurada desde parámetros: {person_name} (ID: {person_id})")
        else:
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
            logger.error(f"Error conectando al BRAZO: {e}")
            return False

    async def scan_for_foot_device(self, timeout=None):
        """Escanea dispositivos BLE para encontrar el Arduino del pie"""
        timeout = timeout or self.scan_timeout
        logger.info(f"Escaneando dispositivo del PIE por {timeout}s...")
        
        foot_device = None
        
        devices = await BleakScanner.discover(timeout=timeout)
        
        for device in devices:
            if device.name:
                # Sensor del PIE
                if device.name == "Arduino_Pie_Sensor":
                    foot_device = device
                    logger.info(f"Sensor PIE encontrado: {device.address}")
                    break
                # Búsqueda alternativa
                elif "Arduino" in device.name:
                    if "pie" in device.name.lower() or "foot" in device.name.lower():
                        foot_device = device
                        logger.info(f"Sensor PIE (alternativo) encontrado: {device.address}")
                        break
        
        return foot_device

    async def connect_to_foot(self, device):
        """Conecta al sensor del pie"""
        try:
            logger.info(f"Conectando al sensor PIE: {device.address}")
            
            self.foot_client = BleakClient(device.address)
            await self.foot_client.connect()
            
            if self.foot_client.is_connected:
                logger.info("Conectado al sensor PIE")
                self.foot_connected = True
                
                # Activar notificaciones
                await self.foot_client.start_notify(
                    self.FOOT_CHAR_UUID, 
                    self.foot_notification_handler
                )
                logger.info("Notificaciones PIE activadas")
                return True
            else:
                logger.error("Falló conexión al sensor PIE")
                return False
                
        except Exception as e:
            logger.error(f"Error conectando al PIE: {e}")
            return False

    async def scan_for_both_sensors(self, timeout=None):
        """Escanea ambos sensores en paralelo de forma independiente"""
        timeout = timeout or self.scan_timeout
        logger.info(f"Escaneando sensores BRAZO y PIE por {timeout}s...")
        
        arm_device = None
        foot_device = None
        
        devices = await BleakScanner.discover(timeout=timeout)
        
        for device in devices:
            if device.name:
                # Buscar sensor del BRAZO
                if device.name == "Arduino_Brazo_Sensor":
                    arm_device = device
                    logger.info(f"Sensor BRAZO encontrado: {device.address}")
                # Buscar sensor del PIE
                elif device.name == "Arduino_Pie_Sensor":
                    foot_device = device
                    logger.info(f"Sensor PIE encontrado: {device.address}")
                # Búsquedas alternativas
                elif "Arduino" in device.name:
                    if "brazo" in device.name.lower() or "arm" in device.name.lower():
                        arm_device = device
                        logger.info(f"Sensor BRAZO (alternativo): {device.address}")
                    elif "pie" in device.name.lower() or "foot" in device.name.lower():
                        foot_device = device
                        logger.info(f"Sensor PIE (alternativo): {device.address}")
        
        return arm_device, foot_device

    async def continuous_scan_and_connect(self):
        """Escanea continuamente hasta conectar ambos sensores"""
        logger.info("🔄 Iniciando escaneo continuo hasta conectar ambos sensores...")
        
        scan_attempt = 0
        
        while self.running and (not self.arm_connected or not self.foot_connected):
            scan_attempt += 1
            logger.info(f"🔍 Intento de escaneo #{scan_attempt}")
            
            try:
                # Solo escanear sensores que no están conectados
                scan_tasks = []
                
                if not self.arm_connected:
                    scan_tasks.append(asyncio.create_task(self.scan_for_arm_device()))
                else:
                    scan_tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Placeholder
                    
                if not self.foot_connected:
                    scan_tasks.append(asyncio.create_task(self.scan_for_foot_device()))
                else:
                    scan_tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Placeholder
                
                # Esperar resultados de escaneo
                results = await asyncio.gather(*scan_tasks, return_exceptions=True)
                
                arm_device = results[0] if not self.arm_connected and not isinstance(results[0], Exception) else None
                foot_device = results[1] if not self.foot_connected and not isinstance(results[1], Exception) else None
                
                # Intentar conectar sensores encontrados
                connection_tasks = []
                
                if arm_device and not self.arm_connected:
                    logger.info("🦾 Sensor de brazo encontrado, intentando conectar...")
                    connection_tasks.append(asyncio.create_task(self.connect_to_arm(arm_device)))
                    
                if foot_device and not self.foot_connected:
                    logger.info("🦶 Sensor de pie encontrado, intentando conectar...")
                    connection_tasks.append(asyncio.create_task(self.connect_to_foot(foot_device)))
                
                # Ejecutar conexiones
                if connection_tasks:
                    await asyncio.gather(*connection_tasks, return_exceptions=True)
                
                # Verificar estado de conexiones
                connected_sensors = []
                if self.arm_connected:
                    connected_sensors.append("brazo")
                if self.foot_connected:
                    connected_sensors.append("pie")
                
                if connected_sensors:
                    logger.info(f"✅ Conectado a: {', '.join(connected_sensors)}")
                
                # Si ambos están conectados, salir del bucle
                if self.arm_connected and self.foot_connected:
                    logger.info("🎉 ¡Ambos sensores conectados exitosamente!")
                    break
                    
                # Si ninguno se conectó en este intento, esperar antes del siguiente
                if not connected_sensors or (not self.arm_connected or not self.foot_connected):
                    missing_sensors = []
                    if not self.arm_connected:
                        missing_sensors.append("brazo")
                    if not self.foot_connected:
                        missing_sensors.append("pie")
                    
                    logger.info(f"⏳ Esperando 3 segundos antes del siguiente escaneo...")
                    logger.info(f"📋 Sensores pendientes: {', '.join(missing_sensors)}")
                    await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"❌ Error en escaneo continuo: {e}")
                await asyncio.sleep(3)
        
        if not self.running:
            logger.info("⏹️ Escaneo continuo detenido por usuario")
        elif self.arm_connected and self.foot_connected:
            logger.info("✅ Escaneo continuo completado: ambos sensores conectados")

    async def reconnect_sensors(self):
        """Reconecta sensores desconectados de forma automática"""
        if hasattr(self, '_reconnecting') and self._reconnecting:
            return  # Ya hay una reconexión en progreso
            
        self._reconnecting = True
        logger.info("🔄 Iniciando proceso de reconexión automática...")
        
        try:
            reconnect_attempt = 0
            
            while self.running and (not self.arm_connected or not self.foot_connected):
                reconnect_attempt += 1
                logger.info(f"🔁 Intento de reconexión #{reconnect_attempt}")
                
                # Intentar reconectar sensores desconectados
                if not self.arm_connected:
                    arm_device = await self.scan_for_arm_device()
                    if arm_device:
                        await self.connect_to_arm(arm_device)
                        if self.arm_connected:
                            logger.info("✅ Brazo reconectado exitosamente")
                
                if not self.foot_connected:
                    foot_device = await self.scan_for_foot_device()
                    if foot_device:
                        await self.connect_to_foot(foot_device)
                        if self.foot_connected:
                            logger.info("✅ Pie reconectado exitosamente")
                
                # Si ambos están conectados, terminar reconexión
                if self.arm_connected and self.foot_connected:
                    logger.info("🎉 Todos los sensores han sido reconectados")
                    break
                
                # Esperar antes del siguiente intento
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"❌ Error en reconexión automática: {e}")
        finally:
            self._reconnecting = False
    
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
    
    def foot_notification_handler(self, sender, data):
        """Maneja datos recibidos del sensor del pie"""
        try:
            json_data = data.decode('utf-8')
            raw_foot_data = json.loads(json_data)
            self.foot_data = self.transform_arduino_data(raw_foot_data)
            logger.info(f"🦶 Datos PIE (original): {raw_foot_data}")
            logger.info(f"🦶 Datos PIE (transformado): {self.foot_data}")
            self.process_foot_data()
            
        except Exception as e:
            logger.error(f"❌ Error procesando datos PIE: {e}")
    
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
    
    def process_foot_data(self):
        """Procesa datos del sensor del pie"""
        if self.foot_data:
            foot_reading = {
                "timestamp": datetime.now().isoformat(),
                "pie": self.foot_data
            }
            
            # Agregar información de la persona activa si está disponible
            if self.active_person:
                foot_reading.update({
                    "nombre": self.active_person.get('nombre'),
                    "persona_id": self.active_person.get('id'),
                    "edad": self.active_person.get('edad'),
                    "genero": self.active_person.get('genero')
                })
            
            self.data_count += 1
            
            if self.active_person:
                logger.info(f"🎯 Datos Pie #{self.data_count} para {self.active_person.get('nombre')}")
            else:
                logger.info(f"🎯 Datos Pie #{self.data_count} (sin persona asignada)")
            
            # Enviar a Firebase según intervalo
            current_time = time.time()
            if current_time - self.last_firebase_send >= self.firebase_interval:
                self.send_to_firebase(foot_reading)
                self.last_firebase_send = current_time

    def send_to_firebase(self, sensor_reading):
        """Actualiza los datos del sensor (brazo o pie) en la persona activa"""
        def firebase_sender():
            try:
                if self.active_person and self.active_person.get('firebase_id'):
                    # Agregar nueva lectura del sensor al historial de la persona
                    success, person_id = self.firebase.add_sensor_reading_to_person(
                        self.active_person.get('firebase_id'), 
                        sensor_reading
                    )
                    if success:
                        sensor_type = "brazo" if "brazo" in sensor_reading else "pie"
                        logger.info(f"✅ Firebase: Nueva lectura de {sensor_type} agregada a {self.active_person.get('nombre')}")
                        # Incrementar contador de lecturas
                        if hasattr(self, f'{sensor_type}_readings_count'):
                            setattr(self, f'{sensor_type}_readings_count', getattr(self, f'{sensor_type}_readings_count') + 1)
                        else:
                            setattr(self, f'{sensor_type}_readings_count', 1)
                    else:
                        sensor_type = "brazo" if "brazo" in sensor_reading else "pie"
                        logger.warning(f"⚠️ Firebase: Error agregando lectura de {sensor_type} para {self.active_person.get('nombre')}")
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
        """Actualiza la sesión de la persona activa con información de sensores conectados"""
        if not person_data or not person_data.get('firebase_id'):
            return
            
        try:
            # Campos de sesión basados en sensores conectados
            session_update = {}
            current_time = datetime.now().isoformat()
            
            if self.arm_connected:
                session_update.update({
                    'brazo_session_start': current_time,
                    'device_brazo_connected': True,
                    'raspberry_brazo_id': 'raspberry_pi_brazo_001',
                    'last_brazo_connection': current_time
                })
                
            if self.foot_connected:
                session_update.update({
                    'pie_session_start': current_time,
                    'device_pie_connected': True,
                    'raspberry_pie_id': 'raspberry_pi_pie_001',
                    'last_pie_connection': current_time
                })
            
            # Determinar modo del sensor
            if self.arm_connected and self.foot_connected:
                session_update['sensor_mode'] = 'dual_activo'
            elif self.arm_connected:
                session_update['sensor_mode'] = 'brazo_activo'
            elif self.foot_connected:
                session_update['sensor_mode'] = 'pie_activo'
            
            active_sensors = []
            if self.arm_connected:
                active_sensors.append("brazo")
            if self.foot_connected:
                active_sensors.append("pie")
            
            logger.info(f"📝 Actualizando sesión de {' y '.join(active_sensors)} para: {person_data.get('nombre', 'Usuario')}")
            
            # URL para actualizar la persona existente específica
            url = f"{self.firebase.firebase_url}/persons/{person_data.get('firebase_id')}.json"
            
            # Usar PATCH para solo actualizar los campos de sesión
            response = requests.patch(url, json=session_update, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ Sesión de {' y '.join(active_sensors)} actualizada exitosamente")
            else:
                logger.warning(f"⚠️ Error actualizando sesión de {' y '.join(active_sensors)}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error actualizando sesión: {e}")
    
    def show_statistics(self):
        """Muestra estadísticas del sistema dual"""
        logger.info("📊 ESTADÍSTICAS DEL SISTEMA DUAL (BRAZO + PIE)")
        logger.info(f"   📈 Datos totales recibidos: {self.data_count}")
        logger.info(f"   🔗 Brazo conectado: {'✅' if self.arm_connected else '❌'}")
        logger.info(f"   🔗 Pie conectado: {'✅' if self.foot_connected else '❌'}")
        
        # Mostrar estado de reconexión si está activa
        if hasattr(self, '_reconnecting') and self._reconnecting:
            logger.info(f"   🔄 Reconectando sensores desconectados...")
            
        if self.active_person:
            logger.info(f"   👤 Persona activa: {self.active_person.get('nombre')} (ID: {self.active_person.get('firebase_id')})")
            arm_readings = getattr(self, 'brazo_readings_count', 0)
            foot_readings = getattr(self, 'pie_readings_count', 0)
            logger.info(f"   📊 Lecturas brazo: {arm_readings}")
            logger.info(f"   📊 Lecturas pie: {foot_readings}")
        else:
            logger.info(f"   👤 Persona activa: Sin seleccionar")
        logger.info(f"   🔥 Último envío Firebase: {int(time.time() - self.last_firebase_send)}s atrás")
        logger.info(f"   ⏱️  Intervalo Firebase: {self.firebase_interval}s")
        logger.info("─" * 50)
    
    async def monitor_connection(self):
        """Monitor para reconectar ambos dispositivos si se desconectan"""
        person_check_counter = 0
        
        while self.running:
            try:
                # Verificar conexión del brazo
                if self.arm_client and not self.arm_client.is_connected:
                    logger.warning("⚠️ Brazo desconectado, iniciando reconexión automática...")
                    self.arm_connected = False
                    # Iniciar escaneo continuo para reconectar sensores desconectados
                    asyncio.create_task(self.reconnect_sensors())
                
                # Verificar conexión del pie
                if self.foot_client and not self.foot_client.is_connected:
                    logger.warning("⚠️ Pie desconectado, iniciando reconexión automática...")
                    self.foot_connected = False
                    # El método reconnect_sensors manejará ambos sensores
                
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
        """Desconecta ambos dispositivos (brazo y pie)"""
        logger.info("🔌 Desconectando sensores...")
        
        disconnect_tasks = []
        
        if self.arm_client and self.arm_client.is_connected:
            disconnect_tasks.append(asyncio.create_task(self.arm_client.disconnect()))
            
        if self.foot_client and self.foot_client.is_connected:
            disconnect_tasks.append(asyncio.create_task(self.foot_client.disconnect()))
            
        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
            
        if self.arm_connected:
            logger.info("✅ Brazo desconectado")
        if self.foot_connected:
            logger.info("✅ Pie desconectado")
    
    async def run(self):
        """Función principal del maestro BLE dual (brazo y pie)"""
        logger.info("🚀 Iniciando Maestro BLE DUAL (BRAZO + PIE)...")
        logger.info("� MODO: Escaneo continuo hasta conectar ambos sensores")
        
        try:
            # 1. Iniciar escaneo continuo hasta conectar ambos sensores
            await self.continuous_scan_and_connect()
            
            # Verificar que al menos un sensor se haya conectado
            if not self.arm_connected and not self.foot_connected:
                logger.error("❌ No se pudo conectar a ningún sensor después del escaneo continuo")
                return
            
            # Mostrar resumen de conexiones exitosas
            logger.info("📊 RESUMEN DE CONEXIONES:")
            if self.arm_connected:
                logger.info("   ✅ Sensor del brazo: CONECTADO")
            else:
                logger.info("   ❌ Sensor del brazo: NO CONECTADO")
            if self.foot_connected:
                logger.info("   ✅ Sensor del pie: CONECTADO")
            else:
                logger.info("   ❌ Sensor del pie: NO CONECTADO")
            
            # 2. Obtener persona activa del monitor (si no se configuró desde parámetros)
            if not self.active_person:
                self.active_person = self.get_active_person()
            
            if self.active_person:
                logger.info(f"👤 Usando persona: {self.active_person.get('nombre')} (ID: {self.active_person.get('firebase_id')})")
                if self.active_person.get('edad'):
                    logger.info(f"   Edad: {self.active_person.get('edad')} años")
                # Actualizar sesión para sensores conectados
                if self.active_person.get('edad') and self.active_person.get('genero'):
                    self.update_person_session(self.active_person)
            else:
                logger.warning("⚠️ No hay persona seleccionada en el monitor. Los datos se guardarán sin asociar a una persona específica.")
            
            # 4. Iniciar monitoreo
            monitor_task = asyncio.create_task(self.monitor_connection())
            
            # 5. Mantener el programa corriendo
            active_sensors = []
            if self.arm_connected:
                active_sensors.append("brazo")
            if self.foot_connected:
                active_sensors.append("pie")
            
            logger.info(f"📡 Recolectando datos de {' y '.join(active_sensors)}... Presiona Ctrl+C para salir")
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
            logger.info("⏹️ Deteniendo maestro BLE dual...")
            self.running = False
            
        finally:
            await self.disconnect()


def parse_arguments():
    """Parsear argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Maestro BLE Dual - Conectar sensores de brazo y pie independientemente",
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
        type=float, 
        default=0.3,
        help='Intervalo de envío a Firebase en segundos (acepta decimales entre 0.1-0.5)'
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Activar modo debug'
    )
    
    parser.add_argument(
        '--person_id', 
        type=str,
        help='ID de Firebase de la persona seleccionada'
    )
    
    parser.add_argument(
        '--person_name', 
        type=str,
        help='Nombre de la persona seleccionada'
    )
    
    return parser.parse_args()

async def main():
    """Función principal"""
    # Parsear argumentos de línea de comandos
    args = parse_arguments()
    
    logger.info("🔵 Modo: SENSORES DUAL (BRAZO + PIE)")
    logger.info(f"⚙️ Configuración:")
    logger.info(f"   - Timeout escaneo: {args.scan_timeout}s")
    logger.info(f"   - Intervalo Firebase: {args.firebase_interval}s")
    logger.info(f"   - Debug: {'Activado' if args.debug else 'Desactivado'}")
    if args.person_id:
        logger.info(f"   - Persona ID: {args.person_id}")
    if args.person_name:
        logger.info(f"   - Persona: {args.person_name}")
    
    # Crear maestro dual con parámetros
    master = BLEDualSensorMaster(
        scan_timeout=args.scan_timeout,
        firebase_interval=args.firebase_interval,
        debug=args.debug,
        person_id=args.person_id,
        person_name=args.person_name
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
    
    # Ejecutar maestro dual (brazo + pie)
    asyncio.run(main())