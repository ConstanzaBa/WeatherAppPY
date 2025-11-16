"""
Script para actualizar los gráficos de temperatura de todas las provincias.
Este módulo se ejecuta después de que los datos climáticos han sido actualizados.

Funciones:
    - Ejecuta la generación de gráficos llamando a generar_graficos_todas_provincias_web()

Entradas:
    No recibe parámetros.

Salidas:
    Genera y guarda archivos PNG de gráficos en el directorio configurado por graficos.py
"""

from graficos import generar_graficos_todas_provincias_web

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Actualizando Graficos...")
    print("=" * 60 + "\n")

    generar_graficos_todas_provincias_web()

    print("\n" + "=" * 60)
    print("Actualizacion Completada.")
    print("=" * 60)
