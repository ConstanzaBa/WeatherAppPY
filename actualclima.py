import pandas as pd
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import json
from codclimatico import weather_icons, weather_descriptions
from parametros import calcular_sensacion_termica, calcular_radiacion_uv, calcular_visibilidad

provincia_dir = "dataset/provincia"
ahora = datetime.now(tz=ZoneInfo("America/Argentina/Buenos_Aires"))
clima_actual = []  # lista para los datos actuales de cada provincia
clima_horario = {}  # diccionario con pronóstico horario por provincia

for archivo in os.listdir(provincia_dir):
    
    if not archivo.endswith(".csv"):
        continue

    provincia = archivo.replace("clima_", "").replace(".csv", "")
    df = pd.read_csv(os.path.join(provincia_dir, archivo))

    # Convertimos fecha_hora a tipo datetime tz-aware en Argentina
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
    df['fecha_hora'] = df['fecha_hora'].dt.tz_localize("America/Argentina/Buenos_Aires", nonexistent='shift_forward', ambiguous='NaT')

    # CLIMA ACTUAL (hora más reciente pasada)
    df_pasado = df[df['fecha_hora'] <= ahora]

    if not df_pasado.empty:
        fila = df_pasado.iloc[-1]  # última hora pasada
    else:
        fila = df.iloc[0]  # por si el CSV tiene solo horas futuras

    coco = int(fila['coco']) if not pd.isna(fila['coco']) else None
    icono = weather_icons.get(coco, "unknown.svg")
    descripcion = weather_descriptions.get(coco, "Desconocido")

    # si la hora actual está entre las 20:00 y las 07:00, usamos versiones con luna
    hora_actual = ahora.hour
    if 20 <= hora_actual or hora_actual < 7:
        if icono == "clear.svg":
            icono = "clear_night.svg"
        elif icono == "fair.svg":
            icono = "fair_night.svg"

    fecha_iso = fila['fecha_hora'].strftime("%Y-%m-%dT%H:%M:%SZ")

    clima_actual.append({
        "provincia": provincia,
        "temperatura": round(fila['temp'], 1) if not pd.isna(fila['temp']) else None,
        "humedad": round(fila['rhum'], 1) if not pd.isna(fila['rhum']) else None,
        "precipitacion": round(fila['prcp'], 1) if not pd.isna(fila['prcp']) else None,
        "viento": round(fila['wspd'], 1) if not pd.isna(fila['wspd']) else None,
        "visibilidad": calcular_visibilidad(fila['temp'], fila['rhum'], fila['dwpt'], fila['prcp'], fila['snow'], fila['wspd'], coco),
        "sensacionTermica": calcular_sensacion_termica(fila['temp'], fila['rhum'], fila['wspd']),
        "uvIndex": calcular_radiacion_uv(fila['temp'], coco, fecha_iso),
        "coco": coco,
        "icono": icono,
        "condicion": descripcion,
        "fecha_hora": fila['fecha_hora'].strftime("%Y-%m-%d %H:%M:%S %Z")
    })

    # PRONÓSTICO HORARIO
    # buscamos primero la hora más reciente pasada o igual a la hora actual
    idx_actual = df[df['fecha_hora'] <= ahora].index.max()
    if pd.isna(idx_actual):
        idx_actual = 0

    # seleccionamos desde esa hora en adelante (máximo 6 filas)
    df_futuro = df.loc[idx_actual:].head(6)
    
    if not df_futuro.empty:
        horas_provincia = []
        
        for idx, fila_hora in enumerate(df_futuro.itertuples()):
            coco_hora = int(fila_hora.coco) if not pd.isna(fila_hora.coco) else None
            icono_hora = weather_icons.get(coco_hora, "unknown.svg")
            
            # Determinar si es de noche
            hora_fila = fila_hora.fecha_hora.hour
            if 20 <= hora_fila or hora_fila < 7:
                if icono_hora == "clear.svg":
                    icono_hora = "clear_night.svg"
                elif icono_hora == "fair.svg":
                    icono_hora = "fair_night.svg"
            
            # Formato de hora
            if idx == 0:  # Primera hora (actual)
                tiempo = "AHORA"
            else:
                # Formato 12 horas: "3 PM", "4 PM", etc.
                hora_12 = fila_hora.fecha_hora.strftime("%I %p").lstrip("0")
                tiempo = hora_12
            
            horas_provincia.append({
                "time": tiempo,
                "icon": icono_hora,
                "temp": round(fila_hora.temp, 1) if not pd.isna(fila_hora.temp) else None,
                "coco": coco_hora,
                "fecha_hora": fila_hora.fecha_hora.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        clima_horario[provincia] = horas_provincia

# guardamos los JSON

# clima actual
output_actual = os.path.join("web", "clima_actual.json")
with open(output_actual, "w", encoding="utf-8") as f:
    json.dump(clima_actual, f, ensure_ascii=False, indent=2)

# clima horario
output_horario = os.path.join("web", "clima_horario.json")
with open(output_horario, "w", encoding="utf-8") as f:
    json.dump(clima_horario, f, ensure_ascii=False, indent=2)

