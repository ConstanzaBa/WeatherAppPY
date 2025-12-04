"""
Módulo: parámetros meteorológicos derivados

Este archivo contiene funciones para calcular valores derivados a partir
de datos climáticos horarios:

- Sensación térmica (Wind Chill, Heat Index, Apparent Temperature)
- Código COCO (condiciones meteorológicas)
- Índice UV estimado
- Visibilidad atmosférica

Todas las funciones son robustas ante valores None o NaN.
"""

import math          # Funciones matemáticas y exponenciales
from datetime import datetime  # Manejo de fechas y horas


def asignar_estacion(mes):
    """
    Asigna la estación del año según el mes.
    
    Parámetros:
        mes (int): Número del mes (1-12)
        
    Retorna:
        str: "verano", "otoño", "invierno" o "primavera"
    """
    if mes in [12, 1, 2]:
        return "verano"
    elif mes in [3, 4, 5]:
        return "otoño"
    elif mes in [6, 7, 8]:
        return "invierno"
    else:
        return "primavera"

def _vapour_pressure_hpa(temp_c, rh_pct):
    """
    Calcula la presión de vapor en hPa.
    
    Parámetros:
        temp_c (float): Temperatura en °C
        rh_pct (float): Humedad relativa en %
        
    Retorna:
        float: Presión de vapor en hPa
    """
    try:
        if temp_c is None or rh_pct is None:
            return 0.0
        
        t = float(temp_c)
        rh = float(rh_pct)
        
        # Magnus-Tetens
        es = 6.112 * math.exp((17.62 * t) / (243.12 + t))  # hPa
        
        return (rh / 100.0) * es
    
    except Exception:
        return 0.0

def calcular_coco(temp, dwpt, rhum, pres, precip):
    """
    Calcula el código COCO según condiciones meteorológicas.
    
    Parámetros:
        temp (float): Temperatura (°C)
        dwpt (float): Punto de rocío (°C)
        rhum (float): Humedad relativa (%)
        pres (float): Presión atmosférica (hPa)
        precip (float): Precipitación estimada (mm)
        
    Retorna:
        int: Código COCO
    """
    try:
        temp = None if temp is None else float(temp)
        dwpt = None if dwpt is None else float(dwpt)
        rhum = None if rhum is None else float(rhum)
        pres = None if pres is None else float(pres)
        precip = None if precip is None else float(precip)
        snow = None if snow is None else float(snow)
    except Exception:
        return 2
    
    # Valores por defecto
    
    if rhum is None:
        rhum = 50.0
    if temp is None:
        temp = 15.0
    if dwpt is None:
        dwpt = temp - 2.0
    if pres is None:
        pres = 1013.0
    if precip is None:
        precip = 0.0
    if snow is None:
        snow = 0.0
        
    spread = abs(temp - dwpt)
    
    # -- Nieve
    if snow >= 5.0:
        return 23  # nieve fuerte
    if snow >= 2.0:
        return 22  # nieve moderada
    if snow > 0.0:
        return 21  # nieve ligera
    
    # -- Tormenta 
    if precip >= 50.0:
        return 27  # tormenta extrema
    if precip >= 20.0 and pres < 1005.0:
        return 27  # tormenta
    if precip >= 20.0:
        return 26  # lluvia muy intensa
    
    # -- Lluvia
    if precip >= 15.0:
        return 9   # lluvia intensa
    if precip >= 5.0:
        return 8   # lluvia moderada
    if precip >= 2.5:
        return 7   # lluvia ligera
    
    # -- Niebla
    if rhum >= 98 and spread <= 1.0:
        return 5   # niebla densa
    if rhum >= 95 and spread <= 2.0:
        return 4   # niebla
    
    # -- Nubosidad por humedad
    if rhum >= 85:
        return 3
    if rhum >= 70:
        return 2
    
    # -- Despejado 
    if rhum < 55 and spread > 6.0:
        return 1
    
    return 2

def calcular_wind_chill(temp_c, wspd_kmh):
    """
    Wind Chill (sensación térmica por frío y viento).
    
    Parámetros:
        temp_c (float): Temperatura (°C)
        wspd_kmh (float): Velocidad del viento (km/h)
        
    Retorna:
        float | None: Sensación térmica o None si no aplica
    """
    if temp_c is None or wspd_kmh is None:
        return None
    t, w = float(temp_c), float(wspd_kmh)
    if t > 10 or w < 4.8:
        return None
    return round(13.12 + 0.6215*t - 11.37*math.pow(w, 0.16) + 0.3965*t*math.pow(w, 0.16), 1)

def calcular_heat_index(temp_c, rh_pct):
    """
    Heat Index (sensación térmica por calor + humedad).
    
    Parámetros:
        temp_c (float): Temperatura (°C)
        rh_pct (float): Humedad relativa (%)
        
    Retorna:
        float | None: Índice de calor o None si no aplica
    """
    try:
        if temp_c is None or rh_pct is None:
            return None
        t = float(temp_c)
        rh = float(rh_pct)
    except Exception:
        return None
    
    if t < 27.0 or rh < 40.0:
        return None
    
    # Convertir a Fahrenheit
    t_f = t * 9.0/5.0 + 32.0
    
    # Rothfusz regression (NOAA)
    hi_f = (-42.379 + 2.04901523 * t_f + 10.14333127 * rh
            - 0.22475541 * t_f * rh - 0.00683783 * t_f**2
            - 0.05481717 * rh**2 + 0.00122874 * t_f**2 * rh
            + 0.00085282 * t_f * rh**2 - 0.00000199 * t_f**2 * rh**2)
    
    # Humedad baja / alta (según NOAA)
    if rh < 13 and 80.0 <= t_f <= 112.0:
        adj = ((13.0 - rh) / 4.0) * math.sqrt((17.0 - abs(t_f - 95.0)) / 17.0)
        hi_f -= adj
    elif rh > 85 and 80.0 <= t_f <= 87.0:
        adj = ((rh - 85.0) / 10.0) * ((87.0 - t_f) / 5.0)
        hi_f += adj
        
    # Convertir de vuelta a °C
    hi_c = (hi_f - 32.0) * 5.0/9.0
    return round(hi_c, 1)

def calcular_apparent_temperature(temp_c, rh_pct, wspd_kmh):
    """
    Apparent Temperature (Australian-style): AT = T + 0.33*e - 0.70*v - 4.0
    - e = vapour pressure en hPa (usamos _vapour_pressure_hpa)
    - v = wind speed en m/s (convertir de km/h)
    
    Parámetros:
        temp_c (float): Temperatura (°C)
        rh_pct (float): Humedad relativa (%)
        wspd_kmh (float): Velocidad del viento (km/h)
        
    Retorna:
        float (°C) | None
    """
    try:
        if temp_c is None or rh_pct is None or wspd_kmh is None:
            return None
        t = float(temp_c)
        rh = float(rh_pct)
        w_kmh = float(wspd_kmh)
    except Exception:
        return None
    
    # convertir
    v = w_kmh / 3.6  # m/s
    e = _vapour_pressure_hpa(t, rh)  # hPa
    
    at = t + 0.33 * e - 0.70 * v - 4.0
    return round(at, 1)

def calcular_sensacion_termica(temp, rhum, wspd):
    """
    Calcula la sensación térmica combinando:
        - Wind Chill
        - Heat Index
        - Apparent Temperature (fallback)
        
    Parámetros:
        temp (float): Temperatura (°C)
        rhum (float): Humedad relativa (%)
        wspd (float): Velocidad del viento (km/h)
        
    Retorna:
        float: Sensación térmica aproximada
    """
    try:
        # primeros intentos
        wc = calcular_wind_chill(temp, wspd)
        hi = calcular_heat_index(temp, rhum)
        at = calcular_apparent_temperature(temp, rhum, wspd)
        
        # priorizar: WC > HI > AT
        if wc is not None:
            return round(wc, 1)
        if hi is not None:
            return round(hi, 1)
        if at is not None:
            return round(at, 1)
        
        # fallback: si temp disponible, devolver temp redondeada
        if temp is not None:
            return round(float(temp), 1)
        
    except Exception:
        pass
    
    return None

def calcular_radiacion_uv(temp, coco, fecha_hora):
    """
    Estima el índice UV según temperatura, COCO y hora.

    Parámetros:
        temp (float): Temperatura (°C)
        coco (int): Código COCO
        fecha_hora (str): Fecha ISO "YYYY-MM-DDTHH:MM:SSZ"
        
    Retorna:
        float | None: Índice UV estimado
    """
    if fecha_hora is None:
        return 0.0
    
    try:
        dt = datetime.fromisoformat(fecha_hora.replace("Z", "+00:00"))
    except:
        return 0.0
    
    # Hora solar aproximada
    hora_local = dt.hour + dt.minute/60.0    
    mes = dt.month
    
    if mes in [12, 1, 2]:       # Verano
        amanecer = 5.45
        atardecer = 20.30
    elif mes in [3, 4, 5]:     # Otoño
        amanecer = 6.50
        atardecer = 19.10
    elif mes in [6, 7, 8]:     # Invierno
        amanecer = 7.40
        atardecer = 18.25
    else:                      # Primavera
        amanecer = 6.20
        atardecer = 19.45
    
    # Si está de noche: UV = 0
    if hora_local < amanecer or hora_local > atardecer:
        return 0.0
    
    # Conversion a hora solar
    eq_time = -7.65 * math.sin(math.radians((360/365)*(dt.timetuple().tm_yday + 10)))
    long_corr = -4.0  # aprox GMT-3
    hora_solar = hora_local + (eq_time/60.0) + (long_corr/60.0)
    
    # Curva solar tipo campana
    peak = 12.88
    sigma = 2.4
    base_uv = 12.5 * math.exp(-0.5 * ((hora_solar - peak) / sigma) ** 2)
    
    # Factor estacional
    
    if mes in [12, 1, 2]:
        base_uv *= 1.15   # verano
    elif mes in [3, 4, 5]:
        base_uv *= 0.85   # otoño
    elif mes in [6, 7, 8]:
        base_uv *= 0.55   # invierno
    else:
        base_uv *= 1.00   # primavera
        
    # Factor coco
    coco_factor = {
        1: 1.00,  # despejado 
        2: 0.90,
        3: 0.70,  # parcialmente nublado
        4: 0.40,  # niebla ligera
        5: 0.25,  # niebla densa
        7: 0.65,  # llovizna
        8: 0.55,
        9: 0.50,
        21: 0.50, # nieve ligera
        22: 0.40,
        23: 0.30,
        26: 0.25,
        27: 0.10  # tormenta
    }
    
    attenuation = coco_factor.get(coco, 0.60)
    uv = base_uv * attenuation
    
    uv = max(0.0, min(uv, 13.0))
    return round(uv, 1)

def calcular_visibilidad(temp, rhum, dwpt, prcp, snow, wspd, coco):
    """
    Estima la visibilidad atmosférica (km) según condiciones.
    
    Parámetros:
        temp (float) : Temperatura (°C)
        rhum (float) : Humedad relativa (%)
        dwpt (float) : Punto de rocío (°C)
        prcp (float) : Precipitación (mm/h)
        snow (float) : Nieve (mm/h)
        wspd (float) : Viento (km/h)
        coco (int)   : Código COCO
        
    Retorna:
        float | None: Visibilidad estimada en km
    """
    
    try:
        t = float(temp)
        d = float(dwpt)
        rh = float(rhum)
        v = float(wspd)
        r = float(prcp)
        s = float(snow)
        cc = int(coco) if coco is not None else 2
    except:
        return 20.0
    
    if s > 0:
        vis_m = max(100, 1500 - s * 80) 
        return round(vis_m / 1000, 1)
    
    if r > 0:
        vis_m = max(300, 6000 - r * 1000)
        return round(vis_m / 1000, 1)
    
    delta = t - d
    if delta < 0.5:
        return 0.2 
    if delta < 1.0:
        return 0.4
    if delta < 2.0:
        return 0.8
    if delta < 3.0:
        return 2.0
    
    vis = 22.0
    
    # Humedad alta reduce visibilidad
    if rh > 95:
        vis -= 15
    elif rh > 85:
        vis -= 10
    elif rh > 75:
        vis -= 5
    elif rh > 65:
        vis -= 3
        
    # Niebla 
    if cc in [4, 5]:
        vis = 0.5
        
    # Viento levanta polvo en zonas secas
    if v > 35:
        vis -= 5
        
    # Colapsar a rango válido
    vis = max(0.2, min(vis, 22.0))

    return round(vis, 1)