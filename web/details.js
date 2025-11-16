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
      cloud.style.top = `${Math.random() * ((sky.clientHeight || 150) * 0.7 - 20) + 5
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
    const rainGlass = document.getElementById("rainGlass");

    // USAMOS VARIABLES CSS DEL ROOT SEGÚN TEMA
    const rootStyles = getComputedStyle(document.documentElement);

    if (rainGlass && hasValidPrecip) {
      let topVar, bottomVar;

      if (precipitation === 0) {
        topVar = "--sky-good-top";
        bottomVar = "--sky-good-bottom";
      } else if (precipitation < 10) {
        topVar = "--sky-medium-top";
        bottomVar = "--sky-medium-bottom";
      } else if (precipitation < 50) {
        topVar = "--sky-low-top";
        bottomVar = "--sky-low-bottom";
      } else {
        topVar = "--sky-verylow-top";
        bottomVar = "--sky-verylow-bottom";
      }

      const topColor = rootStyles.getPropertyValue(topVar).trim();
      const bottomColor = rootStyles.getPropertyValue(bottomVar).trim();

      rainGlass.style.background = `linear-gradient(to bottom, ${topColor}, ${bottomColor})`;
    }

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

    // Gotas de lluvia
    if (raindropsContainer) {
      raindropsContainer.innerHTML = "";

      if (hasValidPrecip && precipitation > 0) {
        const numDrops = Math.max(10, Math.floor((precipitation / 100) * 80));

        for (let i = 0; i < numDrops; i++) {
          const drop = document.createElement("div");
          drop.classList.add("raindrop");

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

  //HUMEDAD

  // HUMEDAD
  try {
    const humidity = Number(clima.humedad ?? clima.hum ?? clima.humidity);
    if (Number.isNaN(humidity)) return;

    const humStatus = document.getElementById("humStatus");
    const humiditySky = document.getElementById("humiditySky");

    const rootStyles = getComputedStyle(document.documentElement);

    let topVar, bottomVar, status;

    if (humidity < 30) {
      status = "Seco";
      topVar = "--sky-good-top";
      bottomVar = "--sky-good-bottom";
    } else if (humidity < 60) {
      status = "Moderado";
      topVar = "--sky-medium-top";
      bottomVar = "--sky-medium-bottom";
    } else if (humidity < 85) {
      status = "Húmedo";
      topVar = "--sky-low-top";
      bottomVar = "--sky-low-bottom";
    } else {
      status = "Condensado";
      topVar = "--sky-verylow-top";
      bottomVar = "--sky-verylow-bottom";
    }

    const topColor = rootStyles.getPropertyValue(topVar).trim();
    const bottomColor = rootStyles.getPropertyValue(bottomVar).trim();

    if (humStatus) humStatus.textContent = status;

    if (humiditySky) {
      humiditySky.style.background = `linear-gradient(to bottom, ${topColor}, ${bottomColor})`;

      humiditySky.innerHTML = ""; // limpiar vapor

      const numParticles = Math.max(5, Math.floor((humidity / 100) * 25));

      for (let i = 0; i < numParticles; i++) {
        const particle = document.createElement("div");
        particle.className = "vapor-particle";

        const size = 15 + Math.random() * 25;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;

        particle.style.left = `${Math.random() * 100}%`;
        particle.style.bottom = "-20px";

        particle.style.animationDuration = `${4 + Math.random() * 4}s`;
        particle.style.animationDelay = `${Math.random() * 3}s`;

        humiditySky.appendChild(particle);
      }
    }
  } catch (e) {
    console.error("Error en animación de humedad:", e);
  }


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
  } catch (e) { }

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

    // Definir colores según la intensidad del viento
    const isDark = document.documentElement.classList.contains("dark-theme");
    const rootStyles = getComputedStyle(document.documentElement);
    const baseTop = rootStyles.getPropertyValue("--sky-good-top").trim();
    const baseBottom = rootStyles.getPropertyValue("--sky-good-bottom").trim();

    let desc, colorTop, colorBottom;

    if (windSpeed < 5) {
      // Calma - usa los colores de "Buena" visibilidad
      desc = "Calma";
      colorTop = baseTop;
      colorBottom = baseBottom;
    } else if (windSpeed < 15) {
      // Brisa ligera - usa los colores de "Moderada" visibilidad
      desc = "Brisa ligera";
      colorTop = rootStyles.getPropertyValue("--sky-medium-top").trim();
      colorBottom = rootStyles.getPropertyValue("--sky-medium-bottom").trim();
    } else if (windSpeed < 30) {
      // Hay brisa - usa los colores de "Reducida" visibilidad
      desc = "Hay brisa";
      colorTop = rootStyles.getPropertyValue("--sky-low-top").trim();
      colorBottom = rootStyles.getPropertyValue("--sky-low-bottom").trim();
    } else if (windSpeed < 50) {
      // Viento fuerte - usa los colores de "Muy baja" visibilidad
      desc = "Viento fuerte";
      colorTop = isDark
        ? rootStyles.getPropertyValue("--sky-verylow-top").trim()
        : rootStyles.getPropertyValue("--sky-verylow-bottom").trim();
      colorBottom = isDark
        ? rootStyles.getPropertyValue("--sky-verylow-bottom").trim()
        : rootStyles.getPropertyValue("--sky-verylow-top").trim();
    } else {
      // Temporal - usa tonos aún más oscuros
      desc = "Temporal";
      colorTop = isDark
        ? rootStyles.getPropertyValue("--sky-verylow-top").trim()
        : rootStyles.getPropertyValue("--sky-verylow-bottom").trim();
      colorBottom = isDark
        ? rootStyles.getPropertyValue("--sky-verylow-bottom").trim()
        : rootStyles.getPropertyValue("--sky-verylow-top").trim();
    }

    if (windStatus) windStatus.textContent = desc;

    // Crear animación de líneas de viento
    if (windBackground) {
      windBackground.innerHTML = ""; // Limpiar líneas anteriores

      // Aplicar el color de fondo según la intensidad
      windBackground.style.background = `linear-gradient(135deg, ${colorTop} 0%, ${colorBottom} 100%)`;

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
  } catch (e) { }

  // UV
  try {
    const uvVal = Number(clima.uvIndex ?? clima.uv ?? clima.uv_value);
    if (Number.isNaN(uvVal)) return;

    const uvCardEl = document.querySelector(".uv-card");
    if (uvCardEl) uvCardEl.dataset.uv = uvVal;

    const uvValueEl = document.getElementById("uvValue");
    const statusEl = document.getElementById("uvStatus");
    const uvSky = document.getElementById("uvSky");

    // Actualizar el valor numérico del índice UV
    if (uvValueEl) uvValueEl.textContent = uvVal;

    // Determinar el estado según el valor UV
    let estado;
    if (uvVal <= 2) {
      estado = "Bajo";
    } else if (uvVal <= 5) {
      estado = "Moderado";
    } else if (uvVal <= 7) {
      estado = "Alto";
    } else if (uvVal <= 10) {
      estado = "Muy alto";
    } else {
      estado = "Extremo";
    }

    if (statusEl) statusEl.textContent = estado;

    // Animación visual del UV (sol y nubes)
    if (uvSky) {
      uvSky.innerHTML = "";

      const rootStyles = getComputedStyle(document.documentElement);
      const baseTop = rootStyles.getPropertyValue("--sky-good-top").trim();
      const baseBottom = rootStyles.getPropertyValue("--sky-good-bottom").trim();
      const isDark = document.documentElement.classList.contains("dark-theme");

      // Color del cielo según intensidad UV usando las mismas variables que visibilidad
      let skyColorTop, skyColorBottom;
      if (uvVal <= 2) {
        // UV bajo - usa colores de "Muy baja" visibilidad (más gris/nublado)
        skyColorTop = isDark
          ? rootStyles.getPropertyValue("--sky-verylow-top").trim()
          : rootStyles.getPropertyValue("--sky-verylow-bottom").trim();
        skyColorBottom = isDark
          ? rootStyles.getPropertyValue("--sky-verylow-bottom").trim()
          : rootStyles.getPropertyValue("--sky-verylow-top").trim();
      } else if (uvVal <= 5) {
        // UV moderado - usa colores de "Reducida" visibilidad
        skyColorTop = rootStyles.getPropertyValue("--sky-low-top").trim();
        skyColorBottom = rootStyles.getPropertyValue("--sky-low-bottom").trim();
      } else if (uvVal <= 7) {
        // UV alto - usa colores de "Moderada" visibilidad
        skyColorTop = rootStyles.getPropertyValue("--sky-medium-top").trim();
        skyColorBottom = rootStyles.getPropertyValue("--sky-medium-bottom").trim();
      } else {
        // UV muy alto/extremo - usa colores de "Buena" visibilidad (cielo más despejado)
        skyColorTop = baseTop;
        skyColorBottom = baseBottom;
      }

      uvSky.style.background = `linear-gradient(to bottom, ${skyColorTop}, ${skyColorBottom})`;

      // Determinar si es de noche (20:00 a 07:00)
      const fechaHora = clima.fecha_hora ?? new Date().toISOString();
      const hora = new Date(fechaHora).getHours();
      const esNoche = hora >= 20 || hora < 7;

      // Crear el sol o la luna según la hora
      const celestialBody = document.createElement("div");

      if (esNoche) {
        // Es de noche - mostrar luna
        celestialBody.classList.add("uv-moon");

        // Posición de la luna (más baja en la noche)
        const moonHeight = 20; // Posición fija para la luna
        celestialBody.style.top = `${moonHeight}%`;

        // Tamaño de la luna
        const moonSize = 35;
        celestialBody.style.width = `${moonSize}px`;
        celestialBody.style.height = `${moonSize}px`;

        // Brillo suave de la luna (resplandor plateado suave)
        celestialBody.style.boxShadow = `0 0 20px 8px rgba(220, 230, 255, 0.5)`;
      } else {
        // Es de día - mostrar sol
        celestialBody.classList.add("uv-sun");

        // Posición del sol según intensidad UV (más alto = más UV)
        const sunHeight = Math.max(10, Math.min(50, uvVal * 5)); // 10% a 50% desde arriba
        celestialBody.style.top = `${sunHeight}%`;

        // Tamaño e intensidad del sol según UV
        const sunSize = 30 + (uvVal * 3); // 30px a 60px
        celestialBody.style.width = `${sunSize}px`;
        celestialBody.style.height = `${sunSize}px`;

        // Brillo del sol según UV (color amarillo pastel suave)
        const glowIntensity = Math.min(uvVal * 2, 20);
        celestialBody.style.boxShadow = `0 0 ${glowIntensity}px ${glowIntensity / 2}px rgba(255, 245, 157, 0.7)`;
      }

      uvSky.appendChild(celestialBody);

      // Nubes según código climático (si está disponible)
      const coco = Number(clima.coco ?? clima.condition_code);
      let cloudCount = 0;
      let cloudOpacity = 0.7;

      if (!Number.isNaN(coco)) {
        if (coco >= 1 && coco <= 2) {
          // Despejado
          cloudCount = Math.max(0, 3 - Math.floor(uvVal / 3));
          cloudOpacity = 0.3;
        } else if (coco >= 3 && coco <= 4) {
          // Parcialmente nublado
          cloudCount = 5;
          cloudOpacity = 0.6;
        } else if (coco >= 5 && coco <= 6) {
          // Niebla
          cloudCount = 10;
          cloudOpacity = 0.8;
        } else if (coco >= 7 && coco <= 27) {
          // Lluvia, nieve, tormentas
          cloudCount = 12;
          cloudOpacity = 0.9;
        }
      } else {
        // Si no hay coco, inferir por UV
        cloudCount = Math.max(2, 10 - Math.floor(uvVal * 1.5));
        cloudOpacity = 0.5;
      }

      // Crear nubes
      const cloudShapes = [
        '<svg viewBox="0 0 64 32"><path d="M10 20c2-6 8-10 14-10 4 0 8 2 10 5 2-1 4-1 6-1 6 0 11 4 12 9 1 4-2 7-6 7H16c-5 0-8-4-6-10z"/></svg>',
        '<svg viewBox="0 0 64 32"><path d="M12 20c1-5 6-8 11-8 3 0 6 1 8 3 2-1 4-1 6-1 5 0 9 3 10 7 1 4-2 6-5 6H18c-4 0-7-3-6-7z"/></svg>',
      ];

      for (let i = 0; i < cloudCount; i++) {
        const cloud = document.createElement("div");
        cloud.classList.add("uv-cloud");
        cloud.innerHTML = cloudShapes[Math.floor(Math.random() * cloudShapes.length)];

        const path = cloud.querySelector("path");
        if (path) {
          path.setAttribute("fill", "#ffffff");
          path.setAttribute("opacity", cloudOpacity);
        }

        cloud.style.width = `${Math.random() * 50 + 40}px`;
        cloud.style.top = `${Math.random() * 60 + 5}%`;
        cloud.style.left = `${Math.random() * 200 - 50}px`;
        cloud.style.animationDuration = `${15 + Math.random() * 10}s`;
        cloud.style.animationDelay = `${Math.random() * -20}s`;

        uvSky.appendChild(cloud);
      }
    }
  } catch (e) { }
}
