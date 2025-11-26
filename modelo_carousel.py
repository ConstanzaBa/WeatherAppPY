"""
Modelo SVR para predicción meteorológica del día siguiente
Genera datos de probabilidad de lluvia, sensación térmica y nubosidad
Mejorado para coherencia con modelo_pronostico.py
"""

import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import warnings
warnings.filterwarnings('ignore')


# ============================
# FUNCIÓN DE PRECIPITACIÓN COMPARTIDA (igual a modelo_pronostico.py)
# ============================
def calcular_precipitacion(temp, dwpt, rhum, pres):
    """
    Calcula precipitación basado en parámetros físicos.
    Coherente con modelo_pronostico.py
    """
    temp = float(temp)
    dwpt = float(dwpt)
    rhum = float(rhum)
    pres = float(pres)

    # spread entre T y dewpoint
    t_dd_spread = max(0.1, temp - dwpt)

    # factor de saturación proporcional a cercanía a saturación
    sat_factor = np.exp(-t_dd_spread / 2.0)

    # humedad relativa normalizada
    hum_factor = np.clip(rhum / 100.0, 0.0, 1.0)

    # presión: baja presión favorece lluvia
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

    # Categoría de lluvia
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


# ------------------------------------------------------
# ENTRENAMIENTO GENÉRICO SVR (con features mejoradas)
# ------------------------------------------------------
def entrenar_modelo_svr(df, target_col):
    """
    Entrena un modelo SVR para predecir una variable específica.
    Mejorado con lag features y rolling windows para coherencia con modelo_pronostico.py
    """
    df = df.copy()
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
    df = df.sort_values("fecha_hora").reset_index(drop=True)

    # Features base
    base_features = ["temp", "dwpt", "rhum", "wspd", "pres"]
    
    for col in base_features:
        if col not in df.columns:
            df[col] = 0.0

    # Features temporales
    df["hour"] = df["fecha_hora"].dt.hour
    df["dayofyear"] = df["fecha_hora"].dt.dayofyear
    df["month"] = df["fecha_hora"].dt.month

    # Lag features (igual que modelo_pronostico.py)
    lag_hours = [1, 24, 48, 72]
    for col in base_features:
        for lag in lag_hours:
            df[f"{col}_lag{lag}"] = df[col].shift(lag)

    # Rolling features (igual que modelo_pronostico.py)
    for col in ["temp", "dwpt", "rhum", "pres"]:
        df[f"{col}_rolling24"] = df[col].rolling(24, min_periods=1).mean()
        df[f"{col}_rolling72"] = df[col].rolling(72, min_periods=1).mean()

    # Lista completa de features
    features = [
        *base_features,
        # Lags
        *[f"{c}_lag{l}" for c in base_features for l in lag_hours],
        # Rollings
        *[f"{c}_rolling24" for c in ["temp", "dwpt", "rhum", "pres"]],
        *[f"{c}_rolling72" for c in ["temp", "dwpt", "rhum", "pres"]],
        # Temporales
        "hour", "dayofyear", "month"
    ]

    # Asegurar que todas las features existan
    for f in features:
        if f not in df.columns:
            df[f] = 0.0

    if target_col not in df.columns:
        df[target_col] = 0.0

    # Convertir a numérico y llenar NaN
    df[features] = df[features].apply(pd.to_numeric, errors="coerce").ffill().bfill().fillna(0.0)
    df[target_col] = pd.to_numeric(df[target_col], errors="coerce").ffill().bfill().fillna(0.0)

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
    Mejorado para coherencia con modelo_pronostico.py
    """

    df = df.copy()
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])

    # Obtener la fecha actual usando zona horaria de Argentina (igual que modelo_pronostico.py)
    ahora_ar = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires"))
    fecha_hoy = ahora_ar.date()
    fecha_manana = fecha_hoy + timedelta(days=1)
    
    # Último registro disponible
    ultimo = df.iloc[-1].copy()

    # ----------------------
    # Sensación térmica mañana (usando SVR con features mejoradas)
    # ----------------------
    sens_termica_manana = float(ultimo.get('sensacionTermica', 20)) if pd.notna(ultimo.get('sensacionTermica')) else 20.0
    
    try:
        modelo_sens, scaler_sens, features = entrenar_modelo_svr(df, 'sensacionTermica')
        
        # Preparar entrada con todas las features
        entrada = {}
        for f in features:
            if f in df.columns:
                if f.startswith('temp_') or f.startswith('dwpt_') or f.startswith('rhum_') or f.startswith('pres_') or f.startswith('wspd_'):
                    # Features derivadas: usar último valor del dataframe
                    entrada[f] = df[f].iloc[-1] if pd.notna(df[f].iloc[-1]) else 0.0
                elif f in ['hour', 'dayofyear', 'month']:
                    # Features temporales para mañana
                    if f == 'dayofyear':
                        entrada[f] = fecha_manana.timetuple().tm_yday
                    elif f == 'month':
                        entrada[f] = fecha_manana.month
                    elif f == 'hour':
                        entrada[f] = 12  # predicción del mediodía
                else:
                    entrada[f] = ultimo.get(f, 0.0)
            else:
                entrada[f] = 0.0
        
        entrada_df = pd.DataFrame([entrada])
        entrada_scaled = scaler_sens.transform(entrada_df)
        sens_termica_manana = float(modelo_sens.predict(entrada_scaled)[0])
    except Exception as e:
        sens_termica_manana = float(ultimo.get('sensacionTermica', 20))

    # ----------------------
    # Predicción de temperatura mañana (para calcular precipitación)
    # ----------------------
    temp_manana = float(ultimo.get('temp', 20.0))
    dwpt_manana = float(ultimo.get('dwpt', 15.0))
    rhum_manana = float(ultimo.get('rhum', 60.0))
    pres_manana = float(ultimo.get('pres', 1013.0))

    try:
        # Predecir temperatura con SVR
        modelo_temp, scaler_temp, features_temp = entrenar_modelo_svr(df, 'temp')
        entrada_temp = {}
        for f in features_temp:
            if f in df.columns:
                if f.startswith('temp_') or f.startswith('dwpt_') or f.startswith('rhum_') or f.startswith('pres_') or f.startswith('wspd_'):
                    entrada_temp[f] = df[f].iloc[-1] if pd.notna(df[f].iloc[-1]) else 0.0
                elif f in ['hour', 'dayofyear', 'month']:
                    if f == 'dayofyear':
                        entrada_temp[f] = fecha_manana.timetuple().tm_yday
                    elif f == 'month':
                        entrada_temp[f] = fecha_manana.month
                    elif f == 'hour':
                        entrada_temp[f] = 12  # predicción del mediodía
                else:
                    entrada_temp[f] = ultimo.get(f, 0.0)
            else:
                entrada_temp[f] = 0.0
        
        entrada_temp_df = pd.DataFrame([entrada_temp])
        entrada_temp_scaled = scaler_temp.transform(entrada_temp_df)
        temp_manana = float(modelo_temp.predict(entrada_temp_scaled)[0])
        
        # Predecir dwpt, rhum, pres de forma similar
        modelo_dwpt, scaler_dwpt, _ = entrenar_modelo_svr(df, 'dwpt')
        dwpt_manana = float(modelo_dwpt.predict(entrada_temp_scaled)[0])
        
        modelo_rhum, scaler_rhum, _ = entrenar_modelo_svr(df, 'rhum')
        rhum_manana = float(modelo_rhum.predict(entrada_temp_scaled)[0])
        
        modelo_pres, scaler_pres, _ = entrenar_modelo_svr(df, 'pres')
        pres_manana = float(modelo_pres.predict(entrada_temp_scaled)[0])
        
    except Exception:
        pass

    # ----------------------
    # Precipitación mañana usando función física (coherente con modelo_pronostico)
    # ----------------------
    precip_manana = calcular_precipitacion(temp_manana, dwpt_manana, rhum_manana, pres_manana)

    # Probabilidad de lluvia (basado en precipitación predicha)
    prob_lluvia = min(100, int((precip_manana / 5.0) * 100)) if precip_manana > 0.1 else 0

    # ----------------------
    # Nubosidad (basado en código climático y precipitación)
    # ----------------------
    coco_hoy = int(ultimo.get('coco', 1))
    
    # Determinar nivel de nubosidad
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
