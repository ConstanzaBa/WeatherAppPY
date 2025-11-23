"""
IA - Predicción de temperatura con Red Neuronal Simple (MLPRegressor)
"""

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from datetime import timedelta


# ------------------------------------------------------
# ENTRENAR MODELO
# ------------------------------------------------------
def entrenar_modelo(df):
    """
    Entrena un modelo MLPRegressor usando columnas clave.
    Interpola NaN y normaliza features.
    """

    # Features reducidas
    features = ["temp", "dwpt", "rhum", "wspd", "pres"]

    # Asegurar que existan columnas
    for col in features:
        if col not in df.columns:
            df[col] = 0.0

    # Convertir a float
    df[features] = df[features].apply(pd.to_numeric, errors='coerce')

    # Interpolar y llenar NaN
    df[features] = df[features].interpolate().fillna(0.0)

    X = df[features]
    y = df["temp"]

    # Normalización
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Red neuronal
    modelo = MLPRegressor(
        hidden_layer_sizes=(32, 16),
        activation='relu',
        solver='adam',
        max_iter=400,
        learning_rate_init=0.003,
        early_stopping=True,
        n_iter_no_change=20,
        random_state=42
    )

    modelo.fit(X_scaled, y)

    return modelo, scaler, features


# ------------------------------------------------------
# PREDICTOR DE 7 DÍAS
# ------------------------------------------------------
def predecir_7dias(modelo, scaler, features, df):
    """
    Genera predicción iterativa de 7 días
    """

    from datetime import datetime
    
    # Último registro real
    ultimo = df.iloc[-1].copy()

    # Convertir a float y llenar NaN
    ultimo[features] = ultimo[features].apply(pd.to_numeric, errors='coerce').fillna(0.0)

    # Fecha inicial = HOY
    fecha_actual = datetime.now().date()

    # Asegurar coco
    if "coco" not in ultimo or pd.isna(ultimo["coco"]):
        ultimo["coco"] = 0

    predicciones = []

    for i in range(7):
        entrada = pd.DataFrame([ultimo[features]])
        entrada_scaled = scaler.transform(entrada)

        temp_pred = float(modelo.predict(entrada_scaled)[0])
        coco_pred = int(ultimo["coco"])

        fecha_pred = fecha_actual + timedelta(days=i)

        predicciones.append({
            "fecha": fecha_pred.strftime("%Y-%m-%d"),
            "temp_high": round(temp_pred + 2, 1),
            "temp_low": round(temp_pred - 2, 1),
            "precip": float(round(ultimo.get("prcp", 0.0), 1)),
            "coco": coco_pred
        })

        # Actualizar valores para la próxima iteración
        ultimo["temp"] = temp_pred

    return predicciones
