"""
Sistema principal del proyecto Clima Argentina.

Este script:
1. Actualiza datasets por fecha (estaciones y provincias)
2. Actualiza los datos meteorológicos según la hora actual
3. Genera todos los gráficos iniciales
4. Genera el pronóstico IA de 7 días
5. Inicia un hilo que detecta cuando cambia la hora real del sistema
6. Vuelve a actualizar datos + gráficos + pronóstico automáticamente cada hora
7. Abre la interfaz HTML utilizando pywebview
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

            # Actualizar pronóstico IA cada hora
            try:
                subprocess.run(["python", "actualizarpronostico.py"], check=True)
                print("Pronóstico actualizado correctamente.")
            except Exception as e:
                print(f"Error al actualizar pronóstico IA: {e}")

            # Actualizar insights del carrusel cada hora
            try:
                subprocess.run(["python", "actualizarcarousel.py"], check=True)
                print("Insights del carrusel actualizados correctamente.")
            except Exception as e:
                print(f"Error al actualizar carousel: {e}")

            ultima_hora = hora_actual


if __name__ == '__main__':
    print("\n========== INICIO DEL SISTEMA ==========\n")

    # --- Paso 1: Actualizar dataset diario ---
    try:
        print("Actualizando dataset completo...")
        subprocess.run(["python", "actualizarxfecha.py"], check=True)
        print("Dataset actualizado.\n")
    except Exception as e:
        print(f"Error al actualizar dataset inicial: {e}")

    # --- Paso 2: Actualización inicial por hora ---
    hora_actual = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).hour
    try:
        print(f"Actualizando clima inicial para la hora {hora_actual}:00...")
        subprocess.run(["python", "actualizarxhora.py"], check=True)
        print("Clima inicial listo.\n")
    except Exception as e:
        print(f"Error al actualizar clima inicial: {e}")

    # --- Paso 3: Generar gráficos iniciales ---
    try:
        print("Generando gráficos iniciales...")
        subprocess.run(["python", "actualizargraficos.py"], check=True)
        print("Gráficos generados.\n")
    except Exception as e:
        print(f"Error al generar gráficos: {e}")

    # --- Paso 4: Generar pronóstico IA inicial ---
    try:
        print("Generando pronóstico IA inicial...")
        subprocess.run(["python", "actualizarpronostico.py"], check=True)
        print("Pronóstico IA generado.\n")
    except Exception as e:
        print(f"Error al generar pronóstico IA: {e}")

    # --- Paso 5: Generar datos del carrusel ---
    try:
        print("Generando datos del carrusel...")
        subprocess.run(["python", "actualizarcarousel.py"], check=True)
        print("Datos del carrusel generados.\n")
    except Exception as e:
        print(f"Error al generar datos del carrusel: {e}")
        print("Pronóstico inicial generado.\n")
    except Exception as e:
        print(f"Error al generar pronóstico IA inicial: {e}")

    # --- Paso 5: Iniciar hilo de monitoreo de hora ---
    hilo = threading.Thread(target=actualizar_clima_en_tiempo_real, daemon=True)
    hilo.start()

    # --- Paso 6: Iniciar interfaz gráfica ---
    print("Iniciando interfaz...\n")
    api = Api()
    window = webview.create_window("El clima en Argentina", "web/index.html", js_api=api)
    webview.start()

    print("\n========== SISTEMA FINALIZADO ==========\n")
