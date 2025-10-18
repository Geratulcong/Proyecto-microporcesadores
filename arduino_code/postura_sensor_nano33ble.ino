/*
  Arduino Nano 33 BLE Sense - Acelerómetro + Bluetooth
  Proyecto Microprocesadores - Sistema de Posturas
  
  Envía datos del acelerómetro en formato JSON vía Bluetooth
  al Raspberry Pi para análisis de posturas corporales.
*/

#include <ArduinoBLE.h>
#include <Arduino_LSM9DS1.h>
#include <ArduinoJson.h>

// Configuración Bluetooth
BLEService sensorService("12345678-1234-1234-1234-123456789abc");
BLECharacteristic sensorCharacteristic("87654321-4321-4321-4321-cba987654321", BLERead | BLENotify, 512);

// Variables del acelerómetro
float accel_x, accel_y, accel_z;
unsigned long lastReading = 0;
const unsigned long readingInterval = 1000; // Enviar cada 1 segundo

// Variables para detección de postura
String currentPosture = "unknown";
String previousPosture = "unknown";

// ID único del dispositivo
String deviceID = "arduino_nano_33_ble_001";

void setup() {
  Serial.begin(9600);
  while (!Serial);
  
  Serial.println("🚀 Iniciando Arduino Nano 33 BLE Sense...");
  
  // Inicializar IMU (acelerómetro)
  if (!IMU.begin()) {
    Serial.println("❌ Error al inicializar IMU!");
    while (1);
  }
  Serial.println("✅ IMU inicializado correctamente");
  
  // Inicializar BLE
  if (!BLE.begin()) {
    Serial.println("❌ Error al inicializar BLE!");
    while (1);
  }
  
  // Configurar servicio BLE
  BLE.setLocalName("Arduino Postura Sensor");
  BLE.setAdvertisedService(sensorService);
  sensorService.addCharacteristic(sensorCharacteristic);
  BLE.addService(sensorService);
  
  // Iniciar advertising
  BLE.advertise();
  Serial.println("✅ Bluetooth iniciado - Esperando conexiones...");
  Serial.println("📡 Nombre del dispositivo: Arduino Postura Sensor");
  
  // LED integrado para indicar estado
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  // Verificar conexión BLE
  BLEDevice central = BLE.central();
  
  if (central) {
    Serial.print("📱 Conectado a: ");
    Serial.println(central.address());
    digitalWrite(LED_BUILTIN, HIGH); // LED encendido = conectado
    
    while (central.connected()) {
      unsigned long currentTime = millis();
      
      if (currentTime - lastReading >= readingInterval) {
        readAccelerometer();
        detectPosture();
        String jsonData = createJSON();
        sendData(jsonData);
        
        lastReading = currentTime;
      }
    }
    
    digitalWrite(LED_BUILTIN, LOW); // LED apagado = desconectado
    Serial.println("📱 Cliente desconectado");
  }
  
  // Parpadear LED cuando no está conectado
  digitalWrite(LED_BUILTIN, HIGH);
  delay(100);
  digitalWrite(LED_BUILTIN, LOW);
  delay(900);
}

void readAccelerometer() {
  if (IMU.accelerationAvailable()) {
    IMU.readAcceleration(accel_x, accel_y, accel_z);
    
    // Mostrar valores en Serial Monitor
    Serial.print("📊 Accel X: "); Serial.print(accel_x, 3);
    Serial.print(" | Y: "); Serial.print(accel_y, 3);
    Serial.print(" | Z: "); Serial.println(accel_z, 3);
  }
}

void detectPosture() {
  previousPosture = currentPosture;
  
  // Algoritmo simple de detección de postura basado en acelerómetro
  if (abs(accel_z) > 0.8 && abs(accel_x) < 0.5 && abs(accel_y) < 0.5) {
    currentPosture = "erguido";
  }
  else if (accel_y > 0.4 && accel_z > 0.3) {
    currentPosture = "semi_inclinado";
  }
  else if (abs(accel_y) > 0.8 && abs(accel_z) < 0.5) {
    currentPosture = "acostado";
  }
  else {
    currentPosture = "movimiento";
  }
  
  // Notificar cambio de postura
  if (currentPosture != previousPosture) {
    Serial.print("🔄 Cambio de postura: ");
    Serial.print(previousPosture);
    Serial.print(" → ");
    Serial.println(currentPosture);
  }
}

String createJSON() {
  // Crear objeto JSON con ArduinoJson library
  StaticJsonDocument<300> doc;
  
  doc["device_id"] = deviceID;
  doc["timestamp"] = millis();
  doc["accelerometer_x"] = round(accel_x * 1000.0) / 1000.0; // 3 decimales
  doc["accelerometer_y"] = round(accel_y * 1000.0) / 1000.0;
  doc["accelerometer_z"] = round(accel_z * 1000.0) / 1000.0;
  doc["postura_detectada"] = currentPosture;
  doc["battery_level"] = getBatteryLevel(); // Simulado
  doc["signal_strength"] = -50; // dBm simulado
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  return jsonString;
}

void sendData(String jsonData) {
  // Enviar por BLE
  sensorCharacteristic.writeValue(jsonData.c_str());
  
  // Mostrar en Serial Monitor
  Serial.print("📡 Enviado: ");
  Serial.println(jsonData);
  
  // Indicador visual
  digitalWrite(LED_BUILTIN, LOW);
  delay(50);
  digitalWrite(LED_BUILTIN, HIGH);
}

int getBatteryLevel() {
  // Simulación del nivel de batería (0-100%)
  // En un proyecto real, leerías el voltaje de la batería
  return random(80, 100);
}

void printWiFiStatus() {
  Serial.print("📶 Signal strength (RSSI): ");
  Serial.print("N/A");
  Serial.println(" dBm");
}