// sensación térmica estimada a partir de datos de Meteostat
// temperatura
// velocidad del viento
// humedad relativa
function calcularSensacionTermica(tempC, humedad, vientoKmh) {
  if (tempC === null || humedad === null || vientoKmh === null) return null;

  // Si hace frío: fórmula de Wind Chill (válida ≤ 10°C)
  if (tempC <= 10 && vientoKmh >= 4.8) {
    const st =
      13.12 +
      0.6215 * tempC -
      11.37 * Math.pow(vientoKmh, 0.16) +
      0.3965 * tempC * Math.pow(vientoKmh, 0.16);
    return parseFloat(st.toFixed(1));
  }

  // Si hace calor: fórmula de Heat Index (válida > 10°C)
  const tempF = (tempC * 9) / 5 + 32;
  const HI =
    -42.379 +
    2.04901523 * tempF +
    10.14333127 * humedad -
    0.22475541 * tempF * humedad -
    0.00683783 * Math.pow(tempF, 2) -
    0.05481717 * Math.pow(humedad, 2) +
    0.00122874 * Math.pow(tempF, 2) * humedad +
    0.00085282 * tempF * Math.pow(humedad, 2) -
    0.00000199 * Math.pow(tempF, 2) * Math.pow(humedad, 2);

  const hiC = ((HI - 32) * 5) / 9;
  return parseFloat(hiC.toFixed(1));
}

// Estimar radiación UV según hora, nubosidad (coco) y temperatura
function calcularRadiacionUV(tempC, coco, fechaHoraStr) {
  if (tempC === null || coco === null) return null;

  // Determinar hora local
  const hora = new Date(fechaHoraStr || Date.now()).getHours();

  // Base UV por hora (máximo al mediodía)
  let baseUV = 0;
  if (hora >= 10 && hora <= 15) {
    baseUV = 8; // rango máximo típico en Argentina
  } else if (hora >= 8 && hora < 10 || hora > 15 && hora <= 17) {
    baseUV = 4;
  } else {
    baseUV = 1; // noche o amanecer
  }

  // Ajuste por nubosidad según código "coco"
  // (aproximación: 1=despejado, 2=few, 3=cloudy, 7=rain, 17=heavy rain)
  let factorNubosidad = 0;
  if ([1, 2].includes(coco)) factorNubosidad = 0;      // despejado
  else if (coco === 3) factorNubosidad = 0.3;          // nublado
  else if ([7, 17].includes(coco)) factorNubosidad = 0.6; // lluvia
  else factorNubosidad = 0.4;                          // intermedio

  // Ajuste leve por temperatura (más alta, más radiación)
  const tempFactor = Math.min(Math.max((tempC - 10) / 15, 0.8), 1.2);

  const uv = baseUV * (1 - factorNubosidad) * tempFactor;
  return parseFloat(uv.toFixed(1));
}

export { calcularSensacionTermica, calcularRadiacionUV };