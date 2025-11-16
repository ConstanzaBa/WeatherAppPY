"""
Generador de datos horarios meteorológicos para todas las provincias de Argentina.

Este script:
    1. Lee la lista de estaciones desde dataset/stations.csv
    2. Descarga datos horarios desde Meteostat (desde las 00:00 de hoy hasta +48h)
    3. Convierte todos los horarios a la zona horaria de Argentina
    4. Calcula columnas extra: sensación térmica, UV, visibilidad
    5. Genera un CSV por provincia: dataset/provincia/clima_<provincia>.csv
    6. Genera un CSV combinado: dataset/clima_argentina.csv
"""

import os
import pandas as pd
from meteostat import Hourly
from datetime import datetime, timedelta
import pytz
from parametros import calcular_sensacion_termica, calcular_radiacion_uv, calcular_visibilidad

dataset = "dataset"
provincia_dir = os.path.join(dataset, "provincia")
os.makedirs(provincia_dir, exist_ok=True)

stations_path = os.path.join(dataset, "stations.csv")
stations = pd.read_csv(stations_path)

tz_arg = pytz.timezone("America/Argentina/Buenos_Aires")
hoy_local = datetime.now(tz_arg).date()
start_local = tz_arg.localize(datetime.combine(hoy_local, datetime.min.time()))
end_local = start_local + timedelta(hours=48)

start, end = start_local.astimezone(pytz.utc), end_local.astimezone(pytz.utc)

all_data = []
provincias_actualizadas = []
provincias_omitidas = []

for _, row in stations.iterrows():
    provincia = row["province"]
    archivo_provincia = os.path.join(provincia_dir, f"clima_{provincia}.csv")

    if os.path.exists(archivo_provincia) and os.path.getmtime(archivo_provincia) > os.path.getmtime(stations_path):
        all_data.append(pd.read_csv(archivo_provincia))
        provincias_omitidas.append(provincia)
        continue

    print(f"Descargando datos de {provincia}...")

    try:
        data = Hourly(row["id_estacion"], start.replace(tzinfo=None), end.replace(tzinfo=None)).fetch()
        if data.empty:
            continue

        data = data.reset_index().rename(columns={"time": "fecha_hora"})
        data["fecha_hora"] = data["fecha_hora"].dt.tz_localize("UTC").dt.tz_convert(tz_arg).dt.tz_localize(None)
        data["province"] = provincia

        data["temp"].ffill(inplace=True)
        data["rhum"].ffill(inplace=True)
        data["dwpt"].ffill(inplace=True)
        data["prcp"].fillna(0.0, inplace=True)
        data["snow"].fillna(0.0, inplace=True)
        data["wspd"].ffill(inplace=True)
        data["coco"].fillna(-1, inplace=True)

        data["sensacionTermica"] = data.apply(lambda x: calcular_sensacion_termica(x["temp"], x["rhum"], x["wspd"]), axis=1)
        data["uvIndex"] = data.apply(lambda x: calcular_radiacion_uv(x["temp"], x["coco"], x["fecha_hora"].strftime("%Y-%m-%dT%H:%M:%SZ")), axis=1)
        data["visibilidad"] = data.apply(lambda x: calcular_visibilidad(x["temp"], x["rhum"], x["dwpt"], x["prcp"], x["snow"], x["wspd"], x["coco"]), axis=1)

        data.to_csv(archivo_provincia, index=False)
        all_data.append(data)
        provincias_actualizadas.append(provincia)

    except Exception as e:
        print(f"Error con {provincia}: {e}")

if all_data:
    combinado = pd.concat(all_data, ignore_index=True)
    archivo_combi = os.path.join(dataset, "clima_argentina.csv")
    combinado.to_csv(archivo_combi, index=False)

if provincias_actualizadas:
    print(f"Provincias actualizadas: {', '.join(provincias_actualizadas)}")
if provincias_omitidas:
    print(f"Provincias ya actualizadas: {', '.join(provincias_omitidas)}")
print("Descarga y procesamiento finalizados.")
