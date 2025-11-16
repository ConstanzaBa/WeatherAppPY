"""
Sistema principal del proyecto Clima Argentina.

Este script:
1. Actualiza datasets por fecha (estaciones y provincias)
2. Actualiza los datos meteorológicos según la hora actual
3. Genera todos los gráficos iniciales
4. Inicia un hilo que detecta cuando cambia la hora real del sistema
5. Vuelve a actualizar datos + gráficos automáticamente cada hora
6. Abre la interfaz HTML utilizando pywebview
"""

import webview
import threading
import time
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

class Api:
    """Comunicación JS con Python."""
    def saludar(self, provincia):
        return f"{provincia}"

def actualizar_clima_en_tiempo_real():
    zona = ZoneInfo("America/Argentina/Buenos_Aires")
    ultima_hora = datetime.now(tz=zona).hour
    print(f"[Monitoreo] Hora inicial registrada: {ultima_hora}:00")

    while True:
        time.sleep(10)
        hora_actual = datetime.now(tz=zona).hour
        if hora_actual != ultima_hora:
            print(f"\nCambio de hora detectado: {hora_actual}:00")
            try:
                subprocess.run(["python", "actualizarxhora.py"], check=True)
                print("Clima actualizado correctamente.")
            except Exception as e:
                print(f"Error al actualizar el clima: {e}")
            try:
                subprocess.run(["python", "actualizargraficos.py"], check=True)
                print("Gráficos actualizados correctamente.")
            except Exception as e:
                print(f"Error al actualizar gráficos: {e}")
            ultima_hora = hora_actual

if __name__ == '__main__':
    print("\n========== INICIO DEL SISTEMA ==========\n")

    try:
        print("Actualizando dataset completo...")
        subprocess.run(["python", "actualizarxfecha.py"], check=True)
        print("Dataset actualizado.\n")
    except Exception as e:
        print(f"Error al actualizar dataset inicial: {e}")

    hora_actual = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).hour
    try:
        print(f"Actualizando clima inicial para la hora {hora_actual}:00...")
        subprocess.run(["python", "actualizarxhora.py"], check=True)
        print("Clima inicial listo.\n")
    except Exception as e:
        print(f"Error al actualizar clima inicial: {e}")

    try:
        print("Generando gráficos iniciales...")
        subprocess.run(["python", "actualizargraficos.py"], check=True)
        print("Gráficos generados.\n")
    except Exception as e:
        print(f"Error al generar gráficos: {e}")

    hilo = threading.Thread(target=actualizar_clima_en_tiempo_real, daemon=True)
    hilo.start()

    print("Iniciando interfaz...\n")
    api = Api()
    window = webview.create_window("El clima en Argentina", "web/index.html", js_api=api)
    webview.start()

    print("\n========== SISTEMA FINALIZADO ==========\n")
