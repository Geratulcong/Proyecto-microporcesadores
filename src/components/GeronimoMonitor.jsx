import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Badge, Alert, Container } from 'react-bootstrap';
import { ref, onValue, query, orderByKey, limitToLast } from 'firebase/database';
import { database } from '../firebase/config';
import MainCard from './MainCard';

const GeronimoMonitor = () => {
  const [sensorData, setSensorData] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('Desconectado');
  const [lastUpdate, setLastUpdate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dataCount, setDataCount] = useState(0);

  useEffect(() => {
    // Listener en tiempo real para los últimos datos de sensores
    const sensorsRef = query(
      ref(database, 'sensor_readings'),
      orderByKey(),
      limitToLast(1)
    );
    
    const unsubscribe = onValue(sensorsRef, (snapshot) => {
      if (snapshot.exists()) {
        const data = snapshot.val();
        // Obtener el último registro
        const lastKey = Object.keys(data)[0];
        const lastData = data[lastKey];
        
        setSensorData(lastData);
        setLastUpdate(new Date().toLocaleTimeString());
        setConnectionStatus('Conectado');
        setLoading(false);
        setDataCount(prev => prev + 1);
        
        // Auto-desconectar si no hay actualizaciones en 15 segundos
        setTimeout(() => {
          const now = new Date();
          const lastUpdateTime = new Date(lastData.timestamp);
          const diffSeconds = (now - lastUpdateTime) / 1000;
          
          if (diffSeconds > 10) {
            setConnectionStatus('Sin datos recientes');
          }
        }, 10000);
        
      } else {
        setLoading(false);
        setConnectionStatus('Usuario no encontrado');
      }
    }, (error) => {
      console.error('Error listening to Firebase:', error);
      setConnectionStatus('Error de conexión');
      setLoading(false);
    });

    // Cleanup listener al desmontar componente
    return () => unsubscribe();
  }, []);

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

  if (!sensorData) {
    return (
      <Container>
        <MainCard title="Monitor de Geronimo">
          <Alert variant="warning">
            <h5>👤 Usuario no encontrado</h5>
            <p>No se encontraron datos de sensores</p>
            <p>Asegúrate de que:</p>
            <ul>
              <li>El Arduino esté conectado y enviando datos</li>
              <li>El Raspberry Pi esté ejecutando el receptor Bluetooth</li>
              <li>Los datos se estén guardando en Firebase</li>
            </ul>
          </Alert>
        </MainCard>
      </Container>
    );
  }

  return (
    <Container>
      <MainCard title={`📊 Monitor en Tiempo Real - Geronimo`}>
        
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
                <p><strong>Nombre:</strong> Geronimo</p>
                <p><strong>Género:</strong> {sensorData.genero || 'M'}</p>
                <p><strong>Edad:</strong> {sensorData.edad || '75'} años</p>
                <p><strong>Device ID:</strong> {sensorData.device_id || 'N/A'}</p>
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

        {/* Datos del Sensor del Brazo */}
        <Row className="mb-4">
          <Col md={6}>
            <Card className="h-100">
              <Card.Header className="bg-primary text-white">
                <h6 className="mb-0">� Sensor del Brazo</h6>
              </Card.Header>
              <Card.Body>
                {sensorData?.brazo ? (
                  <Row>
                    <Col md={4}>
                      <div className="text-center p-2 border rounded">
                        <h5 className="text-danger mb-0">
                          {formatAccelValue(sensorData.brazo.acc?.x)}
                        </h5>
                        <small className="text-muted">X (g)</small>
                        <div className="progress mt-1" style={{ height: '6px' }}>
                          <div 
                            className="progress-bar bg-danger" 
                            style={{ 
                              width: `${Math.abs(sensorData.brazo.acc?.x || 0) * 50}%` 
                            }}
                          ></div>
                        </div>
                      </div>
                    </Col>
                    <Col md={4}>
                      <div className="text-center p-2 border rounded">
                        <h5 className="text-warning mb-0">
                          {formatAccelValue(sensorData.brazo.acc?.y)}
                        </h5>
                        <small className="text-muted">Y (g)</small>
                        <div className="progress mt-1" style={{ height: '6px' }}>
                          <div 
                            className="progress-bar bg-warning" 
                            style={{ 
                              width: `${Math.abs(sensorData.brazo.acc?.y || 0) * 50}%` 
                            }}
                          ></div>
                        </div>
                      </div>
                    </Col>
                    <Col md={4}>
                      <div className="text-center p-2 border rounded">
                        <h5 className="text-success mb-0">
                          {formatAccelValue(sensorData.brazo.acc?.z)}
                        </h5>
                        <small className="text-muted">Z (g)</small>
                        <div className="progress mt-1" style={{ height: '6px' }}>
                          <div 
                            className="progress-bar bg-success" 
                            style={{ 
                              width: `${Math.abs(sensorData.brazo.acc?.z || 0) * 50}%` 
                            }}
                          ></div>
                        </div>
                      </div>
                    </Col>
                    <Col md={12} className="mt-2">
                      <small className="text-muted">
                        <strong>Timestamp:</strong> {sensorData.brazo.ts || 'N/A'}
                      </small>
                    </Col>
                  </Row>
                ) : (
                  <div className="text-center text-muted">
                    <p>📡 Esperando datos del sensor del brazo...</p>
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
                {sensorData?.pie ? (
                  <Row>
                    <Col md={4}>
                      <div className="text-center p-2 border rounded">
                        <h5 className="text-danger mb-0">
                          {formatAccelValue(sensorData.pie.acc?.x)}
                        </h5>
                        <small className="text-muted">X (g)</small>
                        <div className="progress mt-1" style={{ height: '6px' }}>
                          <div 
                            className="progress-bar bg-danger" 
                            style={{ 
                              width: `${Math.abs(sensorData.pie.acc?.x || 0) * 50}%` 
                            }}
                          ></div>
                        </div>
                      </div>
                    </Col>
                    <Col md={4}>
                      <div className="text-center p-2 border rounded">
                        <h5 className="text-warning mb-0">
                          {formatAccelValue(sensorData.pie.acc?.y)}
                        </h5>
                        <small className="text-muted">Y (g)</small>
                        <div className="progress mt-1" style={{ height: '6px' }}>
                          <div 
                            className="progress-bar bg-warning" 
                            style={{ 
                              width: `${Math.abs(sensorData.pie.acc?.y || 0) * 50}%` 
                            }}
                          ></div>
                        </div>
                      </div>
                    </Col>
                    <Col md={4}>
                      <div className="text-center p-2 border rounded">
                        <h5 className="text-success mb-0">
                          {formatAccelValue(sensorData.pie.acc?.z)}
                        </h5>
                        <small className="text-muted">Z (g)</small>
                        <div className="progress mt-1" style={{ height: '6px' }}>
                          <div 
                            className="progress-bar bg-success" 
                            style={{ 
                              width: `${Math.abs(sensorData.pie.acc?.z || 0) * 50}%` 
                            }}
                          ></div>
                        </div>
                      </div>
                    </Col>
                    <Col md={12} className="mt-2">
                      <small className="text-muted">
                        <strong>Timestamp:</strong> {sensorData.pie.ts || 'N/A'}
                      </small>
                    </Col>
                  </Row>
                ) : (
                  <div className="text-center text-muted">
                    <p>📡 Esperando datos del sensor del pie...</p>
                  </div>
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Información técnica */}
        <Row className="mb-4">
          <Col md={6}>
            <Card>
              <Card.Header>
                <h6 className="mb-0">🔧 Estado de Conexión</h6>
              </Card.Header>
              <Card.Body>
                <div className="mb-2">
                  <Badge bg={sensorData?.brazo ? 'success' : 'secondary'} className="me-2">
                    💪 Brazo: {sensorData?.brazo ? 'Conectado' : 'Desconectado'}
                  </Badge>
                </div>
                <div className="mb-2">
                  <Badge bg={sensorData?.pie ? 'success' : 'secondary'} className="me-2">
                    🦶 Pie: {sensorData?.pie ? 'Conectado' : 'Desconectado'}
                  </Badge>
                </div>
                <p><strong>Datos recibidos:</strong> {dataCount} veces</p>
                <p><strong>Última actualización:</strong> {lastUpdate || 'N/A'}</p>
              </Card.Body>
            </Card>
          </Col>
          <Col md={6}>
            <Card>
              <Card.Header>
                <h6 className="mb-0">📊 Información del Sistema</h6>
              </Card.Header>
              <Card.Body>
                <p><strong>Timestamp Sistema:</strong> {
                  sensorData?.timestamp 
                    ? new Date(sensorData.timestamp).toLocaleString()
                    : 'N/A'
                }</p>
                <p><strong>Protocolo:</strong> Bluetooth Low Energy (BLE)</p>
                <p><strong>Sensores:</strong> Arduino Nano 33 BLE Sense</p>
                <p><strong>Base de datos:</strong> Firebase Realtime Database</p>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Instrucciones */}
        <Row className="mt-4">
          <Col>
            <Alert variant="info">
              <h6>📱 Información del Monitor:</h6>
              <ul className="mb-0">
                <li><strong>💪 Sensor del Brazo:</strong> Muestra datos del acelerómetro del Arduino en el brazo</li>
                <li><strong>🦶 Sensor del Pie:</strong> Muestra datos del acelerómetro del Arduino en el pie</li>
                <li><strong>📊 Barras de Progreso:</strong> Representan la intensidad de movimiento en cada eje (X, Y, Z)</li>
                <li><strong>🔄 Actualización Automática:</strong> Los datos se actualizan en tiempo real vía BLE</li>
                <li><strong>📡 Estados de Conexión:</strong> Verde = Conectado, Gris = Desconectado</li>
              </ul>
            </Alert>
          </Col>
        </Row>

      </MainCard>
    </Container>
  );
};

export default GeronimoMonitor;