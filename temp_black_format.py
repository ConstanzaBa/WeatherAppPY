"""
Módulo encargado de generar gráficos climáticos a partir del dataset
clima_argentina.csv. Incluye:

- Precipitación
- Velocidad del viento
- Dirección del viento (Rosa de los vientos)
- Dirección del viento lineal
- Gráficos web de temperatura con fondo transparente

Además, provee funciones auxiliares y un menú interactivo.

Este módulo está pensado tanto para visualización local como para
integración en sitios web (carpeta web/).
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime
import os
from matplotlib.colors import LinearSegmentedColormap

# ----------------------------------------
# CONFIGURACIÓN GLOBAL DE GRÁFICOS
# ----------------------------------------
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


# ========================================
#     FUNCIONES AUXILIARES 
# ========================================

def cargar_datos(archivo='dataset/clima_argentina.csv'):
    """
    Carga el dataset climático desde un archivo CSV.

    Parámetros:
        archivo (str): Ruta del archivo CSV a cargar.

    Retorna:
        pd.DataFrame: DataFrame con la columna fecha_hora convertida a datetime.
    """
    df = pd.read_csv(archivo)
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
    return df


def nueva_figura(figsize=(14, 6), titulo=None):
    """
    Crea una nueva figura estandarizada.

    Parámetros:
        figsize (tuple): Tamaño de figura.
        titulo (str): Título opcional del gráfico.
    """
    plt.figure(figsize=figsize)
    if titulo:
        plt.title(titulo, fontsize=14, fontweight='bold', pad=20)


def formatear_fechas(formato='%d/%m %H:%M', xlabel='Fecha y Hora'):
    """
    Aplica formato al eje X para mostrar fechas correctamente.

    Parámetros:
        formato (str): Formato de las fechas.
        xlabel (str): Etiqueta del eje X.
    """
    plt.gcf().autofmt_xdate()
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter(formato))
    ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')


def guardar_grafico(prefijo, provincia=None, output_dir='.'):
    """
    Guarda un gráfico con nombre estandarizado.

    Parámetros:
        prefijo (str): Prefijo del archivo (ej: 'grafico_precipitacion').
        provincia (str | None): Provincia opcional.
        output_dir (str): Carpeta de destino.
    """
    nombre = f"{prefijo}_{provincia if provincia else 'argentina'}.png"

    if output_dir:
        ensure_dir(output_dir)
        nombre = os.path.join(output_dir, nombre)

    plt.savefig(nombre, dpi=300, bbox_inches='tight')
    print(f'Gráfico guardado como: {nombre}')


def ensure_dir(path):
    """
    Crea la carpeta si no existe.

    Parámetros:
        path (str): Carpeta a crear.
    """
    if path:
        os.makedirs(path, exist_ok=True)


def normalize_filename(text):
    """
    Convierte un texto en un nombre de archivo válido.

    Parámetros:
        text (str): Texto original.

    Retorna:
        str: Texto normalizado (sin acentos y en minúsculas).
    """
    import unicodedata
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.replace(' ', '_').lower()


# ========================================
#     GRÁFICOS PRINCIPALES
# ========================================

def grafico_precipitacion(df, provincia=None, guardar=True, output_dir='.'):
    """
    Genera el gráfico de precipitación total por fecha/hora.

    Parámetros:
        df (pd.DataFrame): Dataset ya cargado.
        provincia (str | None): Provincia a filtrar.
        guardar (bool): Si True guarda el PNG.
        output_dir (str): Carpeta de salida.
    """
    if provincia:
        df_filtrado = df[df['province'] == provincia]
        titulo = f'Precipitación en {provincia}'
    else:
        df_filtrado = df
        titulo = 'Precipitación en Argentina'

    precip_total = df_filtrado.groupby('fecha_hora')['prcp'].sum()

    nueva_figura(figsize=(14, 6), titulo=titulo)
    plt.bar(precip_total.index, precip_total.values,
            color='#4ECDC4', alpha=0.8, width=0.03)

    plt.ylabel('Precipitación (mm)', fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3, axis='y')

    formatear_fechas()

    plt.tight_layout()
    if guardar:
        guardar_grafico('grafico_precipitacion', provincia, output_dir)
    plt.close()


def grafico_velocidad_viento(df, provincia=None, guardar=True, output_dir='.'):
    """
    Genera el gráfico de velocidad promedio y ráfagas de viento.

    Parámetros:
        df (pd.DataFrame)
        provincia (str | None)
        guardar (bool)
        output_dir (str)
    """
    if provincia:
        df_filtrado = df[df['province'] == provincia]
        titulo = f'Velocidad del Viento en {provincia}'
    else:
        df_filtrado = df
        titulo = 'Velocidad del Viento en Argentina'

    vel_prom = df_filtrado.groupby('fecha_hora')['wspd'].mean()
    vel_max = df_filtrado.groupby('fecha_hora')['wpgt'].mean()

    nueva_figura(figsize=(14, 6), titulo=titulo)

    plt.plot(vel_prom.index, vel_prom.values,
            color='#95E1D3', linewidth=2.5, label='Velocidad Promedio', marker='o', markersize=3)

    if not vel_max.empty and not vel_max.isna().all():
        plt.plot(vel_max.index, vel_max.values,
                color='#F38181', linewidth=2, linestyle='--',
                label='Ráfagas de Viento', alpha=0.7)

    plt.xlabel('Fecha y Hora', fontsize=12, fontweight='bold')
    plt.ylabel('Velocidad del Viento (km/h)', fontsize=12, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)

    formatear_fechas()

    plt.tight_layout()
    if guardar:
        guardar_grafico('grafico_velocidad_viento', provincia, output_dir)
    plt.close()


def grafico_direccion_viento(df, provincia=None, guardar=True, output_dir='.'):
    """
    Genera una rosa de los vientos usando dirección + velocidad.

    Parámetros:
        df (pd.DataFrame)
        provincia (str | None)
        guardar (bool)
        output_dir (str)
    """
    df_filtrado = df[df['province'] == provincia] if provincia else df
    titulo = f'Dirección del Viento en {provincia}' if provincia else 'Dirección del Viento en Argentina'

    df_viento = df_filtrado[['wdir', 'wspd']].dropna()
    if df_viento.empty:
        print("No hay datos de dirección del viento.")
        return

    direcciones_rad = np.deg2rad(df_viento['wdir'].values)
    velocidades = df_viento['wspd'].values

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='polar')

    num_bins = 16
    bins = np.linspace(0, 2 * np.pi, num_bins + 1)
    counts, _ = np.histogram(direcciones_rad, bins=bins, weights=velocidades)

    max_count = max(counts.max(), 1)
    colors = plt.cm.YlOrRd(counts / max_count)

    width = 2 * np.pi / num_bins
    theta = bins[:-1] + width / 2

    ax.bar(theta, counts, width=width,
        color=colors, alpha=0.8, edgecolor='white', linewidth=1.5)

    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_title(titulo, fontsize=14, fontweight='bold')

    cbar = plt.colorbar(
        plt.cm.ScalarMappable(cmap='YlOrRd',
                            norm=plt.Normalize(0, max_count)),
        ax=ax, pad=0.1, shrink=0.8
    )
    cbar.set_label('Velocidad acumulada (km/h)', fontsize=10)

    if guardar:
        guardar_grafico('grafico_direccion_viento', provincia, output_dir)
    plt.close()


def grafico_lineal_direccion_viento(df, provincia=None, guardar=True, output_dir='.'):
    """
    Genera un scatter lineal de la dirección del viento en grados.

    Parámetros:
        df (pd.DataFrame)
        provincia (str | None)
        guardar (bool)
        output_dir (str)
    """
    df_filtrado = df[df['province'] == provincia] if provincia else df
    titulo = f'Dirección del Viento en {provincia} (lineal)' if provincia else \
            'Dirección del Viento en Argentina (lineal)'

    dir_prom = df_filtrado.groupby('fecha_hora')['wdir'].mean()

    nueva_figura(figsize=(14, 6), titulo=titulo)

    sc = plt.scatter(dir_prom.index, dir_prom.values,
                    c=dir_prom.values, cmap='twilight', s=50, alpha=0.7)

    plt.xlabel('Fecha y Hora', fontsize=12)
    plt.ylabel('Dirección del Viento (°)', fontsize=12)
    plt.grid(True, alpha=0.3)

    formatear_fechas()

    plt.colorbar(sc, label='Dirección (°)')

    if guardar:
        guardar_grafico('grafico_direccion_viento_lineal', provincia, output_dir)
    plt.close()


# ========================================
#     GRAFICO TEMPERATURA 
# ========================================

def grafico_temperatura(provincia, df=None, output_dir='web/img/graphs'):
    """
    Genera un gráfico de temperatura

    Parámetros:
        provincia (str): Provincia a graficar.
        df (pd.DataFrame | None): DataFrame (si no se pasa se carga del CSV).
        output_dir (str): Carpeta donde guardar el PNG.

    Retorna:
        str | None: Ruta del archivo generado o None si no hay datos.
    """
    if df is None:
        df = cargar_datos()

    df_filtrado = df[df['province'] == provincia].sort_values('fecha_hora')
    if df_filtrado.empty:
        print(f"No hay datos para {provincia}")
        return None

    df_filtrado = df_filtrado.head(24)

    fig, ax = plt.subplots(figsize=(12, 4))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    primary_color = '#9381ff'
    secondary_color = "#4545dd"
    cmap = LinearSegmentedColormap.from_list('custom', [primary_color, secondary_color])

    n = len(df_filtrado)
    for i in range(n - 1):
        color = cmap(i / max(n - 1, 1))
        ax.plot(df_filtrado['fecha_hora'].iloc[i:i+2],
                df_filtrado['temp'].iloc[i:i+2],
                color=color, linewidth=3)

    ax.scatter(df_filtrado['fecha_hora'], df_filtrado['temp'],
            c=primary_color, s=40, zorder=5,
            edgecolors='white', linewidths=2)

    ax.fill_between(df_filtrado['fecha_hora'], df_filtrado['temp'],
                    alpha=0.3, color=primary_color)

    text_color = '#9381FF'  # color único para ambos temas

    ax.set_xlabel('Hora', color=text_color)
ax.set_ylabel('Temperatura (°C)', color=text_color)
ax.grid(True, alpha=0.2, color=text_color, linestyle='--')
ax.tick_params(colors=text_color)


    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))

    plt.tight_layout()

    ensure_dir(output_dir)
    out = os.path.join(output_dir, f'temp_chart_{normalize_filename(provincia)}.png')

    plt.savefig(out, dpi=150, transparent=True, bbox_inches='tight', facecolor='none')
    plt.close()

    print(f'Gráfico web guardado: {out}')
    return out


# ========================================
#     FLUJOS DE GENERACIÓN
# ========================================

def generar_todos_los_graficos(provincia=None, output_dir='.'):
    """
    Genera todos los gráficos.

    Parámetros:
        provincia (str | None): Provincia específica o None para todas.
        output_dir (str): Carpeta donde guardar.
    """
    df = cargar_datos()

    grafico_precipitacion(df, provincia, output_dir=output_dir)
    grafico_velocidad_viento(df, provincia, output_dir=output_dir)
    grafico_direccion_viento(df, provincia, output_dir=output_dir)
    grafico_lineal_direccion_viento(df, provincia, output_dir=output_dir)


def generar_graficos_todas_provincias_web(df=None, output_dir='web/img/graphs'):
    """
    Genera gráficos web de temperatura para todas las provincias.

    Parámetros:
        df (pd.DataFrame | None): DataFrame (None = se carga).
        output_dir (str): Carpeta de salida.
    """
    if df is None:
        df = cargar_datos()

    provincias = df['province'].unique()
    for p in provincias:
        grafico_temperatura(p, df=df, output_dir=output_dir)


# ========================================
#     MENU INTERACTIVO
# ========================================

def menu_interactivo():
    """
    Menú para seleccionar provincia y tipo de gráfico.
    """
    df = cargar_datos()

    provincias = sorted(df['province'].unique())

    print("=== Provincias ===")
    for i, p in enumerate(provincias, 1):
        print(f"{i}. {p}")
    print(f"{len(provincias)+1}. Todas")

    op = int(input("Seleccione: "))
    provincia = None if op == len(provincias) + 1 else provincias[op - 1]

    print("1. Precipitación\n2. Velocidad\n3. Dirección (Rosa)\n4. Dirección lineal\n5. Todos\n6. Web Temperatura")
    g = int(input("Elija gráfico: "))

    if g == 1: grafico_precipitacion(df, provincia)
    elif g == 2: grafico_velocidad_viento(df, provincia)
    elif g == 3: grafico_direccion_viento(df, provincia)
    elif g == 4: grafico_lineal_direccion_viento(df, provincia)
    elif g == 5: generar_todos_los_graficos(provincia)
    elif g == 6: grafico_temperatura(provincia, df=df)


# ========================================
#     MAIN
# ========================================

if __name__ == "__main__":
    generar_graficos_todas_provincias_web()
