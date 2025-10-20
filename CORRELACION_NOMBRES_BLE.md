# 🔗 Correlación de Nombres BLE - Arduino ↔ Python

## 📊 Tabla de Correlación

| **Sensor** | **Arduino (LocalName)** | **Arduino (DeviceName)** | **Python (Búsqueda)** | **UUID Servicio** |
|------------|--------------------------|---------------------------|------------------------|-------------------|
| BRAZO      | `Arduino_Brazo_Sensor`   | `Arduino_Brazo_BLE`       | `Arduino_Brazo_Sensor` | `12345678-1234-1234-1234-123456789abc` |
| PIE        | `Arduino_Pie_Sensor`     | `Arduino_Pie_BLE`         | `Arduino_Pie_Sensor`   | `22345678-2234-2234-2234-223456789abc` |

## 🎯 Nombres Exactos Configurados

### Arduino del BRAZO (`sensor_brazo_periferico.ino`)
```cpp
BLE.setLocalName("Arduino_Brazo_Sensor");
BLE.setDeviceName("Arduino_Brazo_BLE");
```

### Arduino del PIE (`arduino_Esclavo.ino`)
```cpp
BLE.setLocalName("Arduino_Pie_Sensor");
BLE.setDeviceName("Arduino_Pie_BLE");
```

### Python Maestro (`maestro_ble.py`)
```python
# Búsqueda exacta prioritaria
if device.name == "Arduino_Brazo_Sensor":
    arm_device = device
elif device.name == "Arduino_Pie_Sensor":
    foot_device = device
```

## 🔍 Método de Identificación

El código Python usa **múltiples métodos** para identificar dispositivos:

### 1. **Identificación Exacta** (Prioritaria)
- Busca exactamente `Arduino_Brazo_Sensor`
- Busca exactamente `Arduino_Pie_Sensor`

### 2. **Identificación por UUID** (Secundaria)
- Brazo: `12345678-1234-1234-1234-123456789abc`
- Pie: `22345678-2234-2234-2234-223456789abc`

### 3. **Identificación por Palabras Clave** (Terciaria)
- Cualquier nombre que contenga "brazo", "arm" → Sensor BRAZO
- Cualquier nombre que contenga "pie", "foot" → Sensor PIE

## ✅ Verificación de Correlación

### En el Arduino (Serial Monitor)
Debes ver:
```
✅ BLE inicializado correctamente
🔵 Dispositivo BLE anunciándose...
📡 UUID Servicio: [UUID correspondiente]
📡 UUID Característica: [UUID correspondiente]
```

### En Python (Terminal)
Debes ver:
```
📱 Encontrado: Arduino_Brazo_Sensor - AA:BB:CC:DD:EE:FF
✅ Sensor BRAZO encontrado: AA:BB:CC:DD:EE:FF
📱 Encontrado: Arduino_Pie_Sensor - 11:22:33:44:55:66
✅ Sensor PIE encontrado: 11:22:33:44:55:66
```

## 🛠️ Comandos de Prueba

### Verificar Nombres de Dispositivos
```bash
# Escanear todos los dispositivos BLE
python -c "
import asyncio
from bleak import BleakScanner

async def scan():
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name and 'Arduino' in device.name:
            print(f'✅ {device.name} - {device.address}')

asyncio.run(scan())
"
```

### Probar Conexión Individual
```bash
# Probar con un Arduino
python raspberry_pi_code/prueba_simple.py
```

### Probar Sistema Completo
```bash
# Con ambos Arduino encendidos
python raspberry_pi_code/maestro_ble.py
```

## 🚨 Solución de Problemas

### ❌ "No se encontró sensor BRAZO/PIE"
1. **Verificar nombres en Arduino**:
   - Abrir Serial Monitor
   - Debe mostrar: `📡 Nombre: Arduino_Brazo_Sensor` (o `Arduino_Pie_Sensor`)

2. **Verificar código cargado correctamente**:
   - Asegurar que el código fue subido sin errores
   - Verificar que se seleccionó "Arduino Nano 33 BLE"

3. **Verificar escaneo BLE**:
   ```bash
   python -c "
   import asyncio
   from bleak import BleakScanner
   
   async def scan():
       devices = await BleakScanner.discover(timeout=15)
       print('Dispositivos encontrados:')
       for device in devices:
           print(f'  {device.name or \"Sin nombre\"} - {device.address}')
   
   asyncio.run(scan())
   "
   ```

### ❌ Nombres no coinciden
1. **Revisar exactamente los nombres**:
   - Arduino debe usar: `Arduino_Brazo_Sensor` / `Arduino_Pie_Sensor`
   - Python debe buscar: `Arduino_Brazo_Sensor` / `Arduino_Pie_Sensor`

2. **Verificar caracteres especiales**:
   - Usar guiones bajos (`_`) no espacios
   - No usar acentos ni caracteres especiales

3. **Recargar código si es necesario**:
   - Subir nuevamente el código Arduino
   - Reiniciar el Arduino (botón reset)

## 📋 Checklist Final

- [ ] Arduino BRAZO muestra `Arduino_Brazo_Sensor` en Serial Monitor
- [ ] Arduino PIE muestra `Arduino_Pie_Sensor` en Serial Monitor  
- [ ] Python encuentra exactamente estos nombres al escanear
- [ ] La prueba simple conecta exitosamente
- [ ] El sistema completo encuentra ambos sensores
- [ ] Los datos JSON llegan correctamente

¡Con esta correlación exacta, el sistema debería funcionar perfectamente! 🎉