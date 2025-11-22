import os
import json
import pandas as pd
from modelo_pronostico import entrenar_modelo, predecir_7dias
from codclimatico import weather_icons, weather_descriptions

RUTA_SALIDA = "web/pronostico.json"
PROVINCIA_DIR = "dataset/provincia"

def main():
    print("[Pronóstico] Generando pronóstico para todas las provincias...")
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
        print(f"[Pronóstico] Entrenando IA para {prov}...")

        modelo, scaler, features = entrenar_modelo(df)
        preds = predecir_7dias(modelo, scaler, features, df)

        for p in preds:
            coco = p["coco"]
            p["icon"] = weather_icons.get(coco, "cloudy.svg")
            p["desc"] = weather_descriptions.get(coco, "N/A")

        resultado.append({
            "provincia": prov,
            "pronostico": preds
        })

    os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
    with open(RUTA_SALIDA, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)

    print("[Pronóstico] pronostico.json generado correctamente.")

if __name__ == "__main__":
    main()
