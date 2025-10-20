# Sistema BLE Maestro con Firebase Integration 🚀

## 📋 Descripción
Sistema de recolección de datos de sensores con arquitectura BLE invertida:
- **Raspberry Pi**: Actúa como maestro BLE y gestor de Firebase
- **Arduino Nano 33 BLE**: Actúan como periféricos BLE (sensores básicos)
- **Firebase**: Base de datos en tiempo real para almacenar datos de sensores

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Arduino       │────▶│   Raspberry Pi   │────▶│    Firebase     │
│   Brazo         │ BLE │   Maestro BLE    │HTTP │   Database      │
│   Periférico    │     │                  │     │                 │
└─────────────────┘     │                  │     └─────────────────┘
                        │                  │              ▲
┌─────────────────┐     │                  │              │
│   Arduino       │────▶│  - Escaneo BLE   │              │
│   Pie           │ BLE │  - Conexiones    │              │
│   Periférico    │     │  - Procesamiento │              │
└─────────────────┘     │  - Firebase API  │              │
                        └──────────────────┘              │
                                    │                     │
                        ┌──────────────────┐              │
                        │   Web Dashboard  │──────────────┘
                        │   (React/JS)     │
                        └──────────────────┘
```

## 📁 Archivos del Sistema

### 🔧 Raspberry Pi (Maestro BLE)
- `maestro_ble.py` - Aplicación principal del maestro BLE
- `test_maestro.py` - Script de pruebas del sistema
- `sender.py` - Script original de envío a Firebase (referencia)
- `sensor_simulator.py` - Simulador para pruebas

### 📟 Arduino (Periféricos BLE)
- `sensor_brazo_periferico.ino` - Sensor del brazo (Arduino_Brazo_Sensor)
- `arduino_Esclavo.ino` - Sensor del pie (Arduino_Pie_Sensor)

### 📚 Documentación
- `CORRELACION_NOMBRES_BLE.md` - Documentación de nombres correlacionados
- `README_Sistema_BLE.md` - Este archivo

## 🛠️ Configuración e Instalación

### 1. Preparación del Hardware

#### Arduino Nano 33 BLE Sense (x2)
```cpp
// Sensor del BRAZO - Cargar: sensor_brazo_periferico.ino
// Nombre BLE: "Arduino_Brazo_Sensor"
// UUID: 12345678-1234-1234-1234-123456789abc

// Sensor del PIE - Cargar: arduino_Esclavo.ino  
// Nombre BLE: "Arduino_Pie_Sensor"
// UUID: 22345678-2234-2234-2234-223456789abc
```

### 2. Instalación en Raspberry Pi
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python y pip
sudo apt install python3 python3-pip -y

# Instalar dependencias BLE
sudo apt install bluetooth bluez bluez-tools -y

# Instalar librerías Python
pip3 install bleak requests

# Verificar instalación
python3 -c "import bleak; print('Bleak OK')"
python3 -c "import requests; print('Requests OK')"
```

### 3. Configuración de Firebase
```python
# URL de Firebase (en maestro_ble.py)
FIREBASE_URL = "https://proyecto-posturas-microp-default-rtdb.firebaseio.com"

# Estructura de datos:
# /sensores/{timestamp} - Datos de sensores en tiempo real
# /personas/{person_id} - Información de personas/sesiones
```

## 🚀 Ejecución del Sistema

### 1. Pruebas del Sistema
```bash
# Ejecutar pruebas completas
python3 test_maestro.py

# Ver ayuda
python3 test_maestro.py --help
```

### 2. Ejecutar Sistema Principal
```bash
# Iniciar maestro BLE
python3 maestro_ble.py

# Salida esperada:
# 🚀 Iniciando Maestro BLE...
# 🔍 Escaneando dispositivos BLE...
# ✅ Encontrado: Arduino_Brazo_Sensor
# ✅ Encontrado: Arduino_Pie_Sensor
# 🔗 Conectando a Arduino_Brazo_Sensor...
# 🔗 Conectando a Arduino_Pie_Sensor...
# 🎉 Todos los sensores conectados exitosamente!
# 📡 Recolectando datos... Presiona Ctrl+C para salir
```

## 📊 Datos y Protocolo

### Formato de Datos BLE (JSON)
```json
// Desde Arduino Brazo
{
  "sensor": "brazo",
  "acc": {"x": 0.12, "y": -0.05, "z": 9.81},
  "gyr": {"x": 0.02, "y": -0.01, "z": 0.00},
  "timestamp": 1640995200000
}

// Desde Arduino Pie  
{
  "sensor": "pie",
  "acc": {"x": 0.15, "y": 0.02, "z": 9.75},
  "gyr": {"x": 0.01, "y": 0.03, "z": -0.02},
  "timestamp": 1640995200000
}
```

### Datos Enviados a Firebase
```json
// /sensor_readings/{timestamp}
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "raspberry_id": "raspberry_pi_maestro_001",
  "brazo": {
    "accel": {"x": 0.12, "y": -0.05, "z": 9.81},
    "gyro": {"x": 0.02, "y": -0.01, "z": 0.00}
  },
  "pie": {
    "accel": {"x": 0.15, "y": 0.02, "z": 9.75},
    "gyro": {"x": 0.01, "y": 0.03, "z": -0.02}
  },
  "session_id": "session_1640995200"
}

// /personas/{person_id}
{
  "nombre": "Usuario de Prueba",
  "genero": "No especificado", 
  "edad": 25,
  "session_start": "2024-01-15T10:00:00.000Z",
  "device_brazo": "Arduino_Brazo_Sensor",
  "device_pie": "Arduino_Pie_Sensor",
  "status": "sesion_activa"
}
```

## 🔧 Configuración Avanzada

### Parámetros del Sistema (maestro_ble.py)
```python
class BLESensorMaster:
    def __init__(self):
        # Configuración Firebase
        self.firebase_interval = 5  # Segundos entre envíos
        
        # Configuración BLE
        self.scan_timeout = 10.0    # Timeout de escaneo
        self.connection_timeout = 10.0  # Timeout de conexión
        
        # Nombres de dispositivos (DEBEN COINCIDIR)
        self.arm_device_name = "Arduino_Brazo_Sensor"
        self.foot_device_name = "Arduino_Pie_Sensor"
```

### UUIDs de Servicios BLE
```python
# Servicio del brazo
ARM_SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"

# Servicio del pie
FOOT_SERVICE_UUID = "22345678-2234-2234-2234-223456789abc"
```

## 🐛 Troubleshooting

### Problemas Comunes

#### 1. Arduino no encontrado
```bash
# Verificar que el Arduino esté encendido y el código cargado
# Verificar nombres en el código Arduino:
# - Arduino_Brazo_Sensor
# - Arduino_Pie_Sensor

# Probar escaneo manual
python3 -c "
import asyncio
from bleak import BleakScanner

async def scan():
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name:
            print(f'{device.name}: {device.address}')

asyncio.run(scan())
"
```

#### 2. Error de conexión BLE
```bash
# Reiniciar servicio Bluetooth
sudo systemctl restart bluetooth

# Verificar estado
sudo systemctl status bluetooth

# Limpiar caché BLE
sudo systemctl stop bluetooth
sudo rm -rf /var/lib/bluetooth/*
sudo systemctl start bluetooth
```

#### 3. Error de Firebase
```bash
# Probar conexión directa
curl -X GET "https://proyecto-posturas-microp-default-rtdb.firebaseio.com/test.json"

# Verificar conectividad
ping firebase.google.com
```

#### 4. Dependencias faltantes
```bash
# Reinstalar bleak
pip3 uninstall bleak
pip3 install bleak

# Verificar versión Python
python3 --version  # Debe ser >= 3.7

# Instalar requests
pip3 install requests
```

## 📈 Monitoreo y Estadísticas

### Logs del Sistema
```bash
# Durante ejecución verás:
📊 ESTADÍSTICAS DEL SISTEMA
   📈 Datos recibidos: 1250
   🔗 Brazo conectado: ✅
   🦶 Pie conectado: ✅  
   🔥 Último envío Firebase: 3s atrás
──────────────────────────────────────────────────
```

### Verificar Datos en Firebase
```bash
# Ver datos recientes
curl "https://proyecto-posturas-microp-default-rtdb.firebaseio.com/sensores.json?orderBy=\"\$key\"&limitToLast=5"

# Ver personas registradas  
curl "https://proyecto-posturas-microp-default-rtdb.firebaseio.com/personas.json"
```

## 🔄 Flujo de Datos Completo

1. **Arduino Periféricos** → Leen sensores IMU cada 100ms
2. **BLE Broadcasting** → Envían datos JSON básicos via BLE characteristics  
3. **Raspberry Pi Maestro** → Escanea, conecta y lee datos BLE
4. **Recolección de Datos** → Combina datos de ambos sensores
5. **Firebase Integration** → Envía datos cada 5 segundos
6. **Web Dashboard** → Consume datos de Firebase en tiempo real

## 📚 Referencias

- [Documentación Arduino BLE](https://www.arduino.cc/en/Reference/ArduinoBLE)
- [Bleak Documentation](https://bleak.readthedocs.io/)
- [Firebase REST API](https://firebase.google.com/docs/reference/rest/database)
- [Correlación de Nombres BLE](./CORRELACION_NOMBRES_BLE.md)

## 🤝 Contribución

Para modificar el sistema:

1. **Cambiar intervalos de envío**: Modificar `firebase_interval` en `maestro_ble.py`
2. **Agregar sensores**: Actualizar UUIDs y lógica de escaneo
3. **Modificar datos Firebase**: Cambiar métodos `send_sensor_data()` y `send_person_data()`
4. **Debugging**: Usar `test_maestro.py` para pruebas individuales

---

**✅ Sistema listo para producción con arquitectura BLE invertida y integración Firebase completa**