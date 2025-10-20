# Estructura Corregida de Archivos Arduino

## 📁 Archivos Correctos del Sistema

### ✅ **Nuevos archivos con nombres correctos:**

1. **`sensor_brazo_periferico.ino`** - Sensor del BRAZO
   - Nombre BLE: `"Arduino_Brazo_Sensor"`
   - UUID Service: `"12345678-1234-1234-1234-123456789abc"`
   - UUID Characteristic: `"12654321-1321-1321-1321-1ba987654321"`
   - Device ID: `"arduino_brazo_001"`

2. **`sensor_pie_periferico.ino`** - Sensor del PIE
   - Nombre BLE: `"Arduino_Pie_Sensor"`
   - UUID Service: `"22345678-2234-2234-2234-223456789abc"`
   - UUID Characteristic: `"22654321-2321-2321-2321-2ba987654321"`
   - Device ID: `"arduino_pie_001"`

### ❌ **Archivos viejos para eliminar:**

- `arduino_Esclavo.ino` (nombre confuso, reemplazado por sensor_brazo_periferico.ino)
- `sensor _pie_periferico.ino` (nombre con espacio, reemplazado por sensor_pie_periferico.ino)

## 🔧 Cambios Realizados

### 1. **Nombres de Dispositivos BLE Corregidos:**
```cpp
// Sensor del BRAZO
BLE.setLocalName("Arduino_Brazo_Sensor");
BLE.setDeviceName("Arduino_Brazo_Sensor");

// Sensor del PIE
BLE.setLocalName("Arduino_Pie_Sensor");
BLE.setDeviceName("Arduino_Pie_Sensor");
```

### 2. **UUIDs Únicos por Sensor:**
```cpp
// BRAZO - UUIDs que empiezan con "1"
serviceUUID = "12345678-1234-1234-1234-123456789abc"
characteristicUUID = "12654321-1321-1321-1321-1ba987654321"

// PIE - UUIDs que empiezan con "2"  
serviceUUID = "22345678-2234-2234-2234-223456789abc"
characteristicUUID = "22654321-2321-2321-2321-2ba987654321"
```

### 3. **JSON Simplificado (sin análisis de posturas):**
```json
// Formato de datos enviados por ambos sensores
{
  "dev": "arduino_brazo_001",  // o "arduino_pie_001"
  "sensor": "brazo",           // o "pie"
  "ts": 1640995200000,
  "acc": {"x": 0.12, "y": -0.05, "z": 9.81},
  "gyr": {"x": 0.02, "y": -0.01, "z": 0.00}
}
```

## 🚀 Instrucciones de Carga

### **Paso 1: Cargar en Arduino #1 (BRAZO)**
1. Abrir `sensor_brazo_periferico.ino` en Arduino IDE
2. Seleccionar Arduino Nano 33 BLE
3. Cargar código
4. Verificar en Serial Monitor: "Arduino Sensor BRAZO - Periférico BLE"

### **Paso 2: Cargar en Arduino #2 (PIE)**
1. Abrir `sensor_pie_periferico.ino` en Arduino IDE
2. Seleccionar Arduino Nano 33 BLE
3. Cargar código
4. Verificar en Serial Monitor: "Arduino Sensor PIE - Periférico BLE"

### **Paso 3: Probar Conexión**
```bash
# En Raspberry Pi
cd raspberry_pi_code
python test_maestro.py

# Salida esperada:
# ✅ Encontrado sensor BRAZO: Arduino_Brazo_Sensor
# ✅ Encontrado sensor PIE: Arduino_Pie_Sensor
```

## 🔍 Indicadores LED

### **Sensor del BRAZO:**
- 🔴 **Rojo fijo**: Iniciando
- 🟢 **Verde fijo**: Advertising (esperando conexión)
- 🔵 **Azul fijo**: Conectado y enviando datos
- 🔴 **Rojo parpadeante**: Error IMU/BLE

### **Sensor del PIE:**
- 🔴 **Rojo fijo**: Iniciando  
- 🟢 **Verde fijo**: Advertising (esperando conexión)
- 🔵 **Azul fijo**: Conectado y enviando datos
- 🔴 **Rojo parpadeante**: Error IMU/BLE

## 📡 Correlación con Raspberry Pi

El maestro BLE en Raspberry Pi (`maestro_ble.py`) busca exactamente estos nombres:

```python
# En scan_devices()
if device.name == "Arduino_Brazo_Sensor":
    arm_device = device
elif device.name == "Arduino_Pie_Sensor":
    foot_device = device
```

## ✅ Verificación de Funcionamiento

### **1. Serial Monitor Arduino BRAZO:**
```
💪 Arduino Sensor BRAZO - Periférico BLE
✅ IMU inicializado correctamente
✅ BLE inicializado correctamente
🟢 BLE Advertising como: Arduino_Brazo_Sensor
📡 Esperando conexión del maestro...
```

### **2. Serial Monitor Arduino PIE:**
```
🦶 Arduino Sensor PIE - Periférico BLE  
✅ IMU inicializado correctamente
✅ BLE inicializado correctamente
🟢 BLE Advertising como: Arduino_Pie_Sensor
📡 Esperando conexión del maestro...
```

### **3. Al conectar Raspberry Pi:**
```
🔗 Conectado a maestro: XX:XX:XX:XX:XX:XX
📤 Enviado: {"dev":"arduino_brazo_001","sensor":"brazo",...}
```

## 🐛 Solución de Problemas

### **Si no se encuentran los sensores:**
1. Verificar que ambos Arduino muestren "🟢 BLE Advertising"
2. Reiniciar ambos Arduino
3. Verificar distancia (< 10 metros)
4. Probar escaneo manual: `python -c "import asyncio; from bleak import BleakScanner; asyncio.run(BleakScanner.discover())"`

### **Si hay errores de conexión:**
1. Verificar UUIDs únicos en cada sensor
2. Reiniciar servicio Bluetooth en Raspberry Pi
3. Cargar códigos de nuevo en Arduino

---

✅ **Sistema listo con archivos correctamente nombrados y configurados**