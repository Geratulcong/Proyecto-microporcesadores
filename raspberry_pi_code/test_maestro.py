#!/usr/bin/env python3
"""
Prueba del Sistema BLE Maestro con Firebase
Verifica la conectividad y funcionalidad del sistema completo

Autor: Sistema de Monitoreo de Posturas
Fecha: 2024
"""

import asyncio
import json
import requests
import time
from maestro_ble import BLESensorMaster, logger

def test_firebase_connection():
    """Prueba la conexión a Firebase"""
    firebase_url = "https://proyecto-posturas-microp-default-rtdb.firebaseio.com"
    
    logger.info("🔥 Probando conexión a Firebase...")
    
    try:
        # Probar lectura de datos existentes
        response = requests.get(f"{firebase_url}/test.json", timeout=10)
        logger.info(f"📡 Respuesta Firebase: {response.status_code}")
        
        # Probar escritura de datos de prueba
        test_data = {
            "timestamp": time.time(),
            "test": "conexion_exitosa",
            "sistema": "maestro_ble"
        }
        
        response = requests.put(
            f"{firebase_url}/test_maestro.json",
            data=json.dumps(test_data),
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("✅ Firebase: Conexión exitosa")
            return True
        else:
            logger.error(f"❌ Firebase: Error {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Firebase: Error de conexión - {e}")
        return False

async def test_ble_scanning():
    """Prueba el escaneo BLE"""
    logger.info("📡 Probando escaneo BLE...")
    
    master = BLESensorMaster()
    
    try:
        # Probar escaneo de dispositivos
        arm_device, foot_device = await master.scan_devices()
        
        if arm_device:
            logger.info(f"✅ Encontrado sensor BRAZO: {arm_device.name}")
        else:
            logger.warning("⚠️ No se encontró sensor del BRAZO")
            
        if foot_device:
            logger.info(f"✅ Encontrado sensor PIE: {foot_device.name}")
        else:
            logger.warning("⚠️ No se encontró sensor del PIE")
            
        return arm_device is not None and foot_device is not None
        
    except Exception as e:
        logger.error(f"❌ Error en escaneo BLE: {e}")
        return False

def check_dependencies():
    """Verifica las dependencias del sistema"""
    logger.info("📋 Verificando dependencias...")
    
    dependencies = {
        "bleak": False,
        "requests": False,
        "json": True,  # Módulo estándar
        "threading": True,  # Módulo estándar
        "asyncio": True,  # Módulo estándar
    }
    
    # Verificar bleak
    try:
        import bleak
        dependencies["bleak"] = True
        logger.info(f"✅ bleak: {getattr(bleak, '__version__', 'instalado')}")
    except ImportError:
        logger.error("❌ bleak: No instalado - pip install bleak")
    
    # Verificar requests
    try:
        import requests
        dependencies["requests"] = True
        logger.info(f"✅ requests: {getattr(requests, '__version__', 'instalado')}")
    except ImportError:
        logger.error("❌ requests: No instalado - pip install requests")
    
    all_ok = all(dependencies.values())
    logger.info(f"📦 Dependencias: {'✅ Completas' if all_ok else '❌ Faltantes'}")
    return all_ok

async def run_system_test():
    """Ejecuta pruebas completas del sistema"""
    logger.info("🧪 INICIANDO PRUEBAS DEL SISTEMA")
    logger.info("=" * 50)
    
    # 1. Verificar dependencias
    deps_ok = check_dependencies()
    if not deps_ok:
        logger.error("❌ Faltan dependencias críticas")
        return False
    
    # 2. Probar Firebase
    firebase_ok = test_firebase_connection()
    
    # 3. Probar BLE
    ble_ok = await test_ble_scanning()
    
    # 4. Resumen
    logger.info("=" * 50)
    logger.info("📋 RESUMEN DE PRUEBAS:")
    logger.info(f"   🔥 Firebase: {'✅ OK' if firebase_ok else '❌ FALLO'}")
    logger.info(f"   📡 BLE Scan: {'✅ OK' if ble_ok else '❌ FALLO'}")
    logger.info(f"   📦 Dependencias: {'✅ OK' if deps_ok else '❌ FALLO'}")
    
    all_tests_ok = firebase_ok and ble_ok and deps_ok
    
    if all_tests_ok:
        logger.info("🎉 SISTEMA LISTO PARA EJECUTAR")
        logger.info("💡 Para ejecutar: python maestro_ble.py")
    else:
        logger.error("⚠️ SISTEMA CON PROBLEMAS - Revisar errores arriba")
    
    return all_tests_ok

def show_help():
    """Muestra información de ayuda"""
    help_text = """
🚀 SISTEMA BLE MAESTRO - AYUDA

📋 COMANDOS DISPONIBLES:
   python test_maestro.py          - Ejecutar todas las pruebas
   python maestro_ble.py          - Ejecutar el sistema principal
   
🔧 REQUISITOS:
   - 2x Arduino Nano 33 BLE Sense
   - Códigos Arduino cargados: sensor_brazo_periferico.ino y arduino_Esclavo.ino
   - Python 3.7+ con bleak y requests
   - Conexión a internet para Firebase
   
📡 DISPOSITIVOS BLE ESPERADOS:
   - "Arduino_Brazo_Sensor" (UUID: 12345678-1234-1234-1234-123456789abc)
   - "Arduino_Pie_Sensor"   (UUID: 22345678-2234-2234-2234-223456789abc)
   
🔥 FIREBASE:
   - URL: https://proyecto-posturas-microp-default-rtdb.firebaseio.com
   - Estructura: /sensor_readings/{timestamp} y /personas/{id}
   
⚡ TROUBLESHOOTING:
   - Si falla BLE: Verificar que los Arduino estén encendidos y cerca
   - Si falla Firebase: Verificar conexión a internet
   - Si falla imports: pip install bleak requests
"""
    print(help_text)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        show_help()
    else:
        # Ejecutar pruebas
        asyncio.run(run_system_test())