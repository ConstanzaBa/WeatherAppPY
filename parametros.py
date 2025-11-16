"""
Módulo: parámetros meteorológicos derivados

Este archivo contiene funciones para calcular valores derivados a partir
de datos climáticos horarios:

- Sensación térmica (frío, calor o templado)
- Índice UV estimado
- Visibilidad estimada

Todas las funciones están preparadas para recibir valores None o NaN
y responder de manera robusta.
"""

import math
from datetime import datetime

# ============================================================
#   Funciones auxiliares
# ============================================================

def _vapour_pressure_hpa(temp_c, rh_pct):
    """
    Calcula la presión de vapor (hPa).

    Parámetros:
        temp_c (float): Temperatura (°C)
        rh_pct (float): Humedad relativa (%)

    Retorna:
        float: presión de vapor en hPa
    """
    return (rh_pct / 100.0) * 6.105 * math.exp((17.27 * temp_c) / (237.7 + temp_c))


# ============================================================
#   Cálculo de sensación térmica
# ============================================================

def calcular_wind_chill(temp_c, wspd_kmh):
    """
    Calcula Wind Chill (sensación térmica por viento).

    Parámetros:
        temp_c (float): Temperatura (°C)
        wspd_kmh (float): Velocidad del viento (km/h)

    Retorna:
        float | None: Sensación térmica o None si no aplica.
    """
    if temp_c is None or wspd_kmh is None:
        return None
    try:
        t = float(temp_c)
        w = float(wspd_kmh)
    except:
        return None

    if t > 10 or w < 4.8:
        return None

    wc = 13.12 + 0.6215 * t - 11.37 * math.pow(w, 0.16) + 0.3965 * t * math.pow(w, 0.16)
    return round(wc, 1)


def calcular_heat_index(temp_c, rh_pct):
    """
    Calcula Heat Index (sensación térmica por calor + humedad).

    Parámetros:
        temp_c (float): Temperatura (°C)
        rh_pct (float): Humedad relativa (%)

    Retorna:
        float | None: Índice de calor o None si no aplica.
    """
    if temp_c is None or rh_pct is None:
        return None

    try:
        t = float(temp_c)
        rh = float(rh_pct)
    except:
        return None

    if t < 27 or rh < 40:
        return None

    t_f = t * 9/5 + 32
    hi_f = (
        -42.379 + 2.04901523*t_f + 10.14333127*rh
        - 0.22475541*t_f*rh - 0.00683783*t_f**2
        - 0.05481717*rh**2 + 0.00122874*t_f**2*rh
        + 0.00085282*t_f*rh**2 - 0.00000199*t_f**2*rh**2
    )

    hi_c = (hi_f - 32) * 5/9
    return round(hi_c, 1)


def calcular_apparent_temperature(temp_c, rh_pct, wspd_kmh):
    """
    Calcula Apparent Temperature (sensación térmica australiana).

    Parámetros:
        temp_c (float): Temperatura (°C)
        rh_pct (float): Humedad (%) 
        wspd_kmh (float): Viento (km/h)

    Retorna:
        float | None
    """
    if temp_c is None or rh_pct is None or wspd_kmh is None:
        return None

    try:
        t = float(temp_c)
        rh = float(rh_pct)
        w = float(wspd_kmh)
    except:
        return None

    if not (-50 <= t <= 60 and 0 <= rh <= 100 and w >= 0):
        return None

    v = w / 3.6
    e = _vapour_pressure_hpa(t, rh)

    at = t + 0.33 * e - 0.70 * v - 4.00
    return round(at, 1)


def calcular_sensacion_termica(temp, rhum, wspd):
    """
    Selecciona automáticamente la mejor sensación térmica disponible.

    Parámetros:
        temp (float): Temperatura (°C)
        rhum (float): Humedad (%)
        wspd (float): Viento (km/h)

    Retorna:
        float | None
    """
    if temp is None or rhum is None or wspd is None:
        return None

    try:
        temp = float(temp)
        rhum = float(rhum)
        wspd = float(wspd)
    except:
        return None

    wc = calcular_wind_chill(temp, wspd)
    hi = calcular_heat_index(temp, rhum)
    at = calcular_apparent_temperature(temp, rhum, wspd)

    if wc is not None:
        return wc
    if hi is not None:
        return hi
    return at


# ============================================================
#   Cálculo UV
# ============================================================

def calcular_radiacion_uv(temp, coco, fecha_hora):
    """
    Estima el índice UV a partir de:
    - Temperatura
    - Código de condición (Meteostat)
    - Hora del día

    Parámetros:
        temp (float): Temperatura (°C)
        coco (int): Código Meteostat
        fecha_hora (str): Fecha ISO "YYYY-MM-DDTHH:MM:SSZ"

    Retorna:
        float | None
    """
    if temp is None or coco is None or fecha_hora is None:
        return None

    try:
        temp = float(temp)
        dt = datetime.fromisoformat(fecha_hora.replace("Z", "+00:00"))
        hora = dt.hour
    except:
        return None

    if temp < -50 or temp > 60:
        return None

    # Curva diaria simple
    if 10 <= hora <= 15:
        base_uv = 8.0
    elif 8 <= hora < 10 or 15 < hora <= 17:
        base_uv = 4.0
    else:
        base_uv = 1.0

    # Atenuación por nubosidad
    if coco in [1, 2]:
        factor = 0.0     # despejado
    elif coco in [3, 4]:
        factor = 0.4     # nubes
    elif coco in [5, 6]:
        factor = 0.6     # niebla
    elif coco in [7, 8, 9, 10, 11, 12, 13]:
        factor = 0.7     # lluvia
    elif coco in [14, 15, 16, 21, 22]:
        factor = 0.8     # nieve
    elif coco in [23, 24, 25, 26, 27]:
        factor = 0.9     # tormentas
    else:
        factor = 0.5

    temp_factor = max(0.8, min(1.2, (temp - 10) / 15))

    uv = base_uv * (1 - factor) * temp_factor
    return round(uv, 1)


# ============================================================
#   Visibilidad
# ============================================================

def calcular_visibilidad(temp, rhum, dwpt, prcp, snow, wspd, coco):
    """
    Estima la visibilidad atmosférica (km).

    Parámetros:
        temp (float) : Temperatura (°C)
        rhum (float) : Humedad relativa (%)
        dwpt (float) : Punto de rocío (°C)
        prcp (float) : Precipitación (mm/h)
        snow (float) : Nieve (mm/h)
        wspd (float) : Viento (km/h)
        coco (int)   : Código Meteostat

    Retorna:
        float | None : visibilidad estimada en km
    """
    # Parsing seguro
    try:
        temp = None if temp is None else float(temp)
        rhum = None if rhum is None else float(rhum)
        dwpt = None if dwpt is None else float(dwpt)
        prcp = 0.0 if prcp in [None, math.nan] else float(prcp)
        snow = 0.0 if snow in [None, math.nan] else float(snow)
        wspd = 0.0 if wspd in [None, math.nan] else float(wspd)
        coco = None if coco is None else int(coco)
    except:
        return None

    if temp is None or rhum is None:
        return None
    if not (-80 <= temp <= 70 and 0 <= rhum <= 100 and wspd >= 0):
        return None

    vis_km = 20.0  # valor base máximo

    # --- Niebla ---
    if dwpt is not None:
        dep = temp - dwpt
    else:
        dep = None

    if rhum >= 95 and dep is not None and dep <= 2:
        base_fog = 0.05 if (rhum >= 99 and dep <= 0.5) else (0.2 if rhum >= 97 else 0.5)

        if wspd >= 40:
            vis_km = base_fog * 3
        elif wspd >= 15:
            vis_km = base_fog * 1.5
        else:
            vis_km = base_fog

        return round(max(vis_km, 0.05), 1)

    # --- Neblina ---
    if rhum >= 85 and dep is not None and dep <= 4:
        vis_km = 1.0 + (rhum - 85) / 15 * 3
        if wspd >= 30:
            vis_km *= 1.3
        return round(min(vis_km, 20.0), 1)

    # --- Precipitación ---
    if prcp > 0:
        if prcp < 0.5:
            vis_km = 10.0
        elif prcp < 2:
            vis_km = 6.0
        elif prcp < 10:
            vis_km = 3.0
        else:
            vis_km = 0.8

        if coco in [23, 24, 25, 26, 27, 9, 8, 18]:
            vis_km = min(vis_km, 2.0)

        if wspd > 80:
            vis_km *= 0.8

        return round(max(vis_km, 0.05), 1)

    # --- Nieve ---
    if snow > 0:
        if snow < 0.5:
            vis_km = 6.0
        elif snow < 2:
            vis_km = 3.0
        elif snow < 5:
            vis_km = 1.5
        else:
            vis_km = 0.5

        if wspd >= 30:
            vis_km *= 0.6

        return round(max(vis_km, 0.05), 1)

    # --- Otros ajustes por códigos ---
    if coco is not None:
        if coco in [7, 17]:
            vis_km = min(vis_km, 10.0)
        elif coco in [8, 18]:
            vis_km = min(vis_km, 6.0)
        elif coco in [23, 24, 25, 26, 27]:
            vis_km = min(vis_km, 3.0)

    # --- Reducción por viento fuerte ---
    if wspd >= 80:
        vis_km = min(vis_km, 8.0)
    elif wspd >= 60:
        vis_km = min(vis_km, 12.0)

    return round(max(min(vis_km, 20.0), 0.05), 1)
