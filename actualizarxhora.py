"""
Módulo: actualización de datos meteorológicos actuales

Este script ejecuta el módulo `actualclima.py` para generar los JSON con:
- clima_actual.json
- clima_horario.json

Entradas:
    Ninguna directamente.

Salidas:
    Archivos JSON en /web con datos meteorológicos por provincia.
"""

# ============================
# Imports principales
# ============================
import subprocess  # Para ejecutar otros scripts de Python

# ============================
# Ejecución principal
# ============================
print("Actualizando datos meteorologicos...")

# Ejecuta el script que genera los JSON
subprocess.run(["python", "actualclima.py"], check=False)

print("Datos meteorologicos actualizados.")
