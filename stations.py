"""
Script: stations.py
-------------------

Genera y actualiza el archivo `dataset/stations.csv` con la estación meteorológica
más representativa de cada provincia argentina.

Flujo general:
1. Contiene un diccionario con el nombre y coordenadas de cada provincia.
2. Para cada provincia:
    - Busca las 5 estaciones más cercanas usando Meteostat.
    - Selecciona la estación que tenga un identificador válido (WMO o ICAO).
    - Guarda la estación junto con el nombre de la provincia.
3. Crea/actualiza el CSV final en dataset/stations.csv.

Entradas:
    - No recibe parámetros externos.
    - Requiere acceso a la API de Meteostat.

Salidas:
    - Crea/actualiza archivo CSV: dataset/stations.csv

Contenido del CSV:
    id_estacion → Código WMO o ICAO
    name        → Nombre de la estación
    latitude    → Latitud
    longitude   → Longitud
    elevation   → Altitud
    province    → Provincia asociada
"""

from meteostat import Stations
import pandas as pd
import os

# Crear carpeta dataset si no existe
os.makedirs("dataset", exist_ok=True)

# Coordenadas centrales aproximadas por provincia (latitud, longitud)
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
    """
    Obtiene la estación más cercana y con identificador válido (WMO o ICAO).

    Parámetros:
        lat (float): Latitud aproximada de la provincia.
        lon (float): Longitud aproximada de la provincia.
        provincia (str): Nombre de la provincia.

    Retorna:
        pandas.Series o None:
            Una fila con la información de la estación seleccionada
            o None si no se encontró ninguna estación válida.
    """
    estaciones = Stations().nearby(lat, lon)
    estaciones = estaciones.fetch(5)  # Busca las 5 estaciones más cercanas

    if estaciones.empty:
        return None

    # Crear id_estacion usando WMO o ICAO
    estaciones['id_estacion'] = estaciones.apply(
        lambda fila: fila['wmo'] if pd.notna(fila['wmo'])
        else fila['icao'] if pd.notna(fila['icao'])
        else None,
        axis=1
    )

    # Filtrar estaciones sin identificador
    estaciones = estaciones.dropna(subset=['id_estacion'])

    if estaciones.empty:
        return None

    estacion = estaciones.iloc[0].copy()
    estacion['province'] = provincia
    return estacion


def generar_csv_estaciones():
    """
    Genera el archivo dataset/stations.csv con las estaciones seleccionadas.

    Retorna:
        None
    """
    stations_list = []

    for provincia, (lat, lon) in provincias.items():
        estacion = obtener_estacion_valida(lat, lon, provincia)

        if estacion is not None:
            stations_list.append(estacion)
            print(f"Estación encontrada para {provincia}")
        else:
            print(f"No se encontró estación válida para {provincia}")

    df = pd.DataFrame(stations_list)
    df.to_csv("dataset/stations.csv", index=False)
    print("\nCSV de stations creado correctamente.")


if __name__ == "__main__":
    generar_csv_estaciones()
