# Sistema de Detección de Posturas
## Arduino Nano 33 BLE Sense + Raspberry Pi + Firebase + React

### 🏗️ Arquitectura del Sistema

```
Arduino Nano 33 BLE Sense
    ↓ (Bluetooth BLE)
Raspberry Pi
    ↓ (WiFi/Internet) 
Firebase Realtime Database
    ↓ (API REST)
Aplicación React (Web)
```

### 📱 Componentes

1. **Arduino Nano 33 BLE Sense**
   - Lee acelerómetro LSM9DS1
   - Detecta posturas (erguido, semi-inclinado, acostado)
   - Envía datos JSON vía Bluetooth BLE

2. **Raspberry Pi** 
   - Recibe datos Bluetooth del Arduino
   - Procesa y valida información
   - Envía a Firebase via REST API

3. **Firebase Realtime Database**
   - Almacena datos de personas y posturas
   - Sincronización en tiempo real
   - API REST para acceso desde web

4. **Aplicación React**
   - Interfaz web para visualizar datos
   - Formularios para registrar personas
   - Tablas con historial de posturas

### 🚀 Configuración Paso a Paso

#### Arduino Nano 33 BLE Sense:

1. **Instalar librerías en Arduino IDE:**
   ```
   - ArduinoBLE (v1.3.6+)
   - Arduino_LSM9DS1 (v1.1.0+) 
   - ArduinoJson (v6.21.3+)
   ```

2. **Cargar código:**
   ```bash
   # Abrir Arduino IDE
   # File > Open > arduino_code/postura_sensor_nano33ble.ino
   # Tools > Board > Arduino Nano 33 BLE
   # Upload
   ```

#### Raspberry Pi:

1. **Clonar repositorio:**
   ```bash
   git clone https://github.com/Geratulcong/Proyecto-microporcesadores.git
   cd Proyecto-microporcesadores
   git checkout Features/connection-to-arduino-via-BLE
   cd raspberry_pi_code
   ```

2. **Instalar dependencias:**
   ```bash
   chmod +x install_bluetooth.sh
   ./install_bluetooth.sh
   sudo reboot
   ```

3. **Ejecutar receptor:**
   ```bash
   python3 bluetooth_receiver.py
   ```

#### Aplicación Web:

1. **Instalar y ejecutar:**
   ```bash
   npm install
   npm start
   ```

2. **Acceder a:** http://localhost:3001/demos/admin-templates/datta-able/react/free/persons

### 📊 Formato de Datos

#### JSON del Arduino:
```json
{
  "device_id": "arduino_nano_33_ble_001",
  "timestamp": 123456789,
  "accelerometer_x": 0.245,
  "accelerometer_y": -0.832, 
  "accelerometer_z": 9.756,
  "postura_detectada": "erguido",
  "battery_level": 85,
  "signal_strength": -50
}
```

#### Datos en Firebase:
```json
{
  "nombre": "Arduino_Usuario_143052",
  "genero": "No especificado",
  "edad": 25,
  "accelerometer_x": 0.245,
  "accelerometer_y": -0.832,
  "accelerometer_z": 9.756,
  "postura_detectada": "erguido",
  "device_id": "arduino_nano_33_ble_001",
  "timestamp": "2024-10-18T14:30:52.123Z",
  "source": "arduino_nano_33_ble"
}
```

### 🔧 Troubleshooting

#### Arduino no se conecta:
- Verificar que esté en modo advertising (LED parpadeando)
- Reiniciar Arduino (botón reset)
- Verificar Serial Monitor (9600 baud)

#### Raspberry Pi no encuentra Arduino:
```bash
# Verificar Bluetooth activo
sudo systemctl status bluetooth

# Escanear dispositivos manualmente
bluetoothctl
power on
scan on
# Buscar "Arduino Postura Sensor"
```

#### Datos no llegan a Firebase:
- Verificar reglas de Firebase (deben permitir read/write)
- Comprobar conectividad: `ping firebase.google.com`
- Revisar logs en Raspberry Pi

### 📈 Algoritmo de Detección de Posturas

```cpp
// Basado en valores del acelerómetro (g = 9.8 m/s²)
if (|z| > 0.8 && |x| < 0.5 && |y| < 0.5) {
    postura = "erguido";        // Vertical, gravedad en Z
}
else if (y > 0.4 && z > 0.3) {
    postura = "semi_inclinado"; // Inclinado hacia adelante
}
else if (|y| > 0.8 && |z| < 0.5) {
    postura = "acostado";       // Horizontal, gravedad en Y
}
```

### 🔋 Optimización de Energía

- **Intervalo de envío:** 1 segundo (configurable)
- **BLE Low Energy:** Consumo mínimo en standby
- **Deep Sleep:** Implementable para mayor duración

### 📝 Próximas Mejoras

1. **Autenticación de usuarios** en la app web
2. **Calibración automática** del acelerómetro
3. **Alertas** por posturas incorrectas prolongadas
4. **Dashboard** con gráficos en tiempo real
5. **App móvil** complementaria