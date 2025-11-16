"""
Script para actualizar los gráficos de temperatura de todas las provincias.
Este módulo se ejecuta después de que los datos climáticos han sido actualizados.

Funciones:
    - Ejecuta la generación de gráficos llamando a generar_graficos_provincia()

Entradas:
    No recibe parámetros.

Salidas:
    Genera y guarda archivos PNG de gráficos en el directorio configurado por graficos.py
"""

from graficos import cargar_datos, generar_todos_los_graficos_web

if __name__ == "__main__":
    print("\n--- Actualizando gráficos ---\n")

    df = cargar_datos()
    generar_todos_los_graficos_web(df)

    print("\n--- Actualización completada ---\n")
