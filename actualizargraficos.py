"""
Script para actualizar los gráficos de temperatura de todas las provincias.
Este módulo se ejecuta después de que los datos climáticos han sido actualizados.

Funciones:
    - Llama a generar_todos_los_graficos() sin parámetros
Entradas:
    No recibe parámetros.
Salidas:
    Genera y guarda PNGs para cada provincia en /graficos/
"""

from graficos import generar_todos_los_graficos

if __name__ == "__main__":
    print("\n--- Actualizando gráficos ---\n")

    generar_todos_los_graficos()

    print("\n--- Actualización completada ---\n")
