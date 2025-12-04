"""
Script de generación de gráficos del proyecto Clima Argentina.

Descripción general:
Este script toma los datos horarios de cada provincia desde los CSV generados
por el sistema de actualización de clima y genera los gráficos meteorológicos
para la interfaz web. Se centra en visualizaciones de temperatura, precipitación,
viento, humedad y sensación térmica, usando Matplotlib en modo servidor (sin GUI).

Funciones principales:
1. Carga datos horarios de cada provincia y filtra los últimos 7 días.
2. Construye cache local para optimizar cálculos y gráficos:
    - Datos diarios agregados (precipitación, viento, temperatura, humedad)
    - Datos horarios de hoy para gráficos web
    - Histograma de dirección y velocidad de viento
3. Genera gráficos individuales por provincia:
    - Temperatura horaria
    - Precipitación diaria acumulada
    - Velocidad y ráfagas de viento
    - Dirección de viento (polar)
    - Humedad relativa diaria
    - Comparación temperatura vs sensación térmica
4. Guarda los gráficos como PNG en `web/img/graphs`, verificando si ya están actualizados.
5. Permite generar todos los gráficos de todas las provincias en paralelo.
6. Se ejecuta automáticamente cuando se llama directamente, asegurando la carpeta de salida.
"""


# ===========================
# IMPORTS
# ===========================
import matplotlib  # Librería principal para gráficos
matplotlib.use('Agg')  # Configura Matplotlib en modo 'server', sin abrir ventanas GUI

import pandas as pd  # Para manejo de CSVs y datos tabulares
import matplotlib.pyplot as plt  # Para graficar con Matplotlib
import matplotlib.dates as mdates  # Para formatear fechas en los ejes de los gráficos
import numpy as np  # Para operaciones numéricas, arreglos y cálculos de histogramas
import os  # Para manejo de archivos y directorios
from matplotlib.colors import LinearSegmentedColormap  # Para crear gradientes de color personalizados
from matplotlib.collections import LineCollection  # Para dibujar líneas con gradientes de color
from concurrent.futures import ThreadPoolExecutor, as_completed  
# Para paralelización de la generación de gráficos por provincia

from datetime import datetime, timedelta  # Para manejo de fechas y cálculos de rangos temporales
import warnings  # Para suprimir advertencias innecesarias
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")  # Ignora warnings de Matplotlib


# =============================================================
# CONFIGURACIÓN GLOBAL
# =============================================================
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 7)
plt.rcParams['font.size'] = 11
DEFAULT_DPI = 200

PURPLE_A = "#6C4CCF"
PURPLE_B = "#8E6BFF"
PURPLE_C = "#B79CFF"

WEEKDAY_SHORT_ES = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

PROVINCIA_DIR = os.path.join("dataset", "provincia")
OUTPUT_DIR_DEFAULT = 'web/img/graphs'


# =============================================================
# FUNCIONES AUXILIARES
# =============================================================

def ensure_dir(path):
    """
    Asegura que el directorio exista.
    
    Parámetros:
        path (str): Ruta de directorio.
        
    Retorna:
        None
    """
    if path:
        os.makedirs(path, exist_ok=True)


def normalize_filename(text):
    """
    Normaliza un texto para usarlo como nombre de archivo.
    Convierte a minúsculas, reemplaza espacios por '_' y elimina tildes.
    
    Parámetros:
        text (str | None): Texto a normalizar.
        
    Retorna:
        str: Nombre de archivo normalizado.
    """
    if text is None:
        return "argentina"
    import unicodedata
    text = unicodedata.normalize('NFD', str(text))
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.replace(' ', '_').lower()


def esta_actualizado(archivo_csv, archivo_png):
    """
    Verifica si el PNG está más actualizado que el CSV correspondiente.
    
    Parámetros:
        archivo_csv (str): Ruta al CSV de origen.
        archivo_png (str): Ruta al PNG generado.
        
    Retorna:
        bool: True si PNG existe y es más reciente que el CSV, False en caso contrario.
    """
    if not os.path.exists(archivo_png):
        return False
    fecha_csv = os.path.getmtime(archivo_csv)
    fecha_png = os.path.getmtime(archivo_png)
    return fecha_png > fecha_csv


def guardar_fig(fig, nombre_png):
    """
    Guarda la figura de Matplotlib en disco y la cierra.
    
    Parámetros:
        fig (matplotlib.figure.Figure): Figura a guardar.
        nombre_png (str): Ruta de salida para el PNG.
        
    Retorna:
        None
    """
    plt.tight_layout()
    fig.savefig(nombre_png, dpi=DEFAULT_DPI, bbox_inches='tight', transparent=True)
    plt.close(fig)


def fechas_ultimos_7_dias():
    """
    Genera una lista de fechas de los últimos 7 días incluyendo hoy.
    
    Retorna:
        list[date]: Lista de objetos date.
    """
    hoy = pd.Timestamp.now().normalize()
    fecha_inicio = hoy - pd.Timedelta(days=6)  # incluye hoy => 7 días
    fechas = [ (fecha_inicio + pd.Timedelta(days=i)).date() for i in range(7) ]
    return fechas


def labels_from_dates(dates):
    """
    Genera etiquetas cortas en español para los días de la semana de una lista de fechas.
    
    Parámetros:
        dates (list[date | datetime]): Lista de fechas.
        
    Retorna:
        list[str]: Lista de etiquetas ['Lun', 'Mar', ...].
    """
    return [WEEKDAY_SHORT_ES[pd.to_datetime(d).weekday()] for d in dates]


# =============================================================
# CARGA DE DATOS POR PROVINCIA
# =============================================================

def cargar_datos_provincia(provincia):
    """
    Lee el CSV de una provincia y filtra los últimos 7 días incluyendo hoy.
    
    Parámetros:
        provincia (str): Nombre de la provincia.
        
    Retorna:
        tuple:
            pd.DataFrame | None: DataFrame filtrado o None si no existe.
            str: Ruta al archivo CSV correspondiente.
    """
    archivo_prov = os.path.join(PROVINCIA_DIR, f"clima_{provincia}.csv")
    if not os.path.exists(archivo_prov):
        return None, archivo_prov

    df = pd.read_csv(archivo_prov)
    if 'fecha_hora' not in df.columns:
        return None, archivo_prov

    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
    hoy = pd.Timestamp.now().normalize()
    inicio = hoy - pd.Timedelta(days=6)
    manana = hoy + pd.Timedelta(days=1)
    df = df[(df['fecha_hora'] >= inicio) & (df['fecha_hora'] < manana)].sort_values('fecha_hora')
    return df, archivo_prov

# =============================================================
# CACHE LOCAL POR PROVINCIA
# =============================================================

def construir_cache_local(df_prov):
    """
    Construye la cache para una provincia.
    Contiene:
        - daily: datos agregados por día (precipitación, viento, temperatura, humedad)
        - temp_web: datos horarios para hoy (para gráficos web)
        - viento_hist: histograma de dirección y velocidad de viento
    
    Parámetros:
        df_prov (pd.DataFrame | None): DataFrame de la provincia, puede ser None o vacío.
        
    Retorna:
        dict: Diccionario con claves 'daily', 'temp_web' y 'viento_hist'. 
        Retorna dict vacío si df_prov es None o está vacío.
    """
    cache = {}
    if df_prov is None or df_prov.empty:
        return cache

    df_copy = df_prov.copy()
    df_copy['dia'] = df_copy['fecha_hora'].dt.date

    # --------------------------------------------------------
    # Datos diarios agregados (por día)
    # --------------------------------------------------------
    daily = df_copy.groupby('dia').agg({
        'prcp': 'sum',                 # precipitación total
        'wspd': 'mean',                # velocidad promedio del viento
        'wpgt': 'mean',                # ráfagas promedio
        'wdir': 'mean',                # dirección promedio
        'rhum': 'mean',                # humedad relativa promedio
        'temp': 'mean',                # temperatura promedio
        'sensacionTermica': 'mean'     # sensación térmica promedio
    }).reset_index()

    # --------------------------------------------------------
    # Datos horarios para hoy (temp_web)
    # --------------------------------------------------------
    hoy = pd.Timestamp.now().normalize()
    manana = hoy + pd.Timedelta(days=1)
    df_hoy = df_copy[(df_copy['fecha_hora'] >= hoy) & (df_copy['fecha_hora'] < manana)].sort_values('fecha_hora')

    # --------------------------------------------------------
    # Histograma de viento: acumulación por dirección
    # --------------------------------------------------------
    v_raw = df_copy[['wdir','wspd']].dropna()
    if not v_raw.empty:
        direcciones = np.deg2rad(v_raw['wdir'].values)  # convertir a radianes
        velocidades = v_raw['wspd'].values
        bins = np.linspace(0, 2*np.pi, 17)  # 16 sectores (16 barras)
        counts, _ = np.histogram(direcciones, bins=bins, weights=velocidades)
    else:
        bins = np.linspace(0, 2*np.pi, 17)
        counts = np.zeros(len(bins)-1)

    # --------------------------------------------------------
    # Guardar en cache
    # --------------------------------------------------------
    cache['daily'] = daily
    cache['temp_web'] = df_hoy.reset_index(drop=True)
    cache['viento_hist'] = {'bins': bins, 'counts': counts}

    return cache

# =============================================================
# FUNCIONES DE GRAFICOS
# =============================================================

def grafico_temp(df_prov, provincia, output_dir=OUTPUT_DIR_DEFAULT, archivo_csv=None, cache_local=None):
    """
    Grafico de temperatura horaria para hoy.
    
    Parámetros:
        df_prov (pd.DataFrame): DataFrame con datos de la provincia.
        provincia (str): Nombre de la provincia.
        output_dir (str): Carpeta de salida para el PNG.
        archivo_csv (str | None): CSV de origen para chequear si el PNG está actualizado.
        cache_local (dict | None): Cache construida con construir_cache_local.
        
    Retorna:
        None. Guarda el PNG del gráfico si no está actualizado.
    """
    if cache_local is not None and 'temp_web' in cache_local:
        df_filtrado = cache_local['temp_web']
    else:
        hoy = pd.Timestamp.now().normalize()
        manana = hoy + pd.Timedelta(days=1)
        df_filtrado = df_prov[(df_prov['fecha_hora'] >= hoy) & (df_prov['fecha_hora'] < manana)].sort_values('fecha_hora')

    if df_filtrado is None or df_filtrado.empty:
        return

    nombre_png = os.path.join(output_dir, f'temp_chart_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if archivo_csv and esta_actualizado(archivo_csv, nombre_png):
        return

    fig, ax = plt.subplots()
    fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    primary_color = PURPLE_B; secondary_color = PURPLE_A
    cmap = LinearSegmentedColormap.from_list('custom_purple', [primary_color, secondary_color])

    dates = mdates.date2num(pd.to_datetime(df_filtrado['fecha_hora']))
    temps = df_filtrado['temp'].values
    points = np.array([dates, temps]).T.reshape(-1,1,2)

    if len(points) > 1:
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        lc = LineCollection(segments, cmap=cmap, linewidths=4)
        lc.set_array(np.linspace(0,1,len(segments)))
        ax.add_collection(lc)

    ax.scatter(pd.to_datetime(df_filtrado['fecha_hora']), temps, c=primary_color, s=60, edgecolors='white')
    ax.fill_between(pd.to_datetime(df_filtrado['fecha_hora']), temps, alpha=0.18, color=primary_color)

    ax.set_xlabel('Hora', color=primary_color, fontsize=20, labelpad=15)
    ax.set_ylabel('Temperatura (°C)',  color=primary_color, fontsize=20, labelpad=15)
    ax.tick_params(axis='x', colors=primary_color, labelsize=16, pad=10)
    ax.tick_params(axis='y', colors=primary_color, labelsize=16, pad=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    fig.autofmt_xdate(rotation=30)
    guardar_fig(fig, nombre_png)


def grafico_precipitacion(df_prov, provincia, output_dir=OUTPUT_DIR_DEFAULT, archivo_csv=None, cache_local=None):
    """
    Grafico de precipitación diaria acumulada para los últimos 7 días.
    
    Parámetros:
        df_prov (pd.DataFrame): DataFrame con datos de la provincia.
        provincia (str): Nombre de la provincia.
        output_dir (str): Carpeta de salida para el PNG.
        archivo_csv (str | None): CSV de origen para chequear actualización.
        cache_local (dict | None): Cache construida con construir_cache_local.
        
    Retorna:
        None. Guarda el PNG del gráfico.
    """
    fechas_7 = fechas_ultimos_7_dias()
    if cache_local is not None and 'daily' in cache_local:
        d = cache_local['daily']
        mapping = { pd.to_datetime(row['dia']).date(): row['prcp'] for _, row in d.iterrows() }
    else:
        df_local = df_prov.copy()
        df_local['dia'] = df_local['fecha_hora'].dt.date
        mapping = df_local.groupby('dia')['prcp'].sum().to_dict()

    valores = [ float(mapping.get(day, 0.0)) for day in fechas_7 ]
    labels = labels_from_dates(fechas_7)

    nombre_png = os.path.join(output_dir, f'grafico_precipitacion_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if archivo_csv and esta_actualizado(archivo_csv, nombre_png):
        return

    fig, ax = plt.subplots()
    x = np.arange(len(fechas_7))
    ax.bar(x, valores, color=PURPLE_B, alpha=0.85)

    ax.set_xlabel('Día', fontsize=13, color=PURPLE_B)
    ax.set_ylabel('Precipitación (mm)', fontsize=13, color=PURPLE_B)
    ax.tick_params(axis='x', colors=PURPLE_B, labelsize=11)
    ax.tick_params(axis='y', colors=PURPLE_B, labelsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    fig.autofmt_xdate(rotation=30)
    guardar_fig(fig, nombre_png)


def grafico_velocidad_viento(df_prov, provincia, output_dir=OUTPUT_DIR_DEFAULT, archivo_csv=None, cache_local=None):
    """
    Grafico de velocidad promedio y ráfagas promedio por día para los últimos 7 días.
    
    Parámetros:
        df_prov (pd.DataFrame): Datos de la provincia.
        provincia (str): Nombre de la provincia.
        output_dir (str): Carpeta de salida.
        archivo_csv (str | None): CSV para verificación de actualización.
        cache_local (dict | None): Cache local para optimizar cálculos.
    
    Retorna:
        None. Guarda el PNG del gráfico.
    """
    fechas_7 = fechas_ultimos_7_dias()
    if cache_local is not None and 'daily' in cache_local:
        d = cache_local['daily']
        mapping_vprom = { pd.to_datetime(row['dia']).date(): row['wspd'] for _, row in d.iterrows() }
        mapping_vmax = { pd.to_datetime(row['dia']).date(): row['wpgt'] for _, row in d.iterrows() }
    else:
        df_local = df_prov.copy()
        df_local['dia'] = df_local['fecha_hora'].dt.date
        g = df_local.groupby('dia')
        mapping_vprom = g['wspd'].mean().to_dict()
        mapping_vmax = g['wpgt'].mean().to_dict()

    vprom = [ float(mapping_vprom.get(day, np.nan)) for day in fechas_7 ]
    vmax = [ float(mapping_vmax.get(day, np.nan)) for day in fechas_7 ]
    labels = labels_from_dates(fechas_7)
    x = np.arange(len(fechas_7))

    nombre_png = os.path.join(output_dir, f'grafico_velocidad_viento_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if archivo_csv and esta_actualizado(archivo_csv, nombre_png):
        return

    fig, ax = plt.subplots()
    ax.plot(x, vprom, color=PURPLE_B, linewidth=3)
    ax.plot(x, vmax, color=PURPLE_A, linewidth=2.2, linestyle='--')

    ax.set_xlabel('Día', fontsize=13, color=PURPLE_B)
    ax.set_ylabel('Velocidad (km/h)', fontsize=13, color=PURPLE_B)
    ax.tick_params(axis='x', colors=PURPLE_B)
    ax.tick_params(axis='y', colors=PURPLE_B)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    fig.autofmt_xdate(rotation=30)
    guardar_fig(fig, nombre_png)


def grafico_direccion_viento(df_prov, provincia, output_dir=OUTPUT_DIR_DEFAULT, archivo_csv=None, cache_local=None):
    """
    Grafico polar de dirección de viento usando histograma cacheado.
    
    Parámetros:
        df_prov (pd.DataFrame): Datos de la provincia.
        provincia (str): Nombre de la provincia.
        output_dir (str): Carpeta de salida del PNG.
        archivo_csv (str | None): CSV para chequear actualización.
        cache_local (dict | None): Cache con histograma de viento.
        
    Retorna:
        None. Guarda el PNG del gráfico polar.
    """
    if cache_local is not None and 'viento_hist' in cache_local:
        bins = cache_local['viento_hist']['bins']
        counts = cache_local['viento_hist']['counts']
    else:
        v_raw = df_prov[['wdir','wspd']].dropna()
        if v_raw.empty:
            return
        direcciones = np.deg2rad(v_raw['wdir'].values)
        velocidades = v_raw['wspd'].values
        bins = np.linspace(0, 2*np.pi, 17)
        counts, _ = np.histogram(direcciones, bins=bins, weights=velocidades)

    nombre_png = os.path.join(output_dir, f'grafico_direccion_viento_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if archivo_csv and esta_actualizado(archivo_csv, nombre_png):
        return

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='polar')
    max_count = max(counts.max() if hasattr(counts, 'max') else np.max(counts), 1)
    cmap = LinearSegmentedColormap.from_list('purple_map', [PURPLE_C, PURPLE_B, PURPLE_A])
    colors = cmap(counts / max_count)
    width = 2*np.pi / 16
    theta = bins[:-1] + width/2
    ax.bar(theta, counts, width=width, color=colors, alpha=0.9, edgecolor='white')
    ax.set_xlabel('Dirección del Viento', color=PURPLE_A)
    ax.set_ylabel('Velocidad Acumulada', color=PURPLE_A)
    guardar_fig(fig, nombre_png)


def grafico_humedad(df_prov, provincia, output_dir=OUTPUT_DIR_DEFAULT, archivo_csv=None, cache_local=None):
    """
    Grafico de humedad relativa promedio diaria (7 días).
    
    Parámetros:
        df_prov (pd.DataFrame): Datos de la provincia.
        provincia (str): Nombre de la provincia.
        output_dir (str): Carpeta de salida.
        archivo_csv (str | None): CSV para chequear actualización.
        cache_local (dict | None): Cache con datos diarios.
    
    Retorna:
        None. Guarda el PNG del gráfico.
    """
    fechas_7 = fechas_ultimos_7_dias()
    if cache_local is not None and 'daily' in cache_local:
        d = cache_local['daily']
        mapping = { pd.to_datetime(row['dia']).date(): row['rhum'] for _, row in d.iterrows() }
    else:
        df_local = df_prov.copy()
        df_local['dia'] = df_local['fecha_hora'].dt.date
        mapping = df_local.groupby('dia')['rhum'].mean().to_dict()

    valores = [ float(mapping.get(day, np.nan)) for day in fechas_7 ]
    labels = labels_from_dates(fechas_7)
    x = np.arange(len(fechas_7))

    nombre_png = os.path.join(output_dir, f'grafico_humedad_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if archivo_csv and esta_actualizado(archivo_csv, nombre_png):
        return

    fig, ax = plt.subplots()
    ax.plot(x, valores, color=PURPLE_B, linewidth=3)
    ax.set_xlabel('Día', fontsize=13, color=PURPLE_B)
    ax.set_ylabel('Humedad (%)', fontsize=13, color=PURPLE_B)
    ax.tick_params(axis='x', colors=PURPLE_B)
    ax.tick_params(axis='y', colors=PURPLE_B)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    fig.autofmt_xdate(rotation=30)
    guardar_fig(fig, nombre_png)


def grafico_temp_vs_sensacion(df_prov, provincia, output_dir=OUTPUT_DIR_DEFAULT, archivo_csv=None, cache_local=None):
    """
    Grafico comparando temperatura promedio vs sensación térmica diaria (7 días).
    
    Parámetros:
        df_prov (pd.DataFrame): Datos de la provincia.
        provincia (str): Nombre de la provincia.
        output_dir (str): Carpeta de salida.
        archivo_csv (str | None): CSV para chequear actualización.
        cache_local (dict | None): Cache con datos diarios.
    
    Retorna:
        None. Guarda el PNG del gráfico.
    """
    fechas_7 = fechas_ultimos_7_dias()
    if cache_local is not None and 'daily' in cache_local:
        d = cache_local['daily']
        mapping_t = { pd.to_datetime(row['dia']).date(): row['temp'] for _, row in d.iterrows() }
        mapping_s = { pd.to_datetime(row['dia']).date(): row['sensacionTermica'] for _, row in d.iterrows() }
    else:
        df_local = df_prov.copy()
        df_local['dia'] = df_local['fecha_hora'].dt.date
        g = df_local.groupby('dia')
        mapping_t = g['temp'].mean().to_dict()
        mapping_s = g['sensacionTermica'].mean().to_dict()

    t = [ float(mapping_t.get(day, np.nan)) for day in fechas_7 ]
    s = [ float(mapping_s.get(day, np.nan)) for day in fechas_7 ]
    labels = labels_from_dates(fechas_7)
    x = np.arange(len(fechas_7))

    nombre_png = os.path.join(output_dir, f'grafico_temp_vs_sensacion_{normalize_filename(provincia)}.png')
    ensure_dir(output_dir)
    if archivo_csv and esta_actualizado(archivo_csv, nombre_png):
        return

    fig, ax = plt.subplots()
    ax.plot(x, t, color=PURPLE_B, linewidth=3)
    ax.plot(x, s, color=PURPLE_A, linewidth=3)
    ax.set_xlabel('Día', fontsize=13, color=PURPLE_B)
    ax.set_ylabel('Temperatura (°C)', fontsize=13, color=PURPLE_B)
    ax.tick_params(axis='x', colors=PURPLE_B)
    ax.tick_params(axis='y', colors=PURPLE_B)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    fig.autofmt_xdate(rotation=30)
    guardar_fig(fig, nombre_png)


# =============================================================
# GENERACIÓN DE GRAFICOS POR PROVINCIA
# =============================================================

def generar_graficos_provincia_por_archivo(provincia, output_dir=OUTPUT_DIR_DEFAULT, max_workers_local=1):
    """
    Genera todos los gráficos de una provincia.
    
    Parámetros:
        provincia (str): Nombre de la provincia.
        output_dir (str): Carpeta de salida.
        max_workers_local (int): Para paralelización interna (no usado en esta versión).
    
    Retorna:
        tuple: (provincia, estado)
            estado: 'ok' si generó todos los gráficos
                    'no_file' si no existe CSV
                    'error' si ocurrió algún error
    """
    df_prov, archivo_prov = cargar_datos_provincia(provincia)
    if df_prov is None:
        return provincia, "no_file"

    cache_local = construir_cache_local(df_prov)

    try:
        grafico_precipitacion(df_prov, provincia, output_dir, archivo_prov, cache_local)
        grafico_velocidad_viento(df_prov, provincia, output_dir, archivo_prov, cache_local)
        grafico_direccion_viento(df_prov, provincia, output_dir, archivo_prov, cache_local)
        grafico_humedad(df_prov, provincia, output_dir, archivo_prov, cache_local)
        grafico_temp_vs_sensacion(df_prov, provincia, output_dir, archivo_prov, cache_local)
        grafico_temp(df_prov, provincia, output_dir, archivo_prov, cache_local)
        return provincia, "ok"
    except Exception as e:
        print(f"[ERROR-GRAFS] {provincia}: {e}")
        return provincia, "error"

def listar_provincias_desde_csvs(dir_prov=PROVINCIA_DIR):
    """
    Lista todas las provincias disponibles según los CSVs en un directorio.
    
    Parámetros:
        dir_prov (str): Directorio donde buscar CSVs.
    
    Retorna:
        list[str]: Lista de nombres de provincias.
    """
    files = [f for f in os.listdir(dir_prov) if f.startswith("clima_") and f.endswith(".csv")]
    provincias = [ f[len("clima_"):-len(".csv")] for f in files ]
    return provincias


def generar_todos_los_graficos(output_dir=OUTPUT_DIR_DEFAULT, max_workers=6):
    """
    Genera todos los gráficos para todas las provincias en paralelo.
    
    Parámetros:
        output_dir (str): Carpeta de salida de PNGs.
        max_workers (int): Número de hilos paralelos para procesamiento.
    
    Retorna:
        None. Imprime un resumen de estados por provincia.
    """
    provincias = listar_provincias_desde_csvs()
    status = {"ok": [], "no_file": [], "error": []}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = { executor.submit(generar_graficos_provincia_por_archivo, p, output_dir): p for p in provincias }
        for fut in as_completed(futures):
            prov = futures[fut]
            try:
                provincia, estado = fut.result()
                status.setdefault(estado, []).append(provincia)
            except Exception as e:
                status.setdefault("error", []).append(prov)
                print(f"[ERROR-FUTURE] {prov}: {e}")

    if status.get("ok"):
        print("Generados:", ", ".join(status["ok"]))
    if status.get("no_file"):
        print("Sin CSV:", ", ".join(status["no_file"]))
    if status.get("error"):
        print("Errores:", ", ".join(status["error"]))
        
# =============================================================
# MAIN
# =============================================================
if __name__ == "__main__":
    """
    Punto de entrada del script cuando se ejecuta directamente.
    - Asegura que la carpeta de salida de gráficos exista.
    - Llama a la función para generar todos los gráficos de todas las provincias en paralelo.
    """
    ensure_dir(OUTPUT_DIR_DEFAULT)
    generar_todos_los_graficos(output_dir=OUTPUT_DIR_DEFAULT, max_workers=6)
