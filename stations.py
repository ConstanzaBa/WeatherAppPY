"""
Módulo: generación y actualización de stations.csv

Este script genera y mantiene actualizado el archivo `dataset/stations.csv`
con la estación meteorológica más cercana a las coordenadas de cada provincia
argentina.

Funciones principales:
- obtener_estacion_exacta(lat, lon, provincia): devuelve la estación más cercana.
- generar_csv_estaciones(): genera el CSV con todas las provincias.
"""

# ============================
# Imports principales
# ============================
from meteostat import Stations  # Librería para obtener estaciones meteorológicas
import pandas as pd             # Manejo de DataFrames
import os                       # Gestión de archivos y directorios

# ============================
# Diccionario de coordenadas
# ============================
# Coordenadas aproximadas (latitud, longitud) de cada capital provincial
provincias = {
    "Buenos Aires": (-34.5667, -58.4167),
    "Catamarca": (-28.6, -65.7667),
    "Chaco": (-26.7333, -60.4833),
    "Chubut": (-42.77, -65.1),
    "Córdoba": (-31.45, -64.2667),
    "Corrientes": (-27.45, -59.05),
    "Entre Ríos": (-33, -58.6167),
    "Formosa": (-26.85, -58.3167),
    "Jujuy": (-24.3833, -65.0833),
    "La Pampa": (-36.5667, -64.2667),
    "La Rioja": (-29.2333, -67.4333),
    "Mendoza": (-32.8333, -68.7833),
    "Misiones": (-27.3667, -55.9667),
    "Neuquén": (-40.0833, -71.1333),
    "Río Negro": (-41.25, -68.7333),
    "Salta": (-23.15, -64.3167),
    "San Juan": (-32.6, -69.3333),
    "San Luis": (-33.7333, -65.3833),
    "Santa Cruz": (-49.3167, -67.75),
    "Santa Fe": (-32.9167, -60.7833),
    "Santiago del Estero": (-29.9, -63.6833),
    "Tierra del Fuego": (-54.8, -68.3167),
    "Tucumán": (-26.85, -65.1)
}

# ============================
# Funciones auxiliares
# ============================

def esta_actualizado(archivo):
    """
    Verifica si un archivo existe en el sistema.

    Parámetros:
        archivo (str): Ruta del archivo

    Retorna:
        bool: True si existe, False si no
    """
    return os.path.exists(archivo)

def obtener_estacion_exacta(lat, lon, provincia):
    """
    Obtiene la estación meteorológica más cercana a las coordenadas dadas.

    Parámetros:
        lat (float): Latitud
        lon (float): Longitud
        provincia (str): Nombre de la provincia

    Retorna:
        pd.Series | None: Serie con los datos de la estación o None si no se encuentra
    """
    try:
        estaciones = Stations().nearby(lat, lon).fetch(1)
    except Exception as e:
        print(f"Error al buscar estaciones para {provincia}: {e}")
        return None

    if estaciones.empty:
        print(f"No se encontraron estaciones cerca de {provincia}")
        return None

    # Seleccionamos la estación más cercana
    estacion = estaciones.iloc[0].copy()
    estacion["province"] = provincia
    # ID de estación: prioriza WMO (id mundial), si no existe usa ICAO(id internacional)
    estacion["id_estacion"] = estacion["wmo"] if pd.notna(estacion["wmo"]) else estacion["icao"]
    return estacion

def generar_csv_estaciones():
    """
    Genera el CSV con las estaciones meteorológicas de cada provincia argentina.
    Si el archivo ya existe, no se sobrescribe.

    Retorna:
        None
    """
    os.makedirs("dataset", exist_ok=True)
    stations_path = "dataset/stations.csv"

    if esta_actualizado(stations_path):
        print("stations.csv ya existe. No se genera nuevamente.")
        return

    print("Generando stations.csv...")
    lista = []

    for provincia, (lat, lon) in provincias.items():
        est = obtener_estacion_exacta(lat, lon, provincia)
        if est is not None:
            lista.append(est)
            print(f"Estación encontrada para {provincia}")
        else:
            print(f"No se pudo obtener una estación para {provincia}")

    if lista:
        df = pd.DataFrame(lista)
        df.to_csv(stations_path, index=False)
        print("\nstations.csv creado correctamente.")
    else:
        print("No se generó ningún CSV porque no se encontraron estaciones.")

# ============================
# Ejecutable
# ============================

if __name__ == "__main__":
    generar_csv_estaciones()
