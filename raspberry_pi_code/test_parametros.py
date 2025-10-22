#!/usr/bin/env python3
"""
Script de Prueba con Parámetros
Proyecto Microprocesadores - Demostración de parámetros

Este script demuestra cómo recibir y usar parámetros desde la web.
"""

import argparse
import time
import sys
import json
from datetime import datetime

def parse_arguments():
    """Parsear argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Script de prueba con parámetros configurables",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Parámetros de ejemplo
    parser.add_argument(
        '--mensaje', 
        type=str, 
        default="Hola desde Raspberry Pi",
        help='Mensaje a mostrar'
    )
    
    parser.add_argument(
        '--repeticiones', 
        type=int, 
        default=5,
        help='Número de repeticiones del mensaje'
    )
    
    parser.add_argument(
        '--intervalo', 
        type=float, 
        default=1.0,
        help='Intervalo entre mensajes en segundos'
    )
    
    parser.add_argument(
        '--formato_json', 
        action='store_true',
        help='Mostrar salida en formato JSON'
    )
    
    parser.add_argument(
        '--incluir_timestamp', 
        action='store_true',
        help='Incluir timestamp en cada mensaje'
    )
    
    parser.add_argument(
        '--tipo_salida', 
        choices=['simple', 'detallado', 'compacto'],
        default='simple',
        help='Tipo de formato de salida'
    )
    
    return parser.parse_args()

def mostrar_configuracion(args):
    """Mostrar configuración actual"""
    print("🎯 Script de Prueba con Parámetros Iniciado")
    print("=" * 50)
    print(f"📝 Mensaje: {args.mensaje}")
    print(f"🔢 Repeticiones: {args.repeticiones}")
    print(f"⏱️  Intervalo: {args.intervalo}s")
    print(f"📊 Formato JSON: {'Sí' if args.formato_json else 'No'}")
    print(f"🕐 Timestamp: {'Sí' if args.incluir_timestamp else 'No'}")
    print(f"📋 Tipo salida: {args.tipo_salida}")
    print("=" * 50)

def generar_mensaje(args, numero):
    """Generar mensaje según configuración"""
    timestamp = datetime.now().isoformat() if args.incluir_timestamp else None
    
    if args.formato_json:
        data = {
            "numero": numero,
            "mensaje": args.mensaje,
            "configuracion": {
                "repeticiones_total": args.repeticiones,
                "intervalo": args.intervalo,
                "tipo_salida": args.tipo_salida
            }
        }
        
        if timestamp:
            data["timestamp"] = timestamp
            
        return json.dumps(data, indent=2 if args.tipo_salida == 'detallado' else None)
    
    else:
        # Formato texto
        if args.tipo_salida == 'simple':
            base = f"[{numero}/{args.repeticiones}] {args.mensaje}"
        elif args.tipo_salida == 'detallado':
            base = f"🔹 Mensaje #{numero} de {args.repeticiones}: {args.mensaje}"
        else:  # compacto
            base = f"{numero}: {args.mensaje}"
        
        if timestamp:
            base = f"[{timestamp}] {base}"
            
        return base

def main():
    """Función principal"""
    try:
        # Parsear argumentos
        args = parse_arguments()
        
        # Mostrar configuración
        mostrar_configuracion(args)
        
        # Ejecutar bucle principal
        for i in range(1, args.repeticiones + 1):
            mensaje = generar_mensaje(args, i)
            print(mensaje)
            
            # Pausa entre mensajes (excepto en el último)
            if i < args.repeticiones:
                time.sleep(args.intervalo)
        
        print("\n✅ Script completado exitosamente")
        
        # Resumen final
        if args.tipo_salida == 'detallado':
            print(f"\n📊 Resumen:")
            print(f"   • Total de mensajes: {args.repeticiones}")
            print(f"   • Tiempo total: ~{args.repeticiones * args.intervalo:.1f}s")
            print(f"   • Configuración: {args.tipo_salida} + JSON: {args.formato_json}")
    
    except KeyboardInterrupt:
        print("\n⏹️ Script interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()