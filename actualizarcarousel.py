"""
Genera predicciones del carrusel para todas las provincias
usando SVR (Support Vector Regression)
"""

import os
import json
import pandas as pd
from modelo_carousel import predecir_manana

RUTA_SALIDA = "web/carousel.json"
PROVINCIA_DIR = "dataset/provincia"


def main():
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

    # Guardar JSON
    os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
    with open(RUTA_SALIDA, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)

    print(f"[Carrusel] {RUTA_SALIDA} generado correctamente con {len(resultado)} provincias.")


if __name__ == "__main__":
    main()
