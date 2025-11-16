"""
Sistema principal del proyecto Clima Argentina.

Este script:
1. Actualiza datasets por fecha (estaciones y provincias)
2. Actualiza los datos meteorológicos según la hora actual
3. Genera todos los gráficos iniciales
4. Inicia un hilo que detecta cuando cambia la hora real del sistema
5. Vuelve a actualizar datos + gráficos automáticamente cada hora
6. Abre la interfaz HTML utilizando pywebview

Entradas:
    - No recibe parámetros externos.

Salidas:
    - Ejecuta scripts secundarios mediante subprocess.
    - Actualiza archivos CSV y PNG dentro de /web.

Dependencias externas:
    - pywebview
    - estaciones.py / data.py / actualclima.py / graficos.py
"""

import webview          
import threading        
import time
import subprocess       
from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
#      API expuesta para JavaScript (interacción con la UI)
# ============================================================

class Api:
    """API: comunicación JS con Python."""
    def saludar(self, provincia):
        return f"{provincia}"


# ============================================================
#         SISTEMA DE ACTUALIZACIÓN HORARIA AUTOMÁTICA
# ============================================================

def actualizar_clima_en_tiempo_real():
    """
    Monitorea cada 10 segundos la hora actual.
    Cuando detecta un cambio de hora real:
        - Ejecuta actualizarxhora.py  (actualiza clima)
        - Ejecuta actualizargraficos.py (regenera gráficos)

    Corre en un hilo daemon, sin bloquear la interfaz.
    """
    zona = ZoneInfo("America/Argentina/Buenos_Aires")
    ahora = datetime.now(tz=zona)

    ultima_hora = ahora.hour
    print(f"[Monitoreo] Hora inicial registrada: {ultima_hora}:00\n")

    while True:
        time.sleep(10)

        ahora = datetime.now(tz=zona)
        hora_actual = ahora.hour

        if hora_actual != ultima_hora:
            print("..........................................................")
            print(f"{ahora.strftime('%H:%M:%S')} Cambio de hora detectado.")
            print(f"Actualizando clima y gráficos para las {hora_actual}:00...\n")

            # 1 — Actualizar clima por hora
            try:
                subprocess.run(["python", "actualizarxhora.py"], check=True)
                print("Clima actualizado correctamente.")
            except Exception as e:
                print(f"Error al actualizar el clima: {e}")

            # 2 — Regenerar gráficos
            try:
                print("Actualizando gráficos...")
                subprocess.run(["python", "actualizargraficos.py"], check=True)
                print("Gráficos actualizados correctamente.")
            except Exception as e:
                print(f"Error al actualizar gráficos: {e}")

            ultima_hora = hora_actual


# ============================================================
#                         MAIN
# ============================================================

if __name__ == '__main__':

    zona = ZoneInfo("America/Argentina/Buenos_Aires")
    hora_actual = datetime.now(tz=zona).hour

    print("\n========== INICIO DEL SISTEMA ==========\n")

    # 1 — Actualización general según la fecha
    try:
        print("Actualizando dataset completo (fecha)...")
        subprocess.run(["python", "actualizarxfecha.py"], check=True)
        print("Dataset actualizado.")
    except Exception as e:
        print(f"Error al actualizar dataset inicial: {e}")

    # 2 — Actualizar clima según hora actual
    try:
        print(f"Actualizando clima inicial para la hora {hora_actual}:00...")
        subprocess.run(["python", "actualizarxhora.py"], check=True)
        print("Clima inicial listo.")
    except Exception as e:
        print(f"Error al actualizar clima inicial: {e}")

    # 3 — Generar gráficos iniciales
    try:
        print("Generando gráficos iniciales...")
        subprocess.run(["python", "actualizargraficos.py"], check=True)
        print("Gráficos generados.")
    except Exception as e:
        print(f"Error al generar gráficos: {e}")

    # 4 — Activar el hilo que detecta el cambio de hora real
    hilo = threading.Thread(target=actualizar_clima_en_tiempo_real, daemon=True)
    hilo.start()

    # 5 — Crear ventana WebView
    print("\nIniciando interfaz ...\n")

    api = Api()
    window = webview.create_window(
        "El clima en Argentina",
        "web/index.html",
        js_api=api
    )

    webview.start()

    print("\n========== SISTEMA FINALIZADO ==========\n")



# Ejecutar:
#     venv\Scripts\activate.bat
#     python main.py

