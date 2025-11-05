from meteostat import Stations
import pandas as pd
import os

os.makedirs("dataset", exist_ok=True)

# diccinario con las coordenadas de cada provincia
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

stations_list = []

for provincia, (lat, lon) in provincias.items():
    estaciones = Stations().nearby(lat, lon)
    estacion = estaciones.fetch(5) 
    # busca las 5 estaciones mas cercanas y guarda la mas completa en datos

    estacion['id_estacion'] = estacion.apply(
        lambda fila: fila['wmo'] if pd.notna(fila['wmo']) else (fila['icao'] if pd.notna(fila['icao']) else None),
        axis=1
    )
    
    # el filtro es para que en data no se guarde la estacion en caso de que no tenga wmo o icao
    
    estacion = estacion.dropna(subset=['id_estacion']) # elimina los no validos

    if not estacion.empty:
        estacion_valida = estacion.iloc[0].copy() # toma la mas representativa
        estacion_valida['province'] = provincia # le agrega una columna provincia
        stations_list.append(estacion_valida) # y la guarda


# y bueno, si ya exite lo actualiza y guarda, si no lo crea
all_stations = pd.DataFrame(stations_list)
all_stations.to_csv("dataset/stations.csv", index=False)

print("CSV de stations creado correctamente.")
