"""
Script para actualizar los gráficos de temperatura de forma automática
Se ejecuta después de actualizar los datos climáticos
"""

from graficos import generar_graficos_todas_provincias_web

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  ACTUALIZANDO GRÁFICOS DE TEMPERATURA PARA LA WEB")
    print("="*60 + "\n")
    
    generar_graficos_todas_provincias_web()
    
    print("\n" + "="*60)
    print("  ✓ ACTUALIZACIÓN COMPLETADA")
    print("="*60)
