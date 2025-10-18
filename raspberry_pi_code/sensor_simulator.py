#!/usr/bin/env python3
"""
Simulador de sensores de acelerómetro para diferentes posturas
"""

import random
import json
from datetime import datetime

class PostureSensor:
    """Simula lecturas de acelerómetro para diferentes posturas"""
    
    # Rangos típicos para cada postura (X, Y, Z)
    POSTURAS = {
        "erguido": {
            "x_range": (-0.5, 0.5),
            "y_range": (-0.5, 0.5), 
            "z_range": (9.0, 10.5)  # Gravedad hacia abajo
        },
        "semi_inclinado": {
            "x_range": (-2.0, 2.0),
            "y_range": (2.0, 6.0),   # Inclinado hacia adelante
            "z_range": (6.0, 9.0)
        },
        "acostado": {
            "x_range": (-1.0, 1.0),
            "y_range": (8.5, 10.5),  # Gravedad hacia el lado
            "z_range": (-1.0, 1.0)
        }
    }
    
    def get_reading(self, postura="random"):
        """Genera lectura del acelerómetro para una postura específica"""
        
        if postura == "random":
            postura = random.choice(list(self.POSTURAS.keys()))
        
        if postura not in self.POSTURAS:
            raise ValueError(f"Postura '{postura}' no válida. Usa: {list(self.POSTURAS.keys())}")
        
        ranges = self.POSTURAS[postura]
        
        # Generar valores aleatorios dentro del rango
        x = round(random.uniform(*ranges["x_range"]), 3)
        y = round(random.uniform(*ranges["y_range"]), 3)
        z = round(random.uniform(*ranges["z_range"]), 3)
        
        return {
            "postura_detectada": postura,
            "accelerometer_x": x,
            "accelerometer_y": y,
            "accelerometer_z": z,
            "timestamp": datetime.now().isoformat()
        }
    
    def create_person_with_posture(self, nombre, genero, edad, postura="random"):
        """Crea datos completos de persona con postura simulada"""
        
        sensor_data = self.get_reading(postura)
        
        return {
            "nombre": nombre,
            "genero": genero,
            "edad": edad,
            "accelerometer_x": sensor_data["accelerometer_x"],
            "accelerometer_y": sensor_data["accelerometer_y"],
            "accelerometer_z": sensor_data["accelerometer_z"],
            "postura_detectada": sensor_data["postura_detectada"],
            "timestamp": sensor_data["timestamp"]
        }

def main():
    """Ejemplo de uso del simulador"""
    
    sensor = PostureSensor()
    
    print("🔬 Simulador de sensores de postura")
    print("=" * 40)
    
    # Generar lecturas para cada postura
    posturas = ["erguido", "semi_inclinado", "acostado"]
    
    for postura in posturas:
        print(f"\n📊 Postura: {postura.upper()}")
        reading = sensor.get_reading(postura)
        
        for key, value in reading.items():
            print(f"  {key}: {value}")
    
    # Crear persona con postura aleatoria
    print(f"\n👤 Persona con postura aleatoria:")
    person_data = sensor.create_person_with_posture(
        nombre="Juan Simulado",
        genero="Masculino", 
        edad=25
    )
    
    for key, value in person_data.items():
        print(f"  {key}: {value}")
    
    # Guardar en archivo JSON
    filename = f"person_simulated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(person_data, file, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Datos guardados en: {filename}")

if __name__ == "__main__":
    main()