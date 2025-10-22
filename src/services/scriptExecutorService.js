/**
 * Servicio para ejecutar scripts remotamente desde cualquier vista
 * Utiliza la API del script_executor_api.py
 */

// URL base de la API (ajustar según tu configuración)
const API_BASE_URL = 'http://localhost:5000/api';

class ScriptExecutorService {
  
  /**
   * Obtener la lista de scripts disponibles
   */
  static async getAvailableScripts() {
    try {
      const response = await fetch(`${API_BASE_URL}/scripts`);
      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }
      const data = await response.json();
      return { success: true, scripts: data.scripts };
    } catch (error) {
      console.error('Error obteniendo scripts:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Ejecutar un script con parámetros opcionales
   */
  static async executeScript(scriptId, parameters = {}) {
    try {
      const response = await fetch(`${API_BASE_URL}/scripts/${scriptId}/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ parameters })
      });

      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      console.error('Error ejecutando script:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Detener un script en ejecución
   */
  static async stopScript(scriptId) {
    try {
      const response = await fetch(`${API_BASE_URL}/scripts/${scriptId}/stop`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      console.error('Error deteniendo script:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Obtener el estado de un script
   */
  static async getScriptStatus(scriptId) {
    try {
      const response = await fetch(`${API_BASE_URL}/scripts/${scriptId}/status`);
      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }
      const data = await response.json();
      return { success: true, status: data };
    } catch (error) {
      console.error('Error obteniendo estado:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Obtener la salida/logs de un script
   */
  static async getScriptOutput(scriptId) {
    try {
      const response = await fetch(`${API_BASE_URL}/scripts/${scriptId}/output`);
      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }
      const data = await response.json();
      return { success: true, output: data.output };
    } catch (error) {
      console.error('Error obteniendo salida:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Obtener todos los scripts en ejecución
   */
  static async getRunningScripts() {
    try {
      const response = await fetch(`${API_BASE_URL}/scripts/running`);
      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }
      const data = await response.json();
      return { success: true, running: data.running_scripts };
    } catch (error) {
      console.error('Error obteniendo scripts ejecutándose:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Detener todos los scripts en ejecución
   */
  static async stopAllScripts() {
    try {
      const response = await fetch(`${API_BASE_URL}/scripts/stop-all`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      console.error('Error deteniendo todos los scripts:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Método de conveniencia para ejecutar el script del brazo
   */
  static async executeBrazoScript(parameters = {}) {
    return await this.executeScript('maestro_brazo_ble', parameters);
  }

  /**
   * Método de conveniencia para ejecutar el script combinado
   */
  static async executeCombinedScript(parameters = {}) {
    return await this.executeScript('maestro_ble', parameters);
  }

  /**
   * Método para verificar si la API está disponible
   */
  static async checkApiStatus() {
    try {
      const response = await fetch(`${API_BASE_URL}/scripts`);
      return response.ok;
    } catch (error) {
      return false;
    }
  }
}

export default ScriptExecutorService;