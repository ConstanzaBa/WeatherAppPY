"""
Script de predicción meteorológica del proyecto Clima Argentina.

Este script entrena modelos de Random Forest para predecir variables 
meteorológicas clave (temperatura, humedad relativa, presión y viento) 
y genera:
    - pronósticos de 7 días (lista de predicciones diarias)
    - resúmenes estilo "carousel" para web (resumen del primer día)
    
El flujo general es:
    1. Leer los datos históricos horarios por provincia.
    2. Generar features temporales y estacionales.
    3. Crear lags y medias móviles de las variables principales.
    4. Entrenar Random Forest para cada variable objetivo.
    5. Generar predicciones con ruido y percentiles históricos para realismo.
"""

# ============================
# Imports principales
# ============================
import numpy as np  # Para operaciones matemáticas, trigonométricas y generación de ruido
import pandas as pd  # Para manipulación de datos tipo DataFrame
from sklearn.ensemble import RandomForestRegressor  # Modelo de regresión basado en árboles
from datetime import date
from sklearn.preprocessing import StandardScaler  # Para escalar features
from parametros import asignar_estacion, calcular_coco, calcular_sensacion_termica
# - asignar_estacion: asigna estación del año según el mes
# - calcular_coco: calcula índice COCO (condición meteorológica)
# - calcular_sensacion_termica: calcula sensación térmica según temp, humedad y viento
from codclimatico import weather_icons, weather_descriptions
# - weather_icons: diccionario que mapea el código COCO a un archivo SVG con el ícono climático
# - weather_descriptions: diccionario que mapea el código COCO a una descripción textual legible del clima


# ============================
# Funciones
# ============================

def entrenar_modelo(df):
    """
    Entrena modelos Random Forest para predecir temperatura, humedad, presión y viento.

    Parámetros:
        df (pd.DataFrame): Datos históricos de clima de una provincia.
            Columnas esperadas: fecha_hora, temp, dwpt, rhum, pres, prcp, wspd, sensaciontermica, province

    Retorna:
        tuple: (modelos, scaler, features)
            - modelos (dict): Diccionario con RandomForestRegressor entrenados para cada variable
            - scaler (StandardScaler): Escalador ajustado a las features
            - features (list): Lista de nombres de features usadas en el modelo
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
    df = df.dropna(subset=["fecha_hora"])
    df = df.sort_values(["province","fecha_hora"])

    # ============================
    # Features temporales y estacionales
    # ============================
    df["month"] = df["fecha_hora"].dt.month
    df["dayofyear"] = df["fecha_hora"].dt.dayofyear
    df["hour"] = df["fecha_hora"].dt.hour
    df["estacion"] = df["month"].apply(asignar_estacion)
    df["sin_hour"] = np.sin(2*np.pi*df["hour"]/24)
    df["cos_hour"] = np.cos(2*np.pi*df["hour"]/24)
    df["sin_doy"] = np.sin(2*np.pi*df["dayofyear"]/365)
    df["cos_doy"] = np.cos(2*np.pi*df["dayofyear"]/365)

    # ============================
    # Lags y medias móviles
    # ============================
    lag_hours = [1,24,48]
    weather_cols = ["temp","dwpt","rhum","pres","prcp","wspd","sensaciontermica"]
    for col in weather_cols:
        for lag in lag_hours:
            df[f"{col}_lag{lag}"] = df.groupby("province")[col].shift(lag)
        df[f"{col}_roll24"] = df.groupby("province")[col].rolling(24,min_periods=1).mean().reset_index(level=0,drop=True)
        df[f"{col}_roll72"] = df.groupby("province")[col].rolling(72,min_periods=1).mean().reset_index(level=0,drop=True)

    # ============================
    # One-hot encoding de provincia y estación
    # ============================
    df["province"] = df["province"].astype(str)
    df = pd.get_dummies(df, columns=["province","estacion"], drop_first=True)

    # ============================
    # Definición de features
    # ============================
    features = ["temp","dwpt","rhum","pres","prcp","wspd","sensaciontermica",
                "hour","dayofyear","month","sin_hour","cos_hour","sin_doy","cos_doy"]
    for col in weather_cols:
        for lag in lag_hours:
            features.append(f"{col}_lag{lag}")
        features.append(f"{col}_roll24")
        features.append(f"{col}_roll72")
    features += [c for c in df.columns if c.startswith("province_") or c.startswith("estacion_")]

    # Rellenar valores nulos
    df = df.fillna(0)
    X = df[features].values

    # Targets
    y_temp = df["temp"].values
    y_rhum = df["rhum"].values
    y_pres = df["pres"].values
    y_wspd = df["wspd"].values

    # Escalado
    scaler = StandardScaler().fit(X)
    X_scaled = scaler.transform(X)

    # ============================
    # Entrenamiento Random Forest
    # ============================
    modelo_temp = RandomForestRegressor(n_estimators=500,min_samples_leaf=3,
                                        max_features="sqrt",random_state=42,n_jobs=-1).fit(X_scaled,y_temp)
    modelo_rhum = RandomForestRegressor(n_estimators=500,min_samples_leaf=3,
                                        max_features="sqrt",random_state=42,n_jobs=-1).fit(X_scaled,y_rhum)
    modelo_pres = RandomForestRegressor(n_estimators=500,min_samples_leaf=3,
                                        max_features="sqrt",random_state=42,n_jobs=-1).fit(X_scaled,y_pres)
    modelo_wspd = RandomForestRegressor(n_estimators=500,min_samples_leaf=3,
                                        max_features="sqrt",random_state=42,n_jobs=-1).fit(X_scaled,y_wspd)

    modelos = {"temp":modelo_temp,"rhum":modelo_rhum,"pres":modelo_pres,"wspd":modelo_wspd}

    return modelos, scaler, features

# ============================
# Predicción de 7 días
# ============================
def predecir_7dias(df, modelos, scaler, features, provincia):
    """
    Genera predicciones de 7 días para temperatura, humedad, presión, viento,
    precipitación, COCO y sensación térmica.

    Parámetros:
        df (pd.DataFrame): Datos históricos de la provincia
        modelos (dict): Modelos entrenados por entrenar_modelo
        scaler (StandardScaler): Escalador usado en el entrenamiento
        features (list): Lista de features usadas en el entrenamiento
        provincia (str): Nombre de la provincia

    Retorna:
        list[dict]: Lista de diccionarios, cada uno representando la predicción de un día:
            - province (str)
            - fecha (str, "YYYY-MM-DD")
            - temp_avg (float)
            - temp_high (float)
            - temp_low (float)
            - precip (float)
            - coco (int)
            - sensacion_termica (float)
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
    df = df.dropna(subset=["fecha_hora"])
    df = df.sort_values("fecha_hora")

    df["month"] = df["fecha_hora"].dt.month
    df["dayofyear"] = df["fecha_hora"].dt.dayofyear
    df["hour"] = df["fecha_hora"].dt.hour
    df["estacion"] = df["month"].apply(asignar_estacion)
    df["province"] = df["province"].astype(str)
    df = pd.get_dummies(df, columns=["province","estacion"], drop_first=True)

    ultimo = df.iloc[-1].copy()
    fecha_base = pd.Timestamp.now(tz="America/Argentina/Buenos_Aires").date()
    temp_stats_10 = df.groupby(['month','hour'])['temp'].quantile(0.10).to_dict()
    temp_stats_90 = df.groupby(['month','hour'])['temp'].quantile(0.90).to_dict()
    global_std = df['temp'].std() if not df['temp'].empty else 2.0

    predicciones = []

    for dia in range(7):
        fecha_pred = fecha_base + pd.Timedelta(days=dia)
        ultimo["month"] = fecha_pred.month
        ultimo["dayofyear"] = fecha_pred.timetuple().tm_yday
        ultimo["hour"] = 12
        ultimo["estacion"] = asignar_estacion(fecha_pred.month)
        ultimo["sin_hour"] = np.sin(2*np.pi*ultimo["hour"]/24)
        ultimo["cos_hour"] = np.cos(2*np.pi*ultimo["hour"]/24)
        ultimo["sin_doy"] = np.sin(2*np.pi*ultimo["dayofyear"]/365)
        ultimo["cos_doy"] = np.cos(2*np.pi*ultimo["dayofyear"]/365)

        # Completar dummies faltantes
        for col in [c for c in df.columns if c.startswith("province_") or c.startswith("estacion_")]:
            ultimo[col] = ultimo.get(col,0.0)

        X = np.array([ultimo.get(f,0.0) for f in features]).reshape(1,-1)
        X_scaled = scaler.transform(X)

        # Predicciones principales
        temp_pred = float(modelos["temp"].predict(X_scaled)[0])
        rhum_pred = float(modelos["rhum"].predict(X_scaled)[0])
        pres_pred = float(modelos["pres"].predict(X_scaled)[0])
        wspd_pred = float(modelos["wspd"].predict(X_scaled)[0])

        # Ruido para variabilidad realista
        if dia != 0:
            temp_pred += np.random.normal(0, global_std) + np.random.uniform(-1,1)

        # Punto de rocío
        try:
            a,b=17.27,237.7
            alpha = ((a*temp_pred)/(b+temp_pred)) + np.log(np.clip(rhum_pred,1,100)/100)
            dwpt_pred = (b*alpha)/(a-alpha)
        except:
            dwpt_pred = temp_pred-2

        # Precipitación
        humedad_factor = np.clip((rhum_pred-70)/30,0,1)
        presion_factor = np.clip((1018-pres_pred)/20,0,1)
        prob_lluvia = 0.5*humedad_factor + 0.5*presion_factor
        precip = round(prob_lluvia*3.0,1)
        if precip < 0.1: precip = 0.0

        # COCO y sensación térmica
        coco = calcular_coco(temp_pred,dwpt_pred,rhum_pred,pres_pred,precip)
        sens_term = calcular_sensacion_termica(temp_pred,rhum_pred,wspd_pred)

        # Temperaturas alta/baja usando percentiles históricos
        temp_high_hist = temp_stats_90.get((fecha_pred.month,12), temp_pred+global_std)
        temp_low_hist  = temp_stats_10.get((fecha_pred.month,12), temp_pred-global_std)
        temp_high = max(temp_pred,temp_high_hist) + np.random.uniform(0,2)
        temp_low  = min(temp_pred,temp_low_hist) + np.random.uniform(-2,0)

        predicciones.append({
            "province": provincia,
            "fecha": fecha_pred.strftime("%Y-%m-%d"),
            "temp_avg": round(temp_pred),
            "temp_high": round(temp_high),
            "temp_low": round(temp_low),
            "precip": precip,
            "coco": int(coco),
            "sensacion_termica": round(sens_term)
        })

        # Actualizar último registro para siguiente iteración
        ultimo["temp"] = temp_pred
        ultimo["dwpt"] = dwpt_pred
        ultimo["rhum"] = rhum_pred
        ultimo["pres"] = pres_pred
        ultimo["prcp"] = precip
        ultimo["wspd"] = wspd_pred

    return predicciones

# ============================
# Carousel
# ============================
def predecir_carousel(df, modelos, scaler, features, provincia):
    """
    Genera un carousel para la web usando la predicción del primer día.
    
    Utiliza los modelos entrenados y los datos históricos para:
        - Tomar la predicción del primer día (día 0)
        - Usar el código COCO ya calculado
        - Mapear COCO a descripción y porcentaje aproximado de nubosidad
        - Calcular probabilidad de lluvia, sensación térmica y nubosidad para el carousel

    Parámetros:
        df (pd.DataFrame): Datos históricos de la provincia
        modelos (dict): Diccionario con los modelos Random Forest entrenados
        scaler (StandardScaler): Escalador usado en el entrenamiento
        features (list): Lista de features utilizadas por los modelos
        provincia (str): Nombre de la provincia para la predicción

    Retorna:
        dict: Diccionario con la predicción resumida del primer día, incluyendo:
            - probabilidad_lluvia (int): Porcentaje estimado de lluvia
            - sensacion_termica (float): Sensación térmica
            - nubosidad (str): Descripción textual del clima
            - nubosidad_porcentaje (int): Porcentaje aproximado de nubosidad
            - icono (str): Nombre del archivo SVG correspondiente al clima
            - metadata (dict): Información de fechas
                - fecha_prediccion (str): Fecha de la predicción
                - fecha_generacion (str): Fecha y hora de generación del resumen
    """
    # Obtener la predicción de 7 días
    pred_7dias = predecir_7dias(df, modelos, scaler, features, provincia)
    dia1 = pred_7dias[0]  # Tomamos el primer día para el carousel

    # Tomar el código COCO ya calculado en predecir_7dias
    coco_val = dia1["coco"]

    # Calcular nubosidad basada en variables meteorológicas reales de la provincia
    # Obtener datos del último registro para extraer humedad y presión predichas
    df_copy = df.copy()
    df_copy.columns = df_copy.columns.str.strip().str.lower()
    df_copy["fecha_hora"] = pd.to_datetime(df_copy["fecha_hora"], errors="coerce")
    df_copy = df_copy.dropna(subset=["fecha_hora"]).sort_values("fecha_hora")
    
    ultimo = df_copy.iloc[-1]
    precip = dia1["precip"]
    
    # Re-predecir humedad y presión para este día (ya se hizo en predecir_7dias pero no se devolvió)
    # Como alternativa, usamos una estimación basada en COCO y precipitación
    
    # Factor de precipitación (más lluvia = más nubosidad)
    precip_factor = min(precip / 10.0, 1.0)  # Escala hasta 10mm
    
    # Factor de COCO (códigos altos = más nubosidad)
    if coco_val >= 7:  # Lluvia
        coco_factor = 1.0
    elif coco_val >= 3:  # Nublado
        coco_factor = 0.7
    elif coco_val == 2:  # Parcialmente nublado
        coco_factor = 0.4
    else:  # Despejado
        coco_factor = 0.1
    
    # Combinar factores para calcular porcentaje de nubosidad
    nub_pct = int(round(precip_factor * 40 + coco_factor * 60))
    nub_pct = min(max(nub_pct, 0), 100)  # Limitar entre 0-100
    
    # Determinar descripción textual basada en nubosidad calculada
    if nub_pct >= 80:
        descripcion = "Muy nublado"
    elif nub_pct >= 60:
        descripcion = "Nublado"
    elif nub_pct >= 30:
        descripcion = "Parcialmente nublado"
    else:
        descripcion = "Despejado"
    
    # Si hay lluvia, priorizar descripción de lluvia
    if precip >= 5.0:
        descripcion = weather_descriptions.get(coco_val, descripcion)

    # Mapear COCO a icono SVG
    icono_svg = weather_icons.get(coco_val, "cloudy.svg")

    # Devolver el resumen estilo carousel
    return {
        "probabilidad_lluvia": int(round(dia1["precip"] / 3.0 * 100)),  # Escala a %
        "sensacion_termica": dia1["sensacion_termica"],
        "nubosidad": descripcion,
        "nubosidad_porcentaje": nub_pct,
        "icono": icono_svg,
        "metadata": {
            "fecha_prediccion": dia1["fecha"],
            "fecha_generacion": pd.Timestamp.now(tz="America/Argentina/Buenos_Aires").strftime("%Y-%m-%d %H:%M:%S")
        }
    }
