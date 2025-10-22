# Nueva Estructura de Datos del Sensor

## Descripción

El sistema ahora **agrega** las lecturas del sensor como un historial dentro de cada persona, en lugar de sobrescribir los datos existentes.

## Estructura de Firebase

```json
{
  "persons": {
    "persona_id_1": {
      "nombre": "Juan Pérez",
      "edad": 25,
      "genero": "masculino",
      "es_activa": true,
      "last_sensor_update": "2025-10-22T10:30:00.000Z",
      "sensor_readings": {
        "reading_id_1": {
          "timestamp": "2025-10-22T10:30:00.000Z",
          "raspberry_timestamp": "2025-10-22T10:30:00.000Z",
          "arduino_timestamp": 12345678,
          "device_id": "brazo_sensor",
          "sensor_type": "brazo",
          "accelerometer": {
            "x": 0.25,
            "y": -0.15,
            "z": 9.81
          },
          "gyroscope": {
            "x": 0.02,
            "y": 0.01,
            "z": 0.03
          }
        },
        "reading_id_2": {
          "timestamp": "2025-10-22T10:30:03.000Z",
          "raspberry_timestamp": "2025-10-22T10:30:03.000Z",
          "arduino_timestamp": 12345681,
          "device_id": "brazo_sensor",
          "sensor_type": "brazo",
          "accelerometer": {
            "x": 0.28,
            "y": -0.12,
            "z": 9.79
          },
          "gyroscope": {
            "x": 0.03,
            "y": 0.02,
            "z": 0.01
          }
        }
      }
    }
  }
}
```

## Cambios Principales

### 1. Método `add_sensor_reading_to_person`
- **Antes**: `update_person_sensor_data` (sobrescribía datos)
- **Ahora**: `add_sensor_reading_to_person` (agrega nuevas lecturas)

### 2. Estructura de Datos
- **Antes**: Campos del sensor directamente en la persona
- **Ahora**: Array `sensor_readings` con historial completo

### 3. URL de Firebase
- **Antes**: `/persons/{person_id}.json` (PATCH)
- **Ahora**: `/persons/{person_id}/sensor_readings.json` (POST)

## Ventajas del Nuevo Sistema

1. **Historial Completo**: Mantiene todas las lecturas del sensor
2. **No Pérdida de Datos**: Cada lectura se conserva individualmente
3. **Análisis Temporal**: Permite estudiar cambios en el tiempo
4. **Escalabilidad**: Fácil agregar más tipos de sensores

## Estadísticas

El sistema ahora muestra:
- Número total de datos recibidos por BLE
- Número de lecturas guardadas en Firebase
- Estado de conexión y persona activa

## Uso

```bash
# Ejecutar el script normalmente
python maestro_brazo_ble.py

# Con parámetros personalizados
python maestro_brazo_ble.py --firebase_interval 5 --scan_timeout 20 --debug
```

## Verificación de Datos

Para verificar que los datos se están guardando correctamente:

1. Ve al monitor web
2. Selecciona una persona activa
3. Ejecuta el script del brazo
4. Las lecturas se agregarán automáticamente al historial de esa persona