#!/usr/bin/env python3
"""
Script de prueba para Firebase
Verifica conectividad y envía datos de prueba
"""

import requests
import json
import time
from datetime import datetime

# Configuración Firebase
FIREBASE_URL = "https://proyecto-posturas-microp-default-rtdb.firebaseio.com"

def test_firebase_connection():
    """Probar conexión a Firebase"""
    print("🔥 Probando conexión a Firebase...")
    print(f"📡 URL: {FIREBASE_URL}")
    print("-" * 50)
    
    try:
        # Test básico de conectividad
        test_url = f"{FIREBASE_URL}/.json"
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Conexión a Firebase exitosa")
            return True
        else:
            print(f"❌ Error de conexión: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout: Firebase no responde")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión: No se puede conectar a Firebase")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def send_test_data():
    """Enviar datos de prueba a Firebase"""
    print("\n📊 Enviando datos de prueba...")
    
    # Datos de prueba simulando Arduino
    test_data = {
        'timestamp': datetime.now().isoformat(),
        'raspberry_id': 'raspberry_pi_test',
        'device_id': 'test_device_001',
        'test_mode': True,
        'brazo': {
            'accelerometer_x': 0.123,
            'accelerometer_y': -0.456,
            'accelerometer_z': 9.789
        },
        'pie': {
            'accelerometer_x': 0.321,
            'accelerometer_y': -0.654,
            'accelerometer_z': 9.987
        },
        'postura_detectada': 'test_posture',
        'battery_level': 85
    }
    
    try:
        # Enviar a Firebase
        url = f"{FIREBASE_URL}/sensor_readings.json"
        response = requests.post(url, json=test_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Datos enviados exitosamente")
            print(f"📝 ID generado: {result.get('name', 'N/A')}")
            return True
        else:
            print(f"❌ Error enviando datos: HTTP {response.status_code}")
            print(f"📄 Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error enviando datos: {e}")
        return False

def read_recent_data():
    """Leer datos recientes de Firebase"""
    print("\n📖 Leyendo datos recientes...")
    
    try:
        # Leer últimos 3 registros
        url = f"{FIREBASE_URL}/sensor_readings.json?orderBy=\"$key\"&limitToLast=3"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data:
                print(f"✅ Encontrados {len(data)} registros recientes:")
                
                for key, record in data.items():
                    timestamp = record.get('timestamp', 'N/A')
                    device_id = record.get('device_id', 'N/A')
                    test_mode = record.get('test_mode', False)
                    
                    print(f"   📄 ID: {key[:10]}...")
                    print(f"      🕒 Timestamp: {timestamp}")
                    print(f"      🔧 Device: {device_id}")
                    print(f"      🧪 Test: {'Sí' if test_mode else 'No'}")
                    print()
                    
                return True
            else:
                print("📭 No hay datos en Firebase")
                return True
                
        else:
            print(f"❌ Error leyendo datos: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error leyendo datos: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Test de Conectividad Firebase")
    print("=" * 50)
    
    # Test 1: Conexión
    if not test_firebase_connection():
        print("💥 Falló la prueba de conexión - Abortando")
        return
    
    # Test 2: Escribir datos
    print("\n" + "="*30)
    if not send_test_data():
        print("⚠️  Falló el envío de datos")
    
    # Esperar un momento
    print("\n⏱️  Esperando 2 segundos...")
    time.sleep(2)
    
    # Test 3: Leer datos
    print("="*30)
    if not read_recent_data():
        print("⚠️  Falló la lectura de datos")
    
    print("="*50)
    print("🎉 Pruebas de Firebase completadas")

if __name__ == "__main__":
    main()