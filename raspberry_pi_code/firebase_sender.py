#!/usr/bin/env python3
"""
Servicio Firebase optimizado para datos del Arduino
Proyecto Microprocesadores - Sistema de Posturas
"""

import requests
import json
from datetime import datetime

class FirebaseSender:
    def __init__(self, firebase_url="https://proyecto-posturas-microp-default-rtdb.firebaseio.com"):
        self.firebase_url = firebase_url
    
    def update_person_sensors(self, person_id, sensor_data):
        """
        Actualiza solo los datos de sensores de una persona existente
        """
        try:
            # URL para actualizar persona específica
            url = f"{self.firebase_url}/persons/{person_id}.json"
            
            # Usar PATCH para actualizar solo campos específicos
            response = requests.patch(url, json=sensor_data, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Sensores actualizados para persona ID: {person_id}")
                return True
            else:
                print(f"❌ Error HTTP al actualizar: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión a Firebase: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado en Firebase: {e}")
            return False
        
    def send_person_data(self, person_data):
        """
        Envía datos de una persona a Firebase Realtime Database
        """
        try:
            # Agregar metadatos
            person_data['timestamp'] = datetime.now().isoformat()
            person_data['source'] = 'arduino_nano_33_ble'
            
            # URL para agregar nueva persona
            url = f"{self.firebase_url}/persons.json"
            
            # Enviar datos
            response = requests.post(url, json=person_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return True, result['name']
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                print(f"Response: {response.text}")
                return False, None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión a Firebase: {e}")
            return False, None
        except Exception as e:
            print(f"❌ Error inesperado en Firebase: {e}")
            return False, None
    
    def send_realtime_posture(self, posture_data):
        """
        Envía datos de postura en tiempo real
        """
        try:
            # URL para datos en tiempo real
            url = f"{self.firebase_url}/realtime_postures.json"
            
            # Agregar timestamp
            posture_data['timestamp'] = datetime.now().isoformat()
            
            response = requests.post(url, json=posture_data, timeout=5)
            
            if response.status_code == 200:
                return True, response.json()['name']
            else:
                return False, None
                
        except Exception as e:
            print(f"❌ Error enviando postura en tiempo real: {e}")
            return False, None