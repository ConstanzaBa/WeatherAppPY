import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime
import os

# Configuración general de matplotlib
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

def cargar_datos(archivo='dataset/clima_argentina.csv'):
    """Carga los datos del archivo CSV"""
    df = pd.read_csv(archivo)
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
    return df

def grafico_temperatura(df, provincia=None, guardar=True):
    """
    Crea un gráfico de temperatura a lo largo del tiempo
    
    Args:
        df: DataFrame con los datos
        provincia: Nombre de la provincia a filtrar (None para todas)
        guardar: Si True, guarda el gráfico como imagen
    """
    plt.figure(figsize=(14, 6))
    
    if provincia:
        df_filtrado = df[df['province'] == provincia]
        titulo = f'Temperatura en {provincia}'
    else:
        df_filtrado = df
        titulo = 'Temperatura en Argentina'
    
    # Agrupamos por fecha_hora y calculamos temperatura promedio
    temp_promedio = df_filtrado.groupby('fecha_hora')['temp'].mean()
    temp_max = df_filtrado.groupby('fecha_hora')['temp'].max()
    temp_min = df_filtrado.groupby('fecha_hora')['temp'].min()
    
    # Graficamos
    plt.plot(temp_promedio.index, temp_promedio.values, 
             color='#FF6B35', linewidth=2.5, label='Temperatura Promedio')
    plt.fill_between(temp_max.index, temp_min.values, temp_max.values, 
                      alpha=0.2, color='#FF6B35', label='Rango Min-Max')
    
    plt.xlabel('Fecha y Hora', fontsize=12, fontweight='bold')
    plt.ylabel('Temperatura (°C)', fontsize=12, fontweight='bold')
    plt.title(titulo, fontsize=14, fontweight='bold', pad=20)
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # Formato de fecha en el eje X
    plt.gcf().autofmt_xdate()
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
    
    plt.tight_layout()
    
    if guardar:
        nombre_archivo = f'grafico_temperatura_{provincia if provincia else "argentina"}.png'
        plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
        print(f'Gráfico guardado como: {nombre_archivo}')
    
    plt.show()

def grafico_precipitacion(df, provincia=None, guardar=True):
    """
    Crea un gráfico de barras de precipitación a lo largo del tiempo
    
    Args:
        df: DataFrame con los datos
        provincia: Nombre de la provincia a filtrar (None para todas)
        guardar: Si True, guarda el gráfico como imagen
    """
    plt.figure(figsize=(14, 6))
    
    if provincia:
        df_filtrado = df[df['province'] == provincia]
        titulo = f'Precipitación en {provincia}'
    else:
        df_filtrado = df
        titulo = 'Precipitación en Argentina'
    
    # Agrupamos por fecha_hora y sumamos precipitaciones
    precip_total = df_filtrado.groupby('fecha_hora')['prcp'].sum()
    
    # Graficamos barras
    plt.bar(precip_total.index, precip_total.values, 
            color='#4ECDC4', alpha=0.8, width=0.03)
    
    plt.xlabel('Fecha y Hora', fontsize=12, fontweight='bold')
    plt.ylabel('Precipitación (mm)', fontsize=12, fontweight='bold')
    plt.title(titulo, fontsize=14, fontweight='bold', pad=20)
    plt.grid(True, alpha=0.3, axis='y')
    
    # Formato de fecha en el eje X
    plt.gcf().autofmt_xdate()
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
    
    plt.tight_layout()
    
    if guardar:
        nombre_archivo = f'grafico_precipitacion_{provincia if provincia else "argentina"}.png'
        plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
        print(f'Gráfico guardado como: {nombre_archivo}')
    
    plt.show()

def grafico_velocidad_viento(df, provincia=None, guardar=True):
    """
    Crea un gráfico de velocidad del viento a lo largo del tiempo
    
    Args:
        df: DataFrame con los datos
        provincia: Nombre de la provincia a filtrar (None para todas)
        guardar: Si True, guarda el gráfico como imagen
    """
    plt.figure(figsize=(14, 6))
    
    if provincia:
        df_filtrado = df[df['province'] == provincia]
        titulo = f'Velocidad del Viento en {provincia}'
    else:
        df_filtrado = df
        titulo = 'Velocidad del Viento en Argentina'
    
    # Agrupamos por fecha_hora y calculamos velocidad promedio
    vel_promedio = df_filtrado.groupby('fecha_hora')['wspd'].mean()
    vel_max = df_filtrado.groupby('fecha_hora')['wpgt'].mean()  # ráfagas de viento
    
    # Graficamos
    plt.plot(vel_promedio.index, vel_promedio.values, 
             color='#95E1D3', linewidth=2.5, label='Velocidad Promedio', marker='o', markersize=3)
    
    if not vel_max.empty and not vel_max.isna().all():
        plt.plot(vel_max.index, vel_max.values, 
                 color='#F38181', linewidth=2, linestyle='--', 
                 label='Ráfagas de Viento', alpha=0.7)
    
    plt.xlabel('Fecha y Hora', fontsize=12, fontweight='bold')
    plt.ylabel('Velocidad del Viento (km/h)', fontsize=12, fontweight='bold')
    plt.title(titulo, fontsize=14, fontweight='bold', pad=20)
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # Formato de fecha en el eje X
    plt.gcf().autofmt_xdate()
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
    
    plt.tight_layout()
    
    if guardar:
        nombre_archivo = f'grafico_velocidad_viento_{provincia if provincia else "argentina"}.png'
        plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
        print(f'Gráfico guardado como: {nombre_archivo}')
    
    plt.show()

def grafico_direccion_viento(df, provincia=None, guardar=True):
    """
    Crea un gráfico polar (rosa de los vientos) de la dirección del viento
    
    Args:
        df: DataFrame con los datos
        provincia: Nombre de la provincia a filtrar (None para todas)
        guardar: Si True, guarda el gráfico como imagen
    """
    if provincia:
        df_filtrado = df[df['province'] == provincia]
        titulo = f'Dirección del Viento en {provincia}'
    else:
        df_filtrado = df
        titulo = 'Dirección del Viento en Argentina'
    
    # Filtramos valores nulos
    df_viento = df_filtrado[['wdir', 'wspd']].dropna()
    
    if df_viento.empty:
        print("No hay datos de dirección del viento disponibles")
        return
    
    # Convertimos grados a radianes
    direcciones_rad = np.deg2rad(df_viento['wdir'].values)
    velocidades = df_viento['wspd'].values
    
    # Creamos histograma polar (rosa de los vientos)
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='polar')
    
    # Definimos los bins (16 direcciones = 22.5 grados cada una)
    num_bins = 16
    bins = np.linspace(0, 2 * np.pi, num_bins + 1)
    
    # Histograma de frecuencias ponderado por velocidad
    counts, _ = np.histogram(direcciones_rad, bins=bins, weights=velocidades)
    
    # Calculamos el ancho de cada barra
    width = 2 * np.pi / num_bins
    
    # Centramos las barras
    theta = bins[:-1] + width / 2
    
    # Colores según intensidad
    colors = plt.cm.YlOrRd(counts / counts.max())
    
    # Graficamos barras
    bars = ax.bar(theta, counts, width=width, bottom=0.0, 
                   color=colors, alpha=0.8, edgecolor='white', linewidth=1.5)
    
    # Configuramos el gráfico
    ax.set_theta_zero_location('N')  # Norte arriba
    ax.set_theta_direction(-1)  # Sentido horario
    ax.set_title(titulo, fontsize=14, fontweight='bold', pad=20)
    
    # Etiquetas de direcciones cardinales
    direcciones = ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO']
    angulos = [0, 45, 90, 135, 180, 225, 270, 315]
    ax.set_xticks(np.deg2rad(angulos))
    ax.set_xticklabels(direcciones, fontsize=11, fontweight='bold')
    
    # Leyenda de colores
    sm = plt.cm.ScalarMappable(cmap=plt.cm.YlOrRd, 
                                norm=plt.Normalize(vmin=0, vmax=counts.max()))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, pad=0.1, shrink=0.8)
    cbar.set_label('Velocidad acumulada (km/h)', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    
    if guardar:
        nombre_archivo = f'grafico_direccion_viento_{provincia if provincia else "argentina"}.png'
        plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
        print(f'Gráfico guardado como: {nombre_archivo}')
    
    plt.show()

def grafico_lineal_direccion_viento(df, provincia=None, guardar=True):
    """
    Crea un gráfico lineal de la dirección del viento a lo largo del tiempo
    
    Args:
        df: DataFrame con los datos
        provincia: Nombre de la provincia a filtrar (None para todas)
        guardar: Si True, guarda el gráfico como imagen
    """
    plt.figure(figsize=(14, 6))
    
    if provincia:
        df_filtrado = df[df['province'] == provincia]
        titulo = f'Dirección del Viento en {provincia} (a lo largo del tiempo)'
    else:
        df_filtrado = df
        titulo = 'Dirección del Viento en Argentina (a lo largo del tiempo)'
    
    # Agrupamos por fecha_hora y calculamos dirección promedio
    dir_promedio = df_filtrado.groupby('fecha_hora')['wdir'].mean()
    
    # Graficamos
    plt.scatter(dir_promedio.index, dir_promedio.values, 
               c=dir_promedio.values, cmap='twilight', s=50, alpha=0.7)
    
    plt.xlabel('Fecha y Hora', fontsize=12, fontweight='bold')
    plt.ylabel('Dirección del Viento (grados)', fontsize=12, fontweight='bold')
    plt.title(titulo, fontsize=14, fontweight='bold', pad=20)
    plt.grid(True, alpha=0.3)
    
    # Líneas de referencia para direcciones cardinales
    plt.axhline(y=0, color='gray', linestyle='--', alpha=0.3, label='N')
    plt.axhline(y=90, color='gray', linestyle='--', alpha=0.3, label='E')
    plt.axhline(y=180, color='gray', linestyle='--', alpha=0.3, label='S')
    plt.axhline(y=270, color='gray', linestyle='--', alpha=0.3, label='O')
    plt.axhline(y=360, color='gray', linestyle='--', alpha=0.3)
    
    plt.ylim(0, 360)
    plt.yticks([0, 45, 90, 135, 180, 225, 270, 315, 360],
               ['N/360°', 'NE/45°', 'E/90°', 'SE/135°', 'S/180°', 'SO/225°', 'O/270°', 'NO/315°', 'N/0°'])
    
    # Formato de fecha en el eje X
    plt.gcf().autofmt_xdate()
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
    
    # Barra de colores
    cbar = plt.colorbar(plt.cm.ScalarMappable(cmap='twilight', 
                        norm=plt.Normalize(vmin=0, vmax=360)), ax=ax)
    cbar.set_label('Dirección (grados)', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    
    if guardar:
        nombre_archivo = f'grafico_direccion_viento_lineal_{provincia if provincia else "argentina"}.png'
        plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
        print(f'Gráfico guardado como: {nombre_archivo}')
    
    plt.show()

def generar_todos_los_graficos(provincia=None):
    """
    Genera todos los gráficos disponibles
    
    Args:
        provincia: Nombre de la provincia a filtrar (None para todas)
    """
    print("Cargando datos...")
    df = cargar_datos()
    
    print("\n=== Generando gráficos ===\n")
    
    print("1. Gráfico de Temperatura")
    grafico_temperatura(df, provincia)
    
    print("\n2. Gráfico de Precipitación")
    grafico_precipitacion(df, provincia)
    
    print("\n3. Gráfico de Velocidad del Viento")
    grafico_velocidad_viento(df, provincia)
    
    print("\n4. Gráfico de Dirección del Viento (Rosa de los Vientos)")
    grafico_direccion_viento(df, provincia)
    
    print("\n5. Gráfico de Dirección del Viento (Lineal)")
    grafico_lineal_direccion_viento(df, provincia)
    
    print("\n¡Todos los gráficos generados exitosamente!")

def generar_grafico_web_temperatura(provincia, output_dir='web/img/graphs'):
    """
    Genera un gráfico de temperatura optimizado para la web
    
    Args:
        provincia: Nombre de la provincia
        output_dir: Directorio donde guardar el gráfico
    """
    df = cargar_datos()
    df_filtrado = df[df['province'] == provincia].copy()
    
    if df_filtrado.empty:
        print(f"No hay datos disponibles para {provincia}")
        return None
    
    # Ordenar por fecha_hora y tomar solo las próximas 24 horas
    df_filtrado = df_filtrado.sort_values('fecha_hora').head(24)
    
    # Crear figura con fondo transparente
    fig, ax = plt.subplots(figsize=(12, 4))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    
    # Colores del CSS: --primary-color y --secondary-color
    primary_color = '#9381ff'    # --primary-color
    secondary_color = '#b8b8ff'  # --secondary-color
    
    # Crear gradiente para la línea
    from matplotlib.colors import LinearSegmentedColormap
    n_points = len(df_filtrado)
    colors_gradient = [primary_color, secondary_color]
    cmap = LinearSegmentedColormap.from_list('custom', colors_gradient)
    
    # Graficar temperatura con gradiente
    for i in range(len(df_filtrado) - 1):
        color_idx = i / max(n_points - 1, 1)
        segment_color = cmap(color_idx)
        ax.plot(df_filtrado['fecha_hora'].iloc[i:i+2], 
                df_filtrado['temp'].iloc[i:i+2], 
                color=segment_color, linewidth=3)
    
    # Agregar marcadores
    ax.scatter(df_filtrado['fecha_hora'], df_filtrado['temp'], 
               c=primary_color, s=40, zorder=5, 
               edgecolors='white', linewidths=2)
    
    # Rellenar área bajo la curva con gradiente
    ax.fill_between(df_filtrado['fecha_hora'], df_filtrado['temp'], 
                     alpha=0.3, color=primary_color)
    
    # Estilo
    ax.set_xlabel('Hora', fontsize=11, fontweight='bold', color='white')
    ax.set_ylabel('Temperatura (°C)', fontsize=11, fontweight='bold', color='white')
    ax.grid(True, alpha=0.2, color='white', linestyle='--')
    ax.tick_params(colors='white', labelsize=9)
    
    # Formato de hora en el eje X
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Añadir valores de temperatura en cada punto
    for i, row in df_filtrado.iterrows():
        if df_filtrado.index.get_loc(i) % 3 == 0:  # Mostrar cada 3 puntos
            ax.annotate(f"{row['temp']:.1f}°", 
                       xy=(row['fecha_hora'], row['temp']),
                       xytext=(0, 8), textcoords='offset points',
                       ha='center', fontsize=8, color='white',
                       fontweight='bold')
    
    # Ajustar márgenes
    plt.tight_layout()
    
    # Guardar con fondo transparente
    output_path = os.path.join(output_dir, f'temp_chart_{normalize_filename(provincia)}.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                transparent=True, facecolor='none')
    plt.close()
    
    print(f'Gráfico web guardado en: {output_path}')
    return output_path

def normalize_filename(text):
    """Normaliza el nombre de archivo removiendo acentos y espacios"""
    import unicodedata
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.replace(' ', '_').lower()
    return text

def generar_graficos_todas_provincias_web():
    """Genera gráficos de temperatura para todas las provincias para la web"""
    df = cargar_datos()
    provincias = df['province'].unique()
    
    print("\nGenerando gráficos web para todas las provincias...")
    for provincia in provincias:
        print(f"  → {provincia}")
        generar_grafico_web_temperatura(provincia)
    print("\n✓ Todos los gráficos web generados exitosamente!")

def menu_interactivo():
    """Menu interactivo para seleccionar qué gráficos generar"""
    df = cargar_datos()
    
    print("\n" + "="*50)
    print("  GENERADOR DE GRÁFICOS CLIMÁTICOS - ARGENTINA")
    print("="*50)
    
    # Mostrar provincias disponibles
    provincias = sorted(df['province'].unique())
    print("\nProvincias disponibles:")
    for i, prov in enumerate(provincias, 1):
        print(f"  {i}. {prov}")
    print(f"  {len(provincias) + 1}. Todas las provincias")
    
    # Seleccionar provincia
    while True:
        try:
            opcion = int(input(f"\nSeleccione una provincia (1-{len(provincias) + 1}): "))
            if 1 <= opcion <= len(provincias) + 1:
                provincia = None if opcion == len(provincias) + 1 else provincias[opcion - 1]
                break
            else:
                print("Opción no válida. Intente de nuevo.")
        except ValueError:
            print("Por favor ingrese un número válido.")
    
    # Seleccionar tipo de gráfico
    print("\n" + "-"*50)
    print("Tipos de gráficos disponibles:")
    print("  1. Temperatura")
    print("  2. Precipitación")
    print("  3. Velocidad del Viento")
    print("  4. Dirección del Viento (Rosa de los Vientos)")
    print("  5. Dirección del Viento (Lineal)")
    print("  6. Todos los gráficos")
    print("  7. Gráfico Web (para integrar en info.html)")
    
    while True:
        try:
            opcion_grafico = int(input("\nSeleccione el tipo de gráfico (1-7): "))
            if 1 <= opcion_grafico <= 7:
                break
            else:
                print("Opción no válida. Intente de nuevo.")
        except ValueError:
            print("Por favor ingrese un número válido.")
    
    # Generar el gráfico seleccionado
    print("\n" + "="*50)
    print("Generando gráfico(s)...")
    print("="*50 + "\n")
    
    if opcion_grafico == 1:
        grafico_temperatura(df, provincia)
    elif opcion_grafico == 2:
        grafico_precipitacion(df, provincia)
    elif opcion_grafico == 3:
        grafico_velocidad_viento(df, provincia)
    elif opcion_grafico == 4:
        grafico_direccion_viento(df, provincia)
    elif opcion_grafico == 5:
        grafico_lineal_direccion_viento(df, provincia)
    elif opcion_grafico == 6:
        generar_todos_los_graficos(provincia)
    elif opcion_grafico == 7:
        if provincia:
            generar_grafico_web_temperatura(provincia)
        else:
            generar_graficos_todas_provincias_web()

if __name__ == "__main__":
    # Descomentar la opción que prefieras:
    
    # Opción 1: Menu interactivo
    # menu_interactivo()
    
    # Opción 2: Generar todos los gráficos para todas las provincias
    # generar_todos_los_graficos()
    
    # Opción 3: Generar todos los gráficos para una provincia específica
    # generar_todos_los_graficos(provincia="Buenos Aires")
    
    # Opción 4: Generar gráficos individuales
    # df = cargar_datos()
    # grafico_temperatura(df, provincia="Córdoba")
    # grafico_precipitacion(df)
    # grafico_velocidad_viento(df, provincia="Santa Fe")
    # grafico_direccion_viento(df, provincia="Buenos Aires")
    
    # Opción 5: Generar gráficos web para todas las provincias
    generar_graficos_todas_provincias_web()
