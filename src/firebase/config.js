// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getDatabase } from "firebase/database";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBiV_N1j8zkX1dJiYPIyaOKkA8Ru_SAL0Y",
  authDomain: "proyecto-posturas-microp.firebaseapp.com",
  databaseURL: "https://proyecto-posturas-microp-default-rtdb.firebaseio.com/", // Agregar esta línea
  projectId: "proyecto-posturas-microp",
  storageBucket: "proyecto-posturas-microp.firebasestorage.app",
  messagingSenderId: "873011930943",
  appId: "1:873011930943:web:cdb432e5be1cb8aee9d58a",
  measurementId: "G-8L22JK7MB6"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Realtime Database and get a reference to the service
export const database = getDatabase(app);
export default app;