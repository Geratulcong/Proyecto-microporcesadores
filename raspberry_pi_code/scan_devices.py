#!/usr/bin/env python3
"""
Script de ejemplo para escaneo de dispositivos Bluetooth
Utilizado para demostrar ejecución remota desde web
"""

import asyncio
import time
from datetime import datetime
from bleak import BleakScanner

async def scan_bluetooth_devices(timeout=10):
    """Escanear dispositivos Bluetooth BLE"""
    print(f"🔍 Iniciando escaneo de dispositivos Bluetooth BLE...")
    print(f"⏱️  Timeout: {timeout} segundos")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    try:
        # Escaneo de dispositivos
        devices = await BleakScanner.discover(timeout=timeout)
        
        if devices:
            print(f"✅ Encontrados {len(devices)} dispositivos:")
            print()
            
            # Separar Arduino de otros dispositivos
            arduino_devices = []
            other_devices = []
            
            for device in devices:
                device_name = device.name or "Sin nombre"
                
                if "arduino" in device_name.lower() or "sensor" in device_name.lower():
                    arduino_devices.append(device)
                else:
                    other_devices.append(device)
            
            # Mostrar dispositivos Arduino primero
            if arduino_devices:
                print("🔧 DISPOSITIVOS ARDUINO DETECTADOS:")
                for i, device in enumerate(arduino_devices, 1):
                    rssi_info = f" (RSSI: {device.rssi} dBm)" if hasattr(device, 'rssi') and device.rssi else ""
                    print(f"   {i}. {device.name}")
                    print(f"      📍 Dirección: {device.address}")
                    print(f"      📶 Señal: {rssi_info}")
                    print()
            
            # Mostrar otros dispositivos
            if other_devices:
                print("📱 OTROS DISPOSITIVOS BLE:")
                for i, device in enumerate(other_devices[:10], 1):  # Máximo 10
                    device_name = device.name or "Dispositivo sin nombre"
                    rssi_info = f" (RSSI: {device.rssi} dBm)" if hasattr(device, 'rssi') and device.rssi else ""
                    print(f"   {i}. {device_name}{rssi_info}")
                    print(f"      📍 {device.address}")
                
                if len(other_devices) > 10:
                    print(f"   ... y {len(other_devices) - 10} dispositivos más")
        else:
            print("❌ No se encontraron dispositivos Bluetooth BLE")
            
        print("-" * 50)
        print(f"✅ Escaneo completado en {timeout} segundos")
        
    except Exception as e:
        print(f"❌ Error durante el escaneo: {e}")
        return False
    
    return True

def main():
    """Función principal"""
    print("🚀 Script de Escaneo Bluetooth BLE")
    print("=" * 50)
    
    # Ejecutar escaneo
    try:
        result = asyncio.run(scan_bluetooth_devices(timeout=15))
        
        if result:
            print("🎉 Script ejecutado exitosamente")
        else:
            print("⚠️  Script completado con advertencias")
            
    except KeyboardInterrupt:
        print("\n🛑 Script interrumpido por el usuario")
    except Exception as e:
        print(f"💥 Error crítico: {e}")

if __name__ == "__main__":
    main()