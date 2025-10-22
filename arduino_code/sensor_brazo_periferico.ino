/*
  Arduino Nano 33 BLE Sense - Sensor del BRAZO (PERIFÉRICO)
  Proyecto Microprocesadores - Sistema de Sensores Corporales
  
  Este Arduino actúa como PERIFÉRICO BLE simple que:
  - Lee datos de sus sensores (acelerómetro, giroscopio)  
  - Los envía vía BLE al Raspberry Pi (maestro central)
  - Formato JSON compacto para eficiencia BLE
*/

#include <ArduinoBLE.h>
#include <Arduino_LSM9DS1.h>
#include <ArduinoJson.h>

// Configuración BLE - UUIDs para el servicio del brazo
const char* serviceUUID = "12345678-1234-1234-1234-123456789abc";
const char* characteristicUUID = "12654321-1321-1321-1321-1ba987654321";

// Servicio y características BLE
BLEService sensorService(serviceUUID);
BLEStringCharacteristic sensorCharacteristic(characteristicUUID, BLERead | BLENotify, 512);
// Característica para recibir comandos de configuración
BLEStringCharacteristic configCharacteristic("12654321-1321-1321-1321-1ba987654322", BLEWrite, 64);

// Variables del sensor
float accel_x, accel_y, accel_z;
float gyro_x, gyro_y, gyro_z;

// Control de tiempo
unsigned long lastReading = 0;

// ⚡ CONFIGURACIÓN DE VELOCIDAD - Configurable dinámicamente via BLE
unsigned long readingInterval = 1000;  // Valor inicial: 1 segundo

// Valores predefinidos disponibles
const unsigned long ULTRA_FAST = 100;   // 0.1s - Ultra rápido (10 Hz)
const unsigned long VERY_FAST = 500;    // 0.5s - Muy rápido (2 Hz)  
const unsigned long FAST = 1000;        // 1.0s - Rápido (1 Hz)
const unsigned long NORMAL = 3000;      // 3.0s - Normal (0.33 Hz)
const unsigned long SLOW = 5000;        // 5.0s - Lento (0.2 Hz)

// ID único del dispositivo
String deviceID = "arduino_brazo_001";

void setup() {
  Serial.begin(9600);
  while (!Serial);
  
  Serial.println("💪 Arduino Sensor BRAZO - Periférico BLE");
  
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
  BLE.setLocalName("Arduino_Brazo_Sensor");
  BLE.setDeviceName("Arduino_Brazo_Sensor");
  
  // Configurar servicio BLE
  BLE.setAdvertisedService(sensorService);
  sensorService.addCharacteristic(sensorCharacteristic);
  sensorService.addCharacteristic(configCharacteristic);  // Agregar característica de configuración
  BLE.addService(sensorService);
  
  // Inicializar characteristics
  sensorCharacteristic.writeValue("Arduino BRAZO listo");
  configCharacteristic.writeValue("config_ready");
  
  // Comenzar advertising
  BLE.advertise();
  
  // LED verde = listo y advertising
  digitalWrite(LEDR, HIGH);
  digitalWrite(LEDG, LOW);
  digitalWrite(LEDB, HIGH);
  digitalWrite(LED_BUILTIN, HIGH);
  
  Serial.println("🟢 BLE Advertising como: Arduino_Brazo_Sensor");
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
      
      // Verificar si hay comandos de configuración
      if (configCharacteristic.written()) {
        handleConfigCommand();
      }
      
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

// Función para manejar comandos de configuración via BLE
void handleConfigCommand() {
  String command = configCharacteristic.value();
  Serial.print("📡 Comando recibido: ");
  Serial.println(command);
  
  // Procesar comando de intervalo: "interval:100" para 100ms
  if (command.startsWith("interval:")) {
    int newInterval = command.substring(9).toInt();
    
    // Validar rango (50ms mínimo, 10s máximo)
    if (newInterval >= 50 && newInterval <= 10000) {
      readingInterval = newInterval;
      Serial.print("⏱️ Intervalo actualizado a: ");
      Serial.print(readingInterval);
      Serial.println("ms");
      
      // Confirmar cambio
      String response = "interval_set:" + String(readingInterval);
      configCharacteristic.writeValue(response);
    } else {
      Serial.println("❌ Intervalo inválido (rango: 50-10000ms)");
      configCharacteristic.writeValue("error:invalid_interval");
    }
  }
  // Procesar comandos predefinidos
  else if (command == "ultra_fast") {
    readingInterval = ULTRA_FAST;
    Serial.println("⚡ Modo Ultra Rápido: 100ms");
    configCharacteristic.writeValue("mode:ultra_fast");
  }
  else if (command == "very_fast") {
    readingInterval = VERY_FAST;
    Serial.println("🔥 Modo Muy Rápido: 500ms");
    configCharacteristic.writeValue("mode:very_fast");
  }
  else if (command == "fast") {
    readingInterval = FAST;
    Serial.println("💨 Modo Rápido: 1000ms");
    configCharacteristic.writeValue("mode:fast");
  }
  else if (command == "normal") {
    readingInterval = NORMAL;
    Serial.println("📊 Modo Normal: 3000ms");
    configCharacteristic.writeValue("mode:normal");
  }
  else if (command == "slow") {
    readingInterval = SLOW;
    Serial.println("🐢 Modo Lento: 5000ms");
    configCharacteristic.writeValue("mode:slow");
  }
  else {
    Serial.println("❓ Comando desconocido");
    configCharacteristic.writeValue("error:unknown_command");
  }
}

void readAndSendSensorData() {
  // Leer IMU
  if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
    IMU.readAcceleration(accel_x, accel_y, accel_z);
    IMU.readGyroscope(gyro_x, gyro_y, gyro_z);
    
    // Crear JSON compacto para BLE
    StaticJsonDocument<256> doc;
    
    doc["dev"] = deviceID;
    doc["sensor"] = "brazo";
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
      shortDoc["sensor"] = "brazo";
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