import { database } from './config';
import { ref, push, set, onValue, off } from 'firebase/database';

// Referencia a la tabla de personas
const personsRef = ref(database, 'persons');

// Agregar nueva persona
export const addPerson = async (personData) => {
  try {
    const newPersonRef = push(personsRef);
    await set(newPersonRef, {
      ...personData,
      id: newPersonRef.key,
      timestamp: new Date().toISOString()
    });
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

// Estructura de ejemplo de Person
export const personTemplate = {
  nombre: '',
  genero: '',
  edad: 0,
  accelerometer_x: 0,
  accelerometer_y: 0,
  accelerometer_z: 0
};