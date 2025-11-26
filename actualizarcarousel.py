"""
Genera predicciones del carrusel para todas las provincias
usando SVR (Support Vector Regression)
"""

import os
import json
import pandas as pd
from datetime import datetime
from modelo_carousel import predecir_manana

RUTA_SALIDA = "web/carousel.json"
PROVINCIA_DIR = "dataset/provincia"


# =====================================================
# Chequear si ya existe un carrusel del día actual
# =====================================================
def carousel_del_dia(path_json):
    if not os.path.exists(path_json):
        return False
    
    try:
        with open(path_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return False

    fecha_generacion = data.get("fecha_generacion")
    hoy = datetime.now().strftime("%Y-%m-%d")

    return fecha_generacion == hoy


# =====================================================
# MAIN PRINCIPAL
# =====================================================
def main():
    print("[Carrusel] Verificando si es necesario recalcular...")

    # Si ya existe el carousel del día → no recalcular
    if carousel_del_dia(RUTA_SALIDA):
        print("[Carrusel] Ya existe el carrusel de hoy. No se recalcula.")
        return

    print("[Carrusel] Generando carrusel para todas las provincias...")
    resultado = []

    for archivo in os.listdir(PROVINCIA_DIR):
        if not archivo.endswith(".csv"):
            continue

        prov = archivo.replace("clima_", "").replace(".csv", "")
        csv_path = os.path.join(PROVINCIA_DIR, archivo)

        if not os.path.exists(csv_path):
            print(f"[Carrusel] CSV no encontrado para {prov}")
            continue

        try:
            df = pd.read_csv(csv_path)

            if df.empty:
                print(f"[Carrusel] Dataset vacío para {prov}, omitiendo...")
                continue

            print(f"[Carrusel] Prediciendo datos de carrusel para {prov}...")

            carousel_data = predecir_manana(df)

            resultado.append({
                "provincia": prov,
                "insights": carousel_data
            })

        except Exception as e:
            print(f"[Carrusel] Error procesando {prov}: {e}")
            continue

    # Agregar fecha
    salida = {
        "fecha_generacion": datetime.now().strftime("%Y-%m-%d"),
        "provincias": resultado
    }

    # Guardar JSON final
    os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
    with open(RUTA_SALIDA, "w", encoding="utf-8") as f:
        json.dump(salida, f, indent=4, ensure_ascii=False)

    print(f"[Carrusel] carousel.json generado correctamente con {len(resultado)} provincias.")


if __name__ == "__main__":
    main()
