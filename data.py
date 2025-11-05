import pandas as pd
from meteostat import Hourly
from datetime import datetime
import os

# creamos la carpeta dataset y provincia si no existen
dataset = "dataset"
provincia_dir = os.path.join(dataset, "provincia")
os.makedirs(provincia_dir, exist_ok=True)

# para obtener el pronostico de cada hora obtenemos primero las estaciones que hay en cada provincia
stations = pd.read_csv(os.path.join(dataset, "stations.csv"))

# Periodo del pronostico
start = datetime(2025, 10, 31)
end = datetime(2025, 11, 10, 23, 59)

all_data = []

for idx, row in stations.iterrows():
    id_estacion = row['id_estacion']
    nombre = row['name']          # estacion
    provincia = row['province']   # provincia correspondiente
    
    print(f"Descargando datos de {nombre} ({provincia})...")
    
    try:
        data = Hourly(id_estacion, start, end)
        data = data.fetch()
        
        if data.empty:
            print(f"No hay datos para {nombre}.")
            continue
        
        data = data.reset_index()
        data.rename(columns={'time': 'fecha_hora'}, inplace=True)

        # convertimos la hora 
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
