import webview  # esta es para usar html
import threading  # esta es para las tareas en segundo plano
import time 
import subprocess  # y esta es para ejecutar los .py desde el main
from datetime import datetime
from zoneinfo import ZoneInfo

class Api:
    def saludar(self, provincia):
        return f"¡Hola desde {provincia}!"

def actualizar_clima_en_tiempo_real():
    ultima_hora = None  # guardamos la última hora que actualizamos

    while True:
        ahora = datetime.now(tz=ZoneInfo("America/Argentina/Buenos_Aires"))
        hora_actual = ahora.hour

        # Ejecutamos solo si cambió la hora
        if hora_actual != ultima_hora:
            try:
                print(f"{ahora.strftime('%H:%M:%S')} → Actualizando el clima...")
                subprocess.run(["python", "actualizarxhora.py"], check=True)
                print("Actualización exitosa.")
            except Exception as e:
                print(f"Error al actualizar el clima: {e}")
            
            ultima_hora = hora_actual 

        # Revisamos cada 10 segundos si cambió la hora
        time.sleep(10)

if __name__ == '__main__':
    # Actualizamos los datos iniciales antes de abrir la ventana
    print("Actualizando datos iniciales antes de abrir la ventana...")
    subprocess.run(["python", "actualizarxhora.py"], check=True)
    print("Datos iniciales listos. Abriendo ventana...")

    # hilo daemon que ejecuta la función de actualización en tiempo real
    hilo = threading.Thread(target=actualizar_clima_en_tiempo_real, daemon=True)
    hilo.start()

    api = Api()

    # ventana principal
    window = webview.create_window(
        "El clima en Argentina",
        "web/index.html",
        js_api=api
    )

    # inicia la ventana (bloquea el hilo principal)
    webview.start()

# ejecutar 
# venv\Scripts\activate.bat
# python main.py