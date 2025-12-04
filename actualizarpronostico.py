"""
Script: actualizarpronostico.py

Descripción general:
Este script genera y actualiza los pronósticos meteorológicos y el carrusel
de insights para todas las provincias de Argentina a partir de los datos
horarios descargados previamente (CSV por provincia).  

Funciones principales:
1. Comprueba si los JSON de pronóstico y carrusel ya fueron generados hoy.
2. Para cada provincia:
    - Carga el CSV con los datos horarios.
    - Preprocesa los datos (fechas, estación, mes).
    - Entrena el modelo de predicción.
    - Genera pronóstico de 7 días (con íconos y descripciones) y/o carousel de insights.
3. Guarda los resultados en JSON (pronostico.json y carousel.json).
4. Ejecuta procesamiento en paralelo para acelerar la actualización.
"""

# ===========================
# IMPORTS
# ===========================
import os                       # Para manejo de rutas y archivos
import json                     # Para lectura y escritura de JSON
import pandas as pd             # Para manejo de datos tabulares
from datetime import datetime   # Para manejo de fechas
from concurrent.futures import ThreadPoolExecutor, as_completed
                                # Para procesamiento paralelo de provincias

from modelo_pronostico import entrenar_modelo, predecir_7dias, predecir_carousel
                                # Funciones propias para entrenamiento y predicción

from codclimatico import weather_icons, weather_descriptions
                                # Diccionarios para mapear código COCO a íconos y descripciones

from parametros import asignar_estacion
                                # Función para asignar estación meteorológica según mes


# ===========================
# CONSTANTES
# ===========================
RUTA_PRONOSTICO = "web/pronostico.json"
RUTA_CAROUSEL = "web/carousel.json"
PROVINCIA_DIR = "dataset/provincia"


# ===========================
# FUNCIONES
# ===========================

def archivo_del_dia(path_json):
    """
    Verifica si un JSON ya fue generado en el día actual.
    
    Parámetros:
        path_json (str): Ruta del archivo JSON.
        
    Retorna:
        bool: True si el JSON existe y fue generado hoy, False en caso contrario.
    """
    if not os.path.exists(path_json):
        return False
    try:
        with open(path_json,"r",encoding="utf-8") as f:
            data = json.load(f)
    except:
        return False
    fecha_generacion = data.get("fecha_generacion")
    if not fecha_generacion:
        return False
    hoy = datetime.now().strftime("%Y-%m-%d")
    return fecha_generacion == hoy


def procesar_provincia(archivo, actualizar_pronostico=True, actualizar_carousel=True):
    """
    Procesa los datos de una provincia para generar pronóstico y carousel.
    
    Parámetros:
        archivo (str): Nombre del CSV de la provincia (ej: "clima_BuenosAires.csv").
        actualizar_pronostico (bool): Indica si se debe generar el pronóstico 7 días.
        actualizar_carousel (bool): Indica si se debe generar el carousel de insights.
        
    Retorna:
        tuple:
            pronostico (dict | None): Diccionario con pronóstico 7 días (o None si falla/omitido).
            carousel (dict | None): Diccionario con carousel de insights (o None si falla/omitido).
    """
    prov = archivo.replace("clima_","").replace(".csv","")
    csv_path = os.path.join(PROVINCIA_DIR, archivo)
    if not os.path.exists(csv_path):
        print(f"[Actualizar] CSV no encontrado para {prov}")
        return None,None

    df = pd.read_csv(csv_path)
    if df.empty:
        print(f"[Actualizar] Dataset vacío para {prov}")
        return None,None

    # Preprocesamiento de columnas y fechas
    df.columns = df.columns.str.strip().str.lower()
    if "sensaciontermica" in df.columns:
        df.rename(columns={"sensaciontermica":"sensaciontermica"}, inplace=True)
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
    df = df.dropna(subset=["fecha_hora"])
    df["month"] = df["fecha_hora"].dt.month
    df["estacion"] = df["month"].apply(asignar_estacion)
    df["province"] = df["province"].astype(str)

    # Entrena modelo para la provincia
    print(f"[Actualizar] Entrenando modelo para {prov}...")
    modelos, scaler, features = entrenar_modelo(df)

    pronostico = None
    carousel = None

    # Generación de pronóstico 7 días
    if actualizar_pronostico:
        try:
            preds = predecir_7dias(df, modelos, scaler, features, prov)
            for p in preds:
                coco = p["coco"]
                p["icon"] = weather_icons.get(coco,"cloudy.svg")
                p["desc"] = weather_descriptions.get(coco,"N/A")
            pronostico = {"provincia":prov,"pronostico":preds}
        except Exception as e:
            print(f"[Actualizar] Error generando pronóstico para {prov}: {e}")

    # Generación de carousel de insights
    if actualizar_carousel:
        try:
            carousel_data = predecir_carousel(df, modelos, scaler, features, prov)
            carousel = {"provincia":prov,"insights":carousel_data}
        except Exception as e:
            print(f"[Actualizar] Error generando carousel para {prov}: {e}")

    return pronostico, carousel


def main():
    """
    Función principal que coordina la actualización de pronóstico y carousel
    para todas las provincias.
    """
    print("[Actualizar] Iniciando actualización de pronóstico y carrusel...")
    actualizar_pronostico = not archivo_del_dia(RUTA_PRONOSTICO)
    actualizar_carousel = not archivo_del_dia(RUTA_CAROUSEL)

    if not actualizar_pronostico and not actualizar_carousel:
        print("[Actualizar] Ambos JSON ya están actualizados. No se recalcula nada.")
        return

    pronostico_result = []
    carousel_result = []

    archivos_csv = [f for f in os.listdir(PROVINCIA_DIR) if f.endswith(".csv")]

    # Procesamiento paralelo por provincia
    with ThreadPoolExecutor(max_workers=4) as executor:
        futuros = {executor.submit(procesar_provincia, archivo, actualizar_pronostico, actualizar_carousel): archivo for archivo in archivos_csv}
        for futuro in as_completed(futuros):
            pron, car = futuro.result()
            if pron: pronostico_result.append(pron)
            if car: carousel_result.append(car)

    # Guardar JSON de pronóstico
    if actualizar_pronostico:
        salida_pronostico = {"fecha_generacion":datetime.now().strftime("%Y-%m-%d"),"provincias":pronostico_result}
        os.makedirs(os.path.dirname(RUTA_PRONOSTICO), exist_ok=True)
        with open(RUTA_PRONOSTICO,"w",encoding="utf-8") as f:
            json.dump(salida_pronostico,f,indent=4,ensure_ascii=False)
        print(f"[Actualizar] pronostico.json generado correctamente con {len(pronostico_result)} provincias.")

    # Guardar JSON de carousel
    if actualizar_carousel:
        salida_carousel = {"fecha_generacion":datetime.now().strftime("%Y-%m-%d"),"provincias":carousel_result}
        os.makedirs(os.path.dirname(RUTA_CAROUSEL), exist_ok=True)
        with open(RUTA_CAROUSEL,"w",encoding="utf-8") as f:
            json.dump(salida_carousel,f,indent=4,ensure_ascii=False)
        print(f"[Actualizar] carousel.json generado correctamente con {len(carousel_result)} provincias.")


if __name__ == "__main__":
    main()
