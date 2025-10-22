import { database } from './config';
import { ref, push, set, onValue, off, update } from 'firebase/database';

// Referencia a la tabla de personas
const personsRef = ref(database, 'persons');

// Agregar nueva persona
export const addPerson = async (personData) => {
  try {
    const newPersonRef = push(personsRef);
    const completePersonData = {
      ...personData,
      id: newPersonRef.key,
      timestamp: new Date().toISOString(),
      sensor_readings: {},  // Inicializar historial vacío para lecturas de sensores
      last_sensor_update: null,  // Timestamp de última actualización del sensor
      total_readings_count: 0,  // Contador total de lecturas
      session_active: false  // Estado de sesión
    };
    
    await set(newPersonRef, completePersonData);
    return { success: true, id: newPersonRef.key };
  } catch (error) {
    console.error('Error adding person:', error);
    return { success: false, error: error.message };
  }
};

// Obtener todas las personas
export const getPersons = (callback) => {
  onValue(personsRef, (snapshot) => {
    const data = snapshot.val();
    const persons = data ? Object.values(data) : [];
    callback(persons);
  });
};

// Detener la escucha de cambios
export const stopListening = () => {
  off(personsRef);
};

// Activar una persona (desactiva las demás)
export const setActivePerson = async (personId) => {
  try {
    // Primero obtener todas las personas
    const snapshot = await new Promise((resolve) => {
      onValue(personsRef, resolve, { onlyOnce: true });
    });
    
    const persons = snapshot.val() || {};
    
    // Desactivar todas las personas y activar solo la seleccionada
    const updates = {};
    Object.keys(persons).forEach(key => {
      updates[`${key}/es_activa`] = key === personId;
    });
    
    await update(ref(database), updates);
    return { success: true };
  } catch (error) {
    console.error('Error setting active person:', error);
    return { success: false, error: error.message };
  }
};

// Estructura de ejemplo de Person
export const personTemplate = {
  nombre: '',
  genero: '',
  edad: 0,
  es_activa: false,
  sensor_readings: {},
  last_sensor_update: null,
  total_readings_count: 0,
  session_active: false
};