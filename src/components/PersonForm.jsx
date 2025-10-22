import React, { useState } from 'react';
import { Card, Form, Button, Row, Col, Alert } from 'react-bootstrap';
import { addPerson } from '../firebase/personService';
import MainCard from '../components/MainCard';

const PersonForm = () => {
  const [formData, setFormData] = useState({
    nombre: '',
    genero: '',
    edad: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState({ show: false, message: '', type: '' });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    // Convertir valores numéricos
    const personData = {
      nombre: formData.nombre.trim(),
      genero: formData.genero,
      edad: parseInt(formData.edad),
      es_activa: false  // Por defecto no activa, se puede activar desde el monitor
    };

    try {
      const result = await addPerson(personData);
      
      if (result.success) {
        setAlert({
          show: true,
          message: `Persona registrada exitosamente con ID: ${result.id}`,
          type: 'success'
        });
        
        // Limpiar formulario
        setFormData({
          nombre: '',
          genero: '',
          edad: ''
        });
      } else {
        setAlert({
          show: true,
          message: `Error: ${result.error}`,
          type: 'danger'
        });
      }
    } catch (error) {
      setAlert({
        show: true,
        message: `Error inesperado: ${error.message}`,
        type: 'danger'
      });
    }

    setLoading(false);
    
    // Ocultar alerta después de 5 segundos
    setTimeout(() => {
      setAlert({ show: false, message: '', type: '' });
    }, 5000);
  };

  return (
    <MainCard title="Registro de Persona">
      {alert.show && (
        <Alert variant={alert.type} className="mb-3">
          {alert.message}
        </Alert>
      )}
      
      <Form onSubmit={handleSubmit}>
        <Row>
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Nombre completo *</Form.Label>
              <Form.Control
                type="text"
                name="nombre"
                value={formData.nombre}
                onChange={handleChange}
                placeholder="Ingrese el nombre completo"
                required
              />
            </Form.Group>
          </Col>
          
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Género *</Form.Label>
              <Form.Select
                name="genero"
                value={formData.genero}
                onChange={handleChange}
                required
              >
                <option value="">Seleccionar género</option>
                <option value="Masculino">Masculino</option>
                <option value="Femenino">Femenino</option>
                <option value="Otro">Otro</option>
                <option value="Prefiero no decir">Prefiero no decir</option>
              </Form.Select>
            </Form.Group>
          </Col>
        </Row>

        <Row>
          <Col md={4}>
            <Form.Group className="mb-3">
              <Form.Label>Edad *</Form.Label>
              <Form.Control
                type="number"
                name="edad"
                value={formData.edad}
                onChange={handleChange}
                placeholder="Edad en años"
                min="1"
                max="120"
                required
              />
            </Form.Group>
          </Col>
        </Row>

        <Row>
          <Col md={12}>
            <Button 
              variant="primary" 
              type="submit" 
              disabled={loading}
              className="me-2"
            >
              {loading ? 'Guardando...' : 'Registrar Persona'}
            </Button>
            
            <Button 
              variant="secondary" 
              type="button"
              onClick={() => setFormData({
                nombre: '',
                genero: '',
                edad: ''
              })}
            >
              Limpiar
            </Button>
          </Col>
        </Row>
      </Form>
    </MainCard>
  );
};

export default PersonForm;