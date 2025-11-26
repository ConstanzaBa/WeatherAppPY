"""
IA - Predicción de temperatura/humedad/presión con Red Neuronal (mejorada)

Ahora:
- Entrena 3 modelos (temp, rhum, pres) usando las mismas features temporales + lags + rolling.
- Predice 7 días en modo walk-forward (cada día usa salidas previas como entrada).
- Calcula precipitación con una fórmula más física (temp - dewpoint, humedad, presión).
- Asigna COCO.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo


# ============================
# ENTRENAMIENTO (RandomForest)
# ============================
def entrenar_modelo(df):
    df = df.copy()
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
    df = df.sort_values("fecha_hora").reset_index(drop=True)

    # Features temporales
    df["hour"] = df["fecha_hora"].dt.hour
    df["dayofyear"] = df["fecha_hora"].dt.dayofyear
    df["month"] = df["fecha_hora"].dt.month

    # Lag features
    lag_hours = [1, 24, 48, 72]  # 1h, 24h, 48h, 72h
    for col in ["temp", "dwpt", "rhum", "wspd", "pres"]:
        for lag in lag_hours:
            df[f"{col}_lag{lag}"] = df[col].shift(lag)

    # Rolling 24h y 72h
    for col in ["temp", "dwpt", "rhum", "pres"]:
        df[f"{col}_rolling24"] = df[col].rolling(24, min_periods=1).mean()
        df[f"{col}_rolling72"] = df[col].rolling(72, min_periods=1).mean()

    # Lista de features
    features = [
        "temp", "dwpt", "rhum", "wspd", "pres",
        # Lags
        *[f"{c}_lag{l}" for c in ["temp","dwpt","rhum","wspd","pres"] for l in lag_hours],
        # Rollings
        *[f"{c}_rolling24" for c in ["temp","dwpt","rhum","pres"]],
        *[f"{c}_rolling72" for c in ["temp","dwpt","rhum","pres"]],
        # Temporales
        "hour", "dayofyear", "month"
    ]

    # Asegurar columnas numéricas
    for c in features:
        if c not in df.columns: df[c] = 0.0
    df[features] = df[features].apply(pd.to_numeric, errors="coerce").ffill().bfill().fillna(0.0)

    # Targets
    y_temp = df["temp"].astype(float).ffill().fillna(0.0)
    y_rhum = df["rhum"].astype(float).ffill().fillna(0.0)
    y_pres = df["pres"].astype(float).ffill().fillna(1013.0)

    # Escalado
    X = df[features].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Helper para entrenar RandomForest
    def crear_y_entrenar_rf(y):
        try:
            model = RandomForestRegressor(
                n_estimators=200,
                max_depth=12,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_scaled, y)
        except Exception:
            class MeanModel:
                def __init__(self, mean): self.mean = mean
                def predict(self, X): return np.array([self.mean] * len(X))
            model = MeanModel(float(np.nanmean(y)))
        return model

    modelo_temp = crear_y_entrenar_rf(y_temp)
    modelo_rhum = crear_y_entrenar_rf(y_rhum)
    modelo_pres = crear_y_entrenar_rf(y_pres)

    return {"temp": modelo_temp, "rhum": modelo_rhum, "pres": modelo_pres}, scaler, features


# ============================
# PRECIPITACIÓN
# ============================
def calcular_precipitacion(temp, dwpt, rhum, pres):
    temp = float(temp)
    dwpt = float(dwpt)
    rhum = float(rhum)
    pres = float(pres)

    # spread entre T y dewpoint
    t_dd_spread = max(0.1, temp - dwpt)  # evitar división por cero

    # factor de saturación proporcional a cercanía a saturación (mayor si spread pequeño)
    sat_factor = np.exp(-t_dd_spread / 2.0)  # 0..1, más realista

    # humedad relativa normalizada
    hum_factor = np.clip(rhum / 100.0, 0.0, 1.0)

    # presión: baja presión favorece lluvia, efecto moderado
    pres_anom = 1013.0 - pres
    pres_factor = 1.0 + 0.3 * np.tanh(pres_anom / 10.0)

    # temperatura extrema reduce precipitación
    temp_factor = 1.0
    if temp >= 38:
        temp_factor = max(0.0, 1.0 - (temp - 38) * 0.15)
    elif temp <= -5:
        temp_factor = max(0.0, 1.0 - (-5 - temp) * 0.1)

    # índice final de lluvia
    index = sat_factor * hum_factor * pres_factor * temp_factor

    # Categoría de lluvia más gradual
    if index < 0.05:
        return 0.0
    elif index < 0.2:
        return round(np.random.uniform(0.1, 3.0), 1)
    elif index < 0.45:
        return round(np.random.uniform(3.0, 12.0), 1)
    elif index < 0.7:
        return round(np.random.uniform(12.0, 25.0), 1)
    else:
        return round(np.random.uniform(25.0, 40.0), 1)


# ============================
# COCO
# ============================
def calcular_coco(temp, dwpt, rhum, pres, precip):
    temp = float(temp)
    dwpt = float(dwpt)
    rhum = float(rhum)
    pres = float(pres)
    precip = float(precip)

    t_dd_spread = max(0.1, abs(temp - dwpt))

    # Priorizar precipitación
    if precip >= 25:
        return 9   # lluvia intensa
    elif precip >= 10:
        return 8   # lluvia fuerte
    elif precip >= 2:
        return 7   # lluvia ligera/moderada

    # Niebla
    if rhum >= 95 and t_dd_spread < 2.0:
        return 5

    # Tormenta solo con precip >5 mm y presión muy baja
    if precip >= 5 and pres < 995:
        return 27

    # Nublado si humedad alta pero sin lluvia
    if rhum >= 80:
        return 3

    # Soleado si poca humedad y spread mayor a 3°C
    if rhum < 70 and precip < 1 and t_dd_spread > 3:
        return 1

    # Parcialmente despejado para el resto
    return 2


# ============================
# PREDICCIÓN 7 DÍAS 
# ============================
def predecir_7dias(models, scaler, features, df):
    """
    Predicción walk-forward de 7 días
    Devuelve lista de dicts con:
    fecha, temp_high, temp_low, temp_avg, precip, coco
    """
    df = df.copy()
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
    df = df.sort_values("fecha_hora").reset_index(drop=True)

    if df.empty:
        return []

    ultimo = df.iloc[-1].to_dict()
    ahora_ar = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires"))
    fecha_base = ahora_ar.date()

    # Features temporales
    ultimo["hour"] = ahora_ar.hour
    ultimo["dayofyear"] = fecha_base.timetuple().tm_yday
    ultimo["month"] = fecha_base.month

    # Rolling 24h y 72h
    for c in ["temp", "dwpt", "rhum", "pres"]:
        roll24 = df[c].tail(24).mean() if c in df and not df[c].empty else float(ultimo.get(c, 0.0))
        roll72 = df[c].tail(72).mean() if c in df and not df[c].empty else float(ultimo.get(c, 0.0))
        ultimo[f"{c}_rolling24"] = roll24
        ultimo[f"{c}_rolling72"] = roll72

    # Lag1
    for c in ["temp", "dwpt", "rhum", "wspd", "pres"]:
        ultimo[f"{c}_lag1"] = ultimo.get(c, 0.0)

    # Garantizar todas las features
    for col in features:
        if col not in ultimo or pd.isna(ultimo[col]):
            ultimo[col] = 0.0
        try:
            ultimo[col] = float(ultimo[col])
        except Exception:
            ultimo[col] = 0.0

    predicciones = []

    for i in range(7):
        fecha_pred = fecha_base + timedelta(days=i)
        X_row = np.array([ultimo.get(f, 0.0) for f in features]).reshape(1, -1)
        X_scaled = scaler.transform(X_row)

        # Predicciones base
        temp_pred = float(models.get("temp", ultimo.get("temp", 15.0)).predict(X_scaled)[0])
        rhum_pred = float(models.get("rhum", ultimo.get("rhum", 60.0)).predict(X_scaled)[0])
        pres_pred = float(models.get("pres", ultimo.get("pres", 1013.0)).predict(X_scaled)[0])

        # Ruido leve
        temp_pred += np.random.uniform(-0.5, 0.5)
        rhum_pred += np.random.uniform(-1.0, 1.0)
        pres_pred += np.random.uniform(-0.2, 0.2)

        # Rangos realistas
        temp_pred = np.clip(temp_pred, -10.0, 42.0)
        rhum_pred = np.clip(rhum_pred, 0.0, 100.0)
        pres_pred = np.clip(pres_pred, 950.0, 1060.0)

        # Dew point aproximado
        try:
            a, b = 17.27, 237.7
            hum = max(min(rhum_pred, 100.0), 1.0)
            alpha = ((a * temp_pred) / (b + temp_pred + 1e-9)) + np.log(hum / 100.0)
            denom = a - alpha
            dwpt_pred = (b * alpha) / denom if abs(denom) > 1e-6 else temp_pred - np.random.uniform(0.5, 3.0)
        except Exception:
            dwpt_pred = temp_pred - np.random.uniform(0.5, 3.0)

        # Precipitación y COCO
        precip = calcular_precipitacion(temp_pred, dwpt_pred, rhum_pred, pres_pred)
        coco = calcular_coco(temp_pred, dwpt_pred, rhum_pred, pres_pred, precip)

        rolling_temp = 0.5 * ultimo.get("temp_rolling24", temp_pred) + 0.5 * ultimo.get("temp_rolling72", temp_pred)

        # Patrón día-noche más pronunciado
        hora = 12  # predicción central del día
        temp_pred += 4.0 * np.sin((hora - 14) / 24.0 * 2 * np.pi)  # antes 2.0°C

        # Delta dinámico según tendencia diaria (mayor amplitud)
        delta_high = np.random.normal(3.0, 2.0) + 0.3 * (ultimo["temp"] - ultimo.get("temp_lag1", ultimo["temp"]))
        delta_low  = np.random.normal(3.0, 2.0) + 0.3 * (ultimo["temp"] - ultimo.get("temp_lag1", ultimo["temp"]))

        # Clipping amplio para permitir picos reales
        temp_high = round(np.clip(temp_pred + delta_high, -5, 45), 1)
        temp_low  = round(np.clip(temp_pred - delta_low, -5, 42), 1)

        # Evitar temp_low < dewpoint
        temp_low = max(temp_low, dwpt_pred - 2)
        if temp_high < temp_low:
            temp_high = temp_low + np.random.uniform(1, 3)

        predicciones.append({
            "fecha": fecha_pred.strftime("%Y-%m-%d"),
            "temp_high": temp_high,
            "temp_low": temp_low,
            "temp_avg": round(temp_pred, 1),
            "precip": precip,
            "coco": int(coco)
        })

        # Actualizar 'ultimo' para siguiente día
        for c in ["temp","dwpt","rhum","wspd","pres"]:
            ultimo[c] = temp_pred if c=="temp" else dwpt_pred if c=="dwpt" else rhum_pred if c=="rhum" else pres_pred if c=="pres" else ultimo.get(c, 0.0)
            ultimo[f"{c}_lag1"] = ultimo[c]

        # Rolling exponencial 24h
        for c in ["temp","dwpt","rhum","pres"]:
            ultimo[f"{c}_rolling24"] = (ultimo.get(f"{c}_rolling24", temp_pred)*23 + ultimo[c]) / 24.0

        # Actualizar fecha
        fecha_siguiente = fecha_base + timedelta(days=i + 1)
        ultimo["dayofyear"] = fecha_siguiente.timetuple().tm_yday
        ultimo["month"] = fecha_siguiente.month
        ultimo["hour"] = 12

    return predicciones
