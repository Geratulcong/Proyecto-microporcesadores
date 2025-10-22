/*
  Arduino Nano 33 BLE Sense - Sensor del PIE (PERIFÉRICO)
  Proyecto Microprocesadores - Sistema de Sensores Corporales
  
  Este Arduino actúa como PERIFÉRICO BLE simple que:
  - Lee datos de sus sensores (acelerómetro, giroscopio)  
  - Los envía vía BLE al Raspberry Pi (maestro central)
  - Formato JSON compacto para eficiencia BLE
*/

#include <ArduinoBLE.h>
#include <Arduino_LSM9DS1.h>
#include <ArduinoJson.h>

// Configuración BLE - UUIDs para el servicio del pie
const char* serviceUUID = "22345678-2234-2234-2234-223456789abc";
const char* characteristicUUID = "22654321-2321-2321-2321-2ba987654321";

// Servicio y característica BLE
BLEService sensorService(serviceUUID);
BLEStringCharacteristic sensorCharacteristic(characteristicUUID, BLERead | BLENotify, 512);

// Variables del sensor
float accel_x, accel_y, accel_z;
float gyro_x, gyro_y, gyro_z;

// Control de tiempo
unsigned long lastReading = 0;

// ⚡ CONFIGURACIÓN DE VELOCIDAD - Selecciona el intervalo que necesites:

// DESCOMENTA UNA de estas líneas según la velocidad que necesites:
unsigned long readingInterval = 300;   // ⚡ ULTRA RÁPIDO: 0.1s (10 lecturas/segundo)

// ID único del dispositivo
String deviceID = "arduino_pie_001";

void setup() {
  Serial.begin(9600);
  while (!Serial);
  
  Serial.println("🦶 Arduino Sensor PIE - Periférico BLE");
  
  // Configurar LEDs para indicadores de estado
  pinMode(LEDR, OUTPUT);
  pinMode(LEDG, OUTPUT);
  pinMode(LEDB, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  
  // LED rojo = iniciando
  digitalWrite(LEDR, LOW);
  digitalWrite(LEDG, HIGH);
  digitalWrite(LEDB, HIGH);
  digitalWrite(LED_BUILTIN, LOW);
  
  // Inicializar IMU
  if (!IMU.begin()) {
    Serial.println("❌ Error al inicializar IMU!");
    // LED rojo parpadeante = error
    while (1) {
      digitalWrite(LEDR, LOW);
      delay(200);
      digitalWrite(LEDR, HIGH);
      delay(200);
    }
  }
  Serial.println("✅ IMU inicializado correctamente");
  
  // Inicializar BLE
  if (!BLE.begin()) {
    Serial.println("❌ Error al inicializar BLE!");
    while (1) {
      digitalWrite(LEDR, LOW);
      delay(100);
      digitalWrite(LEDR, HIGH);
      delay(100);
    }
  }
  
  Serial.println("✅ BLE inicializado correctamente");
  
  // Configurar nombre del dispositivo BLE - DEBE COINCIDIR CON EL NOMBRE EN RASPBERRY PI
  BLE.setLocalName("Arduino_Pie_Sensor");
  BLE.setDeviceName("Arduino_Pie_Sensor");
  
  // Configurar servicio BLE
  BLE.setAdvertisedService(sensorService);
  sensorService.addCharacteristic(sensorCharacteristic);
  BLE.addService(sensorService);
  
  // Inicializar characteristic
  sensorCharacteristic.writeValue("Arduino PIE listo");
  
  // Comenzar advertising
  BLE.advertise();
  
  // LED verde = listo y advertising
  digitalWrite(LEDR, HIGH);
  digitalWrite(LEDG, LOW);
  digitalWrite(LEDB, HIGH);
  digitalWrite(LED_BUILTIN, HIGH);
  
  Serial.println("🟢 BLE Advertising como: Arduino_Pie_Sensor");
  Serial.println("📡 Esperando conexión del maestro...");
}

void loop() {
  // Verificar si hay un dispositivo central conectado
  BLEDevice central = BLE.central();
  
  if (central) {
    Serial.print("🔗 Conectado a maestro: ");
    Serial.println(central.address());
    
    // LED azul = conectado
    digitalWrite(LEDR, HIGH);
    digitalWrite(LEDG, HIGH);
    digitalWrite(LEDB, LOW);
    digitalWrite(LED_BUILTIN, HIGH);
    
    // Mientras esté conectado, enviar datos
    while (central.connected()) {
      unsigned long currentTime = millis();
      
      // Enviar datos según el intervalo configurado
      if (currentTime - lastReading >= readingInterval) {
        readAndSendSensorData();
        lastReading = currentTime;
      }
      
      // Parpadear LED para mostrar actividad
      digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
      delay(100);
    }
    
    // Desconectado
    Serial.println("📴 Maestro desconectado");
    
    // LED verde = advertising de nuevo
    digitalWrite(LEDR, HIGH);
    digitalWrite(LEDG, LOW);
    digitalWrite(LEDB, HIGH);
    digitalWrite(LED_BUILTIN, HIGH);
  }
  
  delay(100);
}

void readAndSendSensorData() {
  // Leer IMU
  if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
    IMU.readAcceleration(accel_x, accel_y, accel_z);
    IMU.readGyroscope(gyro_x, gyro_y, gyro_z);
    
    // Crear JSON compacto para BLE
    StaticJsonDocument<256> doc;
    
    doc["dev"] = deviceID;
    doc["sensor"] = "pie";
    doc["ts"] = millis();
    
    // Datos del acelerómetro (nombres cortos para eficiencia BLE)
    JsonObject accel = doc.createNestedObject("acc");
    accel["x"] = round(accel_x * 100) / 100.0; // 2 decimales
    accel["y"] = round(accel_y * 100) / 100.0;
    accel["z"] = round(accel_z * 100) / 100.0;
    
    // Datos del giroscopio
    JsonObject gyro = doc.createNestedObject("gyr");
    gyro["x"] = round(gyro_x * 100) / 100.0; // 2 decimales
    gyro["y"] = round(gyro_y * 100) / 100.0;
    gyro["z"] = round(gyro_z * 100) / 100.0;
    
    // Datos básicos del sensor solamente
    
    // Convertir a string
    String jsonString;
    serializeJson(doc, jsonString);
    
    // Verificar tamaño (límite BLE ~500 bytes)
    if (jsonString.length() < 500) {
      // Enviar vía BLE
      sensorCharacteristic.writeValue(jsonString);
      
      // Debug en Serial
      Serial.print("📤 Enviado: ");
      Serial.println(jsonString);
    } else {
      // JSON muy largo, enviar versión reducida
      StaticJsonDocument<128> shortDoc;
      shortDoc["dev"] = deviceID;
      shortDoc["sensor"] = "pie";
      shortDoc["ts"] = millis();
      shortDoc["ax"] = round(accel_x * 10) / 10.0;
      shortDoc["ay"] = round(accel_y * 10) / 10.0;
      shortDoc["az"] = round(accel_z * 10) / 10.0;
      shortDoc["gx"] = round(gyro_x * 10) / 10.0;
      shortDoc["gy"] = round(gyro_y * 10) / 10.0;
      shortDoc["gz"] = round(gyro_z * 10) / 10.0;
      
      String jsonString;
      serializeJson(shortDoc, jsonString);
      
      sensorCharacteristic.writeValue(jsonString);
      
      Serial.print("📤 Enviado (reducido): ");
      Serial.println(jsonString);
    }
  } else {
    Serial.println("⚠️ IMU no disponible");
  }
}

// Funciones de análisis removidas - solo datos básicos de sensores