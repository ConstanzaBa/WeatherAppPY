"""
Genera y actualiza el archivo dataset/stations.csv con la estación meteorológica
más representativa de cada provincia argentina.
"""

from meteostat import Stations
import pandas as pd
import os

def esta_actualizado(archivo):
    return os.path.exists(archivo)

os.makedirs("dataset", exist_ok=True)

provincias = {
    "Buenos Aires": (-34.9, -57.9),
    "Catamarca": (-28.4, -65.7),
    "Chaco": (-27.4, -58.9),
    "Chubut": (-43.3, -65.1),
    "Córdoba": (-31.4, -64.1),
    "Corrientes": (-27.9, -58.0),
    "Entre Ríos": (-31.7, -60.5),
    "Formosa": (-26.1, -58.1),
    "Jujuy": (-24.1, -65.2),
    "La Pampa": (-36.6, -64.2),
    "La Rioja": (-29.4, -66.8),
    "Mendoza": (-32.8, -68.8),
    "Misiones": (-27.3, -55.8),
    "Neuquén": (-38.9, -68.0),
    "Río Negro": (-40.8, -65.4),
    "Salta": (-24.7, -65.4),
    "San Juan": (-31.5, -68.5),
    "San Luis": (-33.3, -66.3),
    "Santa Cruz": (-51.6, -69.2),
    "Santa Fe": (-31.6, -60.7),
    "Santiago del Estero": (-27.8, -64.2),
    "Tierra del Fuego": (-54.8, -68.3),
    "Tucumán": (-26.8, -65.2)
}

def obtener_estacion_valida(lat, lon, provincia):
    estaciones = Stations().nearby(lat, lon).fetch(5)
    if estaciones.empty:
        return None

    estaciones["id_estacion"] = estaciones.apply(
        lambda x: x["wmo"] if pd.notna(x["wmo"])
        else x["icao"] if pd.notna(x["icao"])
        else None,
        axis=1
    )
    estaciones = estaciones.dropna(subset=["id_estacion"])
    if estaciones.empty:
        return None

    estacion = estaciones.iloc[0].copy()
    estacion["province"] = provincia
    return estacion

def generar_csv_estaciones():
    stations_path = "dataset/stations.csv"
    if esta_actualizado(stations_path):
        print("stations.csv ya existe. No se genera nuevamente.")
        return

    print("Generando stations.csv...")

    lista = []
    for provincia, (lat, lon) in provincias.items():
        est = obtener_estacion_valida(lat, lon, provincia)
        if est is not None:
            lista.append(est)
            print(f"Estación encontrada para {provincia}")
        else:
            print(f"No se encontró estación válida para {provincia}")

    df = pd.DataFrame(lista)
    df.to_csv(stations_path, index=False)
    print("\nstations.csv creado correctamente.")

if __name__ == "__main__":
    generar_csv_estaciones()
