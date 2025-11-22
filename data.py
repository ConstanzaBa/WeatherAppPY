import os
import pandas as pd
from meteostat import Hourly
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed
from parametros import (
    calcular_sensacion_termica,
    calcular_radiacion_uv,
    calcular_visibilidad,
)

# Paths
dataset = "dataset"
provincia_dir = os.path.join(dataset, "provincia")
os.makedirs(provincia_dir, exist_ok=True)

stations_path = os.path.join(dataset, "stations.csv")
stations = pd.read_csv(stations_path)

# Tiempos
tz_arg = pytz.timezone("America/Argentina/Buenos_Aires")
hoy_local = datetime.now(tz_arg).date()

start_local = tz_arg.localize(datetime.combine(hoy_local, datetime.min.time()))
end_local = start_local + timedelta(hours=48)
start, end = start_local.astimezone(pytz.utc), end_local.astimezone(pytz.utc)


# -------------------------------------------------------------------
# CHEQUEAR SI EL ARCHIVO TIENE DATOS DE HOY
# -------------------------------------------------------------------
def archivo_actualizado(path):
    if not os.path.exists(path):
        return False
    try:
        df = pd.read_csv(path)
        if df.empty:
            return False
        fechas = pd.to_datetime(df["fecha_hora"], errors="coerce")
        if fechas.isna().all():
            return False
        return fechas.max().date() >= hoy_local
    except:
        return False


# -------------------------------------------------------------------
# FUNCIÓN QUE PROCESA UNA SOLA PROVINCIA
# -------------------------------------------------------------------
def procesar_provincia(row):
    provincia = row["province"]
    estacion = row["id_estacion"]

    archivo_prov = os.path.join(provincia_dir, f"clima_{provincia}.csv")

    # Si ya tiene datos de hoy → evitar descarga
    if archivo_actualizado(archivo_prov):
        return provincia, "omitida", pd.read_csv(archivo_prov)

    print(f"[Descargando] {provincia}...")

    try:
        data = Hourly(estacion, start.replace(tzinfo=None), end.replace(tzinfo=None)).fetch()
        if data.empty:
            return provincia, "vacia", None

        # Normalizar index y fecha
        data = data.reset_index().rename(columns={"time": "fecha_hora"})
        data["fecha_hora"] = (
            data["fecha_hora"]
            .dt.tz_localize("UTC")
            .dt.tz_convert(tz_arg)
            .dt.tz_localize(None)
        )

        data["province"] = provincia

        # Rellenos sin warnings
        data["temp"] = data["temp"].ffill()
        data["rhum"] = data["rhum"].ffill()
        data["dwpt"] = data["dwpt"].ffill()
        data["prcp"] = data["prcp"].fillna(0.0)
        data["snow"] = data["snow"].fillna(0.0)
        data["wspd"] = data["wspd"].ffill()
        data["coco"] = data["coco"].fillna(-1)

        # Cálculos extra
        data["sensacionTermica"] = data.apply(
            lambda x: calcular_sensacion_termica(x["temp"], x["rhum"], x["wspd"]), axis=1
        )
        data["uvIndex"] = data.apply(
            lambda x: calcular_radiacion_uv(
                x["temp"], x["coco"],
                x["fecha_hora"].strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
            axis=1
        )
        data["visibilidad"] = data.apply(
            lambda x: calcular_visibilidad(
                x["temp"], x["rhum"], x["dwpt"],
                x["prcp"], x["snow"], x["wspd"], x["coco"]
            ),
            axis=1
        )

        # Guardar y devolver
        data.to_csv(archivo_prov, index=False)
        return provincia, "actualizada", data

    except Exception as e:
        print(f"[ERROR] {provincia}: {e}")
        return provincia, "error", None


# -------------------------------------------------------------------
# EJECUCIÓN EN PARALELO
# -------------------------------------------------------------------
all_data = []
status = {"actualizada": [], "omitida": [], "vacia": [], "error": []}

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(procesar_provincia, row) for _, row in stations.iterrows()]

    for fut in as_completed(futures):
        provincia, estado, df = fut.result()
        status[estado].append(provincia)
        if isinstance(df, pd.DataFrame):
            all_data.append(df)


# -------------------------------------------------------------------
# CSV COMBINADO
# -------------------------------------------------------------------
if all_data:
    combinado = pd.concat(all_data, ignore_index=True)
    archivo_combi = os.path.join(dataset, "clima_argentina.csv")
    combinado.to_csv(archivo_combi, index=False)


# -------------------------------------------------------------------
# FINAL
# -------------------------------------------------------------------
if status["actualizada"]:
    print("Actualizadas:", ", ".join(status["actualizada"]))
if status["omitida"]:
    print("Ya estaban al día:", ", ".join(status["omitida"]))
if status["vacia"]:
    print("Sin datos:", ", ".join(status["vacia"]))
if status["error"]:
    print("Errores:", ", ".join(status["error"]))

print("Finalizadas las descargas.")
