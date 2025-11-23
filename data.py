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

# -----------------------------
# Paths y directorios
# -----------------------------
dataset = "dataset"
provincia_dir = os.path.join(dataset, "provincia")
os.makedirs(provincia_dir, exist_ok=True)

stations_path = os.path.join(dataset, "stations.csv")
stations = pd.read_csv(stations_path)

# -----------------------------
# Tiempos
# -----------------------------
tz_arg = pytz.timezone("America/Argentina/Buenos_Aires")
hoy_local = datetime.now(tz_arg).date()

SEMANAS = 6
start_local = tz_arg.localize(datetime.combine(hoy_local - timedelta(weeks=SEMANAS), datetime.min.time()))
end_local = tz_arg.localize(datetime.combine(hoy_local, datetime.min.time()) + timedelta(hours=48))


# -----------------------------
# Obtener última fecha corregida (naive)
# -----------------------------
def obtener_ultima_fecha(df):
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], utc=True, errors="coerce")
    df["fecha_hora"] = df["fecha_hora"].dt.tz_localize(None)
    return df["fecha_hora"].max()


# -----------------------------
# Procesar una sola provincia
# -----------------------------
def procesar_provincia(row):
    provincia = row["province"]
    estacion = row["id_estacion"]
    archivo_prov = os.path.join(provincia_dir, f"clima_{provincia}.csv")

    try:
        # Ver si ya existe CSV previo
        if os.path.exists(archivo_prov):

            df_existente = pd.read_csv(archivo_prov)

            if not df_existente.empty:

                ultima_fecha = obtener_ultima_fecha(df_existente)
                ahora_naive = (datetime.now(tz_arg) - timedelta(hours=1)).replace(tzinfo=None)

                if ultima_fecha >= ahora_naive:
                    return provincia, "omitida", df_existente

        # Si no está actualizado, descargar
        print(f"[Descargando] {provincia} desde {start_local} hasta {end_local}...")

        data = Hourly(
            estacion,
            start_local.replace(tzinfo=None),
            end_local.replace(tzinfo=None)
        ).fetch()

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

        # Rellenos
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

        # Concatenar datos previos si existen
        if os.path.exists(archivo_prov):
            df_existente = pd.read_csv(archivo_prov, parse_dates=["fecha_hora"])
            df_existente["fecha_hora"] = df_existente["fecha_hora"].dt.tz_localize(None)

            df_final = pd.concat([df_existente, data], ignore_index=True)
            df_final = df_final.drop_duplicates(subset="fecha_hora")
        else:
            df_final = data

        df_final.to_csv(archivo_prov, index=False)
        return provincia, "actualizada", df_final

    except Exception as e:
        print(f"[ERROR] {provincia}: {e}")
        return provincia, "error", None


# -----------------------------
# Ejecución en paralelo
# -----------------------------
all_data = []
status = {"actualizada": [], "omitida": [], "vacia": [], "error": []}

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(procesar_provincia, row) for _, row in stations.iterrows()]
    for fut in as_completed(futures):
        provincia, estado, df = fut.result()
        status[estado].append(provincia)
        if isinstance(df, pd.DataFrame):
            all_data.append(df)

# -----------------------------
# Resultados finales
# -----------------------------
if status["actualizada"]:
    print("Actualizadas:", ", ".join(status["actualizada"]))
if status["omitida"]:
    print("Ya estaban al día:", ", ".join(status["omitida"]))
if status["vacia"]:
    print("Sin datos:", ", ".join(status["vacia"]))
if status["error"]:
    print("Errores:", ", ".join(status["error"]))

print("Finalizadas las descargas.")
