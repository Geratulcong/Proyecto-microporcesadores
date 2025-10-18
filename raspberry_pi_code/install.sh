#!/bin/bash
# Script de instalación para Raspberry Pi
# Proyecto Microprocesadores - Sistema de Posturas

echo "🚀 Configurando Raspberry Pi para envío de datos..."

# Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt update
sudo apt upgrade -y

# Instalar Python3 y pip si no están instalados
echo "🐍 Verificando Python3..."
sudo apt install python3 python3-pip -y

# Instalar dependencias Python
echo "📚 Instalando librerías Python..."
pip3 install requests

# Crear directorio del proyecto
echo "📁 Creando estructura de directorios..."
mkdir -p ~/microprocesadores_project
cd ~/microprocesadores_project

# Copiar archivos (debes copiar sender.py y person_data.json aquí)
echo "📄 Copia los archivos sender.py y person_data.json a este directorio:"
echo "   $(pwd)"

# Hacer ejecutable el script
chmod +x sender.py

echo "✅ Configuración completada!"
echo ""
echo "📋 Para usar:"
echo "   python3 sender.py                 # Enviar una vez"
echo "   python3 sender.py --continuous    # Enviar continuamente"
echo ""
echo "📝 Edita person_data.json para cambiar los datos a enviar"