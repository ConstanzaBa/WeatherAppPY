// Actualizar visuales usando los valores del JSON
export function updateVisuals(clima) {
  if (!clima) return;

  // VISIBILIDAD
try {
  const visibility = Number(clima.visibilidad ?? clima.visibilidad_km) || 0;
  const sky = document.getElementById("sky");
  const visStatus = document.getElementById("visStatus");
  if (!sky || !visStatus) return;

  const isDark = document.documentElement.classList.contains("dark-theme");

  const rootStyles = getComputedStyle(document.documentElement);
  const baseTop = rootStyles.getPropertyValue("--sky-good-top").trim();
  const baseBottom = rootStyles.getPropertyValue("--sky-good-bottom").trim();

  let status, cloudCount, colorTop, colorBottom;

  if (visibility < 2) {
    status = "Muy baja";
    cloudCount = 22;
    colorTop = isDark
      ? rootStyles.getPropertyValue("--sky-verylow-top")
      : rootStyles.getPropertyValue("--sky-verylow-bottom");
    colorBottom = isDark
      ? rootStyles.getPropertyValue("--sky-verylow-bottom")
      : rootStyles.getPropertyValue("--sky-verylow-top");
  } else if (visibility < 5) {
    status = "Reducida";
    cloudCount = 16;
    colorTop = rootStyles.getPropertyValue("--sky-low-top");
    colorBottom = rootStyles.getPropertyValue("--sky-low-bottom");
  } else if (visibility < 8) {
    status = "Moderada";
    cloudCount = 10;
    colorTop = rootStyles.getPropertyValue("--sky-medium-top");
    colorBottom = rootStyles.getPropertyValue("--sky-medium-bottom");
  } else {
    status = "Buena";
    cloudCount = 8;
    colorTop = baseTop;
    colorBottom = baseBottom;
  }

  visStatus.textContent = status;
  sky.style.background = `linear-gradient(to bottom, ${colorTop}, ${colorBottom})`;
  sky.innerHTML = "";

  const cloudShapes = [
    '<svg viewBox="0 0 64 32"><path d="M10 20c2-6 8-10 14-10 4 0 8 2 10 5 2-1 4-1 6-1 6 0 11 4 12 9 1 4-2 7-6 7H16c-5 0-8-4-6-10z"/></svg>',
    '<svg viewBox="0 0 64 32"><path d="M12 20c1-5 6-8 11-8 3 0 6 1 8 3 2-1 4-1 6-1 5 0 9 3 10 7 1 4-2 6-5 6H18c-4 0-7-3-6-7z"/></svg>',
    '<svg viewBox="0 0 64 32"><path d="M8 21c2-7 9-11 16-11 5 0 9 3 11 6 2-1 5-1 7-1 7 0 12 5 13 10 1 4-3 7-8 7H18c-6 0-10-4-10-11z"/></svg>',
  ];

  const cloudColors = [
    rootStyles.getPropertyValue("--cloud-light").trim(),
    rootStyles.getPropertyValue("--cloud-medium").trim(),
    rootStyles.getPropertyValue("--cloud-dark").trim(),
    "#ffffff",
    "#f0f8ff",
    "#e6f2ff",
  ];

  for (let i = 0; i < cloudCount; i++) {
    const cloud = document.createElement("div");
    cloud.classList.add("cloud");
    cloud.innerHTML =
      cloudShapes[Math.floor(Math.random() * cloudShapes.length)];
    const path = cloud.querySelector("path");
    if (path) {
      path.setAttribute(
        "fill",
        cloudColors[Math.floor(Math.random() * cloudColors.length)]
      );
      path.setAttribute("opacity", "0.9");
    }
    cloud.style.width = `${Math.random() * 80 + 70}px`;
    cloud.style.top = `${
      Math.random() * ((sky.clientHeight || 150) * 0.7 - 20) + 5
    }px`;
    cloud.style.left = `${Math.random() * 280 - 100}px`;
    cloud.style.animationDuration = `${14 + Math.random() * 10}s`;
    cloud.style.animationDelay = `${Math.random() * -20}s`;
    sky.appendChild(cloud);
  }
} catch (e) {
  console.error("Error al renderizar visibilidad:", e);
}


  // PRECIPITACIÓN
  try {
    const precipValue =
      clima.precipitacion ?? clima.precip_mm ?? clima.precip ?? 0;
    const precipitation = Number(precipValue) || 0;
    const hasValidPrecip =
      precipValue !== null &&
      precipValue !== undefined &&
      !isNaN(precipitation);

    const precipStatus = document.getElementById("precipStatus");
    const rainWater = document.getElementById("rainWater");
    const raindropsContainer = document.getElementById("raindrops");

    // Texto de estado
    if (precipStatus) {
      if (hasValidPrecip) {
        let status;
        if (precipitation === 0) status = "Sin lluvia";
        else if (precipitation < 2.5) status = "Llovizna";
        else if (precipitation < 10) status = "Lluvia ligera";
        else if (precipitation < 50) status = "Lluvia moderada";
        else if (precipitation < 100) status = "Lluvia intensa";
        else status = "Tormenta";
        precipStatus.textContent = status;
      } else if (clima.prob_precipitacion != null) {
        precipStatus.textContent = "Probabilidad";
      } else {
        precipStatus.textContent = "Sin datos";
      }
    }

    // Altura del agua
    if (rainWater) {
      const waterHeight = hasValidPrecip
        ? Math.min((precipitation / 100) * 100, 100)
        : 0;
      rainWater.style.height = waterHeight + "%";
    }

    // Gotas de lluvia animadas
    if (raindropsContainer) {
      raindropsContainer.innerHTML = "";

      if (hasValidPrecip && precipitation > 0) {
        // Aumentamos el número de gotas según intensidad
        const numDrops = Math.max(10, Math.floor((precipitation / 100) * 80));

        for (let i = 0; i < numDrops; i++) {
          const drop = document.createElement("div");
          drop.classList.add("raindrop");

          // Posición y animación aleatoria
          drop.style.left = Math.random() * 100 + "%";
          drop.style.animationDuration =
            (0.8 + Math.random() * 1.2).toFixed(2) + "s";
          drop.style.animationDelay = (Math.random() * 2).toFixed(2) + "s";

          raindropsContainer.appendChild(drop);
        }
      }
    }
  } catch (e) {
    console.warn("Error en animación de precipitación:", e);
  }

  // HUMEDAD
  try {
    const humidity = Number(clima.humedad ?? clima.hum ?? clima.humidity);
    if (Number.isNaN(humidity)) return;

    const humStatus = document.getElementById("humStatus");
    const progressRing = document.querySelector(".progress-ring");

    let status;
    if (humidity < 30) status = "Seco";
    else if (humidity < 60) status = "Moderado";
    else if (humidity < 85) status = "Húmedo";
    else status = "Condensado";
    if (humStatus) humStatus.textContent = status;

    if (progressRing) {
      const radius = progressRing.r.baseVal.value;
      const circumference = 2 * Math.PI * radius;
      progressRing.style.strokeDasharray = `${circumference} ${circumference}`;
      progressRing.style.strokeDashoffset =
        circumference - (humidity / 100) * circumference;
    }
  } catch (e) {}

  // SENSACIÓN TÉRMICA
  try {
    const actualTemp = Number(clima.temperatura ?? clima.temp ?? clima.t);
    const sensacion = Number(
      clima.sensacionTermica ??
        clima.sensacion ??
        clima.feels_like ??
        clima.therm
    );
    if (Number.isNaN(sensacion)) return;

    const diff = sensacion - (actualTemp || sensacion);
    const tempStatus = document.getElementById("tempStatus");
    const thermoFill = document.getElementById("thermoFill");
    const thermoBulb = document.getElementById("thermoBulb");

    let color, status;

    if (diff <= -5) {
      color = "linear-gradient(to top, #5c5cff, #a29bff)";
      status = "Mucho más frío";
    } else if (diff < -3) {
      color = "linear-gradient(to top, #b8b0ff, #e0dbff)";
      status = "Más frío";
    } else if (diff > 5) {
      color = "linear-gradient(to top, #ff6f91, #b347ff)";
      status = "Mucho más cálido";
    } else if (diff > 3) {
      color = "linear-gradient(to top, #ffb37f, #ff7f7f)";
      status = "Más cálido";
    } else {
      color = "linear-gradient(to top, #bfb4ff, #e8e4ff)";
      status = "Similar";
    }

    if (tempStatus) tempStatus.textContent = status;
    if (thermoFill) {
      thermoFill.style.height = Math.min((sensacion / 65) * 170, 170) + "px";
      thermoFill.style.background = color;
    }
    if (thermoBulb) {
      thermoBulb.style.background = color;
      thermoBulb.style.boxShadow =
        diff > 0
          ? "0 0 25px rgba(255,100,50,0.6)"
          : "0 0 25px rgba(100,150,255,0.6)";
    }
  } catch (e) {}

  // VIENTO
  try {
    const windSpeed = Number(
      clima.viento ?? clima.wind ?? clima.wind_kph ?? clima.wind_km
    );
    if (Number.isNaN(windSpeed)) return;

    const windValue = document.querySelector(".wind-value");
    const windStatus = document.getElementById("windStatus");
    const windBackground = document.getElementById("windBackground");

    if (windValue) {
      const pathLength = 251;
      windValue.style.strokeDasharray = pathLength;
      windValue.style.strokeDashoffset = pathLength;
      setTimeout(() => {
        windValue.style.strokeDashoffset =
          pathLength - Math.min(windSpeed / 100, 1) * pathLength;
      }, 100);
    }

    let desc;
    if (windSpeed < 5) desc = "Calma";
    else if (windSpeed < 15) desc = "Brisa ligera";
    else if (windSpeed < 30) desc = "Hay brisa";
    else if (windSpeed < 50) desc = "Viento fuerte";
    else desc = "Temporal";
    if (windStatus) windStatus.textContent = desc;

    // Crear animación de líneas de viento
    if (windBackground) {
      windBackground.innerHTML = ""; // Limpiar líneas anteriores

      // Calcular velocidad de animación basada en velocidad del viento
      // Viento más fuerte = animación más rápida
      let animationSpeed = 3; // velocidad base en segundos
      if (windSpeed < 5) animationSpeed = 6; // muy lento
      else if (windSpeed < 15) animationSpeed = 4; // lento
      else if (windSpeed < 30) animationSpeed = 2.5; // medio
      else if (windSpeed < 50) animationSpeed = 1.5; // rápido
      else animationSpeed = 1; // muy rápido

      // Calcular número de líneas basado en velocidad del viento
      let lineCount = Math.floor(windSpeed / 5) + 3;
      lineCount = Math.min(Math.max(lineCount, 3), 12); // entre 3 y 12 líneas

      for (let i = 0; i < lineCount; i++) {
        const line = document.createElement("div");
        line.classList.add("wind-line");

        // Posición vertical aleatoria
        line.style.top = `${Math.random() * 100}%`;

        // Ancho variable para las líneas
        const width = Math.random() * 150 + 80; // entre 80px y 230px
        line.style.width = `${width}px`;

        // Altura variable para simular diferentes intensidades
        const height = Math.random() * 2 + 1.5; // entre 1.5px y 3.5px
        line.style.height = `${height}px`;

        // Delay aleatorio para que no todas las líneas salgan al mismo tiempo
        line.style.animationDelay = `${Math.random() * animationSpeed}s`;

        // Aplicar la velocidad de animación
        line.style.animationDuration = `${animationSpeed}s`;

        // Opacidad variable
        line.style.opacity = Math.random() * 0.4 + 0.4; // entre 0.4 y 0.8

        windBackground.appendChild(line);
      }
    }
  } catch (e) {}

  // UV
  try {
    const uvVal = Number(clima.uvIndex ?? clima.uv ?? clima.uv_value);
    if (Number.isNaN(uvVal)) return;

    const uvCardEl = document.querySelector(".uv-card");
    if (uvCardEl) uvCardEl.dataset.uv = uvVal;

    const path = document.querySelector(".uv-value");
    const statusEl = document.getElementById("uvStatus");

    if (path) {
      const totalLength = 126;
      path.style.strokeDasharray = totalLength;
      path.style.strokeDashoffset = totalLength;
      setTimeout(() => {
        path.style.strokeDashoffset =
          totalLength * (1 - Math.min(uvVal / 11, 1));
      }, 200);

      let estado, descripcion;
      if (uvVal <= 2) {
        estado = "Bajo ";
      } else if (uvVal <= 5) {
        estado = "Moderado ";
      } else if (uvVal <= 7) {
        estado = "Alto ";
      } else if (uvVal <= 10) {
        estado = "Muy alto ";
      } else {
        estado = "Extremo ";
      }

      if (statusEl) statusEl.textContent = estado;
    }
  } catch (e) {}
}
