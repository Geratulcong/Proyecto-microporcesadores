# 🔄 Nueva Arquitectura BLE - Raspberry Pi Maestro

## 📋 Resumen de Cambios

La arquitectura ha sido **invertida** para mejor eficiencia:

### ❌ Arquitectura Anterior (Problemática)
```
Sensor PIE (Periférico) → Arduino MAESTRO (Dual Central+Server) → Raspberry Pi (Client)
```
**Problemas**: Dual role BLE complejo, conflictos de conexión, límites de memoria Arduino

### ✅ Nueva Arquitectura (Optimizada) 
```
Arduino BRAZO (Periférico) ← Raspberry Pi MAESTRO (Central) → Arduino PIE (Periférico)
```
**Ventajas**: Cada Arduino es simple, Raspberry Pi maneja múltiples conexiones, mejor escalabilidad

## 📁 Archivos Nuevos

### 🐍 Python (Raspberry Pi)
- **`maestro_ble.py`** - Maestro BLE completo que se conecta a múltiples Arduino
- **`prueba_simple.py`** - Script de prueba para conectar un solo Arduino

### 🔧 Arduino (Nano 33 BLE Sense)
- **`sensor_brazo_periferico.ino`** - Arduino del brazo como periférico BLE
- **`arduino_Esclavo.ino`** - Arduino del pie como periférico BLE (actualizado)

## 🚀 Instrucciones de Uso

### Paso 1: Preparar los Arduino

1. **Cargar código en Arduino del BRAZO**:
   ```bash
   # Abrir Arduino IDE
   # Cargar: sensor_brazo_periferico.ino
   # Seleccionar: Arduino Nano 33 BLE
   # Subir código
   ```

2. **Cargar código en Arduino del PIE**:
   ```bash
   # Abrir Arduino IDE  
   # Cargar: arduino_Esclavo.ino
   # Seleccionar: Arduino Nano 33 BLE
   # Subir código
   ```

### Paso 2: Verificar Arduino

Cada Arduino debe mostrar en el Serial Monitor:
```
✅ IMU inicializada correctamente
✅ BLE inicializado correctamente  
🔵 Dispositivo BLE anunciándose...
📡 UUID Servicio: [UUID]
📡 UUID Característica: [UUID]
```

**LEDs de Estado**:
- 🔴 Rojo = Error o iniciando
- 🔵 Azul = Esperando conexión
- 🟢 Verde = Conectado al maestro

### Paso 3: Probar Conexión Simple

```bash
# Ejecutar prueba con UN Arduino encendido
python raspberry_pi_code/prueba_simple.py
```

**Salida esperada**:
```
🔍 Buscando Arduino BLE por 15s...
📱 Encontrado: Arduino Brazo Sensor - AA:BB:CC:DD:EE:FF
✅ Arduino encontrado: AA:BB:CC:DD:EE:FF
🔗 Conectando a AA:BB:CC:DD:EE:FF...
✅ ¡Conectado exitosamente!
📋 Servicios disponibles:
🔔 Notificaciones BRAZO activadas
📡 Recibiendo datos...
```

### Paso 4: Ejecutar Sistema Completo

```bash  
# Con AMBOS Arduino encendidos
python raspberry_pi_code/maestro_ble.py
```

**Salida esperada**:
```
🔍 Escaneando dispositivos BLE por 10s...
✅ Sensor BRAZO encontrado: AA:BB:CC:DD:EE:FF
✅ Sensor PIE encontrado: 11:22:33:44:55:66
🔗 Conectando al sensor BRAZO...
✅ Conectado al sensor BRAZO
🔗 Conectando al sensor PIE...  
✅ Conectado al sensor PIE
🎉 Todos los sensores conectados exitosamente!
📡 Recolectando datos...
```

## 🔧 UUIDs de los Servicios

### Arduino BRAZO
- **Servicio**: `12345678-1234-1234-1234-123456789abc`
- **Característica**: `87654321-4321-4321-4321-cba987654321`

### Arduino PIE  
- **Servicio**: `22345678-2234-2234-2234-223456789abc`
- **Característica**: `22654321-2321-2321-2321-2ba987654321`

## 📊 Formato de Datos JSON

### Arduino BRAZO
```json
{
  "id": "arduino_brazo_001",
  "type": "brazo", 
  "ts": 1234567890,
  "acc": {"x": 0.123, "y": -0.456, "z": 0.789},
  "gyr": {"x": 1.23, "y": -4.56, "z": 7.89},
  "ana": {
    "mov": 1.234,
    "ori": "neutral"
  }
}
```

### Arduino PIE
```json
{
  "id": "arduino_pie_001", 
  "type": "pie",
  "ts": 1234567890,
  "acc": {"x": 0.123, "y": -0.456, "z": 0.789},
  "gyr": {"x": 1.23, "y": -4.56, "z": 7.89}, 
  "ana": {
    "step": true,
    "balance": 0.567
  }
}
```

## 🛠️ Solución de Problemas

### ❌ "No se encontró ningún Arduino BLE"
1. Verificar que el Arduino esté encendido
2. Verificar que el código BLE esté cargado correctamente
3. Verificar Serial Monitor del Arduino (debe mostrar "🔵 Dispositivo BLE anunciándose...")
4. Asegurar que el Bluetooth esté habilitado en el PC/Raspberry Pi

### ❌ "Falló la conexión"
1. Verificar que solo un maestro intente conectarse
2. Reiniciar el Arduino (botón reset)
3. Verificar distancia (mantener <5 metros)
4. Verificar que no haya interferencias Bluetooth

### ❌ "No se pudo activar notificaciones"  
1. Verificar que los UUIDs coincidan entre Arduino y Python
2. Verificar que la característica tenga propiedad NOTIFY
3. Reiniciar conexión completa

### ❌ Datos no llegan
1. Verificar Serial Monitor del Arduino (debe mostrar "📤 Enviado: ...")
2. Verificar formato JSON válido
3. Verificar tamaño del JSON (<500 bytes)

## 🔄 Próximas Mejoras

1. **Reconexión automática** si se pierde la conexión
2. **Guardado en base de datos** (SQLite/Firebase)
3. **Interfaz web** para visualizar datos en tiempo real  
4. **Análisis avanzado** de posturas y movimientos
5. **Alertas** por malas posturas
6. **Histórico** de datos para análisis temporal

## 🎯 Comandos Rápidos

```bash
# Prueba rápida un Arduino
python raspberry_pi_code/prueba_simple.py

# Sistema completo
python raspberry_pi_code/maestro_ble.py

# Ver dispositivos BLE disponibles
python -c "import asyncio; from bleak import BleakScanner; asyncio.run(BleakScanner.discover())"

# Verificar dependencias
python -c "import bleak, json; print('✅ Todo OK')"
```