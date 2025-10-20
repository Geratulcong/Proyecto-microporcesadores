#!/usr/bin/env python3
"""
Script de prueba para recibir datos JSON del Arduino Maestro
Versión simplificada para debugging
"""

import asyncio
import json
import time
from datetime import datetime
from bleak import BleakScanner, BleakClient

# Configuración del Arduino Maestro
ARDUINO_NAME = "Arduino Sensor Maestro"
SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"
CHARACTERISTIC_UUID = "87654321-4321-4321-4321-cba987654321"

class SimpleArduinoReceiver:
    def __init__(self):
        self.client = None
        self.arduino_address = None
        
    async def scan_for_arduino(self, timeout=15):
        """Buscar el Arduino Maestro"""
        print(f"🔍 Buscando '{ARDUINO_NAME}'...")
        
        devices = await BleakScanner.discover(timeout=timeout)
        
        print("\n📱 Dispositivos encontrados:")
        for device in devices:
            name = device.name or "Sin nombre"
            print(f"   {name} - {device.address}")
            
            # Buscar por nombre completo o parcial
            if device.name and ("Arduino Sensor Maestro" in device.name):
                print(f"✅ Arduino encontrado: {device.name} - {device.address}")
                self.arduino_address = device.address
                return True
                
        print("❌ Arduino no encontrado")
        return False
    
    async def connect_to_arduino(self):
        """Conectar al Arduino"""
        if not self.arduino_address:
            print("❌ Dirección del Arduino no disponible")
            return False
            
        try:
            print(f"🔗 Conectando a {self.arduino_address}...")
            self.client = BleakClient(self.arduino_address)
            await self.client.connect()
            
            if self.client.is_connected:
                print("✅ Conectado al Arduino exitosamente")
                
                # Mostrar servicios disponibles
                services = await self.client.get_services()
                print(f"📋 Servicios disponibles: {len(services)}")
                for service in services:
                    print(f"   Servicio: {service.uuid}")
                    for char in service.characteristics:
                        print(f"      Característica: {char.uuid}")
                
                return True
            else:
                print("❌ No se pudo conectar al Arduino")
                return False
                
        except Exception as e:
            print(f"❌ Error al conectar: {e}")
            return False
    
    def process_data(self, sender, data):
        """Procesar datos recibidos"""
        try:
            # Convertir bytes a string
            json_string = data.decode('utf-8').strip()
            print(f"\n📡 Datos recibidos ({len(data)} bytes):")
            print(f"Raw: {json_string}")
            
            # Intentar parsear JSON
            try:
                arduino_data = json.loads(json_string)
                print(f"✅ JSON válido:")
                
                # Mostrar datos formateados
                if "acX1" in arduino_data:  # Formato compacto del maestro
                    print(f"   🦾 BRAZO: X={arduino_data.get('acX1'):.2f}, Y={arduino_data.get('acY1'):.2f}, Z={arduino_data.get('acZ1'):.2f}")
                    print(f"   🦶 PIE:   X={arduino_data.get('acX2'):.2f}, Y={arduino_data.get('acY2'):.2f}, Z={arduino_data.get('acZ2'):.2f}")
                    print(f"   🔗 Pie conectado: {arduino_data.get('foot_connected', False)}")
                    print(f"   🔋 Batería: {arduino_data.get('bat', 0)}%")
                else:
                    print(f"   📊 Datos: {arduino_data}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON inválido: {e}")
                
        except Exception as e:
            print(f"❌ Error procesando datos: {e}")
    
    async def start_listening(self):
        """Iniciar escucha de datos"""
        if not self.client or not self.client.is_connected:
            print("❌ No hay conexión con Arduino")
            return
            
        try:
            print(f"\n📡 Suscribiéndose a característica: {CHARACTERISTIC_UUID}")
            await self.client.start_notify(CHARACTERISTIC_UUID, self.process_data)
            print("✅ Escuchando datos del Arduino...")
            print("🛑 Presiona Ctrl+C para detener\n")
            
            # Mantener la conexión activa
            while True:
                if not self.client.is_connected:
                    print("❌ Conexión perdida")
                    break
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo...")
        except Exception as e:
            print(f"❌ Error durante escucha: {e}")
        finally:
            if self.client and self.client.is_connected:
                await self.client.stop_notify(CHARACTERISTIC_UUID)
                await self.client.disconnect()
                print("🔌 Desconectado")

async def main():
    print("🚀 Receptor Simple para Arduino Maestro")
    print("=" * 50)
    
    receiver = SimpleArduinoReceiver()
    
    # Buscar Arduino
    if not await receiver.scan_for_arduino():
        print("❌ No se pudo encontrar el Arduino")
        return
    
    # Conectar
    if not await receiver.connect_to_arduino():
        print("❌ No se pudo conectar al Arduino")
        return
    
    # Escuchar datos
    await receiver.start_listening()

if __name__ == "__main__":
    asyncio.run(main())