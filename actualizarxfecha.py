"""
Script para actualizar el dataset basado en fecha y hora.
Este archivo ejecuta los scripts necesarios para actualizar la lista de estaciones
y los datos horarios descargados desde la API.

Entradas:
    No recibe parámetros directamente.

Salidas:
    Ejecuta otros scripts que generan o actualizan archivos CSV de estaciones y clima.
"""

import subprocess

print("Actualizando la fecha y hora ...")

subprocess.run(["python", "stations.py"], check=False)
subprocess.run(["python", "data.py"], check=False)

print("Datos horarios actualizados.")
