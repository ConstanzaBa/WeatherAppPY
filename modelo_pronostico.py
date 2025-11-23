"""
IA - Predicción de temperatura con Red Neuronal
"""

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from datetime import timedelta


# ==========================================
# ENTRENAMIENTO
# ==========================================
def entrenar_modelo(df):
    """
    Entrena un modelo MLPRegressor con features climáticas + temporales.
    """

    # ----------------------
    # Features temporales
    # ----------------------
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])
    df["hour"] = df["fecha_hora"].dt.hour
    df["dayofyear"] = df["fecha_hora"].dt.dayofyear
    df["month"] = df["fecha_hora"].dt.month

    # Media móvil (tendencia)
    df["temp_rolling"] = df["temp"].rolling(24, min_periods=1).mean()

    # ----------------------
    # Features del modelo
    # ----------------------
    features = [
        "temp", "dwpt", "rhum", "wspd", "pres",
        "hour", "dayofyear", "month", "temp_rolling"
    ]

    # Asegurar que todo exista
    for col in features:
        if col not in df.columns:
            df[col] = 0

    df[features] = df[features].apply(pd.to_numeric, errors="coerce").interpolate().fillna(0)

    # ======================
    X = df[features]
    y = df["temp"]
    # ======================

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    modelo = MLPRegressor(
        hidden_layer_sizes=(64, 32),
        activation="relu",
        solver="adam",
        learning_rate_init=0.002,
        max_iter=500,
        early_stopping=True,
        random_state=42
    )

    modelo.fit(X_scaled, y)

    return modelo, scaler, features


# ==========================================
# CÁLCULO DE COCO
# ==========================================
def calcular_coco(temp, rhum, pres):
    """
    Estimación del código climático.
    Muy simple pero suficiente para variaciones.
    """

    if rhum > 85:
        return 45   # lluvia fuerte
    if rhum > 75:
        return 3    # nublado
    if temp > 30:
        return 1    # despejado y caluroso
    if pres < 995:
        return 55   # tormenta
    return 1        # despejado estándar


# ==========================================
# PREDICCIÓN 7 DÍAS
# ==========================================
def predecir_7dias(modelo, scaler, features, df):
    """
    Predicción iterativa realista.
    Actualiza TODAS las variables cada día.
    """

    ultimo = df.iloc[-1].copy()
    ultimo[features] = ultimo[features].apply(pd.to_numeric, errors="coerce").fillna(0)

    from datetime import datetime
    fecha_actual = datetime.now().date()

    predicciones = []

    for i in range(7):
        entrada = pd.DataFrame([ultimo[features]])
        entrada_scaled = scaler.transform(entrada)

        # ================
        # TEMPERATURA
        # ================
        temp_pred = float(modelo.predict(entrada_scaled)[0])

        # Variación natural
        temp_pred += np.random.uniform(-1.5, 1.5)

        # ================
        # Actualizar resto de variables
        # ================
        ultimo["dwpt"] += np.random.uniform(-0.8, 0.8)
        ultimo["rhum"] += np.random.uniform(-3, 3)
        ultimo["wspd"] += np.random.uniform(-1.2, 1.2)
        ultimo["pres"] += np.random.uniform(-2.0, 2.0)

        # Mantener límites
        ultimo["rhum"] = np.clip(ultimo["rhum"], 20, 100)
        ultimo["pres"] = np.clip(ultimo["pres"], 980, 1040)

        # Actualizar temperatura real
        ultimo["temp"] = temp_pred

        # Actualizar tendencia móvil
        ultimo["temp_rolling"] = (ultimo["temp_rolling"] * 23 + temp_pred) / 24

        # Temporalidad
        ultimo["dayofyear"] += 1
        if ultimo["dayofyear"] > 365:
            ultimo["dayofyear"] = 1

        # Mes (estimación simple)
        ultimo["month"] = int((ultimo["dayofyear"] / 30.4) + 1)
        ultimo["month"] = max(1, min(12, ultimo["month"]))

        # ===================
        # COCO
        # ===================
        coco = calcular_coco(temp_pred, ultimo["rhum"], ultimo["pres"])

        fecha_pred = fecha_actual + timedelta(days=i)

        predicciones.append({
            "fecha": fecha_pred.strftime("%Y-%m-%d"),
            "temp_high": round(temp_pred + 2, 1),
            "temp_low": round(temp_pred - 2, 1),
            "precip": round(max(0, 100 - ultimo["pres"]), 1),
            "coco": coco
        })

    return predicciones
