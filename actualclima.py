import pandas as pd
import os
from datetime import datetime  # Para manejar fechas y horas
from zoneinfo import ZoneInfo  # Para manejar zonas horarias 
import json 
from codclimatico import weather_icons  # importamos el diccionario

provincia_dir = "dataset/provincia"
# Obtenemos la hora actual en zona horaria de Argentina (tz-aware)
ahora = datetime.now(tz=ZoneInfo("America/Argentina/Buenos_Aires"))
clima_actual = []  # lista para los datos de cada provincia

for archivo in os.listdir(provincia_dir):
    
    # Saltamos todo lo que no sea csv
    if not archivo.endswith(".csv"):
        continue

    # Extraemos el nombre de la provincia del csv
    provincia = archivo.replace("clima_", "").replace(".csv", "")

    # Leemos el csv
    df = pd.read_csv(os.path.join(provincia_dir, archivo))

    # Convertimos fecha_hora a tipo datetime tz-aware en Argentina
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora']).dt.tz_localize(ZoneInfo("America/Argentina/Buenos_Aires"))

    # Filtramos solo las horas que ya pasaron (<= ahora)
    df_pasado = df[df['fecha_hora'] <= ahora]

    # Si no hay horas pasadas, tomamos la primera disponible
    if not df_pasado.empty:
        fila = df_pasado.iloc[-1]  # última hora pasada
    else:
        fila = df.iloc[0]  # por si el CSV tiene solo horas futuras

    # Obtener COCO
    coco = int(fila['coco']) if not pd.isna(fila['coco']) else None

    # Buscamos el ícono en el diccionario weather_icons de codclimatico.py
    icono = weather_icons.get(coco, "unknown.svg")


    # Si la hora actual está entre las 20:00 y las 07:00, usamos versiones con luna
    hora_actual = ahora.hour
    if 20 <= hora_actual or hora_actual < 7:
        if icono == "clear.svg":
            icono = "clear_night.svg"
        elif icono == "fair.svg":
            icono = "fair_night.svg" 

    # Agregamos los datos a la lista
    clima_actual.append({
        "provincia": provincia,
        "temperatura": round(fila['temp'], 1) if not pd.isna(fila['temp']) else None,
        "humedad": round(fila['rhum'], 1) if not pd.isna(fila['rhum']) else None,
        "coco": coco,
        "icono": icono,
        "fecha_hora": fila['fecha_hora'].strftime("%Y-%m-%d %H:%M:%S %Z")  # incluimos zona horaria
    })

# Guardamos el resultado en un json
output_path = os.path.join("web", "clima_actual.json")

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(clima_actual, f, ensure_ascii=False, indent=2)

print(f"JSON actualizado")
