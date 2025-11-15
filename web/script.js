import { updateVisuals } from './details.js';

document.addEventListener("DOMContentLoaded", async () => {
  const cardMapa = document.querySelector(".card.mapa");
  const cardInfo = document.querySelector(".card.info");
  const cardLoader = document.querySelector(".card.loader");
  const svgMapa = document.getElementById("mapa-argentina");

  // variable global para provincia activa
  window.provinciaActual = null;

  // normalizar nombres
  const normalize = (str) => {
    return str
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, "_");
  };

  // variables principales
  let climaData = [];
  let climaPorProvincia = {};
  let climaHorarioPorProvincia = {};
  let iconos = [];
  let infoHtmlTemplate = "";

  // iconos detalle
  const detailIconMap = {
    Humedad: "humidity.svg",
    Viento: "wind.svg",
    Visibilidad: "fog.svg",
    "Sensación Térmica": "thermometer-sun.svg",
    Precipitación: "rain.svg",
    "Radiación UV": "uv-index.svg",
  };

  function getIconFilename(clima) {
    if (!clima) return "clear.svg";
    if (clima.icono) return clima.icono;
    const code = Number(clima.coco);
    if (!Number.isNaN(code) && typeof weatherIcons !== "undefined") {
      return weatherIcons[code] || "clear.svg";
    }
    return "clear.svg";
  }

  // cargar plantilla info.html
  async function cargarTemplateInfo() {
    try {
      const response = await fetch("info.html");
      const html = await response.text();
      const container = document.createElement("div");
      container.innerHTML = html;
      const containerEl = container.querySelector('.container');
      if (containerEl) {
        // Intentar cargar el partial de detalles dinámicamente (si existe)
        try {
          const detailsResp = await fetch('partials/details.html');
          if (detailsResp.ok) {
            const detailsHtml = await detailsResp.text();
            const detailsTemp = document.createElement('div');
            detailsTemp.innerHTML = detailsHtml;
            const detailsEl = detailsTemp.querySelector('.weather-details') || detailsTemp.firstElementChild;
            if (detailsEl) {
              const existing = containerEl.querySelector('.weather-details');
              // reemplazar el bloque de detalles por el partial cargado
              if (existing) existing.replaceWith(detailsEl.cloneNode(true));
              else containerEl.appendChild(detailsEl.cloneNode(true));
            }
          }
        } catch (err) {
          console.warn('No se pudo cargar partial details:', err);
        }
        infoHtmlTemplate = containerEl.outerHTML;
      }
    } catch (err) {
      console.error("Error al cargar info.html:", err);
    }
  }

  // cargar datos clima actual
  async function cargarClima() {
    const response = await fetch("clima_actual.json?cache=" + Date.now());
    const data = await response.json();
    climaPorProvincia = {};
    data.forEach((item) => {
      climaPorProvincia[normalize(item.provincia)] = item;
    });
    climaData = data;
  }

  // cargar datos clima horario
  async function cargarClimaHorario() {
    try {
      const response = await fetch("clima_horario.json?cache=" + Date.now());
      const data = await response.json();
      climaHorarioPorProvincia = {};
      Object.keys(data).forEach((provincia) => {
        climaHorarioPorProvincia[normalize(provincia)] = data[provincia];
      });
      console.log("Clima horario cargado:", climaHorarioPorProvincia);
    } catch (err) {
      console.error("Error al cargar clima_horario.json:", err);
      climaHorarioPorProvincia = {};
    }
  }

  // inicializar
  async function inicializar() {
    await cargarTemplateInfo();
    await cargarClima();
    await cargarClimaHorario();
    colocarIconos();
  }

  // colocar iconos en el mapa
  const labels = document.querySelectorAll("#label_points circle");

  function colocarIconos() {
    iconos.forEach((icon) => icon.remove());
    iconos = [];

    labels.forEach((label) => {
      const provincia = normalize(label.getAttribute("data-provincia"));
      const clima = climaPorProvincia[provincia];
      if (!clima) return;

      const svgImage = document.createElementNS("http://www.w3.org/2000/svg", "image");
      const iconFilename = getIconFilename(clima);

      svgImage.setAttributeNS(null, "href", `img/weather/${iconFilename}`);
      svgImage.setAttributeNS(null, "width", "45");
      svgImage.setAttributeNS(null, "height", "45");

      const cx = label.cx.baseVal.value;
      const cy = label.cy.baseVal.value;

      svgImage.setAttributeNS(null, "x", cx - 24);
      svgImage.setAttributeNS(null, "y", cy - 24);
      svgImage.classList.add("icono-clima");
      svgImage.style.pointerEvents = "none";

      svgMapa.appendChild(svgImage);
      iconos.push(svgImage);
    });
  }

  // pronóstico horario
  function actualizarPronosticoHorario(provincia) {
    const hourlyContainer = cardInfo.querySelector(".hourly-container");
    if (!hourlyContainer) return;

    const provinciaKey = normalize(provincia);
    const horasData = climaHorarioPorProvincia[provinciaKey];

    if (!horasData || horasData.length === 0) {
      hourlyContainer.innerHTML =
        '<p style="text-align: center; color: #666;">No hay datos horarios disponibles</p>';
      return;
    }

    hourlyContainer.innerHTML = "";

    horasData.forEach((hora) => {
      const hourlyItem = document.createElement("div");
      hourlyItem.className = "hourly-item";

      const timeDiv = document.createElement("div");
      timeDiv.className = "time";
      timeDiv.textContent = hora.time;

      const iconDiv = document.createElement("div");
      iconDiv.className = "hour-icon";
      const iconImg = document.createElement("img");
      iconImg.src = `img/weather/${hora.icon}`;
      iconImg.alt = hora.time;
      iconImg.width = 35;
      iconImg.height = 35;
      iconDiv.appendChild(iconImg);

      const tempDiv = document.createElement("div");
      tempDiv.className = "temp";
      tempDiv.textContent = `${hora.temp}°`;

      hourlyItem.appendChild(timeDiv);
      hourlyItem.appendChild(iconDiv);
      hourlyItem.appendChild(tempDiv);
      hourlyContainer.appendChild(hourlyItem);
    });
  }

  // actualizar datos de una provincia
  function actualizarDatosProvincia(nombre, clima) {
    const tituloProvincia = cardInfo.querySelector(".titulo-provincia");
    const horaProvincia = cardInfo.querySelector(".hora-provincia");
    if (tituloProvincia) {
      const ahora = new Date();
      const diaSemana = ahora.toLocaleDateString('es-AR', { weekday: 'long' });
      // Capitalizar primera letra
      tituloProvincia.textContent = diaSemana.charAt(0).toUpperCase() + diaSemana.slice(1);
    }
    if (horaProvincia && clima) {
      const ahora = new Date();
      horaProvincia.textContent = ahora.toLocaleTimeString("es-AR", {
        hour: "2-digit",
        minute: "2-digit",
      });
    }

    if (clima) {
      const tempActual = cardInfo.querySelector(".temperature");
      if (tempActual) tempActual.textContent = `${clima.temperatura}°`;

      const condition = cardInfo.querySelector(".condition");
      if (condition) condition.textContent = clima.condicion || "Despejado";

      const weatherIcon = cardInfo.querySelector(".weather-icon");
      if (weatherIcon) {
        const iconFilename = getIconFilename(clima);
        weatherIcon.innerHTML = `<img src="img/weather/${iconFilename}" alt="${clima.coco ?? ""}" width="75" height="75" class="weather-icon-img">`;
      }

      // Actualizar valores básicos directamente (fallback si updateVisuals falla)
      const humValue = document.getElementById('humValue');
      const windSpeed = document.getElementById('windSpeed');
      const visValue = document.getElementById('visValue');
      const tempValue = document.getElementById('tempValue');
      const precipValue = document.getElementById('precipValue');
      const uvNumber = document.getElementById('uvNumber');

      if (humValue) humValue.textContent = `${clima.humedad}%`;
      if (windSpeed) windSpeed.textContent = `${clima.viento} km/h`;
      if (visValue) visValue.textContent = clima.visibilidad?.toFixed(1) || '0';
      if (tempValue) tempValue.textContent = `${clima.sensacionTermica}°C`;
      if (precipValue) precipValue.textContent = `${clima.precipitacion ?? 0} mm`;
      if (uvNumber) uvNumber.textContent = `${clima.uvIndex}`;

      // iconos de detalle
      const detailItems = cardInfo.querySelectorAll(".detail-item");
      detailItems.forEach((item) => {
        const labelEl = item.querySelector(".label");
        const iconEl = item.querySelector(".icon");
        if (!labelEl || !iconEl) return;
        const label = labelEl.textContent.trim();
        const iconFilename = detailIconMap[label];
        if (iconFilename) {
          iconEl.innerHTML = `<img src="img/weather/${iconFilename}" alt="${label}" width="30" height="30" class="detail-icon-img">`;
        }
      });

      // Actualizar gráfico de temperatura
      const chartImg = cardInfo.querySelector("#temperature-chart");
      if (chartImg) {
        const normalizedName = normalize(nombre);
        chartImg.src = `img/graphs/temp_chart_${normalizedName}.png?cache=${Date.now()}`;
        chartImg.alt = `Gráfico de temperatura de ${nombre}`;
      }

      // Actualizar animaciones visuales con un pequeño delay para asegurar que el DOM esté listo
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          updateVisuals(clima);
        });
      });
    }

    actualizarPronosticoHorario(nombre);
  }

  // evento click en provincias
  const provincias = document.querySelectorAll("#mapa-argentina path[id^='AR']");
  provincias.forEach((provinciaEl) => {
    provinciaEl.addEventListener("click", async () => {
      const nombre = provinciaEl.getAttribute("name");
      const clima = climaPorProvincia[normalize(nombre)];

      // guardar la provincia actual globalmente
      window.provinciaActual = nombre;
      if (typeof actualizarNombreProvincia === "function") {
        actualizarNombreProvincia(nombre);
      }

      cardMapa.style.display = "none";
      cardInfo.style.display = "none";
      cardLoader.style.display = "flex";

      const loaderStart = Date.now();
      await cargarClima();
      await cargarClimaHorario();
      colocarIconos();

      cardInfo.innerHTML = infoHtmlTemplate;
      actualizarDatosProvincia(nombre, clima);

      const elapsed = Date.now() - loaderStart;
      const remaining = Math.max(0, 4000 - elapsed);
      setTimeout(() => {
        cardLoader.style.display = "none";
        cardInfo.style.display = "flex";
      }, remaining);
    });
  });

  // refrescar provincia actual (usado por el header)
  window.cargarProvinciaActual = async function () {
    if (!window.provinciaActual) return;
    const nombre = window.provinciaActual;
    const clima = climaPorProvincia[normalize(nombre)];

    cardLoader.style.display = "flex";
    cardInfo.style.display = "none";

    await cargarClima();
    await cargarClimaHorario();
    colocarIconos();

    cardInfo.innerHTML = infoHtmlTemplate;
    actualizarDatosProvincia(nombre, clima);

    const container = cardInfo.querySelector(".container");
    if (container) {
      const nuevoVolverBtn = document.createElement("button");
      nuevoVolverBtn.addEventListener("click", () => {
        cardInfo.style.display = "none";
        cardLoader.style.display = "none";
        cardMapa.style.display = "flex";
        if (typeof actualizarNombreProvincia === "function") {
          actualizarNombreProvincia("Argentina");
        }
      });
      container.appendChild(nuevoVolverBtn);
    }

    setTimeout(() => {
      cardLoader.style.display = "none";
      cardInfo.style.display = "flex";
    }, 1000);
  };

  // auto-actualización cada hora
  let horaActual = new Date().getHours();
  setInterval(async () => {
    const nuevaHora = new Date().getHours();
    if (nuevaHora !== horaActual) {
      horaActual = nuevaHora;
      console.log("Cambio de hora detectado → recargando datos...");
      await cargarClima();
      await cargarClimaHorario();
      colocarIconos();

      if (cardInfo.style.display === "flex" && window.provinciaActual) {
        const clima = climaPorProvincia[normalize(window.provinciaActual)];
        actualizarDatosProvincia(window.provinciaActual, clima);
      }
    }
  }, 60000);

  // iniciar
  inicializar();
});
