"""
Biblioteca de mapeo de códigos meteorológicos COCO a iconos y descripciones.

Este módulo permite traducir los códigos meteorológicos estándar COCO en:
    - iconos SVG para visualización en la web o aplicaciones,
    - descripciones de texto legibles para usuarios.

Entradas:
    No recibe parámetros directamente.
    Se accede a los diccionarios `weather_icons` y `weather_descriptions`.

Salidas:
    - weather_icons (dict[int, str]): Mapea el código COCO al nombre del archivo SVG correspondiente.
    - weather_descriptions (dict[int, str]): Mapea el código COCO a la descripción textual del clima.

Uso típico:
    from esta_biblioteca import weather_icons, weather_descriptions

    icono = weather_icons[8]             # "rain.svg"
    descripcion = weather_descriptions[8] # "Lluvia"
"""

# =============================================================
# Íconos asociados a cada código de condición climática (COCO)
# =============================================================
# Diccionario que relaciona cada código COCO con un archivo SVG
# representando visualmente la condición climática.
weather_icons = {
    1: "clear.svg",
    2: "fair.svg",
    3: "cloudy.svg",
    4: "overcast.svg",
    5: "fog.svg",
    6: "freezing_fog.svg",
    7: "light_rain.svg",
    8: "rain.svg",
    9: "heavy_rain.svg",
    10: "freezing_rain.svg",
    11: "heavy_sleet.svg",
    12: "sleet.svg",
    13: "heavy_sleet.svg",
    14: "light_snowfall.svg",
    15: "snowfall.svg",
    16: "heavy_snowfall.svg",
    17: "rain.svg",
    18: "heavy_rain.svg",
    19: "sleet.svg",
    20: "heavy_sleet.svg",
    21: "light_snowfall.svg",
    22: "heavy_snowfall.svg",
    23: "lightning.svg",
    24: "hail.svg",
    25: "thunderstorms.svg",
    26: "heavy_thunderstorm.svg",
    27: "storm.svg",
    28: "wind.svg"
}

# =============================================================
# Descripciones de cada código COCO
# =============================================================
# Diccionario que proporciona la descripción en texto de cada
# condición climática, útil para mostrar en la interfaz de usuario.
weather_descriptions = {
    1: "Despejado",
    2: "Parcialmente despejado",
    3: "Nublado",
    4: "Cubierto",
    5: "Niebla",
    6: "Niebla helada",
    7: "Lluvia ligera",
    8: "Lluvia",
    9: "Lluvia intensa",
    10: "Lluvia helada",
    11: "Lluvia helada intensa",
    12: "Aguanieve",
    13: "Aguanieve intensa",
    14: "Nevada ligera",
    15: "Nevada",
    16: "Nevada intensa",
    17: "Chubasco de lluvia",
    18: "Chubasco de lluvia intensa",
    19: "Chubasco de aguanieve",
    20: "Chubasco de aguanieve intensa",
    21: "Chubasco de nieve",
    22: "Chubasco de nieve intensa",
    23: "Relámpagos",
    24: "Granizo",
    25: "Tormenta eléctrica",
    26: "Tormenta eléctrica fuerte",
    27: "Tormenta"
}