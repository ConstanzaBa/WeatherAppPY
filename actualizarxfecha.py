"""
Módulo: actualización de datasets meteorológicos

Este script ejecuta los scripts `stations.py` y `data.py` para:
- Actualizar la lista de estaciones
- Descargar y mantener actualizados los datos horarios

Entradas:
    Ninguna directamente.

Salidas:
    Archivos CSV de estaciones y datos horarios generados o actualizados.
"""

# ============================
# Imports principales
# ============================
import subprocess  # Para ejecutar scripts externos

# ============================
# Ejecución principal
# ============================
print("Actualizando la fecha y hora ...")

# Ejecuta la actualización de estaciones
subprocess.run(["python", "stations.py"], check=False)

# Ejecuta la actualización de datos horarios
subprocess.run(["python", "data.py"], check=False)

print("Datos horarios actualizados.")
