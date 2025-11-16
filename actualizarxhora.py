"""
Script para actualizar los datos meteorológicos en función de la hora actual.
Este módulo ejecuta el script actualclima.py, que genera los JSON con clima actual
y pronóstico horario para cada provincia.

Entradas:
    No recibe parámetros.

Salidas:
    Genera JSON en /web:
        - clima_actual.json
        - clima_horario.json
"""

import subprocess

print("Actualizando datos meteorologicos...")

subprocess.run(["python", "actualclima.py"], check=False)

print("Datos meteorologicos actualizados.")
