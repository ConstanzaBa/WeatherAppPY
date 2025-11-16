"""
Generador de datos horarios meteorológicos para todas las provincias de Argentina.

Este script:
    1. Lee la lista de estaciones desde dataset/stations.csv
    2. Descarga datos horarios desde Meteostat (desde las 00:00 de hoy hasta +48h)
    3. Convierte todos los horarios a la zona horaria de Argentina
    4. Genera un CSV por provincia con nombre: dataset/provincia/clima_<provincia>.csv
    5. Genera un CSV combinado: dataset/clima_argentina.csv

Entradas:
    No recibe parámetros directamente.

Archivos requeridos:
    - dataset/stations.csv

Salidas:
    - dataset/provincia/clima_<provincia>.csv
    - dataset/clima_argentina.csv
"""

import os
import pandas as pd
from meteostat import Hourly
from datetime import datetime, timedelta
import pytz


# -------------------- Carpetas --------------------

dataset = "dataset"
provincia_dir = os.path.join(dataset, "provincia")
os.makedirs(provincia_dir, exist_ok=True)


# -------------------- Cargar estaciones --------------------

stations_path = os.path.join(dataset, "stations.csv")
stations = pd.read_csv(stations_path)


# -------------------- Configuración temporal --------------------

tz_arg = pytz.timezone("America/Argentina/Buenos_Aires")

ahora_local = datetime.now(tz_arg)
hoy_local = ahora_local.date()

# Inicio del día (00:00) en horario argentino
start_local = tz_arg.localize(datetime.combine(hoy_local, datetime.min.time()))

# Fin del rango: 48 horas desde el inicio del día actual
end_local = start_local + timedelta(hours=48)

# Y lo convertimos a UTC (Meteostat trabaja en UTC)
start = start_local.astimezone(pytz.utc)
end = end_local.astimezone(pytz.utc)


# -------------------- Descarga de datos --------------------

all_data = []

for idx, row in stations.iterrows():
    id_estacion = row["id_estacion"]
    nombre = row["name"]
    provincia = row["province"]

    print(f"Descargando datos de {nombre} ({provincia})...")

    try:
        # Pedimos datos al API
        data = Hourly(id_estacion, start.replace(tzinfo=None), end.replace(tzinfo=None))
        data = data.fetch()

        # Filtrar para mantener solo datos desde el inicio del día
        data = data[data.index >= start.replace(tzinfo=None)]

        if data.empty:
            print(f"No hay datos para {nombre}.")
            continue

        data = data.reset_index()
        data.rename(columns={"time": "fecha_hora"}, inplace=True)

        # Convertir a hora local ARG
        data["fecha_hora"] = (
            data["fecha_hora"]
            .dt.tz_localize("UTC")
            .dt.tz_convert("America/Argentina/Buenos_Aires")
            .dt.tz_localize(None)
        )

        data["province"] = provincia

        # Guardar archivo por provincia
        archivo_provincia = os.path.join(provincia_dir, f"clima_{provincia}.csv")

        if os.path.exists(archivo_provincia):
            os.remove(archivo_provincia)

        data.to_csv(archivo_provincia, index=False)
        all_data.append(data)

        print(f"Datos guardados en {archivo_provincia}")

    except Exception as e:
        print(f"Error con {nombre}: {e}")


# -------------------- Guardar CSV combinado --------------------

if all_data:
    combinado = pd.concat(all_data, ignore_index=True)
    archivo_combi = os.path.join(dataset, "clima_argentina.csv")

    if os.path.exists(archivo_combi):
        os.remove(archivo_combi)

    combinado.to_csv(archivo_combi, index=False)
    print(f"CSV combinado guardado en {archivo_combi}")

print("Descarga finalizada.")
