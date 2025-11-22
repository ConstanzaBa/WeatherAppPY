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
    # Columnas que usamos como features
    features = ["temp", "dwpt", "rhum", "prcp", "snow", "wdir", "wspd", "wpgt", "pres", "tsun"]
    
    # Interpolación y llenado de NaN
    df[features] = df[features].interpolate().fillna(0.0)

    X = df[features]
    y = df["temp"]

    # Normalización
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Red neuronal simple
    modelo = MLPRegressor(
        hidden_layer_sizes=(50, 25),
        activation='relu',
        solver='adam',
        max_iter=500,
        random_state=42
    )
    modelo.fit(X_scaled, y)
    return modelo, scaler, features

# ------------------------------------------------------
# PREDICTOR DE 7 DÍAS
# ------------------------------------------------------
def predecir_7dias(modelo, scaler, features, df):
    """
    Genera predicción iterativa de 7 días usando la columna fecha_hora
    y todas las features proporcionadas, con normalización.
    """
    predicciones = []
    ultimo = df.iloc[-1].copy()
    ultimo["fecha_hora"] = pd.to_datetime(ultimo["fecha_hora"])
    
    # Convertir features a float y llenar NaN
    ultimo[features] = ultimo[features].apply(pd.to_numeric, errors='coerce').fillna(0.0)
    
    for _ in range(7):
        entrada = pd.DataFrame([ultimo[features]])
        entrada_scaled = scaler.transform(entrada)
        
        temp_pred = float(modelo.predict(entrada_scaled)[0])
        coco_pred = int(ultimo.get("coco", 0))
        nueva_fecha = ultimo["fecha_hora"] + timedelta(days=1)
        
        predicciones.append({
            "fecha": nueva_fecha.strftime("%Y-%m-%d"),
            "temp_high": round(temp_pred + 2, 1),
            "temp_low": round(temp_pred - 2, 1),
            "precip": float(round(ultimo.get("prcp", 0.0), 1)),
            "coco": coco_pred
        })
        
        # Actualizamos último para la siguiente iteración
        ultimo["temp"] = temp_pred
        ultimo["fecha_hora"] = nueva_fecha
    
    return predicciones
