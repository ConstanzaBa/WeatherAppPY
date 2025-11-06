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

export { calcularSensacionTermica };