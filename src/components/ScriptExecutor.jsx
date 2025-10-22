import React, { useState, useEffect, useCallback } from 'react';
import { Card, Row, Col, Button, Badge, Alert, ListGroup, Spinner, Modal, Form } from 'react-bootstrap';
import MainCard from './MainCard';

const ScriptExecutor = () => {
  // Estados del componente
  const [scripts, setScripts] = useState([]);
  const [runningScripts, setRunningScripts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [apiStatus, setApiStatus] = useState('unknown');
  
  // Modal para output del script
  const [showOutputModal, setShowOutputModal] = useState(false);
  const [selectedScript, setSelectedScript] = useState(null);
  const [scriptOutput, setScriptOutput] = useState([]);
  const [autoRefreshOutput, setAutoRefreshOutput] = useState(false);
  
  // Modal para parámetros del script
  const [showParamsModal, setShowParamsModal] = useState(false);
  const [scriptToRun, setScriptToRun] = useState(null);
  const [scriptParameters, setScriptParameters] = useState({});

  // Configuración de la API
  const API_BASE_URL = 'http://localhost:5001/api';

  // Función para hacer requests a la API
  const apiRequest = async (endpoint, options = {}) => {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (err) {
      console.error(`Error en API request ${endpoint}:`, err);
      throw err;
    }
  };

  // Verificar estado de la API
  const checkApiHealth = useCallback(async () => {
    try {
      const response = await apiRequest('/scripts');
      setApiStatus(response.success ? 'online' : 'error');
      return response.success;
    } catch (err) {
      setApiStatus('offline');
      return false;
    }
  }, []);

  // Obtener scripts disponibles
  const loadScripts = useCallback(async () => {
    try {
      const response = await apiRequest('/scripts');
      if (response.success) {
        setScripts(response.scripts || []);
      }
    } catch (err) {
      console.error('Error cargando scripts:', err);
    }
  }, []);

  // Obtener scripts en ejecución
  const loadRunningScripts = useCallback(async () => {
    try {
      const response = await apiRequest('/scripts/running');
      if (response.success) {
        setRunningScripts(response.running_scripts || []);
      }
    } catch (err) {
      console.error('Error cargando scripts en ejecución:', err);
    }
  }, []);

  // Iniciar script con parámetros
  const startScript = async (scriptId, parameters = {}) => {
    setError(null);
    setLoading(true);

    try {
      const response = await apiRequest(`/scripts/${scriptId}/start`, {
        method: 'POST',
        body: JSON.stringify({ parameters })
      });

      if (response.success) {
        setSuccess(`Script ${response.status.script_name} iniciado`);
        await loadScripts();
        await loadRunningScripts();
      } else {
        throw new Error(response.error || 'Error desconocido');
      }
    } catch (err) {
      setError(`Error iniciando script: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Detener script
  const stopScript = async (scriptId) => {
    setError(null);
    setLoading(true);

    try {
      const response = await apiRequest(`/scripts/${scriptId}/stop`, {
        method: 'POST'
      });

      if (response.success) {
        setSuccess(`Script detenido`);
        await loadScripts();
        await loadRunningScripts();
      } else {
        throw new Error(response.error || 'Error desconocido');
      }
    } catch (err) {
      setError(`Error deteniendo script: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Detener todos los scripts
  const stopAllScripts = async () => {
    setError(null);
    setLoading(true);

    try {
      const response = await apiRequest('/scripts/stop-all', {
        method: 'POST'
      });

      if (response.success) {
        setSuccess(`${response.stopped.length} scripts detenidos`);
        await loadScripts();
        await loadRunningScripts();
      } else {
        throw new Error(response.errors?.join(', ') || 'Error desconocido');
      }
    } catch (err) {
      setError(`Error deteniendo scripts: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Obtener output de script
  const loadScriptOutput = useCallback(async (scriptId) => {
    try {
      const response = await apiRequest(`/scripts/${scriptId}/output?lines=50`);
      if (response.success) {
        setScriptOutput(response.output || []);
      }
    } catch (err) {
      console.error('Error cargando output:', err);
    }
  }, []);

  // Mostrar output del script
  const showScriptOutput = (script) => {
    setSelectedScript(script);
    setShowOutputModal(true);
    loadScriptOutput(script.id);
  };

  // Abrir modal de parámetros para ejecutar script
  const openParametersModal = (script) => {
    setScriptToRun(script);
    
    // Inicializar parámetros con valores por defecto
    const defaultParameters = {};
    if (script.parameters) {
      Object.entries(script.parameters).forEach(([key, param]) => {
        defaultParameters[key] = param.default;
      });
    }
    setScriptParameters(defaultParameters);
    setShowParamsModal(true);
  };

  // Ejecutar script directamente (sin parámetros)
  const executeScriptDirect = (script) => {
    if (script.parameters && Object.keys(script.parameters).length > 0) {
      // Tiene parámetros, mostrar modal
      openParametersModal(script);
    } else {
      // Sin parámetros, ejecutar directamente
      startScript(script.id, {});
    }
  };

  // Ejecutar script con parámetros configurados
  const executeScriptWithParameters = () => {
    if (scriptToRun) {
      startScript(scriptToRun.id, scriptParameters);
      setShowParamsModal(false);
      setScriptToRun(null);
      setScriptParameters({});
    }
  };

  // Actualizar parámetro específico
  const updateParameter = (key, value) => {
    setScriptParameters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Auto-refresh del output cuando el modal está abierto
  useEffect(() => {
    let interval;
    if (showOutputModal && selectedScript && autoRefreshOutput) {
      interval = setInterval(() => {
        loadScriptOutput(selectedScript.id);
      }, 2000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [showOutputModal, selectedScript, autoRefreshOutput, loadScriptOutput]);

  // Auto-refresh de estados cada 5 segundos
  useEffect(() => {
    const interval = setInterval(() => {
      loadRunningScripts();
    }, 5000);
    return () => clearInterval(interval);
  }, [loadRunningScripts]);

  // Cargar datos iniciales
  useEffect(() => {
    checkApiHealth();
    loadScripts();
    loadRunningScripts();
  }, [checkApiHealth, loadScripts, loadRunningScripts]);

  // Auto-cerrar mensajes
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 8000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  return (
    <MainCard title="🐍 Ejecución de Scripts Python - Raspberry Pi">
      {/* Estado de la API */}
      <Row className="mb-3">
        <Col>
          <div className="d-flex justify-content-between align-items-center">
            <div className="d-flex gap-2">
              <Badge bg={apiStatus === 'online' ? 'success' : apiStatus === 'offline' ? 'danger' : 'warning'}>
                🖥️ Raspberry Pi: {apiStatus === 'online' ? 'En Línea' : apiStatus === 'offline' ? 'Sin Conexión' : 'Verificando...'}
              </Badge>
              {runningScripts.length > 0 && (
                <Badge bg="info">
                  ⚡ {runningScripts.length} Script{runningScripts.length !== 1 ? 's' : ''} Ejecutándose
                </Badge>
              )}
            </div>
            {runningScripts.length > 0 && (
              <Button 
                variant="outline-danger" 
                size="sm"
                onClick={stopAllScripts}
                disabled={loading}
              >
                🛑 Detener Todos
              </Button>
            )}
          </div>
        </Col>
      </Row>

      {/* Alertas */}
      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          <strong>Error:</strong> {error}
        </Alert>
      )}
      
      {success && (
        <Alert variant="success" dismissible onClose={() => setSuccess(null)}>
          <strong>Éxito:</strong> {success}
        </Alert>
      )}

      {/* Scripts en ejecución */}
      {runningScripts.length > 0 && (
        <Row className="mb-4">
          <Col>
            <Card border="success">
              <Card.Header className="bg-light">
                <h6 className="mb-0">⚡ Scripts en Ejecución ({runningScripts.length})</h6>
              </Card.Header>
              <Card.Body>
                <ListGroup variant="flush">
                  {runningScripts.map((script) => (
                    <ListGroup.Item key={script.script_id} className="d-flex justify-content-between align-items-center">
                      <div>
                        <strong>{script.script_name}</strong>
                        <br />
                        <small className="text-muted">
                          Duración: {script.duration || '0s'} | 
                          Líneas: {script.output_lines || 0}
                        </small>
                        {script.last_output && (
                          <div className="small text-info mt-1" style={{fontFamily: 'monospace'}}>
                            {script.last_output.substring(0, 60)}...
                          </div>
                        )}
                      </div>
                      <div className="d-flex gap-2">
                        <Badge bg="success">Ejecutándose</Badge>
                        <Button 
                          variant="outline-info" 
                          size="sm"
                          onClick={() => showScriptOutput(scripts.find(s => s.id === script.script_id) || { id: script.script_id, name: script.script_name })}
                        >
                          📋 Ver Output
                        </Button>
                        <Button 
                          variant="outline-danger" 
                          size="sm"
                          onClick={() => stopScript(script.script_id)}
                          disabled={loading}
                        >
                          🛑 Detener
                        </Button>
                      </div>
                    </ListGroup.Item>
                  ))}
                </ListGroup>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Scripts disponibles */}
      <Row>
        <Col>
          <Card>
            <Card.Header>
              <div className="d-flex justify-content-between align-items-center">
                <h6 className="mb-0">📜 Scripts Disponibles ({scripts.length})</h6>
                <Button 
                  variant="outline-secondary" 
                  size="sm"
                  onClick={loadScripts}
                  disabled={loading}
                >
                  🔄 Refrescar
                </Button>
              </div>
            </Card.Header>
            <Card.Body>
              {scripts.length === 0 ? (
                <div className="text-center py-4">
                  <p className="text-muted">No hay scripts disponibles</p>
                </div>
              ) : (
                <ListGroup variant="flush">
                  {scripts.map((script) => (
                    <ListGroup.Item key={script.id} className="d-flex justify-content-between align-items-center">
                      <div>
                        <div className="d-flex align-items-center gap-2">
                          <span style={{fontSize: '1.2em'}}>{script.icon}</span>
                          <strong>{script.name}</strong>
                          {!script.exists && <Badge bg="warning">Archivo no encontrado</Badge>}
                          {script.is_running && <Badge bg="success">Ejecutándose</Badge>}
                        </div>
                        <div className="small text-muted">{script.description}</div>
                        <div className="small text-info">{script.file}</div>
                        {script.parameters && Object.keys(script.parameters).length > 0 && (
                          <div className="small text-warning">
                            ⚙️ {Object.keys(script.parameters).length} parámetro{Object.keys(script.parameters).length !== 1 ? 's' : ''} configurables
                          </div>
                        )}
                      </div>
                      <div className="d-flex gap-2">
                        {script.is_running ? (
                          <>
                            <Button 
                              variant="outline-info" 
                              size="sm"
                              onClick={() => showScriptOutput(script)}
                            >
                              📋 Ver Output
                            </Button>
                            <Button 
                              variant="outline-danger" 
                              size="sm"
                              onClick={() => stopScript(script.id)}
                              disabled={loading}
                            >
                              🛑 Detener
                            </Button>
                          </>
                        ) : (
                          <Button 
                            variant="outline-success" 
                            size="sm"
                            onClick={() => executeScriptDirect(script)}
                            disabled={loading || !script.exists}
                          >
                            ▶️ Ejecutar
                          </Button>
                        )}
                      </div>
                    </ListGroup.Item>
                  ))}
                </ListGroup>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Modal de output del script */}
      <Modal show={showOutputModal} onHide={() => setShowOutputModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>📋 Output: {selectedScript?.name}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="d-flex justify-content-between align-items-center mb-3">
            <Form.Check 
              type="switch"
              id="auto-refresh-output"
              label="Auto-actualizar (2s)"
              checked={autoRefreshOutput}
              onChange={(e) => setAutoRefreshOutput(e.target.checked)}
            />
            <Button 
              variant="outline-secondary" 
              size="sm"
              onClick={() => selectedScript && loadScriptOutput(selectedScript.id)}
            >
              🔄 Refrescar
            </Button>
          </div>
          
          <div 
            style={{
              backgroundColor: '#000',
              color: '#00ff00',
              fontFamily: 'monospace',
              fontSize: '0.85em',
              padding: '15px',
              borderRadius: '5px',
              maxHeight: '400px',
              overflowY: 'auto'
            }}
          >
            {scriptOutput.length === 0 ? (
              <div style={{color: '#666'}}>Sin output disponible...</div>
            ) : (
              scriptOutput.map((line, index) => (
                <div key={index}>{line}</div>
              ))
            )}
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowOutputModal(false)}>
            Cerrar
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Modal para configurar parámetros del script */}
      <Modal 
        show={showParamsModal} 
        onHide={() => setShowParamsModal(false)}
        size="lg"
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>
            ⚙️ Configurar Parámetros - {scriptToRun?.name}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {scriptToRun && scriptToRun.parameters && (
            <Form>
              {Object.entries(scriptToRun.parameters).map(([key, param]) => (
                <Form.Group key={key} className="mb-3">
                  <Form.Label>
                    <strong>{key.replace(/_/g, ' ')}</strong>
                    {param.description && (
                      <div className="small text-muted">{param.description}</div>
                    )}
                  </Form.Label>
                  
                  {param.type === 'boolean' ? (
                    <Form.Check
                      type="checkbox"
                      id={`param-${key}`}
                      label={param.description || key}
                      checked={scriptParameters[key] || false}
                      onChange={(e) => updateParameter(key, e.target.checked)}
                    />
                  ) : param.type === 'select' ? (
                    <Form.Select
                      value={scriptParameters[key] || param.default}
                      onChange={(e) => updateParameter(key, e.target.value)}
                    >
                      {param.options?.map(option => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </Form.Select>
                  ) : param.type === 'number' ? (
                    <Form.Control
                      type="number"
                      min={param.min}
                      max={param.max}
                      step={param.step || (param.step === 0.1 ? 0.1 : 1)}
                      value={scriptParameters[key] || param.default}
                      onChange={(e) => updateParameter(key, parseFloat(e.target.value))}
                      placeholder={`Valor por defecto: ${param.default}`}
                    />
                  ) : (
                    <Form.Control
                      type="text"
                      value={scriptParameters[key] || param.default}
                      onChange={(e) => updateParameter(key, e.target.value)}
                      placeholder={`Valor por defecto: ${param.default}`}
                    />
                  )}
                  
                  {param.min !== undefined && param.max !== undefined && (
                    <Form.Text className="text-muted">
                      Rango: {param.min} - {param.max}
                    </Form.Text>
                  )}
                </Form.Group>
              ))}
            </Form>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowParamsModal(false)}>
            Cancelar
          </Button>
          <Button 
            variant="success" 
            onClick={executeScriptWithParameters}
            disabled={loading}
          >
            🚀 Ejecutar Script
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Mensaje si API offline */}
      {apiStatus === 'offline' && (
        <Row className="mt-4">
          <Col>
            <Alert variant="warning">
              <h6>⚠️ API No Disponible</h6>
              <p>No se puede conectar con el Raspberry Pi en <code>localhost:5001</code></p>
              <p>Asegúrate de que:</p>
              <ul className="mb-0">
                <li>El Raspberry Pi esté encendido y conectado</li>
                <li>La API de scripts esté ejecutándose: <code>python script_executor_api.py</code></li>
                <li>La red permita conexiones al puerto 5001</li>
              </ul>
            </Alert>
          </Col>
        </Row>
      )}
    </MainCard>
  );
};

export default ScriptExecutor;