import os
import pandas as pd
import numpy as np
from meteostat import Hourly
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed

from parametros import (
    calcular_sensacion_termica,
    calcular_radiacion_uv,
    calcular_visibilidad,
)

from modelo_pronostico import calcular_coco


# ==========================================================
# PATHS
# ==========================================================
dataset = "dataset"
provincia_dir = os.path.join(dataset, "provincia")
os.makedirs(provincia_dir, exist_ok=True)

stations_path = os.path.join(dataset, "stations.csv")
stations = pd.read_csv(stations_path)


# ==========================================================
# FECHAS - TODO SE MANEJA COMO DATETIME NAIVE
# ==========================================================
tz_arg = pytz.timezone("America/Argentina/Buenos_Aires")

hoy_local_aware = datetime.now(tz_arg)
hoy_local = hoy_local_aware.replace(tzinfo=None).date()  # → naive date

SEMANAS = 3

start_local_aware = tz_arg.localize(
    datetime.combine(hoy_local - timedelta(weeks=SEMANAS), datetime.min.time())
)
end_local_aware = tz_arg.localize(
    datetime.combine(hoy_local, datetime.min.time()) + timedelta(hours=48)
)

# Convertimos a **naive UTC** porque Meteostat NO acepta tz-aware
start_local = start_local_aware.astimezone(pytz.UTC).replace(tzinfo=None)
end_local = end_local_aware.astimezone(pytz.UTC).replace(tzinfo=None)


# ==========================================================
# Obtener última fecha guardada (naive)
# ==========================================================
def obtener_ultima_fecha(df):
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
    return df["fecha_hora"].max()


# ==========================================================
# Rellenar horas faltantes + completar campos
# ==========================================================
def rellenar_horas_perdidas(df):

    df = df.sort_values("fecha_hora").reset_index(drop=True)

    all_hours = pd.date_range(
        df["fecha_hora"].min(),
        df["fecha_hora"].max(),
        freq="1H"
    )

    df = df.set_index("fecha_hora").reindex(all_hours)
    df.index.name = "fecha_hora"

    # Campos obligatoriamente 0.0
    zero_fields = ["prcp", "snow", "tsun"]
    for f in zero_fields:
        if f in df.columns:
            df[f] = df[f].fillna(0.0)

    # Interpolar variables principales
    interp_fields = ["temp", "dwpt", "rhum", "wspd", "pres"]
    for col in interp_fields:
        if col in df.columns:
            df[col] = df[col].interpolate(limit_direction="both")

    # Provincia fija
    if "province" in df.columns:
        df["province"] = df["province"].ffill().bfill()

    # COCO obligatorio
    def asegurar_coco(row):
        c = row.get("coco", None)
        if pd.isna(c) or c == "" or c == -1:
            # Estimar dewpoint si no existe
            dwpt = row.get("dwpt", row.get("temp", 0.0) - 2.0)
            pres = row.get("pres", 1013.0)
            precip = row.get("prcp", 0.0)
            return calcular_coco(
                row.get("temp", 0.0),
                dwpt,
                row.get("rhum", 50.0),
                pres,
                precip
            )
        return int(c)

    df["coco"] = df.apply(asegurar_coco, axis=1)

    # VISIBILIDAD siempre calculada
    df["visibilidad"] = df.apply(
        lambda r: calcular_visibilidad(
            r.get("temp", 0),
            r.get("rhum", 0),
            r.get("dwpt", 0),
            r.get("prcp", 0),
            r.get("snow", 0),
            r.get("wspd", 0),
            r.get("coco", 3)
        ),
        axis=1
    )

    # Redondeos finales
    round_1 = ["temp", "dwpt", "wspd", "visibilidad"]
    for col in round_1:
        df[col] = df[col].round(1)

    df["rhum"] = df["rhum"].round(0)
    df["pres"] = df["pres"].round(1)
    df["prcp"] = df["prcp"].round(1)
    df["snow"] = df["snow"].round(1)

    return df.reset_index()


# ==========================================================
# Procesar cada provincia
# ==========================================================
def procesar_provincia(row):

    provincia = row["province"]
    estacion = row["id_estacion"]
    archivo_prov = os.path.join(provincia_dir, f"clima_{provincia}.csv")

    try:
        # -------------------------
        # Revisar si ya está actualizado
        # -------------------------
        if os.path.exists(archivo_prov):
            df_existente = pd.read_csv(archivo_prov, parse_dates=["fecha_hora"])

            if not df_existente.empty:
                ultima_fecha = obtener_ultima_fecha(df_existente)

                # Ambas naive → OK
                hace_una_hora = (datetime.now(tz_arg).replace(tzinfo=None) - timedelta(hours=1))

                if ultima_fecha >= hace_una_hora:
                    return provincia, "omitida", df_existente

        print(f"[Descargando] {provincia}...")

        # =======================
        # Descarga Meteostat
        # =======================
        data = Hourly(
            estacion,
            start_local,
            end_local
        ).fetch()

        if data.empty:
            return provincia, "vacia", None

        # Convertir a datetime naive Argentina
        data = data.reset_index().rename(columns={"time": "fecha_hora"})
        data["fecha_hora"] = (
            data["fecha_hora"]
            .dt.tz_localize("UTC")
            .dt.tz_convert(tz_arg)
            .dt.tz_localize(None)       # → quitar tz
        )

        data["province"] = provincia

        # Completar básicos
        for col in ["temp", "rhum", "dwpt", "wspd"]:
            if col in data.columns:
                data[col] = data[col].ffill()

        data["prcp"] = data["prcp"].fillna(0.0)
        data["snow"] = data["snow"].fillna(0.0)

        def clean_coco(c):
            return np.nan if (pd.isna(c) or c == -1) else int(c)

        data["coco"] = data["coco"].apply(clean_coco)

        # Rellenar horas faltantes
        data = rellenar_horas_perdidas(data)

        # Extra parámetros
        data["sensacionTermica"] = data.apply(
            lambda x: calcular_sensacion_termica(x["temp"], x["rhum"], x["wspd"]),
            axis=1
        )

        data["uvIndex"] = data.apply(
            lambda x: calcular_radiacion_uv(
                x["temp"], x["coco"],
                x["fecha_hora"].strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
            axis=1
        )

        # Merge con existentes
        if os.path.exists(archivo_prov):
            df_existente = pd.read_csv(archivo_prov, parse_dates=["fecha_hora"])
            df_final = pd.concat([df_existente, data]).drop_duplicates(
                subset="fecha_hora",
                keep="last"
            )
        else:
            df_final = data

        df_final = df_final.sort_values("fecha_hora")
        df_final.to_csv(archivo_prov, index=False)

        return provincia, "actualizada", df_final

    except Exception as e:
        print(f"[ERROR] {provincia}: {e}")
        return provincia, "error", None


# ==========================================================
# Ejecutar en paralelo
# ==========================================================
all_data = []
status = {"actualizada": [], "omitida": [], "vacia": [], "error": []}

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(procesar_provincia, row) for _, row in stations.iterrows()]
    for fut in as_completed(futures):
        provincia, estado, df = fut.result()
        status[estado].append(provincia)
        if isinstance(df, pd.DataFrame):
            all_data.append(df)

print("Actualizadas:", status["actualizada"])
print("Omitidas:", status["omitida"])
print("Vacías:", status["vacia"])
print("Errores:", status["error"])
print("Finalizadas las descargas.")
