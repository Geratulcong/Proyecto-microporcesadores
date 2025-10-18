# Librerías requeridas para Arduino Nano 33 BLE Sense
# Instalar desde el IDE de Arduino (Tools > Manage Libraries)

## Librerías principales:
1. **ArduinoBLE** (by Arduino) - v1.3.6 o superior
   - Para comunicación Bluetooth Low Energy
   
2. **Arduino_LSM9DS1** (by Arduino) - v1.1.0 o superior  
   - Para el acelerómetro/giroscopio integrado
   
3. **ArduinoJson** (by Benoit Blanchon) - v6.21.3 o superior
   - Para crear y parsear JSON

## Instalación paso a paso:

### En Arduino IDE:
1. Abrir Arduino IDE
2. Tools > Board > Arduino Mbed OS Nano Boards > Arduino Nano 33 BLE
3. Tools > Manage Libraries
4. Buscar e instalar cada librería mencionada arriba
5. File > Open > postura_sensor_nano33ble.ino
6. Upload al Arduino

## Conexiones físicas:
- **No se necesitan conexiones externas**
- El Arduino Nano 33 BLE Sense tiene todo integrado:
  - ✅ Acelerómetro LSM9DS1 (interno)
  - ✅ Bluetooth BLE (interno) 
  - ✅ LED RGB (interno)

## Configuración:
- **Puerto serie:** 9600 baud
- **Intervalo de envío:** 1 segundo (configurable)
- **Nombre BLE:** "Arduino Postura Sensor"