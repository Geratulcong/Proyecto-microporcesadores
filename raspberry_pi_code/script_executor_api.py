"""
API para ejecutar scripts Python específicos en Raspberry Pi desde la web
Proyecto Microprocesadores - Ejecución Remota de Scripts
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import threading
import time
import os
import json
import logging
from datetime import datetime

# Configuración logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)
CORS(app)

# Estado global de procesos
running_processes = {}
script_outputs = {}

# Directorio base para scripts
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

class ScriptRunner:
    def __init__(self, script_name, script_path, args=None):
        self.script_name = script_name
        self.script_path = script_path
        self.args = args or []
        self.process = None
        self.output = []
        self.is_running = False
        self.start_time = None
        self.end_time = None
        self.exit_code = None
        
    def start(self):
        """Iniciar ejecución del script"""
        try:
            cmd = ['python3', self.script_path] + self.args
            logger.info(f"🚀 Ejecutando: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.is_running = True
            self.start_time = datetime.now()
            
            # Hilo para leer output
            threading.Thread(target=self._read_output, daemon=True).start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error iniciando script: {e}")
            self.output.append(f"ERROR: {str(e)}")
            return False
    
    def _read_output(self):
        """Leer output del proceso en tiempo real"""
        try:
            while True:
                line = self.process.stdout.readline()
                if not line:
                    break
                    
                line = line.strip()
                if line:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.output.append(f"[{timestamp}] {line}")
                    
            # Esperar a que termine el proceso
            self.exit_code = self.process.wait()
            self.is_running = False
            self.end_time = datetime.now()
            
            logger.info(f"✅ Script terminado con código: {self.exit_code}")
            
        except Exception as e:
            logger.error(f"❌ Error leyendo output: {e}")
            self.output.append(f"ERROR leyendo output: {str(e)}")
            self.is_running = False
    
    def stop(self):
        """Detener ejecución del script"""
        if self.process and self.is_running:
            try:
                self.process.terminate()
                time.sleep(2)
                if self.process.poll() is None:
                    self.process.kill()
                
                self.is_running = False
                self.end_time = datetime.now()
                self.output.append("SCRIPT DETENIDO POR EL USUARIO")
                logger.info("🛑 Script detenido por el usuario")
                return True
                
            except Exception as e:
                logger.error(f"❌ Error deteniendo script: {e}")
                return False
        return False
    
    def get_status(self):
        """Obtener estado del script"""
        duration = None
        if self.start_time:
            end = self.end_time or datetime.now()
            duration = str(end - self.start_time).split('.')[0]
            
        return {
            'script_name': self.script_name,
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': duration,
            'exit_code': self.exit_code,
            'output_lines': len(self.output),
            'last_output': self.output[-1] if self.output else None
        }

# === SCRIPTS DISPONIBLES ===
AVAILABLE_SCRIPTS = {
    'bluetooth_receiver': {
        'name': 'Receptor Bluetooth',
        'description': 'Script principal para recibir datos del Arduino',
        'file': 'test_receiver.py',
        'icon': '📡',
        'parameters': {
            'timeout': {
                'type': 'number',
                'description': 'Tiempo límite de conexión (segundos)',
                'default': 30,
                'min': 10,
                'max': 120
            },
            'debug': {
                'type': 'boolean',
                'description': 'Activar modo debug',
                'default': False
            }
        }
    },
    'bluetooth_maestro': {
        'name': 'Maestro BLE',
        'description': 'Maestro BLE que se conecta a múltiples Arduino',
        'file': 'maestro_ble.py',
        'icon': '🎛️',
        'parameters': {
            'scan_timeout': {
                'type': 'number',
                'description': 'Tiempo de escaneo BLE (segundos)',
                'default': 10,
                'min': 5,
                'max': 60
            },
            'firebase_interval': {
                'type': 'number',
                'description': 'Intervalo de envío a Firebase (segundos)',
                'default': 0.3,
                'min': 0.1,
                'max': 0.5,
                'step': 0.1
            },
            'debug': {
                'type': 'boolean',
                'description': 'Activar modo debug',
                'default': False
            }
        }
    },
    'maestro_brazo_ble': {
        'name': 'Maestro BLE Solo Brazo',
        'description': 'Conectar solo sensor del brazo',
        'file': 'maestro_brazo_ble.py',
        'icon': '🦾',
        'parameters': {
            'scan_timeout': {
                'type': 'number',
                'description': 'Tiempo de escaneo BLE (segundos)',
                'default': 15,
                'min': 5,
                'max': 60
            },
            'firebase_interval': {
                'type': 'number',
                'description': 'Intervalo de envío a Firebase (segundos)',
                'default': 0.3,
                'min': 0.1,
                'max': 0.5,
                'step': 0.1
            },
            'debug': {
                'type': 'boolean',
                'description': 'Activar modo debug',
                'default': False
            }
        }
    },
    'bluetooth_scan': {
        'name': 'Escaneo BLE',
        'description': 'Escanear dispositivos Bluetooth disponibles',
        'file': 'scan_devices.py',
        'icon': '🔍',
        'parameters': {
            'timeout': {
                'type': 'number',
                'description': 'Duración del escaneo (segundos)',
                'default': 10,
                'min': 3,
                'max': 30
            },
            'show_all': {
                'type': 'boolean',
                'description': 'Mostrar todos los dispositivos (no solo Arduino)',
                'default': False
            }
        }
    },
    'test_firebase': {
        'name': 'Test Firebase',
        'description': 'Probar conexión a Firebase',
        'file': 'test_firebase.py', 
        'icon': '🔥',
        'parameters': {
            'test_mode': {
                'type': 'select',
                'description': 'Tipo de prueba',
                'options': ['read', 'write', 'both'],
                'default': 'both'
            },
            'data_count': {
                'type': 'number',
                'description': 'Cantidad de datos de prueba',
                'default': 5,
                'min': 1,
                'max': 20
            }
        }
    },
    'test_parametros': {
        'name': 'Test Parámetros',
        'description': 'Demostración de parámetros configurables desde web',
        'file': 'test_parametros.py',
        'icon': '🎛️',
        'parameters': {
            'mensaje': {
                'type': 'text',
                'description': 'Mensaje personalizado a mostrar',
                'default': 'Hola desde Raspberry Pi'
            },
            'repeticiones': {
                'type': 'number',
                'description': 'Número de veces que se repetirá el mensaje',
                'default': 5,
                'min': 1,
                'max': 20
            },
            'intervalo': {
                'type': 'number',
                'description': 'Intervalo entre mensajes (segundos)',
                'default': 0.3,
                'min': 0.1,
                'max': 0.5,
                'step': 0.1
            },
            'formato_json': {
                'type': 'boolean',
                'description': 'Mostrar salida en formato JSON',
                'default': False
            },
            'incluir_timestamp': {
                'type': 'boolean',
                'description': 'Incluir timestamp en cada mensaje',
                'default': True
            },
            'tipo_salida': {
                'type': 'select',
                'description': 'Formato de la salida',
                'options': ['simple', 'detallado', 'compacto'],
                'default': 'simple'
            }
        }
    }
}

# === ENDPOINTS DE LA API ===

@app.route('/api/scripts', methods=['GET'])
def get_available_scripts():
    """Obtener lista de scripts disponibles"""
    try:
        scripts_info = []
        for script_id, info in AVAILABLE_SCRIPTS.items():
            script_path = os.path.join(SCRIPTS_DIR, info['file'])
            exists = os.path.exists(script_path)
            
            scripts_info.append({
                'id': script_id,
                'name': info['name'],
                'description': info['description'],
                'icon': info['icon'],
                'file': info['file'],
                'exists': exists,
                'is_running': script_id in running_processes and running_processes[script_id].is_running,
                'parameters': info.get('parameters', {})
            })
        
        return jsonify({
            'success': True,
            'scripts': scripts_info,
            'count': len(scripts_info)
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo scripts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scripts/<script_id>/start', methods=['POST'])
def start_script(script_id):
    """Iniciar un script específico"""
    try:
        if script_id not in AVAILABLE_SCRIPTS:
            return jsonify({
                'success': False,
                'error': f'Script {script_id} no encontrado'
            }), 404
        
        # Verificar si ya está ejecutándose
        if script_id in running_processes and running_processes[script_id].is_running:
            return jsonify({
                'success': False,
                'error': 'Script ya está ejecutándose'
            }), 400
        
        # Obtener parámetros del request
        data = request.get_json() or {}
        
        # Procesar diferentes tipos de parámetros
        params = data.get('parameters', {})
        args_list = data.get('args', [])
        
        # Convertir parámetros a argumentos de línea de comandos
        processed_args = []
        
        # Agregar argumentos simples (lista)
        processed_args.extend(args_list)
        
        # Agregar parámetros con nombre (diccionario)
        for key, value in params.items():
            if isinstance(value, bool):
                if value:  # Solo agregar flags que son True
                    processed_args.append(f"--{key}")
            elif isinstance(value, (str, int, float)):
                # Usar formato --key=value para evitar problemas con valores que comienzan con guión
                processed_args.append(f"--{key}={str(value)}")
            elif isinstance(value, list):
                # Para listas, agregar múltiples valores
                for item in value:
                    processed_args.append(f"--{key}={str(item)}")
        
        # Crear y ejecutar script
        script_info = AVAILABLE_SCRIPTS[script_id]
        script_path = os.path.join(SCRIPTS_DIR, script_info['file'])
        
        if not os.path.exists(script_path):
            return jsonify({
                'success': False,
                'error': f'Archivo {script_info["file"]} no encontrado'
            }), 404
        
        runner = ScriptRunner(script_info['name'], script_path, processed_args)
        
        if runner.start():
            running_processes[script_id] = runner
            
            return jsonify({
                'success': True,
                'message': f'Script {script_info["name"]} iniciado',
                'script_id': script_id,
                'status': runner.get_status()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo iniciar el script'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error iniciando script: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scripts/<script_id>/stop', methods=['POST'])
def stop_script(script_id):
    """Detener un script específico"""
    try:
        if script_id not in running_processes:
            return jsonify({
                'success': False,
                'error': 'Script no está ejecutándose'
            }), 400
        
        runner = running_processes[script_id]
        
        if runner.stop():
            return jsonify({
                'success': True,
                'message': f'Script {runner.script_name} detenido',
                'status': runner.get_status()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo detener el script'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error deteniendo script: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scripts/<script_id>/status', methods=['GET'])
def get_script_status(script_id):
    """Obtener estado de un script"""
    try:
        if script_id not in running_processes:
            return jsonify({
                'success': True,
                'status': {
                    'script_name': AVAILABLE_SCRIPTS.get(script_id, {}).get('name', script_id),
                    'is_running': False
                }
            })
        
        runner = running_processes[script_id]
        
        return jsonify({
            'success': True,
            'status': runner.get_status()
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scripts/<script_id>/output', methods=['GET'])
def get_script_output(script_id):
    """Obtener output de un script"""
    try:
        if script_id not in running_processes:
            return jsonify({
                'success': False,
                'error': 'Script no encontrado en procesos activos'
            }), 404
        
        runner = running_processes[script_id]
        
        # Parámetros de paginación
        start_line = request.args.get('start', 0, type=int)
        max_lines = request.args.get('lines', 100, type=int)
        
        output_slice = runner.output[start_line:start_line + max_lines]
        
        return jsonify({
            'success': True,
            'output': output_slice,
            'total_lines': len(runner.output),
            'start_line': start_line,
            'has_more': len(runner.output) > start_line + max_lines,
            'status': runner.get_status()
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo output: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scripts/running', methods=['GET'])
def get_running_scripts():
    """Obtener todos los scripts en ejecución"""
    try:
        running = []
        for script_id, runner in running_processes.items():
            if runner.is_running:
                status = runner.get_status()
                status['script_id'] = script_id
                running.append(status)
        
        return jsonify({
            'success': True,
            'running_scripts': running,
            'count': len(running)
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo scripts en ejecución: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scripts/stop-all', methods=['POST'])
def stop_all_scripts():
    """Detener todos los scripts"""
    try:
        stopped = []
        errors = []
        
        for script_id, runner in running_processes.items():
            if runner.is_running:
                try:
                    if runner.stop():
                        stopped.append(script_id)
                    else:
                        errors.append(script_id)
                except Exception as e:
                    errors.append(f"{script_id}: {str(e)}")
        
        return jsonify({
            'success': len(errors) == 0,
            'stopped': stopped,
            'errors': errors,
            'message': f'Detenidos {len(stopped)} scripts'
        })
        
    except Exception as e:
        logger.error(f"❌ Error deteniendo todos los scripts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# === PUNTO DE ENTRADA ===

if __name__ == '__main__':
    logger.info("🚀 Iniciando API de Ejecución de Scripts Python")
    logger.info("📁 Directorio de scripts: " + SCRIPTS_DIR)
    logger.info("📡 Endpoints disponibles:")
    logger.info("   GET  /api/scripts - Lista de scripts disponibles")
    logger.info("   POST /api/scripts/<id>/start - Iniciar script")
    logger.info("   POST /api/scripts/<id>/stop - Detener script")
    logger.info("   GET  /api/scripts/<id>/status - Estado del script")
    logger.info("   GET  /api/scripts/<id>/output - Output del script")
    logger.info("   GET  /api/scripts/running - Scripts en ejecución")
    logger.info("   POST /api/scripts/stop-all - Detener todos")
    
    try:
        app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
    except Exception as e:
        logger.error(f"❌ Error iniciando servidor: {e}")