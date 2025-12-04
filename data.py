"""
Este script descarga y procesa datos meteorológicos horarios para todas las provincias de Argentina.

Funciones principales:
1. Obtiene datos históricos y recientes de Meteostat según estaciones definidas en 'stations.csv'.
2. Rellena horas faltantes, interpola valores críticos y calcula:
    - coco (condición climática)
    - visibilidad
    - sensación térmica
    - índice UV
3. Guarda los datos procesados en archivos CSV por provincia en 'dataset/provincia/'.
4. Mantiene los datos existentes, evitando duplicados.
5. Maneja errores y reporta estados: actualizada, omitida, vacía o error.
"""

# ===========================
# IMPORTS
# ===========================

import os  # Para manejo de rutas, creación de carpetas y verificación de archivos
import pandas as pd  # Para manejo de datos tabulares y CSVs (DataFrames)
import numpy as np  # Para operaciones numéricas y manejo de valores NaN
from meteostat import Hourly  # Para descargar datos meteorológicos horarios desde Meteostat
from datetime import datetime, timedelta  # Para manejo de fechas y cálculos de rango temporal
import pytz  # Para manejar zonas horarias (timezone aware)
from concurrent.futures import ThreadPoolExecutor, as_completed  # Para ejecutar descargas en paralelo y mejorar performance
from parametros import calcular_sensacion_termica, calcular_radiacion_uv, calcular_visibilidad  

# Funciones propias para calcular:
# - sensación térmica (temperatura percibida)
# - radiación UV estimada
# - visibilidad según condiciones climáticas

from modelo_pronostico import calcular_coco  
                                        # Función propia que calcula el código de condición climática (COCO) basado en temperatura, humedad, precipitación y presión

import threading
                                        # Para evitar escribir en dos archivos a la vez en el cache 
meteostat_lock = threading.Lock()

import warnings
warnings.filterwarnings("ignore", message="divide by zero encountered in log")
warnings.filterwarnings("ignore", category=FutureWarning)
# se ocultan warnings que son originados por problemas de meteostat como el calculo de valores Nan o concatenacion

# ==========================================================
# PATHS
# ==========================================================
dataset = "dataset"
provincia_dir = os.path.join(dataset, "provincia")
os.makedirs(provincia_dir, exist_ok=True)

stations_path = os.path.join(dataset, "stations.csv")
stations = pd.read_csv(stations_path)


# ==========================================================
# ZONA HORARIA
# ==========================================================
tz_arg = pytz.timezone("America/Argentina/Buenos_Aires")

# ==========================================================
# FUNCIONES
# ==========================================================

def obtener_ultima_fecha(df):
    """
    Obtiene la última fecha registrada en un DataFrame de clima.
    
    Parámetros:
        df (pd.DataFrame): DataFrame que contiene la columna 'fecha_hora'.
        
    Retorna:
        datetime: Fecha y hora máxima encontrada en la columna 'fecha_hora'.
    """
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
    return df["fecha_hora"].max()

def rellenar_horas_perdidas(df):
    """
    Rellena horas faltantes en los datos horarios y completa campos críticos.

    Comportamiento:
    - Ordena por fecha_hora y genera un índice horario continuo.
    - Llena con ceros columnas críticas como 'prcp', 'snow' y 'tsun'.
    - Interpola valores de temperatura, punto de rocío, humedad, viento y presión.
    - Completa la columna 'province' hacia adelante y hacia atrás si faltan valores.
    - Calcula 'coco' si no existe o es inválido.
    - Calcula la visibilidad basada en condiciones climáticas.
    - Redondea columnas según criterio de visualización.

    Parámetros:
        df (pd.DataFrame): DataFrame con datos meteorológicos horarios.

    Retorna:
        pd.DataFrame: DataFrame con horas continuas, interpolaciones, cálculos de coco y visibilidad, y redondeo de columnas.
    """
    
    df = df.sort_values("fecha_hora").reset_index(drop=True)

    all_hours = pd.date_range(
        df["fecha_hora"].min(),
        df["fecha_hora"].max(),
        freq="h"
    )

    df = df.set_index("fecha_hora").reindex(all_hours)
    df.index.name = "fecha_hora"

    zero_fields = ["prcp", "snow", "tsun"]
    for f in zero_fields:
        if f in df.columns:
            df[f] = df[f].fillna(0.0)

    interp_fields = ["temp", "dwpt", "rhum", "wspd", "pres"]
    for col in interp_fields:
        if col in df.columns:
            df[col] = df[col].interpolate(limit_direction="both")

    if "province" in df.columns:
        df["province"] = df["province"].ffill().bfill()

    def asegurar_coco(row):
        c = row.get("coco", None)
        if pd.isna(c) or c == "" or c == -1:
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

    round_1 = ["temp", "dwpt", "wspd", "visibilidad"]
    for col in round_1:
        df[col] = df[col].round(1)

    df["rhum"] = df["rhum"].round(0)
    df["pres"] = df["pres"].round(1)
    df["prcp"] = df["prcp"].round(1)
    df["snow"] = df["snow"].round(1)

    return df.reset_index()

def rango_descarga(csv_provincia, semanas=4, horas_extra=48):
    """
    Determina el rango de fechas para descargar datos meteorológicos.

    Comportamiento:
    - Siempre descarga desde la última fecha disponible (CSV) + 1 hora hasta la fecha límite:
        fecha actual 00:00 + horas_extra (48h por defecto).
    - Si no existe CSV, descarga 4 semanas atrás + 48h.
    - Si ya hay datos hasta la fecha límite, retorna None, None (omitida).

    Parámetros:
        csv_provincia (str): Ruta del CSV de la provincia.
        semanas (int): Cantidad de semanas históricas a descargar si no hay CSV.
        horas_extra (int): Horas adicionales después de la fecha límite.

    Retorna:
        tuple(datetime | None, datetime | None):
            start_utc, end_utc: Fechas de inicio y fin en UTC naive.
            None, None si ya está todo actualizado.
    """
    ahora_local_aware = datetime.now(tz_arg)
    hoy_local = ahora_local_aware.date()

    # Fecha límite deseada: hoy 00:00 + horas_extra
    fin_deseado = tz_arg.localize(datetime.combine(hoy_local, datetime.min.time())) + timedelta(hours=horas_extra)

    if os.path.exists(csv_provincia):
        df_existente = pd.read_csv(csv_provincia, parse_dates=["fecha_hora"])
        ultima_fecha = obtener_ultima_fecha(df_existente)
        if pd.isna(ultima_fecha):
            inicio_local_aware = tz_arg.localize(datetime.combine(hoy_local - timedelta(weeks=semanas), datetime.min.time()))
        else:
            inicio_local_aware = tz_arg.localize(ultima_fecha + timedelta(hours=1))
    else:
        inicio_local_aware = tz_arg.localize(datetime.combine(hoy_local - timedelta(weeks=semanas), datetime.min.time()))

    # Si ya tenemos todo hasta la fecha límite → omitida
    if inicio_local_aware >= fin_deseado:
        return None, None

    start_utc = inicio_local_aware.astimezone(pytz.UTC).replace(tzinfo=None)
    end_utc = fin_deseado.astimezone(pytz.UTC).replace(tzinfo=None)
    return start_utc, end_utc


def procesar_provincia(row):
    """
    Descarga y procesa los datos horarios de una provincia de forma incremental.

    Comportamiento:
    - Verifica si el CSV existe y si tiene datos.
    - Determina el rango de descarga usando rango_descarga.
    - Casos posibles:
        - CSV vacío o no existe → devuelve 'vacia'.
        - CSV con datos y ya actualizado → devuelve 'omitida'.
        - Descarga exitosa de nuevos datos → devuelve 'actualizada'.
        - Error en descarga o procesamiento → devuelve 'error'.
    - Ajusta zona horaria, completa datos críticos, calcula coco, visibilidad, sensación térmica e índice UV.
    - Combina datos nuevos con CSV existente y elimina duplicados.

    Parámetros:
        row (pd.Series): Serie con información de la estación y provincia.

    Retorna:
        tuple(str, str, pd.DataFrame | None):
            provincia: Nombre de la provincia.
            estado: 'actualizada', 'omitida', 'vacia' o 'error'.
            df: DataFrame final con datos procesados o None si hubo error o CSV vacío.
    """
    provincia = row["province"]
    estacion = row["id_estacion"]
    archivo_prov = os.path.join(provincia_dir, f"clima_{provincia}.csv")

    # Columnas 
    cols = [
        "fecha_hora", "temp", "dwpt", "rhum", "wspd", "pres",
        "prcp", "snow", "tsun", "coco", "visibilidad",
        "sensacionTermica", "uvIndex", "province",
        "wdir", "wpgt"
    ]
    
    try:
        
        # Leer CSV existente 
        
        if os.path.exists(archivo_prov):
            try:
                df_existente = pd.read_csv(archivo_prov, parse_dates=["fecha_hora"])
                if "fecha_hora" not in df_existente.columns:
                    df_existente = pd.DataFrame()
            except Exception:
                # Si el archivo esta corrupto lo regeneramos
                df_existente = pd.DataFrame()
        else:
            df_existente = pd.DataFrame()
            
        csv_vacio = df_existente.empty
        
        start_utc, end_utc = rango_descarga(archivo_prov)
        
        if start_utc is None:
            if csv_vacio:
                return provincia, "vacia", None
            return provincia, "omitida", df_existente
        
        # Descargar datos desde Meteostat
        
        if estacion is None:
            return provincia, "error", None
        
        print(f"[Descargando] {provincia}")
        
        with meteostat_lock:
            try:
                data = Hourly(estacion, start_utc, end_utc).fetch()
            except Exception:
                return provincia, "error", None
            
        # Nada descargado
        if data is None or data.empty:
            return provincia, ("vacia" if csv_vacio else "omitida"), (
                None if csv_vacio else df_existente
            )
            
        # Normalizar columnas 
        
        data = data.reset_index(drop=False)
        
        if "time" in data.columns:
            data = data.rename(columns={"time": "fecha_hora"})
        else:
            
            fechas = pd.date_range(start_utc, end_utc, freq="H")
            data["fecha_hora"] = fechas[:len(data)]
            
        # Asegurar que sea fecha sin timezone
        try:
            data["fecha_hora"] = (
                data["fecha_hora"]
                .dt.tz_localize("UTC")
                .dt.tz_convert(tz_arg)
                .dt.tz_localize(None)
            )
        except Exception:
            data["fecha_hora"] = pd.to_datetime(data["fecha_hora"], errors="coerce")
            
        data["province"] = provincia
        
        # Agregar columnas faltantes con NaN
        for c in cols:
            if c not in data.columns:
                data[c] = np.nan 
        
        try:
            data = rellenar_horas_perdidas(data)
        except Exception:
            # Si algo falla ahí, evitamos romper todo
            pass
        
        # Cálculo de sensación térmica
        try:
            data["sensacionTermica"] = data.apply(
                lambda x: calcular_sensacion_termica(
                    x.get("temp", np.nan),
                    x.get("rhum", np.nan),
                    x.get("wspd", np.nan)
                ),
                axis=1
            )
        except Exception:
            data["sensacionTermica"] = np.nan

        # Cálculo de UV
        try:
            data["uvIndex"] = data.apply(
                lambda x: calcular_radiacion_uv(
                    x.get("temp", np.nan),
                    x.get("coco", np.nan),
                    x.get("fecha_hora").strftime("%Y-%m-%dT%H:%M:%SZ")
                    if not pd.isna(x.get("fecha_hora")) else "2000-01-01T00:00:00Z"
                ),
                axis=1
            )
        except Exception:
            data["uvIndex"] = np.nan
            
        # Combinar con CSV 
        df_existente = df_existente.reindex(columns=cols)
        data = data.reindex(columns=cols)
        
        # Función interna para determinar si DF es inválido
        def invalido(df):
            return df.empty or df.dropna(how="all").empty
        
        if invalido(df_existente) and invalido(data):
            df_final = pd.DataFrame(columns=cols)
            
        elif invalido(df_existente):
            df_final = data
            
        elif invalido(data):
            df_final = df_existente
            
        else:
            
            df_final = pd.concat([df_existente, data], ignore_index=True)
            df_final = df_final.drop_duplicates(subset="fecha_hora", keep="last")
            df_final = df_final.sort_values("fecha_hora")
        
        try:
            df_final.to_csv(archivo_prov, index=False)
        except Exception:
            return provincia, "error", None
        
        return provincia, "actualizada", df_final
    
    except Exception:
        
        return provincia, "error", None


# ==========================================================
# EJECUCIÓN EN PARALELO
# ==========================================================
all_data = []

status = {"actualizada": [], "omitida": [], "vacia": [], "error": []}

with ThreadPoolExecutor(max_workers=5) as executor:
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


# ==========================================================
# DOCUMENTACIÓN DE COLUMNAS DEL CSV
# ==========================================================
"""
Cada CSV generado por este script contiene datos horarios de estaciones meteorológicas.
A continuación se detallan las columnas, su descripción y la unidad de medida:

| Columna         | Descripción                                                    | Unidad       |
|-----------------|----------------------------------------------------------------|--------------|
| station         | ID de la estación meteorológica                                | String       |
| fecha_hora      | Fecha y hora de la observación                                 | datetime64   |
| temp            | Temperatura del aire                                           | °C           |
| dwpt            | Punto de rocío                                                 | °C           |
| rhum            | Humedad relativa                                               | %            |
| prcp            | Precipitación acumulada en la última hora                      | mm           |
| snow            | Altura de nieve                                                | mm           |
| wdir            | Dirección promedio del viento                                  | grados       |
| wspd            | Velocidad promedio del viento                                  | km/h         |
| wpgt            | Ráfaga máxima de viento                                        | km/h         |
| pres            | Presión atmosférica a nivel del mar                            | hPa          |
| tsun            | Minutos de sol registrados en la última hora                   | minutos      |
| coco            | Código de condición meteorológica (COCO)                       | int          |
| visibilidad     | Visibilidad calculada según condiciones actuales               | m            |
| sensacionTermica| Sensación térmica calculada (temperatura percibida)            | °C           |
| uvIndex         | Índice UV estimado según hora y condición                      | Índice       |
| province        | Nombre de la provincia correspondiente                         | String       |

Notas:
- Todos los datos horarios se rellenan automáticamente para cubrir horas faltantes.
- Campos críticos como temperatura, humedad, presión, precipitación y coco se completan o interpolan si es necesario.
- Los códigos `coco` se pueden mapear a iconos y descripciones usando la biblioteca de `weather_icons` y `weather_descriptions`.
"""
