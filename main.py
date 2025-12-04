"""
Sistema principal del proyecto Clima Argentina.

Descripción general:
Este script es el controlador principal que gestiona la actualización de datos,
generación de gráficos, pronósticos IA y la interfaz web. Realiza actualizaciones
automáticas cada hora y permite interactuar con la interfaz HTML a través de pywebview.

Funciones principales:
1. Actualiza datasets completos por fecha.
2. Actualiza datos meteorológicos por hora.
3. Genera gráficos iniciales y actualizaciones.
4. Genera pronóstico IA de 7 días y carrusel de visualización.
5. Monitorea el cambio de hora del sistema y ejecuta actualizaciones automáticas.
6. Lanza la interfaz web usando pywebview.
"""

# ===========================
# IMPORTS
# ===========================
import webview          # Para mostrar la interfaz web dentro de una ventana nativa
import threading        # Para ejecutar la actualización automática en paralelo
import time             # Para pausas temporales (sleep)
import subprocess       # Para ejecutar otros scripts Python desde este script
from datetime import datetime  # Para manejo de fechas
from zoneinfo import ZoneInfo  # Para manejar zonas horarias

# ===========================
# API DE COMUNICACIÓN JS-PYTHON
# ===========================
class Api:
    """Clase que define la comunicación entre JavaScript y Python en la webview."""
    
    def saludar(self, provincia):
        """
        Función de ejemplo llamada desde JS.
        
        Parámetros:
            provincia (str): Nombre de la provincia recibido desde JS.
            
        Retorna:
            str: Devuelve el mismo nombre recibido.
        """
        return f"{provincia}"

# ===========================
# ACTUALIZACIÓN AUTOMÁTICA HORARIA
# ===========================
def actualizar_clima_en_tiempo_real():
    """
    Monitorea la hora del sistema y ejecuta actualizaciones automáticas.
    
    Funcionamiento:
    - Comprueba cada 10 segundos si la hora cambió.
    - Al detectar un cambio de hora, ejecuta scripts de actualización de clima,
        gráficos y pronóstico IA.
    - Mantiene la última hora registrada para evitar actualizaciones repetidas.
    
    Retorna:
        None
    """
    zona = ZoneInfo("America/Argentina/Buenos_Aires")
    ultima_hora = datetime.now(tz=zona).hour
    print(f"[Monitoreo] Hora inicial registrada: {ultima_hora}:00")

    while True:
        time.sleep(10)  # espera 10 segundos antes de volver a comprobar
        hora_actual = datetime.now(tz=zona).hour

        if hora_actual != ultima_hora:
            print(f"\nCambio de hora detectado: {hora_actual}:00")

            # Ejecutar actualización del clima
            try:
                subprocess.run(["python", "actualizarxhora.py"], check=True)
                print("Clima actualizado correctamente.")
            except Exception as e:
                print(f"Error al actualizar el clima: {e}")

            # Ejecutar actualización de gráficos
            try:
                subprocess.run(["python", "actualizargraficos.py"], check=True)
                print("Gráficos actualizados correctamente.")
            except Exception as e:
                print(f"Error al actualizar gráficos: {e}")

            # Ejecutar actualización de pronóstico IA y carrusel
            try:
                subprocess.run(["python", "actualizarpronostico.py"], check=True)
                print("Pronóstico y carousel actualizados correctamente.")
            except Exception as e:
                print(f"Error al actualizar pronóstico y carousel: {e}")

            ultima_hora = hora_actual  # actualizar la hora registrada

# ===========================
# BLOQUE PRINCIPAL
# ===========================
if __name__ == '__main__':
    print("\n========== INICIO DEL SISTEMA ==========\n")

    # --- Paso 1: Actualizar dataset completo ---
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

    # --- Paso 4: Generar pronóstico IA y carrusel inicial ---
    try:
        print("Generando pronóstico IA y carrusel inicial...")
        subprocess.run(["python", "actualizarpronostico.py"], check=True)
        print("Pronóstico IA y carrusel generados correctamente.\n")
    except Exception as e:
        print(f"Error al generar pronóstico y carrusel inicial: {e}")

    # --- Paso 5: Iniciar hilo de monitoreo de hora ---
    hilo = threading.Thread(target=actualizar_clima_en_tiempo_real, daemon=True)
    hilo.start()

    # --- Paso 6: Iniciar interfaz gráfica ---
    print("Iniciando interfaz...\n")
    api = Api()
    window = webview.create_window("El clima en Argentina", "web/index.html", js_api=api)
    webview.start()

    print("\n========== SISTEMA FINALIZADO ==========\n")
