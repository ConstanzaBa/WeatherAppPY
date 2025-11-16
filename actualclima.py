"""
Módulo para generar los archivos JSON con el clima actual y el pronóstico
horario de cada provincia argentina.

Este script:
1. Lee todos los archivos CSV de la carpeta dataset/provincia.
2. Obtiene para cada provincia:
    - La hora más reciente con datos (clima actual).
    - Las próximas horas (hasta 6 registros) como pronóstico horario.
3. Selecciona el icono adecuado según hora del día.
4. Guarda los datos en formato JSON para ser usados por la interfaz web.

Entradas:
- Archivos CSV en dataset/provincia/ con columnas:
    fecha_hora, temp, rhum, prcp, wspd, dwpt, snow, coco, sensacionTermica, uvIndex, visibilidad

Salidas:
- web/clima_actual.json
- web/clima_horario.json
"""

import os
import json
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

from codclimatico import weather_icons, weather_descriptions

# ============================================================
# Función auxiliar para cargar un CSV de provincia
# ============================================================

def cargar_csv_provincia(ruta):
    """
    Carga un archivo CSV de clima para una provincia y convierte la columna
    fecha_hora a formato datetime con zona horaria de Argentina.
    """
    df = pd.read_csv(ruta)
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])
    df["fecha_hora"] = df["fecha_hora"].dt.tz_localize(
        "America/Argentina/Buenos_Aires",
        nonexistent="shift_forward",
        ambiguous="NaT",
    )
    return df

# ============================================================
# Función que obtiene el clima actual de una provincia
# ============================================================

def obtener_clima_actual(df, ahora, provincia):
    """
    Obtiene el registro de clima más reciente para una provincia.
    """
    df_pasado = df[df["fecha_hora"] <= ahora]

    if not df_pasado.empty:
        fila = df_pasado.iloc[-1]
    else:
        fila = df.iloc[0]

    coco = int(fila["coco"]) if not pd.isna(fila["coco"]) else None
    icono = weather_icons.get(coco, "unknown.svg")
    descripcion = weather_descriptions.get(coco, "Desconocido")

    # Ajuste de icono según la hora (versión noche)
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

# ============================================================
# Función que obtiene el pronóstico horario
# ============================================================

def obtener_clima_horario(df, ahora):
    """
    Genera las próximas horas de pronóstico para una provincia.
    """
    idx_actual = df[df["fecha_hora"] <= ahora].index.max()
    if pd.isna(idx_actual):
        idx_actual = 0

    df_futuro = df.loc[idx_actual:].head(6)
    horas = []

    for i, fila in enumerate(df_futuro.itertuples()):

        coco = int(fila.coco) if not pd.isna(fila.coco) else None
        icono = weather_icons.get(coco, "unknown.svg")

        # Icono de noche
        hora_fila = fila.fecha_hora.hour
        if 20 <= hora_fila or hora_fila < 7:
            if icono == "clear.svg":
                icono = "clear_night.svg"
            elif icono == "fair.svg":
                icono = "fair_night.svg"

        # Texto de hora
        if i == 0:
            tiempo = "AHORA"
        else:
            tiempo = fila.fecha_hora.strftime("%I %p").lstrip("0")

        horas.append({
            "time": tiempo,
            "icon": icono,
            "temp": round(fila.temp, 1) if not pd.isna(fila.temp) else None,
            "coco": coco,
            "fecha_hora": fila.fecha_hora.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return horas

# ============================================================
# Función principal del módulo
# ============================================================

def generar_json_clima():
    """
    Recorre todos los archivos CSV de provincias, calcula el clima actual
    y el pronóstico horario, y genera los archivos JSON usados por la interfaz.
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

# ============================================================
# Ejecución directa del script
# ============================================================

if __name__ == "__main__":
    generar_json_clima()
