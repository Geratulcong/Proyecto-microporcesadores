#!/bin/bash
# Script de descarga rápida para Raspberry Pi
# Descarga el código Python sin Git

echo "🚀 Descargando código Python para Raspberry Pi..."

# Crear directorio
mkdir -p ~/microprocesadores_project
cd ~/microprocesadores_project

# Descargar archivos individuales
echo "📄 Descargando sender.py..."
wget -O sender.py https://raw.githubusercontent.com/Geratulcong/Proyecto-microporcesadores/Features/Raspberry-connection/raspberry_pi_code/sender.py

echo "📄 Descargando person_data.json..."
wget -O person_data.json https://raw.githubusercontent.com/Geratulcong/Proyecto-microporcesadores/Features/Raspberry-connection/raspberry_pi_code/person_data.json

echo "📄 Descargando sensor_simulator.py..."
wget -O sensor_simulator.py https://raw.githubusercontent.com/Geratulcong/Proyecto-microporcesadores/Features/Raspberry-connection/raspberry_pi_code/sensor_simulator.py

# Hacer ejecutables
chmod +x *.py

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip3 install requests

echo "✅ ¡Listo! Archivos descargados en:"
echo "   $(pwd)"
echo ""
echo "🚀 Para ejecutar:"
echo "   python3 sender.py"
echo "   python3 sensor_simulator.py"