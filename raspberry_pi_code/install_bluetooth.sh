#!/bin/bash
# Script de instalación completo para Raspberry Pi
# Proyecto Microprocesadores - Arduino + Raspberry Pi + Firebase

echo "🚀 Configurando Raspberry Pi para recepción Bluetooth del Arduino Nano 33 BLE Sense"
echo "=" * 80

# Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
echo "🔧 Instalando dependencias del sistema..."
sudo apt install -y python3 python3-pip bluetooth bluez git curl wget

# Instalar dependencias Python
echo "🐍 Instalando librerías Python..."
pip3 install --user requests bleak asyncio

# Habilitar Bluetooth
echo "🔵 Configurando Bluetooth..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Configurar permisos Bluetooth para usuario pi
sudo usermod -a -G bluetooth $USER

echo "✅ Instalación completada!"
echo ""
echo "📋 Pasos siguientes:"
echo "1. Reiniciar Raspberry Pi: sudo reboot"
echo "2. Cargar código en Arduino Nano 33 BLE Sense"
echo "3. Ejecutar receptor: python3 bluetooth_receiver.py"
echo ""
echo "🔍 Para verificar Bluetooth:"
echo "   bluetoothctl"
echo "   power on"
echo "   scan on"
echo ""
echo "📱 El Arduino debe aparecer como 'Arduino Postura Sensor'"