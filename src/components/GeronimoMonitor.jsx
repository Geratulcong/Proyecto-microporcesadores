import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Badge, Alert, Container, Form, Button, Dropdown } from 'react-bootstrap';
import { ref, onValue, query, orderByKey, limitToLast } from 'firebase/database';
import { database } from '../firebase/config';
import { getPersons, stopListening } from '../firebase/personService';
import MainCard from './MainCard';
import ScriptExecutorService from '../services/scriptExecutorService';

const GeronimoMonitor = () => {
  const [sensorData, setSensorData] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('Desconectado');
  const [lastUpdate, setLastUpdate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dataCount, setDataCount] = useState(0);
  
  // Estados para selección de personas
  const [availablePersons, setAvailablePersons] = useState([]);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [loadingPersons, setLoadingPersons] = useState(true);
  
  // Estados para ejecución de scripts
  const [scriptExecuting, setScriptExecuting] = useState(false);
  const [scriptStatus, setScriptStatus] = useState(null);
  const [firebaseInterval, setFirebaseInterval] = useState(3.0); // Intervalo en segundos

  // Cargar personas disponibles
  useEffect(() => {
    const handlePersonsData = (persons) => {
      setAvailablePersons(persons);
      setLoadingPersons(false);
      
      // Seleccionar automáticamente la primera persona si no hay ninguna seleccionada
      if (persons.length > 0 && !selectedPerson) {
        setSelectedPerson(persons[0]);
      }
    };

    getPersons(handlePersonsData);

    // Cleanup cuando el componente se desmonta
    return () => {
      stopListening();
    };
  }, [selectedPerson]);

  useEffect(() => {
    if (!selectedPerson || !selectedPerson.id) {
      setLoading(false);
      setConnectionStatus('Selecciona una persona');
      setSensorData(null);
      return;
    }

    // Listener en tiempo real para los datos de sensores de la persona específica
    const personSensorRef = ref(database, `persons/${selectedPerson.id}/sensor_readings`);
    
    const unsubscribe = onValue(personSensorRef, (snapshot) => {
      if (snapshot.exists()) {
        const sensorReadings = snapshot.val();
        
        if (sensorReadings && Object.keys(sensorReadings).length > 0) {
          // Obtener la lectura más reciente
          const readingsArray = Object.values(sensorReadings);
          const lastReading = readingsArray[readingsArray.length - 1];
          
          // Verificar si los datos son recientes (últimos 30 segundos)
          const now = new Date();
          const readingTime = new Date(lastReading.timestamp);
          const diffSeconds = (now - readingTime) / 1000;
          
          if (diffSeconds <= 30) {
            setSensorData({ 
              ...lastReading, 
              personInfo: selectedPerson,
              totalReadings: readingsArray.length
            });
            setLastUpdate(new Date().toLocaleTimeString());
            setConnectionStatus('Sensores Activos');
            setDataCount(readingsArray.length);
          } else {
            setSensorData({ 
              ...lastReading, 
              personInfo: selectedPerson,
              totalReadings: readingsArray.length
            });
            setLastUpdate(readingTime.toLocaleTimeString());
            setConnectionStatus('Datos Antiguos');
            setDataCount(readingsArray.length);
          }
        } else {
          // La persona existe pero no tiene lecturas de sensores
          setSensorData(null);
          setConnectionStatus('Sin Sensores Conectados');
          setDataCount(0);
        }
        setLoading(false);
        
      } else {
        // No hay datos de sensores para esta persona
        setSensorData(null);
        setConnectionStatus('Sin Datos de Sensores');
        setLoading(false);
        setDataCount(0);
      }
    }, (error) => {
      console.error('Error escuchando Firebase:', error);
      setConnectionStatus('Error de Conexión');
      setLoading(false);
    });

    // Cleanup listener al desmontar componente
    return () => unsubscribe();
  }, [selectedPerson]); // Dependencia para recargar cuando cambie la persona

  // Función para ejecutar script automáticamente
  const executeScriptForPerson = async (person) => {
    setScriptExecuting(true);
    setScriptStatus('Ee=jecutando');
    
    try {
      // Ejecutar el script maestro con la persona seleccionada
      const result = await ScriptExecutorService.executeBrazoScript({
        person_id: person.id,
        person_name: person.nombre,
        firebase_interval: firebaseInterval
      });
      
      if (result.success) {
        setScriptStatus('✅ Ejecucion iniciada');
        setConnectionStatus('Conectando sensores...');
      } else {
        setScriptStatus('❌ Error: ' + result.error);
        setConnectionStatus('Error de conexión');
      }
    } catch (error) {
      setScriptStatus('❌ Error inesperado: ' + error.message);
      setConnectionStatus('Error inesperado');
    }
    
    setScriptExecuting(false);
  };

  // Función para cambiar la persona seleccionada
  const handlePersonChange = async (person) => {
    // Si hay un script ejecutándose, detenerlo primero
    if (scriptExecuting) {
      setScriptStatus('⏹️ Deteniendo script anterior...');
      try {
        await ScriptExecutorService.stopScript('maestro');
        setScriptStatus('✅ Script anterior detenido');
      } catch (error) {
        console.error('Error deteniendo script:', error);
        setScriptStatus('⚠️ Error deteniendo script anterior');
      }
      setScriptExecuting(false);
    }
    
    setSelectedPerson(person);
    setSensorData(null);
    setConnectionStatus('Iniciando sensores automáticamente...');
    setLoading(true);
    setDataCount(0);
    setScriptStatus(null); // Limpiar estado del script
    
    // Ejecutar script automáticamente para la nueva persona seleccionada
    if (person && person.id) {
      await executeScriptForPerson(person);
    }
  };

  const getPostureColor = (postura) => {
    switch (postura) {
      case 'erguido': return 'success';
      case 'semi_inclinado': return 'warning';
      case 'acostado': return 'info';
      case 'movimiento': return 'secondary';
      default: return 'dark';
    }
  };

  const getPostureIcon = (postura) => {
    switch (postura) {
      case 'erguido': return '🚶';
      case 'semi_inclinado': return '📐';
      case 'acostado': return '🛏️';
      case 'movimiento': return '🔄';
      default: return '❓';
    }
  };

  const formatAccelValue = (value) => {
    return typeof value === 'number' ? value.toFixed(3) : '0.000';
  };

  if (loading) {
    return (
      <Container>
        <MainCard title="Monitor de Geronimo">
          <div className="text-center p-4">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Cargando...</span>
            </div>
            <p className="mt-2">Conectando con Firebase...</p>
          </div>
        </MainCard>
      </Container>
    );
  }

  if (!sensorData && !loadingPersons) {
    return (
      <Container>
        <MainCard title={`📊 Monitor - ${selectedPerson?.nombre || 'Seleccionar Persona'}`}>
          
          {/* Selector de Personas */}
          <Row className="mb-4">
            <Col md={12}>
              <div className="d-flex align-items-center gap-3">
                <strong>👥 Seleccionar Persona:</strong>
                <Dropdown>
                  <Dropdown.Toggle variant="outline-primary" id="person-selector">
                    {selectedPerson ? (
                      `${selectedPerson.nombre} (${selectedPerson.edad} años)`
                    ) : (
                      'Seleccionar persona...'
                    )}
                  </Dropdown.Toggle>

                  <Dropdown.Menu>
                    {availablePersons.length === 0 ? (
                      <Dropdown.Item disabled>No hay personas registradas</Dropdown.Item>
                    ) : (
                      availablePersons.map((person, index) => (
                        <Dropdown.Item
                          key={person.id || index}
                          onClick={() => handlePersonChange(person)}
                          active={selectedPerson?.id === person.id}
                        >
                          <div>
                            <strong>{person.nombre}</strong>
                            <div className="small text-muted">
                              {person.genero} • {person.edad} años
                            </div>
                          </div>
                        </Dropdown.Item>
                      ))
                    )}
                  </Dropdown.Menu>
                </Dropdown>
              </div>
            </Col>
          </Row>
          
          <Alert variant={selectedPerson ? "warning" : "info"}>
            {selectedPerson ? (
              <>
                <h5>📡 {connectionStatus}</h5>
                <p>Persona seleccionada: <strong>{selectedPerson.nombre}</strong></p>
                <p>Recolección automática de datos:</p>
                <ul>
                  <li>🚀 Los sensores se iniciarán automáticamente</li>
                  <li>🔧 Asegúrate de que el Raspberry Pi tenga acceso a los sensores Arduino</li>
                  <li>⚡ Configura el intervalo de datos según tus necesidades</li>
                  <li>📊 Los datos aparecerán aquí cuando el script esté funcionando</li>
                </ul>
              </>
            ) : (
              <>
                <h5>👥 Selecciona una persona</h5>
                <p>Elige una persona de la lista para ver sus datos de sensores en tiempo real.</p>
                {availablePersons.length === 0 && (
                  <p>Primero necesitas <a href="/person">registrar una persona</a> en el sistema.</p>
                )}
              </>
            )}
          </Alert>
        </MainCard>
      </Container>
    );
  }

  return (
    <Container>
      <MainCard title={`📊 Monitor en Tiempo Real - ${selectedPerson?.nombre || 'Persona'}`}>
        
        {/* Selector de Personas */}
        <Row className="mb-4">
          <Col md={12}>
            <div className="d-flex align-items-center gap-3">
              <strong>👥 Seleccionar Persona:</strong>
              <Dropdown>
                <Dropdown.Toggle variant="outline-primary" id="person-selector">
                  {selectedPerson ? (
                    `${selectedPerson.nombre} (${selectedPerson.edad} años)`
                  ) : (
                    'Seleccionar persona...'
                  )}
                </Dropdown.Toggle>

                <Dropdown.Menu>
                  {loadingPersons ? (
                    <Dropdown.Item disabled>Cargando personas...</Dropdown.Item>
                  ) : availablePersons.length === 0 ? (
                    <Dropdown.Item disabled>No hay personas registradas</Dropdown.Item>
                  ) : (
                    availablePersons.map((person, index) => (
                      <Dropdown.Item
                        key={person.id || index}
                        onClick={() => handlePersonChange(person)}
                        active={selectedPerson?.id === person.id}
                      >
                        <div>
                          <strong>{person.nombre}</strong>
                          <div className="small text-muted">
                            {person.genero} • {person.edad} años
                            {person.timestamp && (
                              <span> • {new Date(person.timestamp).toLocaleDateString()}</span>
                            )}
                          </div>
                        </div>
                      </Dropdown.Item>
                    ))
                  )}
                </Dropdown.Menu>
              </Dropdown>
              
              {availablePersons.length > 0 && (
                <Badge bg="info" className="ms-2">
                  {availablePersons.length} persona{availablePersons.length !== 1 ? 's' : ''} disponible{availablePersons.length !== 1 ? 's' : ''}
                </Badge>
              )}
            </div>
          </Col>
        </Row>

        {/* Configuración de Intervalo y Control Manual */}
        {selectedPerson && (
          <Row className="mb-3">
            <Col md={12}>
              <div className="d-flex align-items-center gap-3">
                <strong>⏱️ Intervalo de datos:</strong>
                <Form.Select 
                  size="sm" 
                  style={{width: '200px'}}
                  value={firebaseInterval}
                  onChange={(e) => setFirebaseInterval(parseFloat(e.target.value))}
                >
                  <option value={0.1}>⚡ 0.1s (100ms) - Ultra rápido</option>
                  <option value={0.2}>⚡ 0.2s (200ms) - Ultra rápido</option>
                  <option value={0.3}>⚡ 0.3s (300ms) - Muy rápido</option>
                  <option value={0.4}>� 0.4s (400ms) - Muy rápido</option>
                  <option value={0.5}>� 0.5s (500ms) - Rápido</option>
                </Form.Select>
                <Badge bg="secondary" className="ms-2">
                  {firebaseInterval < 1 ? `${firebaseInterval * 1000}ms` : `${firebaseInterval}s`}
                </Badge>
              </div>
            </Col>
          </Row>
        )}

        {/* Estado del Script */}
        {(scriptExecuting || scriptStatus) && (
          <Row className="mb-3">
            <Col>
              <Alert variant={scriptExecuting ? "info" : scriptStatus?.includes('✅') ? "success" : "warning"}>
                <div className="d-flex align-items-center">
                  {scriptExecuting && (
                    <div className="spinner-border spinner-border-sm me-2" role="status">
                      <span className="visually-hidden">Ejecutando...</span>
                    </div>
                  )}
                  <strong>🚀 Estado del Script:</strong>
                  <span className="ms-2">{scriptStatus || 'Preparando script...'}</span>
                </div>
              </Alert>
            </Col>
          </Row>
        )}
        
        {/* Estado de conexión */}
        <Row className="mb-3">
          <Col>
            <div className="d-flex justify-content-between align-items-center">
              <Badge 
                bg={connectionStatus === 'Conectado' ? 'success' : 'danger'}
                className="fs-6 p-2"
              >
                📡 {connectionStatus}
              </Badge>
              {lastUpdate && (
                <small className="text-muted">
                  Última actualización: {lastUpdate}
                </small>
              )}
            </div>
          </Col>
        </Row>

        {/* Información del usuario */}
        <Row className="mb-4">
          <Col md={6}>
            <Card className="h-100">
              <Card.Header>
                <h6 className="mb-0">👤 Información Personal</h6>
              </Card.Header>
              <Card.Body>
                <p><strong>Nombre:</strong> {selectedPerson?.nombre || 'Sin seleccionar'}</p>
                <p><strong>Género:</strong> {selectedPerson?.genero || 'N/A'}</p>
                <p><strong>Edad:</strong> {selectedPerson?.edad || 'N/A'} años</p>
                <p><strong>Device ID:</strong> {sensorData?.device_id || selectedPerson?.id || 'N/A'}</p>
                {selectedPerson?.timestamp && (
                  <p><strong>Registrado:</strong> {new Date(selectedPerson.timestamp).toLocaleString()}</p>
                )}
              </Card.Body>
            </Card>
          </Col>
          
          <Col md={6}>
            <Card className="h-100">
              <Card.Header>
                <h6 className="mb-0">🔄 Estado Actual</h6>
              </Card.Header>
              <Card.Body className="text-center">
                <div className="mb-3">
                  <span style={{ fontSize: '3rem' }}>
                    🔄
                  </span>
                </div>
                <Badge 
                  bg={'info'}
                  className="fs-5 p-2"
                >
                  Datos de Sensores
                </Badge>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Estadísticas de Sensores */}
        {sensorData && (
          <Row className="mb-4">
            <Col md={12}>
              <Card>
                <Card.Header className="bg-info text-white">
                  <h6 className="mb-0">📊 Estadísticas de Sensores</h6>
                </Card.Header>
                <Card.Body>
                  <Row>
                    <Col md={3}>
                      <div className="text-center">
                        <h4 className="text-primary mb-0">{sensorData?.totalReadings || 0}</h4>
                        <small className="text-muted">Lecturas Totales</small>
                      </div>
                    </Col>
                    <Col md={3}>
                      <div className="text-center">
                        <h4 className="text-success mb-0">{sensorData?.sensor_type || 'N/A'}</h4>
                        <small className="text-muted">Tipo de Sensor</small>
                      </div>
                    </Col>
                    <Col md={3}>
                      <div className="text-center">
                        <h4 className="text-warning mb-0">{sensorData?.device_id || 'N/A'}</h4>
                        <small className="text-muted">ID del Dispositivo</small>
                      </div>
                    </Col>
                    <Col md={3}>
                      <div className="text-center">
                        <Badge bg={connectionStatus === 'Sensores Activos' ? 'success' : 'warning'} className="fs-6 p-2">
                          {connectionStatus === 'Sensores Activos' ? '🟢 Activo' : '🟡 Inactivo'}
                        </Badge>
                        <small className="text-muted d-block mt-1">Estado</small>
                      </div>
                    </Col>
                  </Row>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        )}

        {/* Datos del Sensor del Brazo */}
        <Row className="mb-4">
          <Col md={6}>
            <Card className="h-100">
              <Card.Header className="bg-primary text-white">
                <h6 className="mb-0">� Sensor del Brazo</h6>
              </Card.Header>
              <Card.Body>
                {sensorData?.accelerometer || sensorData?.brazo?.accelerometer ? (
                  <>
                    <h6 className="text-primary mb-3">🚀 Acelerómetro</h6>
                    <Row>
                      <Col md={4}>
                        <div className="text-center p-2 border rounded">
                          <h5 className="text-danger mb-0">
                            {formatAccelValue(sensorData?.accelerometer?.x || sensorData?.brazo?.accelerometer?.x)}
                          </h5>
                          <small className="text-muted">X (g)</small>
                          <div className="progress mt-1" style={{ height: '6px' }}>
                            <div 
                              className="progress-bar bg-danger" 
                              style={{ 
                                width: `${Math.min(Math.abs((sensorData?.accelerometer?.x || sensorData?.brazo?.accelerometer?.x) || 0) * 10, 100)}%` 
                              }}
                            ></div>
                          </div>
                        </div>
                      </Col>
                      <Col md={4}>
                        <div className="text-center p-2 border rounded">
                          <h5 className="text-warning mb-0">
                            {formatAccelValue(sensorData?.accelerometer?.y || sensorData?.brazo?.accelerometer?.y)}
                          </h5>
                          <small className="text-muted">Y (g)</small>
                          <div className="progress mt-1" style={{ height: '6px' }}>
                            <div 
                              className="progress-bar bg-warning" 
                              style={{ 
                                width: `${Math.min(Math.abs((sensorData?.accelerometer?.y || sensorData?.brazo?.accelerometer?.y) || 0) * 10, 100)}%` 
                              }}
                            ></div>
                          </div>
                        </div>
                      </Col>
                      <Col md={4}>
                        <div className="text-center p-2 border rounded">
                          <h5 className="text-success mb-0">
                            {formatAccelValue(sensorData?.accelerometer?.z || sensorData?.brazo?.accelerometer?.z)}
                          </h5>
                          <small className="text-muted">Z (g)</small>
                          <div className="progress mt-1" style={{ height: '6px' }}>
                            <div 
                              className="progress-bar bg-success" 
                              style={{ 
                                width: `${Math.min(Math.abs((sensorData?.accelerometer?.z || sensorData?.brazo?.accelerometer?.z) || 0) * 10, 100)}%` 
                              }}
                            ></div>
                          </div>
                        </div>
                      </Col>
                    </Row>
                    
                    {(sensorData?.gyroscope || sensorData?.brazo?.gyroscope) && (
                      <>
                        <h6 className="text-secondary mb-3 mt-4">🌀 Giroscopio</h6>
                        <Row>
                          <Col md={4}>
                            <div className="text-center p-2 border rounded">
                              <h5 className="text-info mb-0">
                                {formatAccelValue(sensorData?.gyroscope?.x || sensorData?.brazo?.gyroscope?.x)}
                              </h5>
                              <small className="text-muted">X (°/s)</small>
                            </div>
                          </Col>
                          <Col md={4}>
                            <div className="text-center p-2 border rounded">
                              <h5 className="text-info mb-0">
                                {formatAccelValue(sensorData?.gyroscope?.y || sensorData?.brazo?.gyroscope?.y)}
                              </h5>
                              <small className="text-muted">Y (°/s)</small>
                            </div>
                          </Col>
                          <Col md={4}>
                            <div className="text-center p-2 border rounded">
                              <h5 className="text-info mb-0">
                                {formatAccelValue(sensorData?.gyroscope?.z || sensorData?.brazo?.gyroscope?.z)}
                              </h5>
                              <small className="text-muted">Z (°/s)</small>
                            </div>
                          </Col>
                        </Row>
                      </>
                    )}
                    
                    <Row className="mt-3">
                      <Col md={12}>
                        <div className="d-flex justify-content-between">
                          <small className="text-muted">
                            <strong>Timestamp:</strong> {sensorData?.timestamp ? new Date(sensorData.timestamp).toLocaleString() : 'N/A'}
                          </small>
                          <Badge bg="success" className="ms-2">
                            {sensorData?.totalReadings || 0} lecturas
                          </Badge>
                        </div>
                      </Col>
                    </Row>
                  </>
                ) : (
                  <div className="text-center text-muted p-4">
                    <div className="mb-3">
                      <i className="fas fa-satellite-dish fa-3x text-muted"></i>
                    </div>
                    <h6>📡 No hay datos de sensores</h6>
                    <p>Esperando conexión con sensores del brazo...</p>
                    <small>Los sensores se iniciarán automáticamente</small>
                  </div>
                )}
              </Card.Body>
            </Card>
          </Col>

          {/* Datos del Sensor del Pie */}
          <Col md={6}>
            <Card className="h-100">
              <Card.Header className="bg-success text-white">
                <h6 className="mb-0">🦶 Sensor del Pie</h6>
              </Card.Header>
              <Card.Body>
                {(sensorData?.pie && sensorData?.pie?.accelerometer) || (sensorData?.sensor_type === 'combined' && sensorData?.pie) ? (
                  <>
                    <h6 className="text-primary mb-3">🚀 Acelerómetro</h6>
                    <Row>
                      <Col md={4}>
                        <div className="text-center p-2 border rounded">
                          <h5 className="text-danger mb-0">
                            {formatAccelValue(sensorData?.pie?.accelerometer?.x || 0)}
                          </h5>
                          <small className="text-muted">X (g)</small>
                          <div className="progress mt-1" style={{ height: '6px' }}>
                            <div 
                              className="progress-bar bg-danger" 
                              style={{ 
                                width: `${Math.min(Math.abs(sensorData?.pie?.accelerometer?.x || 0) * 10, 100)}%` 
                              }}
                            ></div>
                          </div>
                        </div>
                      </Col>
                      <Col md={4}>
                        <div className="text-center p-2 border rounded">
                          <h5 className="text-warning mb-0">
                            {formatAccelValue(sensorData?.pie?.accelerometer?.y || 0)}
                          </h5>
                          <small className="text-muted">Y (g)</small>
                          <div className="progress mt-1" style={{ height: '6px' }}>
                            <div 
                              className="progress-bar bg-warning" 
                              style={{ 
                                width: `${Math.min(Math.abs(sensorData?.pie?.accelerometer?.y || 0) * 10, 100)}%` 
                              }}
                            ></div>
                          </div>
                        </div>
                      </Col>
                      <Col md={4}>
                        <div className="text-center p-2 border rounded">
                          <h5 className="text-success mb-0">
                            {formatAccelValue(sensorData?.pie?.accelerometer?.z || 0)}
                          </h5>
                          <small className="text-muted">Z (g)</small>
                          <div className="progress mt-1" style={{ height: '6px' }}>
                            <div 
                              className="progress-bar bg-success" 
                              style={{ 
                                width: `${Math.min(Math.abs(sensorData?.pie?.accelerometer?.z || 0) * 10, 100)}%` 
                              }}
                            ></div>
                          </div>
                        </div>
                      </Col>
                    </Row>
                    
                    {sensorData?.pie?.gyroscope && (
                      <>
                        <h6 className="text-secondary mb-3 mt-4">🌀 Giroscopio</h6>
                        <Row>
                          <Col md={4}>
                            <div className="text-center p-2 border rounded">
                              <h5 className="text-info mb-0">
                                {formatAccelValue(sensorData?.pie?.gyroscope?.x || 0)}
                              </h5>
                              <small className="text-muted">X (°/s)</small>
                            </div>
                          </Col>
                          <Col md={4}>
                            <div className="text-center p-2 border rounded">
                              <h5 className="text-info mb-0">
                                {formatAccelValue(sensorData?.pie?.gyroscope?.y || 0)}
                              </h5>
                              <small className="text-muted">Y (°/s)</small>
                            </div>
                          </Col>
                          <Col md={4}>
                            <div className="text-center p-2 border rounded">
                              <h5 className="text-info mb-0">
                                {formatAccelValue(sensorData?.pie?.gyroscope?.z || 0)}
                              </h5>
                              <small className="text-muted">Z (°/s)</small>
                            </div>
                          </Col>
                        </Row>
                      </>
                    )}
                  </>
                ) : (
                  <div className="text-center text-muted p-4">
                    <div className="mb-3">
                      <i className="fas fa-exclamation-triangle fa-3x text-warning"></i>
                    </div>
                    <h6 className="text-warning">🦶 Sensor del Pie No Conectado</h6>
                    <p>No se detectan datos del sensor del pie</p>
                    <small>Los sensores se inicializarán automáticamente</small>
                    <div className="mt-2">
                      <Badge bg="warning">Esperando conexión</Badge>
                    </div>
                  </div>
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Información Adicional */}
        {sensorData && (
          <Row className="mb-4">
            <Col md={12}>
              <Card>
                <Card.Header className="bg-light">
                  <h6 className="mb-0">ℹ️ Información Adicional del Sensor</h6>
                </Card.Header>
                <Card.Body>
                  <Row>
                    <Col md={4}>
                      <p><strong>Arduino Timestamp:</strong> {sensorData?.arduino_timestamp || 'N/A'}</p>
                    </Col>
                    <Col md={4}>
                      <p><strong>Raspberry Timestamp:</strong> {sensorData?.raspberry_timestamp || 'N/A'}</p>
                    </Col>
                    <Col md={4}>
                      <p><strong>Session ID:</strong> {sensorData?.session_id || 'N/A'}</p>
                    </Col>
                  </Row>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        )}

        {/* Instrucciones cuando no hay datos */}
        {!sensorData && selectedPerson && (
          <Row>
            <Col md={12}>
              <Alert variant="info">
                <h5>🔧 Pasos para conectar sensores</h5>
                <ol>
                  <li>Asegúrate de que el Arduino del brazo esté encendido</li>
                  <li>Los sensores se iniciarán automáticamente para <strong>{selectedPerson.nombre}</strong></li>
                  <li>Verifica que el Raspberry Pi tenga conexión BLE</li>
                  <li>Los datos aparecerán aquí cuando la conexión sea exitosa</li>
                </ol>
              </Alert>
            </Col>
          </Row>
        )}
                    <Col md={4}>
                      <div className="text-center p-2 border rounded">
                        <h5 className="text-danger mb-0">
                          {formatAccelValue(sensorData?.pie?.acc?.x)}
                        </h5>
                        <small className="text-muted">X (g)</small>
                        <div className="progress mt-1" style={{ height: '6px' }}>
                          <div 
                            className="progress-bar bg-danger" 
                            style={{ 
                              width: `${Math.abs(sensorData?.pie?.acc?.x || 0) * 50}%` 
                            }}
                          ></div>
                        </div>
                      </div>
                    </Col>
                    <Col md={4}>
                      <div className="text-center p-2 border rounded">
                        <h5 className="text-warning mb-0">
                          {formatAccelValue(sensorData?.pie?.acc?.y)}
                        </h5>
                        <small className="text-muted">Y (g)</small>
                        <div className="progress mt-1" style={{ height: '6px' }}>
                          <div 
                            className="progress-bar bg-warning" 
                            style={{ 
                              width: `${Math.abs(sensorData?.pie?.acc?.y || 0) * 50}%` 
                            }}
                          ></div>
                        </div>
                      </div>
                    </Col>
        {/* Estado del Script */}
        {(scriptExecuting || scriptStatus) && (
          <Row className="mb-3">
            <Col>
              <Alert variant={scriptStatus?.includes('✅') ? 'success' : scriptStatus?.includes('❌') ? 'danger' : 'info'}>
                <div className="d-flex align-items-center">
                  {scriptExecuting && <div className="spinner-border spinner-border-sm me-2"></div>}
                  <span>{scriptStatus || 'Procesando...'}</span>
                </div>
              </Alert>
            </Col>
          </Row>
        )}

      </MainCard>
    </Container>
  );
};

export default GeronimoMonitor;