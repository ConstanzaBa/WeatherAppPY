# Archivo completo corregido, con docstrings y sin títulos en los gráficos

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
from concurrent.futures import ThreadPoolExecutor

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
    plt.tight_layout()
    fig.savefig(nombre_png, dpi=DEFAULT_DPI, bbox_inches='tight', transparent=True)
    plt.close(fig)

# ------------------------------------------------------------
# GRÁFICOS
# ------------------------------------------------------------

def grafico_precipitacion(df, provincia=None, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv'):
    """
    Genera un gráfico de barras con la precipitación acumulada por hora.
    """
    df_filtrado = df[df['province'] == provincia] if provincia else df
    precip_total = df_filtrado.groupby('fecha_hora')['prcp'].sum()

    nombre_png = os.path.join(output_dir, f'grafico_precipitacion_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if esta_actualizado(archivo_csv, nombre_png):
        return

    fig, ax = plt.subplots()
    ax.bar(precip_total.index, precip_total.values, color=PURPLE_B, alpha=0.85, width=0.03)

    ax.set_xlabel('Hora', fontsize=13, color=PURPLE_B)
    ax.set_ylabel('Precipitación (mm)', fontsize=13, color=PURPLE_B)
    ax.tick_params(axis='x', colors=PURPLE_B, labelsize=11)
    ax.tick_params(axis='y', colors=PURPLE_B, labelsize=11)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    fig.autofmt_xdate(rotation=30)
    guardar_fig(fig, nombre_png)


def grafico_velocidad_viento(df, provincia=None, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv'):
    """
    Grafica velocidad promedio y ráfagas de viento por hora.
    """
    df_filtrado = df[df['province'] == provincia] if provincia else df
    vel_prom = df_filtrado.groupby('fecha_hora')['wspd'].mean()
    vel_max = df_filtrado.groupby('fecha_hora')['wpgt'].mean()

    nombre_png = os.path.join(output_dir, f'grafico_velocidad_viento_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if esta_actualizado(archivo_csv, nombre_png):
        return

    fig, ax = plt.subplots()
    ax.plot(vel_prom.index, vel_prom.values, color=PURPLE_B, linewidth=3)
    if not vel_max.empty and not vel_max.isna().all():
        ax.plot(vel_max.index, vel_max.values, color=PURPLE_A, linewidth=2.2, linestyle='--')

    ax.set_xlabel('Hora', fontsize=13, color=PURPLE_B)
    ax.set_ylabel('Velocidad (km/h)', fontsize=13, color=PURPLE_B)
    ax.tick_params(axis='x', colors=PURPLE_B, labelsize=11)
    ax.tick_params(axis='y', colors=PURPLE_B, labelsize=11)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    fig.autofmt_xdate(rotation=30)
    guardar_fig(fig, nombre_png)


def grafico_direccion_viento(df, provincia=None, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv'):
    """
    Genera un gráfico polar de dirección de viento.
    """
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


def grafico_lineal_direccion_viento(df, provincia=None, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv'):
    """
    Genera un gráfico lineal de dirección promedio del viento.
    """
    df_filtrado = df[df['province'] == provincia] if provincia else df
    dir_prom = df_filtrado.groupby('fecha_hora')['wdir'].mean()
    if dir_prom.empty:
        return

    nombre_png = os.path.join(output_dir, f'grafico_lineal_direccion_viento_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if esta_actualizado(archivo_csv, nombre_png):
        return

    fig, ax = plt.subplots()
    sc = ax.scatter(dir_prom.index, dir_prom.values, c=dir_prom.values, cmap='twilight', s=60, alpha=0.85)

    ax.set_xlabel('Hora', fontsize=13, color=PURPLE_A)
    ax.set_ylabel('Dirección (°)', fontsize=13, color=PURPLE_A)
    ax.tick_params(axis='x', colors=PURPLE_A, labelsize=11)
    ax.tick_params(axis='y', colors=PURPLE_A, labelsize=11)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    fig.autofmt_xdate(rotation=30)

    plt.colorbar(sc, label='Dirección (°)')
    guardar_fig(fig, nombre_png)


def grafico_humedad(df, provincia=None, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv'):
    """
    Grafica la humedad relativa promedio por hora.
    """
    df_filtrado = df[df['province'] == provincia] if provincia else df
    hum_prom = df_filtrado.groupby('fecha_hora')['rhum'].mean()
    if hum_prom.empty:
        return

    nombre_png = os.path.join(output_dir, f'grafico_humedad_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if esta_actualizado(archivo_csv, nombre_png):
        return

    fig, ax = plt.subplots()
    ax.plot(hum_prom.index, hum_prom.values, color=PURPLE_B, linewidth=3)

    ax.set_xlabel('Hora', fontsize=13, color=PURPLE_B)
    ax.set_ylabel('Humedad (%)', fontsize=13, color=PURPLE_B)
    ax.tick_params(axis='x', colors=PURPLE_B, labelsize=11)
    ax.tick_params(axis='y', colors=PURPLE_B, labelsize=11)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    fig.autofmt_xdate(rotation=30)
    guardar_fig(fig, nombre_png)


def grafico_temp_vs_sensacion(df, provincia=None, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv'):
    """
    Compara temperatura y sensación térmica por hora.
    """
    df_filtrado = df[df['province'] == provincia].sort_values('fecha_hora')
    df_filtrado = df_filtrado.dropna(subset=['temp','sensacionTermica'])
    if df_filtrado.empty:
        return

    nombre_png = os.path.join(output_dir, f'grafico_temp_vs_sensacion_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if esta_actualizado(archivo_csv, nombre_png):
        return

    fig, ax = plt.subplots()
    ax.plot(df_filtrado['fecha_hora'], df_filtrado['temp'], color=PURPLE_B, linewidth=3)
    ax.plot(df_filtrado['fecha_hora'], df_filtrado['sensacionTermica'], color=PURPLE_A, linewidth=3)

    ax.set_xlabel('Hora', fontsize=13, color=PURPLE_B)
    ax.set_ylabel('Temperatura (°C)', fontsize=13, color=PURPLE_B)
    ax.tick_params(axis='x', colors=PURPLE_B, labelsize=11)
    ax.tick_params(axis='y', colors=PURPLE_B, labelsize=11)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    fig.autofmt_xdate(rotation=30)
    guardar_fig(fig, nombre_png)


def grafico_temp_web(df, provincia, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv'):
    """
    Gráfico estilizado para temperatura en la web.
    """
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

    dates = mdates.date2num(df_filtrado['fecha_hora'])
    temps = df_filtrado['temp'].values
    points = np.array([dates, temps]).T.reshape(-1,1,2)

    if len(points) > 1:
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        lc = LineCollection(segments, cmap=cmap, linewidths=4)
        lc.set_array(np.linspace(0,1,len(segments)))
        ax.add_collection(lc)

    ax.scatter(df_filtrado['fecha_hora'], temps, c=primary_color, s=60, edgecolors='white')
    ax.fill_between(df_filtrado['fecha_hora'], temps, alpha=0.18, color=primary_color)

    ax.set_xlabel('Hora', color=primary_color, fontsize=20, labelpad=15)
    ax.set_ylabel('Temperatura (°C)',  color=primary_color, fontsize=20, labelpad=15)
    ax.tick_params(axis='x', colors=primary_color, labelsize=16, pad=10)
    ax.tick_params(axis='y', colors=primary_color, labelsize=16, pad=10)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))

    fig.autofmt_xdate(rotation=30)
    guardar_fig(fig, nombre_png)

# ------------------------------------------------------------
# GENERACIÓN POR PROVINCIA
# ------------------------------------------------------------

def generar_graficos_provincia(provincia, df, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv'):
    """
    Genera todos los gráficos para una provincia.
    """
    grafico_precipitacion(df, provincia, output_dir, archivo_csv)
    grafico_velocidad_viento(df, provincia, output_dir, archivo_csv)
    grafico_direccion_viento(df, provincia, output_dir, archivo_csv)
    grafico_lineal_direccion_viento(df, provincia, output_dir, archivo_csv)
    grafico_humedad(df, provincia, output_dir, archivo_csv)
    grafico_temp_vs_sensacion(df, provincia, output_dir, archivo_csv)
    grafico_temp_web(df, provincia, output_dir, archivo_csv)

# ------------------------------------------------------------
# GENERAR TODOS LOS GRÁFICOS
# ------------------------------------------------------------

def generar_todos_los_graficos_web(df=None, output_dir='web/img/graphs', archivo_csv='dataset/clima_argentina.csv', max_workers=4):
    """
    Genera todos los gráficos para todas las provincias usando multihilo.
    """
    if df is None:
        df = cargar_datos(archivo_csv)

    provincias = df['province'].unique()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(lambda p: generar_graficos_provincia(p, df, output_dir, archivo_csv), provincias)

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    df = cargar_datos()
    generar_todos_los_graficos_web(df)
