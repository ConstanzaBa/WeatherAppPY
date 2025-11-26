import os
import json
import pandas as pd
from datetime import datetime
from modelo_pronostico import entrenar_modelo, predecir_7dias
from codclimatico import weather_icons, weather_descriptions

RUTA_SALIDA = "web/pronostico.json"
PROVINCIA_DIR = "dataset/provincia"


# =====================================================
# Chequear si ya existe un pronóstico del día actual
# =====================================================
def pronostico_del_dia(path_json):
    if not os.path.exists(path_json):
        return False
    
    try:
        with open(path_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return False

    # ---- NUEVO ----
    # Si el JSON es una LISTA → formato viejo → regenerar sí o sí
    if isinstance(data, list):
        return False

    # Si falta fecha → regenerar
    fecha_generacion = data.get("fecha_generacion")
    if not fecha_generacion:
        return False

    hoy = datetime.now().strftime("%Y-%m-%d")
    return fecha_generacion == hoy


# =====================================================
# MAIN PRINCIPAL
# =====================================================
def main():
    print("[Pronóstico] Verificando si es necesario recalcular...")

    if pronostico_del_dia(RUTA_SALIDA):
        print("[Pronóstico] Ya existe el pronóstico del día. No se recalcula.")
        return

    print("[Pronóstico] Generando NUEVO pronóstico para todas las provincias...")
    resultado = []

    for archivo in os.listdir(PROVINCIA_DIR):
        if not archivo.endswith(".csv"):
            continue

        prov = archivo.replace("clima_", "").replace(".csv", "")
        csv_path = os.path.join(PROVINCIA_DIR, archivo)

        if not os.path.exists(csv_path):
            print(f"[Pronóstico] CSV no encontrado para {prov}")
            continue

        df = pd.read_csv(csv_path)
        if df.empty:
            print(f"[Pronóstico] Dataset vacío para {prov}, omitiendo...")
            continue

        print(f"[Pronóstico] Entrenando IA para {prov}...")

        modelo, scaler, features = entrenar_modelo(df)
        preds = predecir_7dias(modelo, scaler, features, df)

        # agregar íconos y descripciones
        for p in preds:
            coco = p["coco"]
            p["icon"] = weather_icons.get(coco, "cloudy.svg")
            p["desc"] = weather_descriptions.get(coco, "N/A")

        resultado.append({
            "provincia": prov,
            "pronostico": preds
        })

    # agregar fecha de generación
    salida = {
        "fecha_generacion": datetime.now().strftime("%Y-%m-%d"),
        "provincias": resultado
    }

    os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
    with open(RUTA_SALIDA, "w", encoding="utf-8") as f:
        json.dump(salida, f, indent=4, ensure_ascii=False)

    print("[Pronóstico] pronostico.json generado correctamente.")


if __name__ == "__main__":
    main()
