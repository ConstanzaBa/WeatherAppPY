import pandas as pd
from meteostat import Hourly
from datetime import datetime, timedelta
import pytz
import os

# creamos la carpeta dataset y provincia si no existen
dataset = "dataset"
provincia_dir = os.path.join(dataset, "provincia")
os.makedirs(provincia_dir, exist_ok=True)

# para obtener el pronostico de cada hora obtenemos primero las estaciones que hay en cada provincia
stations = pd.read_csv(os.path.join(dataset, "stations.csv"))

# Periodo del pronostico
# Periodo deseado en hora local (Argentina)
tz_arg = pytz.timezone("America/Argentina/Buenos_Aires")

# fecha y hora actual en Argentina
ahora_local = datetime.now(tz_arg)

# inicio del día actual (00:00 hora local)
hoy_local = ahora_local.date()
start_local = tz_arg.localize(datetime.combine(hoy_local, datetime.min.time()))

# fin del rango: 48 horas desde el inicio del día actual
end_local = start_local + timedelta(hours=48)

# convertimos a UTC para pedírselo a Meteostat
start = start_local.astimezone(pytz.utc)
end = end_local.astimezone(pytz.utc)

all_data = []

for idx, row in stations.iterrows():
    id_estacion = row['id_estacion']
    nombre = row['name']          # estacion
    provincia = row['province']   # provincia correspondiente

    print(f"Descargando datos de {nombre} ({provincia})...")

    try:
        # pedimos datos desde el inicio del día actual (UTC) hasta 48 horas después
        data = Hourly(id_estacion, start.replace(tzinfo=None), end.replace(tzinfo=None))
        data = data.fetch()

        # filtramos para quedarnos solo con datos desde el inicio del día actual en UTC
        data = data[data.index >= start.replace(tzinfo=None)]

        if data.empty:
            print(f"No hay datos para {nombre}.")
            continue

        data = data.reset_index()
        data.rename(columns={'time': 'fecha_hora'}, inplace=True)

        # convertimos la hora a Argentina
        data['fecha_hora'] = (
            data['fecha_hora']
            .dt.tz_localize('UTC')
            .dt.tz_convert('America/Argentina/Buenos_Aires')
            .dt.tz_localize(None)
        )

        data['province'] = provincia

        # creamos el csv por provincia 
        archi_prov = os.path.join(provincia_dir, f"clima_{provincia}.csv")
        if os.path.exists(archi_prov): # si ya existe lo borramos y creamos uno nuevo
            os.remove(archi_prov)

        data.to_csv(archi_prov, index=False)
        all_data.append(data)
        print(f"Datos guardados en {archi_prov}")

    except Exception as e:
        print(f"Error con {nombre}: {e}")

# por si las dudas creamos uno que tenga todos los pronosticos por hora de cada provincia
if all_data:
    datos_combi = pd.concat(all_data, ignore_index=True)
    archi_combi = os.path.join(dataset, "clima_argentina.csv")

    if os.path.exists(archi_combi):
        os.remove(archi_combi)

    datos_combi.to_csv(archi_combi, index=False)
    print(f"CSV combinado guardado en {archi_combi}")

print("Descarga finalizada.")

# Definicion de cada columna

# fecha_hora: fecha y hora del registro (datetime)
# temp: temperatura del aire en °C 
# dwpt: punto de rocío en °C
# rhum: humedad relativa en %
# prcp: precipitación en mm/h
# snow: nieve en mm/h
# wdir: dirección del viento en grados (°)
# wspd: velocidad promedio del viento en km/h
# wpgt: ráfaga máxima de viento en km/h
# pres: presión atmosférica en hPa
# tsun: duración de insolación en minutos (sol)
# coco: código de condición climática (entero)
# province: nombre de la provincia o región
