"""
Módulo: generación de JSON de clima actual y pronóstico horario

Este script procesa los CSV de cada provincia para generar:
- clima_actual.json: registro más reciente de cada provincia
- clima_horario.json: pronóstico horario (hasta 6 horas)

Entradas:
    CSVs en dataset/provincia/ con columnas:
        fecha_hora, temp, rhum, prcp, wspd, dwpt, snow, coco, sensacionTermica, uvIndex, visibilidad

Salidas:
    JSON en web/clima_actual.json y web/clima_horario.json
"""

# ============================
# Imports principales
# ============================
import os
import json
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from codclimatico import weather_icons, weather_descriptions

# ============================
# Función auxiliar: cargar CSV
# ============================
def cargar_csv_provincia(ruta):
    """
    Carga un CSV de clima de provincia y ajusta la columna fecha_hora
    a la zona horaria de Argentina.
    
    Parámetros:
        ruta (str): Ruta al CSV

    Retorna:
        pd.DataFrame: Datos de clima con fecha_hora en tz local
    """
    df = pd.read_csv(ruta)
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])
    df["fecha_hora"] = df["fecha_hora"].dt.tz_localize(
        "America/Argentina/Buenos_Aires",
        nonexistent="shift_forward",
        ambiguous="NaT",
    )
    return df

# ============================
# Función: clima actual de una provincia
# ============================
def obtener_clima_actual(df, ahora, provincia):
    """
    Obtiene el registro más reciente de clima para una provincia,
    asignando iconos y descripciones según COCO y hora del día.

    Parámetros:
        df (pd.DataFrame): Datos de clima de la provincia
        ahora (datetime): Fecha y hora actual
        provincia (str): Nombre de la provincia

    Retorna:
        dict: Datos de clima actual formateados
    """
    df_pasado = df[df["fecha_hora"] <= ahora]
    fila = df_pasado.iloc[-1] if not df_pasado.empty else df.iloc[0]

    coco = int(fila["coco"]) if not pd.isna(fila["coco"]) else None
    icono = weather_icons.get(coco, "unknown.svg")
    descripcion = weather_descriptions.get(coco, "Desconocido")

    # Ajuste de icono según hora (noche)
    hora_actual = ahora.hour
    if 20 <= hora_actual or hora_actual < 7:
        if icono == "clear.svg":
            icono = "clear_night.svg"
        elif icono == "fair.svg":
            icono = "fair_night.svg"

    return {
        "provincia": provincia,
        "temperatura": round(fila["temp"], 1) if not pd.isna(fila["temp"]) else None,
        "humedad": round(fila["rhum"], 1) if not pd.isna(fila["rhum"]) else None,
        "precipitacion": round(fila["prcp"], 1) if not pd.isna(fila["prcp"]) else None,
        "viento": round(fila["wspd"], 1) if not pd.isna(fila["wspd"]) else None,
        "visibilidad": round(fila["visibilidad"], 1) if not pd.isna(fila.get("visibilidad")) else None,
        "sensacionTermica": round(fila["sensacionTermica"], 1) if not pd.isna(fila.get("sensacionTermica")) else None,
        "uvIndex": round(fila["uvIndex"], 1) if not pd.isna(fila.get("uvIndex")) else None,
        "coco": coco,
        "icono": icono,
        "condicion": descripcion,
        "fecha_hora": fila["fecha_hora"].strftime("%Y-%m-%d %H:%M:%S %Z"),
    }

# ============================
# Función: pronóstico horario
# ============================
def obtener_clima_horario(df, ahora):
    """
    Genera los próximos 6 registros de pronóstico horario
    para una provincia, con iconos y formato de hora.

    Parámetros:
        df (pd.DataFrame): Datos de clima de la provincia
        ahora (datetime): Fecha y hora actual

    Retorna:
        list[dict]: Lista de pronósticos horarios
    """
    idx_actual = df[df["fecha_hora"] <= ahora].index.max()
    if pd.isna(idx_actual):
        idx_actual = 0

    df_futuro = df.loc[idx_actual:].head(6)
    horas = []

    for i, fila in enumerate(df_futuro.itertuples()):
        coco = int(fila.coco) if not pd.isna(fila.coco) else None
        icono = weather_icons.get(coco, "unknown.svg")

        # Ajuste icono noche
        hora_fila = fila.fecha_hora.hour
        if 20 <= hora_fila or hora_fila < 7:
            if icono == "clear.svg":
                icono = "clear_night.svg"
            elif icono == "fair.svg":
                icono = "fair_night.svg"

        # Texto de hora
        tiempo = "AHORA" if i == 0 else fila.fecha_hora.strftime("%I %p").lstrip("0")

        horas.append({
            "time": tiempo,
            "icon": icono,
            "temp": round(fila.temp, 1) if not pd.isna(fila.temp) else None,
            "coco": coco,
            "fecha_hora": fila.fecha_hora.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return horas

# ============================
# Función principal
# ============================
def generar_json_clima():
    """
    Recorre todos los CSV de provincias, genera:
    - clima_actual.json
    - clima_horario.json
    """
    provincia_dir = "dataset/provincia"
    ahora = datetime.now(tz=ZoneInfo("America/Argentina/Buenos_Aires"))

    clima_actual = []
    clima_horario = {}

    for archivo in os.listdir(provincia_dir):
        if not archivo.endswith(".csv"):
            continue

        provincia = archivo.replace("clima_", "").replace(".csv", "")
        ruta = os.path.join(provincia_dir, archivo)

        df = cargar_csv_provincia(ruta)

        clima_actual.append(obtener_clima_actual(df, ahora, provincia))
        clima_horario[provincia] = obtener_clima_horario(df, ahora)

    # Guardar JSON clima actual
    os.makedirs("web", exist_ok=True)
    with open("web/clima_actual.json", "w", encoding="utf-8") as f:
        json.dump(clima_actual, f, ensure_ascii=False, indent=2)

    # Guardar JSON pronóstico horario
    with open("web/clima_horario.json", "w", encoding="utf-8") as f:
        json.dump(clima_horario, f, ensure_ascii=False, indent=2)

# ============================
# Ejecución directa
# ============================
if __name__ == "__main__":
    generar_json_clima()
