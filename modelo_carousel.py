"""
Modelo SVR para predicción meteorológica del día siguiente
Genera datos de probabilidad de lluvia, sensación térmica y nubosidad
"""

import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ------------------------------------------------------
# ENTRENAMIENTO GENÉRICO SVR
# ------------------------------------------------------
def entrenar_modelo_svr(df, target_col):
    """
    Entrena un modelo SVR para predecir una variable específica.
    """

    features = ["temp", "dwpt", "rhum", "wspd", "pres"]

    for col in features:
        if col not in df.columns:
            df[col] = 0.0

    if target_col not in df.columns:
        df[target_col] = 0.0

    df[features] = df[features].apply(pd.to_numeric, errors="coerce").interpolate().fillna(0.0)
    df[target_col] = pd.to_numeric(df[target_col], errors="coerce").interpolate().fillna(0.0)

    X = df[features]
    y = df[target_col]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    modelo = SVR(kernel="rbf", C=100, gamma=0.1, epsilon=0.1)
    modelo.fit(X_scaled, y)

    return modelo, scaler, features


# ------------------------------------------------------
# PREDICCIÓN DEL DÍA SIGUIENTE
# ------------------------------------------------------
def predecir_manana(df):
    """
    Genera predicciones del día siguiente usando SVR.
    Retorna: probabilidad de lluvia, sensación térmica y nubosidad
    """

    df = df.copy()
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])

    # Último registro (hoy)
    ultimo = df.iloc[-1].copy()
    fecha_hoy = ultimo['fecha_hora']
    fecha_manana = fecha_hoy + timedelta(days=1)

    # Valores por defecto
    sens_termica_manana = float(ultimo.get('sensacionTermica', 20)) if pd.notna(ultimo.get('sensacionTermica')) else 20.0
    precip_manana = 0.0

    # ----------------------
    # Sensación térmica mañana
    # ----------------------
    try:
        modelo_sens, scaler_sens, features = entrenar_modelo_svr(df, 'sensacionTermica')
        entrada_sens = pd.DataFrame([ultimo[features].fillna(0.0)])
        entrada_sens_scaled = scaler_sens.transform(entrada_sens)
        sens_termica_manana = float(modelo_sens.predict(entrada_sens_scaled)[0])
    except:
        sens_termica_manana = float(ultimo.get('sensacionTermica', 20))

    # ----------------------
    # Precipitación mañana
    # ----------------------
    try:
        modelo_precip, scaler_precip, features_precip = entrenar_modelo_svr(df, 'prcp')
        entrada_precip = pd.DataFrame([ultimo[features_precip].fillna(0.0)])
        entrada_precip_scaled = scaler_precip.transform(entrada_precip)
        precip_manana = max(0, float(modelo_precip.predict(entrada_precip_scaled)[0]))
    except:
        precip_manana = 0.0

    # Probabilidad de lluvia (basado en precipitación predicha)
    prob_lluvia = min(100, int((precip_manana / 5.0) * 100)) if precip_manana > 0.1 else 0

    # ----------------------
    # Nubosidad (basado en código climático)
    # ----------------------
    coco_hoy = int(ultimo.get('coco', 1))
    
    # Determinar nivel de nubosidad basado en código climático y precipitación
    # coco: 1=despejado, 2=parcialmente nublado, 3=nublado, 4+=lluvia/tormenta
    if prob_lluvia > 50:
        nubosidad = "Muy nublado"
        nubosidad_porcentaje = 80
    elif prob_lluvia > 20:
        nubosidad = "Parcialmente nublado"
        nubosidad_porcentaje = 50
    elif coco_hoy in [3, 4]:
        nubosidad = "Nublado"
        nubosidad_porcentaje = 60
    elif coco_hoy == 2:
        nubosidad = "Parcialmente nublado"
        nubosidad_porcentaje = 40
    else:
        nubosidad = "Despejado"
        nubosidad_porcentaje = 10

    # ------------------------------------------------------
    # JSON FINAL
    # ------------------------------------------------------
    carousel_data = {
        "probabilidad_lluvia": prob_lluvia,
        "sensacion_termica": round(sens_termica_manana, 1),
        "nubosidad": nubosidad,
        "nubosidad_porcentaje": nubosidad_porcentaje,
        "metadata": {
            "fecha_prediccion": fecha_manana.strftime("%Y-%m-%d"),
            "fecha_generacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    
    return carousel_data
    return carousel_data
