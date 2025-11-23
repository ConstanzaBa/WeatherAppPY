import matplotlib
matplotlib.use('Agg')

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.collections import LineCollection
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

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

WEEKDAY_SHORT_ES = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

PROVINCIA_DIR = os.path.join("dataset", "provincia")
OUTPUT_DIR_DEFAULT = 'web/img/graphs'

# ------------------------------------------------------------
# FUNCIONES AUXILIARES
# ------------------------------------------------------------
def ensure_dir(path):
    if path:
        os.makedirs(path, exist_ok=True)

def normalize_filename(text):
    if text is None:
        return "argentina"
    import unicodedata
    text = unicodedata.normalize('NFD', str(text))
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.replace(' ', '_').lower()

def esta_actualizado(archivo_csv, archivo_png):
    if not os.path.exists(archivo_png):
        return False
    fecha_csv = os.path.getmtime(archivo_csv)
    fecha_png = os.path.getmtime(archivo_png)
    return fecha_png > fecha_csv

def guardar_fig(fig, nombre_png):
    plt.tight_layout()
    fig.savefig(nombre_png, dpi=DEFAULT_DPI, bbox_inches='tight', transparent=True)
    plt.close(fig)

def fechas_ultimos_7_dias():
    hoy = pd.Timestamp.now().normalize()
    fecha_inicio = hoy - pd.Timedelta(days=6)  # incluye hoy => 7 días
    fechas = [ (fecha_inicio + pd.Timedelta(days=i)).date() for i in range(7) ]
    return fechas  # lista de date()

def labels_from_dates(dates):
    return [WEEKDAY_SHORT_ES[pd.to_datetime(d).weekday()] for d in dates]

# ------------------------------------------------------------
# CARGA POR PROVINCIA
# ------------------------------------------------------------
def cargar_datos_provincia(provincia):
    """
    Lee dataset/provincia/clima_<provincia>.csv y prepara df (últimos 7 días + hoy).
    Devuelve (df_prov, archivo_prov) o (None, archivo_prov) si no existe.
    """
    archivo_prov = os.path.join(PROVINCIA_DIR, f"clima_{provincia}.csv")
    if not os.path.exists(archivo_prov):
        return None, archivo_prov

    df = pd.read_csv(archivo_prov)
    if 'fecha_hora' not in df.columns:
        return None, archivo_prov

    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
    # filtro para últimos 7 días incluyendo hoy (7 días: hoy y 6 anteriores)
    hoy = pd.Timestamp.now().normalize()
    inicio = hoy - pd.Timedelta(days=6)
    mañana = hoy + pd.Timedelta(days=1)
    df = df[(df['fecha_hora'] >= inicio) & (df['fecha_hora'] < mañana)].sort_values('fecha_hora')
    return df, archivo_prov

# ------------------------------------------------------------
# CACHE LOCAL
# ------------------------------------------------------------
def construir_cache_local(df_prov):
    """
    Construye la cache para UNA provincia: contenidos diarios + temp_web + histograma viento.
    """
    cache = {}
    if df_prov is None or df_prov.empty:
        return cache

    df_copy = df_prov.copy()
    df_copy['dia'] = df_copy['fecha_hora'].dt.date

    # Datos diarios agregados (por día)
    daily = df_copy.groupby('dia').agg({
        'prcp': 'sum',
        'wspd': 'mean',
        'wpgt': 'mean',
        'wdir': 'mean',
        'rhum': 'mean',
        'temp': 'mean',
        'sensacionTermica': 'mean'
    }).reset_index()

    # temp_web = hoy (horario)
    hoy = pd.Timestamp.now().normalize()
    manana = hoy + pd.Timedelta(days=1)
    df_hoy = df_copy[(df_copy['fecha_hora'] >= hoy) & (df_copy['fecha_hora'] < manana)].sort_values('fecha_hora')

    # histograma de viento 
    v_raw = df_copy[['wdir','wspd']].dropna()
    if not v_raw.empty:
        direcciones = np.deg2rad(v_raw['wdir'].values)
        velocidades = v_raw['wspd'].values
        bins = np.linspace(0, 2*np.pi, 17)
        counts, _ = np.histogram(direcciones, bins=bins, weights=velocidades)
    else:
        bins = np.linspace(0, 2*np.pi, 17)
        counts = np.zeros(len(bins)-1)

    cache['daily'] = daily
    cache['temp_web'] = df_hoy.reset_index(drop=True)
    cache['viento_hist'] = {'bins': bins, 'counts': counts}
    return cache


# ------------------------------------------------------------
# GRAFICOS 
# ------------------------------------------------------------
def grafico_temp(df_prov, provincia, output_dir=OUTPUT_DIR_DEFAULT, archivo_csv=None, cache_local=None):
    """
    Gráfico estilizado para temperatura en la web (solo hoy).
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
    Precipitación diaria acumulada (7 días) — siempre 7 barras (rellena faltantes).
    """
    fechas_7 = fechas_ultimos_7_dias()  # lista de date()
    if cache_local is not None and 'daily' in cache_local:
        d = cache_local['daily']
        # mapear a diccionario {date: value}
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
    Viento promedio y ráfagas promedio por día (7 días).
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
    Gráfico polar de dirección de viento usando histograma cacheado.
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
    Humedad relativa promedio diaria (7 días).
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
    Compara temperatura y sensación térmica promedio diaria (7 días).
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

# ------------------------------------------------------------
# GENERACIÓN POR PROVINCIA
# ------------------------------------------------------------
def generar_graficos_provincia_por_archivo(provincia, output_dir=OUTPUT_DIR_DEFAULT, max_workers_local=1):
    df_prov, archivo_prov = cargar_datos_provincia(provincia)
    if df_prov is None:
        return provincia, "no_file"

    cache_local = construir_cache_local(df_prov)

    # Llamar a cada gráfico pasando df_prov y cache_local
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
    files = [f for f in os.listdir(dir_prov) if f.startswith("clima_") and f.endswith(".csv")]
    provincias = [ f[len("clima_"):-len(".csv")] for f in files ]
    return provincias

def generar_todos_los_graficos(output_dir=OUTPUT_DIR_DEFAULT, max_workers=6):
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

    # resumen
    if status.get("ok"):
        print("Generados:", ", ".join(status["ok"]))
    if status.get("no_file"):
        print("Sin CSV:", ", ".join(status["no_file"]))
    if status.get("error"):
        print("Errores:", ", ".join(status["error"]))

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    ensure_dir(OUTPUT_DIR_DEFAULT)
    generar_todos_los_graficos(output_dir=OUTPUT_DIR_DEFAULT, max_workers=6)
