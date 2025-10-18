#!/usr/bin/env python3
"""
Raspberry Pi - Receptor de datos Bluetooth desde Arduino Nano 33 BLE Sense
Proyecto Microprocesadores - Sistema de Posturas

Recibe datos JSON del acelerómetro vía Bluetooth y los envía a Firebase
"""

import asyncio
import json
import time
from datetime import datetime
from bleak import BleakScanner, BleakClient
import sys
import os

# Importar nuestro servicio Firebase
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from firebase_sender import FirebaseSender

# Configuración del Arduino
ARDUINO_NAME = "Arduino Postura Sensor"
SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"
CHARACTERISTIC_UUID = "87654321-4321-4321-4321-cba987654321"

class ArduinoBluetoothReceiver:
    def __init__(self):
        self.client = None
        self.arduino_address = None
        self.firebase_sender = FirebaseSender()
        self.running = False
        
    async def scan_for_arduino(self, timeout=10):
        """Buscar el Arduino Nano 33 BLE Sense"""
        print("🔍 Buscando Arduino Nano 33 BLE Sense...")
        
        devices = await BleakScanner.discover(timeout=timeout)
        
        for device in devices:
            print(f"📱 Dispositivo encontrado: {device.name} - {device.address}")
            
            if device.name and ARDUINO_NAME in device.name:
                print(f"✅ Arduino encontrado: {device.address}")
                self.arduino_address = device.address
                return True
                
        print("❌ Arduino no encontrado")
        return False
    
    async def connect_to_arduino(self):
        """Conectar al Arduino vía Bluetooth"""
        if not self.arduino_address:
            print("❌ Dirección del Arduino no disponible")
            return False
            
        try:
            print(f"🔗 Conectando a {self.arduino_address}...")
            self.client = BleakClient(self.arduino_address)
            await self.client.connect()
            
            if self.client.is_connected:
                print("✅ Conectado al Arduino exitosamente")
                return True
            else:
                print("❌ No se pudo conectar al Arduino")
                return False
                
        except Exception as e:
            print(f"❌ Error al conectar: {e}")
            return False
    
    def process_arduino_data(self, sender, data):
        """Procesar datos recibidos del Arduino"""
        try:
            # Convertir bytes a string
            json_string = data.decode('utf-8').strip()
            print(f"📡 Datos recibidos: {json_string}")
            
            # Parsear JSON
            arduino_data = json.loads(json_string)
            
            # Crear datos de persona para Firebase
            person_data = {
                "nombre": f"Arduino_Usuario_{datetime.now().strftime('%H%M%S')}",
                "genero": "No especificado",
                "edad": 25,  # Valor por defecto
                "accelerometer_x": arduino_data.get("accelerometer_x", 0),
                "accelerometer_y": arduino_data.get("accelerometer_y", 0), 
                "accelerometer_z": arduino_data.get("accelerometer_z", 0),
                "postura_detectada": arduino_data.get("postura_detectada", "unknown"),
                "device_id": arduino_data.get("device_id", "arduino_unknown"),
                "arduino_timestamp": arduino_data.get("timestamp", 0),
                "battery_level": arduino_data.get("battery_level", 0),
                "signal_strength": arduino_data.get("signal_strength", 0)
            }
            
            # Enviar a Firebase
            success, firebase_id = self.firebase_sender.send_person_data(person_data)
            
            if success:
                print(f"🔥 Datos enviados a Firebase con ID: {firebase_id}")
                print(f"📊 Postura: {person_data['postura_detectada']}")
                print(f"📐 X:{person_data['accelerometer_x']:.3f} Y:{person_data['accelerometer_y']:.3f} Z:{person_data['accelerometer_z']:.3f}")
            else:
                print("❌ Error al enviar a Firebase")
                
        except json.JSONDecodeError as e:
            print(f"❌ Error al parsear JSON: {e}")
        except Exception as e:
            print(f"❌ Error procesando datos: {e}")
    
    async def start_receiving_data(self):
        """Iniciar recepción continua de datos"""
        if not self.client or not self.client.is_connected:
            print("❌ No hay conexión con Arduino")
            return
            
        try:
            # Suscribirse a notificaciones de la característica
            await self.client.start_notify(CHARACTERISTIC_UUID, self.process_arduino_data)
            print("📡 Escuchando datos del Arduino...")
            print("🛑 Presiona Ctrl+C para detener")
            
            self.running = True
            
            # Mantener la conexión activa
            while self.running and self.client.is_connected:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo recepción de datos...")
            self.running = False
        except Exception as e:
            print(f"❌ Error durante recepción: {e}")
        finally:
            if self.client:
                await self.client.stop_notify(CHARACTERISTIC_UUID)
    
    async def disconnect(self):
        """Desconectar del Arduino"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            print("🔌 Desconectado del Arduino")

async def main():
    """Función principal"""
    print("🚀 Iniciando receptor Bluetooth para Arduino Nano 33 BLE Sense")
    print("=" * 60)
    
    receiver = ArduinoBluetoothReceiver()
    
    try:
        # Buscar Arduino
        if not await receiver.scan_for_arduino():
            print("❌ No se encontró el Arduino. Asegúrate de que esté encendido y advertising.")
            return
        
        # Conectar
        if not await receiver.connect_to_arduino():
            print("❌ No se pudo conectar al Arduino")
            return
        
        # Recibir datos
        await receiver.start_receiving_data()
        
    except KeyboardInterrupt:
        print("\n🛑 Programa interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error en programa principal: {e}")
    finally:
        await receiver.disconnect()

if __name__ == "__main__":
    # Verificar dependencias
    try:
        import bleak
    except ImportError:
        print("❌ Instala bleak: pip3 install bleak")
        sys.exit(1)
    
    asyncio.run(main())