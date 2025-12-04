"""
Módulo: actualización de gráficos meteorológicos

Este script genera los gráficos de temperatura de todas las provincias,
basándose en los datos climáticos previamente actualizados.

Funciones principales:
    - generar_todos_los_graficos(): genera y guarda los PNG para cada provincia

Entradas:
    Ninguna.

Salidas:
    Archivos PNG guardados en /graficos/ por cada provincia.
"""

# ============================
# Imports principales
# ============================
from graficos import generar_todos_los_graficos  # Función que genera todos los gráficos

# ============================
# Ejecución principal
# ============================
if __name__ == "__main__":
    print("\n--- Actualizando gráficos ---\n")

    # Genera los gráficos
    generar_todos_los_graficos()

    print("\n--- Actualización completada ---\n")
