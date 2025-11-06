import math
from datetime import datetime

"""
Funciones para calcular parámetros meteorológicos derivados:
- Sensación térmica (frío, calor o templado)
- Radiación UV estimada

Parámetros esperados:
    temp (°C): Temperatura del aire
    rhum (%): Humedad relativa
    wspd (km/h): Velocidad del viento
    coco (int): Código de condición meteorológica (Meteostat)
    fecha_hora (str): Fecha y hora ISO (ej. "2025-11-06T13:00:00Z")
"""

def _vapour_pressure_hpa(temp_c, rh_pct):
    """Presión de vapor (hPa) según temperatura y humedad."""
    return (rh_pct / 100.0) * 6.105 * math.exp((17.27 * temp_c) / (237.7 + temp_c))

def calcular_wind_chill(temp_c, wspd_kmh):
    """Sensación térmica por viento (fórmula canadiense)."""
    if temp_c is None or wspd_kmh is None:
        return None
    try:
        t = float(temp_c)
        w = float(wspd_kmh)
    except Exception:
        return None
    if t > 10 or w < 4.8:
        return None  # No aplica
    wc = 13.12 + 0.6215 * t - 11.37 * math.pow(w, 0.16) + 0.3965 * t * math.pow(w, 0.16)
    return round(wc, 1)

def calcular_heat_index(temp_c, rh_pct):
    """Índice de calor (NWS, EE.UU.)."""
    if temp_c is None or rh_pct is None:
        return None
    try:
        t = float(temp_c)
        rh = float(rh_pct)
    except Exception:
        return None
    if t < 27 or rh < 40:
        return None  # Solo aplica en calor y humedad alta
    t_f = t * 9.0 / 5.0 + 32.0
    hi_f = (
        -42.379 + 2.04901523 * t_f + 10.14333127 * rh
        - 0.22475541 * t_f * rh - 0.00683783 * (t_f ** 2)
        - 0.05481717 * (rh ** 2) + 0.00122874 * (t_f ** 2) * rh
        + 0.00085282 * t_f * (rh ** 2) - 0.00000199 * (t_f ** 2) * (rh ** 2)
    )
    hi_c = (hi_f - 32.0) * 5.0 / 9.0
    return round(hi_c, 1)

def calcular_apparent_temperature(temp_c, rh_pct, wspd_kmh):
    """Temperatura aparente (Australian Bureau of Meteorology)."""
    if temp_c is None or rh_pct is None or wspd_kmh is None:
        return None
    try:
        t = float(temp_c)
        rh = float(rh_pct)
        w_kmh = float(wspd_kmh)
    except Exception:
        return None
    if not (-50 <= t <= 60 and 0 <= rh <= 100 and w_kmh >= 0):
        return None
    v = w_kmh / 3.6  # m/s
    e = _vapour_pressure_hpa(t, rh)
    at = t + 0.33 * e - 0.70 * v - 4.00
    return round(at, 1)

def calcular_sensacion_termica(temp, rhum, wspd):
    """
    Devuelve la sensación térmica más realista posible:
    - Usa Wind Chill si hace frío
    - Usa Heat Index si hace calor
    - Usa Apparent Temperature para el rango templado
    """
    if temp is None or rhum is None or wspd is None:
        return None
    try:
        temp = float(temp)
        rhum = float(rhum)
        wspd = float(wspd)
    except Exception:
        return None

    wc = calcular_wind_chill(temp, wspd)
    hi = calcular_heat_index(temp, rhum)
    at = calcular_apparent_temperature(temp, rhum, wspd)

    # Regla de decisión según condiciones
    if wc is not None:
        final = wc
    elif hi is not None:
        final = hi
    else:
        final = at

    return round(final, 1) if final is not None else None


def calcular_radiacion_uv(temp, coco, fecha_hora):
    """
    Retorna:
        float → índice UV estimado
        None → si los datos son inválidos o incompletos
    """
    if temp is None or coco is None or fecha_hora is None:
        return None

    try:
        temp = float(temp)
        dt = datetime.fromisoformat(fecha_hora.replace("Z", "+00:00"))
        hora = dt.hour
    except Exception:
        return None

    if temp < -50 or temp > 60:
        return None
    if not (0 <= hora <= 23):
        return None

    # Base UV según hora solar
    if 10 <= hora <= 15:
        base_uv = 8.0
    elif (8 <= hora < 10) or (15 < hora <= 17):
        base_uv = 4.0
    else:
        base_uv = 1.0  # Noche o madrugada

    # Ajuste por nubosidad según coco (meteostat)
    if coco in [1, 2]:  # Despejado
        factor_nubosidad = 0.0
    elif coco in [3, 4]:  # Parcial / Cubierto
        factor_nubosidad = 0.4
    elif coco in [5, 6]:  # Niebla
        factor_nubosidad = 0.6
    elif coco in [7, 8, 9, 10, 11, 12, 13]:  # Lluvia o aguanieve
        factor_nubosidad = 0.7
    elif coco in [14, 15, 16, 21, 22]:  # Nieve
        factor_nubosidad = 0.8
    elif coco in [23, 24, 25, 26, 27]:  # Tormentas
        factor_nubosidad = 0.9
    elif coco in [17, 18, 19, 20]:  # Lluvias aisladas
        factor_nubosidad = 0.6
    else:
        factor_nubosidad = 0.5

    # Ajuste leve por temperatura
    temp_factor = max(0.8, min(1.2, (temp - 10) / 15))

    uv = base_uv * (1 - factor_nubosidad) * temp_factor
    return round(uv, 1)