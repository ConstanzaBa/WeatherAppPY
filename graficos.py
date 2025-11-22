import matplotlib
matplotlib.use('Agg')  # Backend no interactivo para guardar imágenes

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.collections import LineCollection
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------------------------------------------------
# CONFIGURACIÓN GLOBAL
# ------------------------------------------------------------
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 7)
plt.rcParams['font.size'] = 11
DEFAULT_DPI = 200

PURPLE_A = "#6C4CCF"
PURPLE_B = "#8E6BFF"
PURPLE_C = "#B79CFF"

# ------------------------------------------------------------
# FUNCIONES AUXILIARES
# ------------------------------------------------------------

def cargar_datos(archivo='dataset/clima_argentina.csv'):
    """
    Carga el dataset climático.

    Parámetros:
        archivo (str): Ruta al archivo CSV.

    Retorna:
        DataFrame: Datos con columna fecha_hora ya convertida.
    """
    df = pd.read_csv(archivo)
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
    return df


def ensure_dir(path):
    """
    Crea el directorio indicado si no existe.

    Parámetros:
        path (str): Ruta del directorio.
    """
    if path:
        os.makedirs(path, exist_ok=True)


def normalize_filename(text):
    """
    Normaliza un texto para usarlo como parte de un nombre de archivo.

    Parámetros:
        text (str): Texto a normalizar.

    Retorna:
        str: Texto sin tildes, minúsculas y con guiones bajos.
    """
    if text is None:
        return "argentina"
    import unicodedata
    text = unicodedata.normalize('NFD', str(text))
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.replace(' ', '_').lower()


def filtrar_ultimas_horas(serie_o_df, horas=24):
    """
    Filtra una Serie o DataFrame para mantener solo las últimas N horas.
    
    Parámetros:
        serie_o_df: Serie o DataFrame con índice datetime
        horas (int): Número de horas a mantener
    
    Retorna:
        Serie o DataFrame filtrado
    """
    if isinstance(serie_o_df, pd.Series):
        if serie_o_df.empty:
            return serie_o_df
        fecha_limite = serie_o_df.index.max() - pd.Timedelta(hours=horas)
        return serie_o_df[serie_o_df.index >= fecha_limite]
    elif isinstance(serie_o_df, pd.DataFrame):
        if serie_o_df.empty:
            return serie_o_df
        if 'fecha_hora' in serie_o_df.columns:
            fecha_max = pd.to_datetime(serie_o_df['fecha_hora']).max()
            fecha_limite = fecha_max - pd.Timedelta(hours=horas)
            return serie_o_df[pd.to_datetime(serie_o_df['fecha_hora']) >= fecha_limite]
        else:
            fecha_limite = serie_o_df.index.max() - pd.Timedelta(hours=horas)
            return serie_o_df[serie_o_df.index >= fecha_limite]
    return serie_o_df


def esta_actualizado(archivo_csv, archivo_png):
    """
    Determina si el PNG ya fue generado después del CSV.

    Parámetros:
        archivo_csv (str): Ruta del CSV.
        archivo_png (str): Ruta del PNG.

    Retorna:
        bool: True si el PNG es más reciente que el CSV.
    """
    if not os.path.exists(archivo_png):
        return False
    fecha_csv = os.path.getmtime(archivo_csv)
    fecha_png = os.path.getmtime(archivo_png)
    return fecha_png > fecha_csv


def guardar_fig(fig, nombre_png):
    """
    Guarda la figura con formato uniforme.

    Parámetros:
        fig (Figure): Objeto figura.
        nombre_png (str): Ruta de guardado.
    """
    try:
        plt.tight_layout()
    except:
        pass  # Ignorar errores de tight_layout
    fig.savefig(nombre_png, dpi=DEFAULT_DPI, bbox_inches='tight', transparent=True)
    plt.close(fig)
    
    
# ------------------------------------------------------------
# PREPROCESADO / CACHE POR PROVINCIA
# ------------------------------------------------------------

def construir_cache_por_provincia(df):
    """
    Construye y devuelve un diccionario con series/frames pre-agregados por provincia
    para evitar repetir groupby en cada función de graficado.
    """
    cache = {}
    if df is None or df.empty:
        return cache

    # Agrupar por provincia y fecha_hora una sola vez
    gb = df.groupby(['province', 'fecha_hora'], sort=True)

    # Precalcular agregados comunes
    agg = gb.agg({
        'prcp': 'sum',
        'wspd': 'mean',
        'wpgt': 'mean',
        'wdir': 'mean',
        'rhum': 'mean',
        'temp': 'mean',
        'sensacionTermica': 'mean'
    }).reset_index()

    provinces = agg['province'].unique()
    for p in provinces:
        sub = agg[agg['province'] == p].copy()
        sub = sub.sort_values('fecha_hora')
        cache[p] = {
            'precip_total': sub.set_index('fecha_hora')['prcp'],
            'vel_prom': sub.set_index('fecha_hora')['wspd'],
            'vel_max': sub.set_index('fecha_hora')['wpgt'],
            'dir_prom': sub.set_index('fecha_hora')['wdir'],
            'hum_prom': sub.set_index('fecha_hora')['rhum'],
            'temp_mean': sub.set_index('fecha_hora')['temp'],
            'sens_mean': sub.set_index('fecha_hora')['sensacionTermica'],
            # frame para temp web (top 22 por fecha ya ordenadas)
            'temp_web': df[df['province'] == p].sort_values('fecha_hora').head(22).copy(),
            # datos de viento (wdir,wspd) para polar (sin groupby porque usamos valores originales)
            'viento_raw': df[df['province'] == p][['wdir','wspd']].dropna().copy()
        }

    # Cache para 'todas' las provincias combinadas
    combined = {}
    combined_gb = df.groupby('fecha_hora', sort=True)
    combined_agg = combined_gb.agg({
        'prcp': 'sum',
        'wspd': 'mean',
        'wpgt': 'mean',
        'wdir': 'mean',
        'rhum': 'mean'
    }).reset_index()
    combined['precip_total'] = combined_agg.set_index('fecha_hora')['prcp']
    combined['vel_prom'] = combined_agg.set_index('fecha_hora')['wspd']
    combined['vel_max'] = combined_agg.set_index('fecha_hora')['wpgt']
    combined['dir_prom'] = combined_agg.set_index('fecha_hora')['wdir']
    combined['hum_prom'] = combined_agg.set_index('fecha_hora')['rhum']
    cache[None] = {
        'precip_total': combined['precip_total'],
        'vel_prom': combined['vel_prom'],
        'vel_max': combined['vel_max'],
        'dir_prom': combined['dir_prom'],
        'hum_prom': combined['hum_prom'],
        'temp_web': df.sort_values('fecha_hora').head(22),
        'viento_raw': df[['wdir','wspd']].dropna()
    }

    return cache

# ------------------------------------------------------------
# GRÁFICOS
# ------------------------------------------------------------

def grafico_precipitacion(df, provincia=None, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv', cache=None):
    """
    Genera un gráfico de barras con la precipitación acumulada por hora.
    """
    if cache is not None and provincia in cache:
        precip_total = cache[provincia]['precip_total']
    else:
        df_filtrado = df[df['province'] == provincia] if provincia else df
        precip_total = df_filtrado.groupby('fecha_hora')['prcp'].sum()

    # FILTRAR ÚLTIMAS 24 HORAS
    precip_total = filtrar_ultimas_horas(precip_total, horas=24)

    nombre_png = os.path.join(output_dir, f'grafico_precipitacion_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if esta_actualizado(archivo_csv, nombre_png):
        return

    if precip_total.empty:
        return

    fig, ax = plt.subplots()
    fechas = precip_total.index if isinstance(precip_total.index, pd.DatetimeIndex) else pd.to_datetime(precip_total.index)
    ax.bar(fechas, precip_total.values, color=PURPLE_B, alpha=0.85, width=0.03)

    ax.set_xlabel('Hora', fontsize=13, color=PURPLE_B)
    ax.set_ylabel('Precipitación (mm)', fontsize=13, color=PURPLE_B)
    ax.tick_params(axis='x', colors=PURPLE_B, labelsize=11)
    ax.tick_params(axis='y', colors=PURPLE_B, labelsize=11)

    # Ajustar el formatter según la cantidad de datos
    if len(fechas) > 12:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    
    fig.autofmt_xdate(rotation=30, ha='right')
    guardar_fig(fig, nombre_png)


def grafico_velocidad_viento(df, provincia=None, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv', cache=None):
    """
    Grafica velocidad promedio y ráfagas de viento por hora.
    """
    if cache is not None and provincia in cache:
        vel_prom = cache[provincia]['vel_prom']
        vel_max = cache[provincia]['vel_max']
    else:
        df_filtrado = df[df['province'] == provincia] if provincia else df
        vel_prom = df_filtrado.groupby('fecha_hora')['wspd'].mean()
        vel_max = df_filtrado.groupby('fecha_hora')['wpgt'].mean()

    # FILTRAR ÚLTIMAS 24 HORAS
    vel_prom = filtrar_ultimas_horas(vel_prom, horas=24)
    vel_max = filtrar_ultimas_horas(vel_max, horas=24)

    nombre_png = os.path.join(output_dir, f'grafico_velocidad_viento_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if esta_actualizado(archivo_csv, nombre_png):
        return

    if vel_prom.empty:
        return

    fig, ax = plt.subplots()
    fechas = vel_prom.index if isinstance(vel_prom.index, pd.DatetimeIndex) else pd.to_datetime(vel_prom.index)
    ax.plot(fechas, vel_prom.values, color=PURPLE_B, linewidth=3, label='Velocidad promedio')
    if not vel_max.empty and not vel_max.isna().all():
        fechas_max = vel_max.index if isinstance(vel_max.index, pd.DatetimeIndex) else pd.to_datetime(vel_max.index)
        ax.plot(fechas_max, vel_max.values, color=PURPLE_A, linewidth=2.2, linestyle='--', label='Ráfagas')

    ax.set_xlabel('Hora', fontsize=13, color=PURPLE_B)
    ax.set_ylabel('Velocidad (km/h)', fontsize=13, color=PURPLE_B)
    ax.tick_params(axis='x', colors=PURPLE_B, labelsize=11)
    ax.tick_params(axis='y', colors=PURPLE_B, labelsize=11)

    if len(fechas) > 12:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    
    fig.autofmt_xdate(rotation=30, ha='right')
    ax.legend()
    guardar_fig(fig, nombre_png)


def grafico_direccion_viento(df, provincia=None, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv', cache=None):
    """
    Genera un gráfico polar de dirección de viento.
    """
    if cache is not None and provincia in cache:
        df_viento = cache[provincia]['viento_raw']
    else:
        df_filtrado = df[df['province'] == provincia] if provincia else df
        df_viento = df_filtrado[['wdir', 'wspd']].dropna()
    if df_viento.empty:
        return

    nombre_png = os.path.join(output_dir, f'grafico_direccion_viento_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if esta_actualizado(archivo_csv, nombre_png):
        return

    direcciones_rad = np.deg2rad(df_viento['wdir'].values)
    velocidades = df_viento['wspd'].values

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='polar')

    bins = np.linspace(0, 2*np.pi, 17)
    counts, _ = np.histogram(direcciones_rad, bins=bins, weights=velocidades)
    max_count = max(counts.max(), 1)

    cmap = LinearSegmentedColormap.from_list('purple_map', [PURPLE_C, PURPLE_B, PURPLE_A])
    colors = cmap(counts / max_count)

    width = 2*np.pi / 16
    theta = bins[:-1] + width/2

    ax.bar(theta, counts, width=width, color=colors, alpha=0.9, edgecolor='white')

    ax.set_xlabel('Dirección del Viento', color=PURPLE_A)
    ax.set_ylabel('Velocidad Acumulada', color=PURPLE_A)

    guardar_fig(fig, nombre_png)

def grafico_humedad(df, provincia=None, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv', cache=None):
    """
    Grafica la humedad relativa promedio por hora.
    """
    if cache is not None and provincia in cache:
        hum_prom = cache[provincia]['hum_prom']
    else:
        df_filtrado = df[df['province'] == provincia] if provincia else df
        hum_prom = df_filtrado.groupby('fecha_hora')['rhum'].mean()
    
    # FILTRAR ÚLTIMAS 24 HORAS
    hum_prom = filtrar_ultimas_horas(hum_prom, horas=24)
    
    if hum_prom.empty:
        return

    nombre_png = os.path.join(output_dir, f'grafico_humedad_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if esta_actualizado(archivo_csv, nombre_png):
        return

    fig, ax = plt.subplots()
    fechas = hum_prom.index if isinstance(hum_prom.index, pd.DatetimeIndex) else pd.to_datetime(hum_prom.index)
    ax.plot(fechas, hum_prom.values, color=PURPLE_B, linewidth=3)

    ax.set_xlabel('Hora', fontsize=13, color=PURPLE_B)
    ax.set_ylabel('Humedad (%)', fontsize=13, color=PURPLE_B)
    ax.tick_params(axis='x', colors=PURPLE_B, labelsize=11)
    ax.tick_params(axis='y', colors=PURPLE_B, labelsize=11)

    if len(fechas) > 12:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    
    fig.autofmt_xdate(rotation=30, ha='right')
    guardar_fig(fig, nombre_png)


def grafico_temp_vs_sensacion(df, provincia=None, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv', cache=None):
    """
    Compara temperatura y sensación térmica por hora.
    """
    if cache is not None and provincia in cache:
        temps = cache[provincia]['temp_mean']
        sens = cache[provincia]['sens_mean']
        
        # FILTRAR ÚLTIMAS 24 HORAS ANTES DE INTERSECCIÓN
        temps = filtrar_ultimas_horas(temps, horas=24)
        sens = filtrar_ultimas_horas(sens, horas=24)
        
        idx = temps.index.intersection(sens.index)
        if idx.empty:
            return
        df_filtrado = pd.DataFrame({
            'temp': temps.loc[idx].values,
            'sensacionTermica': sens.loc[idx].values
        }, index=idx).reset_index()
        df_filtrado.rename(columns={'index': 'fecha_hora'}, inplace=True)
    else:
        df_filtrado = df[df['province'] == provincia] if provincia else df
        df_filtrado = df_filtrado.sort_values('fecha_hora')
        df_filtrado = df_filtrado.dropna(subset=['temp','sensacionTermica'])
        # FILTRAR ÚLTIMAS 24 HORAS
        df_filtrado = filtrar_ultimas_horas(df_filtrado, horas=24)
    
    if df_filtrado.empty:
        return

    nombre_png = os.path.join(output_dir, f'grafico_temp_vs_sensacion_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if esta_actualizado(archivo_csv, nombre_png):
        return

    fig, ax = plt.subplots()
    fechas = pd.to_datetime(df_filtrado['fecha_hora'])
    ax.plot(fechas, df_filtrado['temp'], color=PURPLE_B, linewidth=3, label='Temperatura')
    ax.plot(fechas, df_filtrado['sensacionTermica'], color=PURPLE_A, linewidth=3, label='Sensación térmica')

    ax.set_xlabel('Hora', fontsize=13, color=PURPLE_B)
    ax.set_ylabel('Temperatura (°C)', fontsize=13, color=PURPLE_B)
    ax.tick_params(axis='x', colors=PURPLE_B, labelsize=11)
    ax.tick_params(axis='y', colors=PURPLE_B, labelsize=11)

    if len(fechas) > 12:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    
    fig.autofmt_xdate(rotation=30, ha='right')
    ax.legend()
    guardar_fig(fig, nombre_png)


def grafico_temp(df, provincia, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv', cache=None):
    """
    Gráfico estilizado para temperatura en la web.
    """
    if cache is not None and provincia in cache:
        df_filtrado = cache[provincia]['temp_web']
    else:
        df_filtrado = df[df['province'] == provincia].sort_values('fecha_hora').head(22)
    if df_filtrado.empty:
        return

    nombre_png = os.path.join(output_dir, f'temp_chart_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if esta_actualizado(archivo_csv, nombre_png):
        return

    fig, ax = plt.subplots()
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    primary_color = PURPLE_B
    secondary_color = PURPLE_A

    cmap = LinearSegmentedColormap.from_list('custom_purple', [primary_color, secondary_color])

    fechas = pd.to_datetime(df_filtrado['fecha_hora'])
    temps = df_filtrado['temp'].values
    
    # Convertir fechas a números para LineCollection
    dates = mdates.date2num(fechas)
    points = np.array([dates, temps]).T.reshape(-1,1,2)

    if len(points) > 1:
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        lc = LineCollection(segments, cmap=cmap, linewidths=4)
        lc.set_array(np.linspace(0,1,len(segments)))
        ax.add_collection(lc)

    ax.scatter(fechas, temps, c=primary_color, s=60, edgecolors='white', zorder=3)
    ax.fill_between(fechas, temps, alpha=0.18, color=primary_color)

    ax.set_xlabel('Hora', color=primary_color, fontsize=20, labelpad=15)
    ax.set_ylabel('Temperatura (°C)',  color=primary_color, fontsize=20, labelpad=15)
    ax.tick_params(axis='x', colors=primary_color, labelsize=16, pad=10)
    ax.tick_params(axis='y', colors=primary_color, labelsize=16, pad=10)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))

    fig.autofmt_xdate(rotation=30, ha='right')
    guardar_fig(fig, nombre_png)

# ------------------------------------------------------------
# GENERACIÓN POR PROVINCIA
# ------------------------------------------------------------

def generar_graficos_provincia(provincia, df, cache, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv'):
    """
    Genera todos los gráficos para una provincia.
    """
    grafico_precipitacion(df, provincia, output_dir, archivo_csv, cache=cache)
    grafico_velocidad_viento(df, provincia, output_dir, archivo_csv, cache=cache)
    grafico_direccion_viento(df, provincia, output_dir, archivo_csv, cache=cache)
    grafico_humedad(df, provincia, output_dir, archivo_csv, cache=cache)
    grafico_temp_vs_sensacion(df, provincia, output_dir, archivo_csv, cache=cache)
    grafico_temp(df, provincia, output_dir, archivo_csv, cache=cache)

# ------------------------------------------------------------
# GENERAR TODOS LOS GRÁFICOS
# ------------------------------------------------------------

def generar_todos_los_graficos(df=None, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv', max_workers=4):
    """
    Genera todos los gráficos para todas las provincias usando multihilo.
    """
    if df is None:
        df = cargar_datos(archivo_csv)

    cache = construir_cache_por_provincia(df)

    provincias = df['province'].unique()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(generar_graficos_provincia, p, df, cache, output_dir, archivo_csv) for p in provincias]
        for fut in as_completed(futures):
            # no prints nuevos; solo consumir excepciones si las hay
            _ = fut.result()

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    df = cargar_datos()
    generar_todos_los_graficos(df)
