#!/usr/bin/env python3
"""
Script para Raspberry Pi - Envío de datos de personas a Firebase
Proyecto Microprocesadores - Sistema de Posturas
"""

import json
import time
import requests
from datetime import datetime
import random

# Configuración Firebase (usando REST API - más simple)
FIREBASE_URL = "https://proyecto-posturas-microp-default-rtdb.firebaseio.com"
FIREBASE_SECRET = None  # Si usas reglas abiertas no necesitas secret

class FirebaseSender:
    def __init__(self, firebase_url):
        self.firebase_url = firebase_url
        
    def send_person_data(self, person_data):
        """
        Envía datos de una persona a Firebase Realtime Database
        """
        try:
            # Agregar timestamp
            person_data['timestamp'] = datetime.now().isoformat()
            person_data['raspberry_id'] = 'raspberry_pi_001'
            
            # URL para agregar nueva persona
            url = f"{self.firebase_url}/persons.json"
            
            # Enviar datos
            response = requests.post(url, json=person_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Persona enviada exitosamente. ID: {result['name']}")
                return True, result['name']
            else:
                print(f"❌ Error al enviar datos: {response.status_code}")
                print(f"Response: {response.text}")
                return False, None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return False, None
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False, None

def load_person_from_json(file_path):
    """
    Carga datos de persona desde archivo JSON
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        # Validar campos requeridos
        required_fields = ['nombre', 'genero', 'edad', 'accelerometer_x', 'accelerometer_y', 'accelerometer_z']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Campo requerido faltante: {field}")
                
        return data
        
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error al decodificar JSON: {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error al cargar JSON: {e}")
        return None

def create_sample_data():
    """
    Crea datos de ejemplo con valores aleatorios del acelerómetro
    """
    nombres = ["Juan Pérez", "María García", "Carlos López", "Ana Martínez", "Luis Rodríguez"]
    generos = ["Masculino", "Femenino"]
    
    return {
        "nombre": random.choice(nombres),
        "genero": random.choice(generos),
        "edad": random.randint(18, 65),
        "accelerometer_x": round(random.uniform(-2.0, 2.0), 3),
        "accelerometer_y": round(random.uniform(-2.0, 2.0), 3),
        "accelerometer_z": round(random.uniform(8.0, 12.0), 3)  # Z suele ser ~9.8 (gravedad)
    }

def main():
    """
    Función principal
    """
    print("🚀 Iniciando envío de datos desde Raspberry Pi...")
    
    # Inicializar cliente Firebase
    firebase_client = FirebaseSender(FIREBASE_URL)
    
    # Opción 1: Cargar desde archivo JSON
    json_file = "person_data.json"
    person_data = load_person_from_json(json_file)
    
    # Opción 2: Si no hay archivo, crear datos de ejemplo
    if person_data is None:
        print("📝 Creando datos de ejemplo...")
        person_data = create_sample_data()
        
        # Guardar datos de ejemplo en archivo
        with open(json_file, 'w', encoding='utf-8') as file:
            json.dump(person_data, file, indent=2, ensure_ascii=False)
        print(f"📄 Datos guardados en {json_file}")
    
    # Mostrar datos a enviar
    print("\n📊 Datos a enviar:")
    for key, value in person_data.items():
        print(f"  {key}: {value}")
    
    # Enviar datos
    print("\n📡 Enviando datos a Firebase...")
    success, person_id = firebase_client.send_person_data(person_data)
    
    if success:
        print(f"🎉 ¡Datos enviados correctamente! ID: {person_id}")
    else:
        print("💥 Error al enviar datos")

def continuous_mode():
    """
    Modo continuo - envía datos cada X segundos (para simulación)
    """
    print("🔄 Modo continuo activado...")
    firebase_client = FirebaseSender(FIREBASE_URL)
    
    try:
        while True:
            # Crear datos aleatorios
            data = create_sample_data()
            
            print(f"\n📊 Enviando: {data['nombre']} - X:{data['accelerometer_x']} Y:{data['accelerometer_y']} Z:{data['accelerometer_z']}")
            
            success, person_id = firebase_client.send_person_data(data)
            
            if success:
                print(f"✅ Enviado con ID: {person_id}")
            else:
                print("❌ Error en envío")
            
            # Esperar 10 segundos
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo envío continuo...")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        continuous_mode()
    else:
        main()