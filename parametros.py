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
    dwpt  : punto de rocío en °C (dew point)
    prcp  : precipitación en mm/h (puede ser 0 o NaN)
    snow  : nieve en mm/h (puede ser 0 o NaN)
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



def calcular_visibilidad(temp, rhum, dwpt, prcp, snow, wspd, coco):
    """
    Retorna:
        float -> visibilidad estimada en km (redondeada a 1 decimal)
        None  -> si datos insuficientes o inválidos
    """
    try:
        # convertir si vienen como strings / NaN -> raise
        temp = None if temp is None else float(temp)
        rhum = None if rhum is None else float(rhum)
        dwpt = None if dwpt is None else float(dwpt)
        prcp = 0.0 if (prcp is None or (isinstance(prcp, float) and math.isnan(prcp))) else float(prcp)
        snow = 0.0 if (snow is None or (isinstance(snow, float) and math.isnan(snow))) else float(snow)
        wspd = 0.0 if (wspd is None or (isinstance(wspd, float) and math.isnan(wspd))) else float(wspd)
        coco = None if coco is None else int(coco)
    except Exception:
        return None

    # Requerimos al menos temp y rhum o dwpt para evaluar niebla; si faltan por completo devolvemos None
    if temp is None or rhum is None:
        return None

    # Checks físicos básicos
    if not (-80 <= temp <= 70 and 0 <= rhum <= 100 and wspd >= 0):
        return None

    # valor base
    vis_km = 20.0

    # Depresión del punto de rocío (T - Td)
    if dwpt is not None:
        dep = temp - dwpt
    else:
        dep = None

    # Condición típica de niebla: RH muy alta y depresión pequeña
    if rhum >= 95 and dep is not None and dep <= 2.0:
        # Niebla densa si RH muy alta y dep muy pequeña
        # Ajuste por viento: viento ligero mantiene niebla; viento fuerte la reduce.
        if rhum >= 99 and dep <= 0.5:
            base_fog = 0.05  # niebla muy densa
        elif rhum >= 97:
            base_fog = 0.2
        else:
            base_fog = 0.5

        # viento ayuda a dispersar la niebla
        if wspd >= 40:
            vis_km = max(base_fog * 3.0, 0.1)  # viento fuerte mejora pero sigue baja vis
        elif wspd >= 15:
            vis_km = max(base_fog * 1.5, 0.05)
        else:
            vis_km = base_fog

        # retornamos inmediatamente porque niebla domina en general
        return round(vis_km, 1)

    # Neblina leve / vapor: RH alto pero no completa
    if rhum >= 85 and dep is not None and dep <= 4.0:
        # reducción moderada
        vis_km = 1.0 + (rhum - 85) / 15.0 * 3.0  # tendencia: de 1 km a ~4 km
        # ajustar por viento
        if wspd >= 30:
            vis_km = max(vis_km * 1.3, 0.5)
        return round(min(vis_km, 20.0), 1)

    # Priorizar precipitación líquida (prcp) y luego nieve (snow)
    if prcp > 0:
        # Umbrales empíricos (mm/h)
        if prcp < 0.5:
            vis_km = 10.0  # llovizna ligera
        elif prcp < 2.0:
            vis_km = 6.0   # lluvia ligera-moderada
        elif prcp < 10.0:
            vis_km = 3.0   # lluvia moderada-fuerte
        else:
            vis_km = 0.8   # lluvia muy intensa / torrencial

        # si coco indica tormenta o lluvia fuerte, bajar otro escalón
        if coco in [23, 24, 25, 26, 27, 9, 8, 18]:  # tormentas, granizo, heavy rain, rain
            vis_km = min(vis_km, 2.0 if prcp >= 2.0 else vis_km)

        # el viento no aumenta vis en lluvia — puede reducir por aire levantado
        if wspd > 80:
            vis_km = max(vis_km * 0.8, 0.1)

        return round(vis_km, 1)
    
    if snow > 0:
        # Umbrales empiricos para nieve (mm/h)
        if snow < 0.5:
            vis_km = 6.0
        elif snow < 2.0:
            vis_km = 3.0
        elif snow < 5.0:
            vis_km = 1.5
        else:
            vis_km = 0.5

        # viento agrava la reducción por blowing snow
        if wspd >= 30:
            vis_km = max(vis_km * 0.6, 0.05)

        return round(vis_km, 1)

    # Si hay códigos de lluvia aislada o tormentas sin prcp, reducir algo
    if coco is not None:
        if coco in [7, 17]:  # light rain / isolated rain (si no hubo prcp registrado, asumimos leve)
            vis_km = min(vis_km, 10.0)
        elif coco in [8, 18]:  # rain / heavy rain indicators
            vis_km = min(vis_km, 6.0)
        elif coco in [23, 24, 25, 26, 27]:  # stormy
            vis_km = min(vis_km, 3.0)

    # Viento muy fuerte puede reducir vis por polvo/suspensión 
    if wspd >= 80:
        vis_km = min(vis_km, 8.0)
    elif wspd >= 60:
        vis_km = min(vis_km, 12.0)

    # Limitar rango final y devolver
    vis_km = max(0.05, min(vis_km, 20.0))
    return round(vis_km, 1)
