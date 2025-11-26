import { updateVisuals } from "./details.js";

window.updateVisuals = updateVisuals;

document.addEventListener("DOMContentLoaded", async () => {
  const cardMapa = document.querySelector(".card.mapa");
  const cardInfo = document.querySelector(".card.info");
  const cardLoader = document.querySelector(".card.loader");
  const svgMapa = document.getElementById("mapa-argentina");

  window.provinciaActual = null;

  const normalize = (str) => {
    return str
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, "_");
  };

  let climaData = [];
  let climaPorProvincia = {};
  let climaHorarioPorProvincia = {};
  let pronosticoPorProvincia = {};
  let carruselPorProvincia = {};
  let iconos = [];
  let infoHtmlTemplate = "";

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

  async function cargarTemplateInfo() {
    try {
      const response = await fetch("info.html");
      const html = await response.text();
      const container = document.createElement("div");
      container.innerHTML = html;

      const containerEl = container.querySelector(".container");
      if (containerEl) {
        try {
          const detailsResp = await fetch("partials/details.html");
          if (detailsResp.ok) {
            const detailsHtml = await detailsResp.text();
            const detailsTemp = document.createElement("div");
            detailsTemp.innerHTML = detailsHtml;
            const detailsEl =
              detailsTemp.querySelector(".weather-details") ||
              detailsTemp.firstElementChild;

            if (detailsEl) {
              const existing = containerEl.querySelector(".weather-details");
              if (existing) existing.replaceWith(detailsEl.cloneNode(true));
              else containerEl.appendChild(detailsEl.cloneNode(true));
            }
          }
        } catch (err) {
          console.warn("No se pudo cargar partial details:", err);
        }
        infoHtmlTemplate = containerEl.outerHTML;
      }
    } catch (err) {
      console.error("Error al cargar info.html:", err);
    }
  }
  async function cargarClima() {
    const response = await fetch("clima_actual.json?cache=" + Date.now());
    const data = await response.json();

    climaPorProvincia = {};
    data.forEach((item) => {
      climaPorProvincia[normalize(item.provincia)] = item;
    });

    climaData = data;

    window.climaPorProvincia = climaPorProvincia;
    window.climaData = climaData;
  }

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

    window.climaHorarioPorProvincia = climaHorarioPorProvincia;
  }

  async function cargarPronostico() {
    try {
      const response = await fetch("pronostico.json?cache=" + Date.now());
      const data = await response.json();

      pronosticoPorProvincia = {};

      // Usar la lista dentro de data.provincias
      const provincias = data.provincias || [];
      provincias.forEach((item) => {
        pronosticoPorProvincia[normalize(item.provincia)] = item.pronostico;
      });

      console.log("Pronóstico cargado:", pronosticoPorProvincia);
    } catch (err) {
      console.error("Error al cargar pronostico.json:", err);
      pronosticoPorProvincia = {};
    }

    window.pronosticoPorProvincia = pronosticoPorProvincia;
  }

  async function cargarCarrusel() {
    try {
      const response = await fetch("carousel.json?cache=" + Date.now());
      const data = await response.json();

      carruselPorProvincia = {};

      // Usar la lista dentro de data.provincias
      const provincias = data.provincias || [];
      provincias.forEach((item) => {
        carruselPorProvincia[normalize(item.provincia)] = item.insights;
      });

      console.log("Carrusel cargado:", carruselPorProvincia);
    } catch (err) {
      console.error("Error al cargar carousel.json:", err);
      carruselPorProvincia = {};
    }

    window.carruselPorProvincia = carruselPorProvincia;
  }

  async function inicializar() {
    await cargarTemplateInfo();
    await cargarClima();
    await cargarClimaHorario();
    await cargarPronostico();
    await cargarCarrusel();

    window.climaPorProvincia = climaPorProvincia;
    window.climaHorarioPorProvincia = climaHorarioPorProvincia;
    window.pronosticoPorProvincia = pronosticoPorProvincia;
    window.carruselPorProvincia = carruselPorProvincia;

    colocarIconos();
  }

  const labels = document.querySelectorAll("#label_points circle");

  function colocarIconos() {
    iconos.forEach((icon) => icon.remove());
    iconos = [];

    labels.forEach((label) => {
      const provincia = normalize(label.getAttribute("data-provincia"));
      const clima = climaPorProvincia[provincia];
      if (!clima) return;

      const svgImage = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "image"
      );
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

  function actualizarPronosticoSemanal(provincia) {
    const weeklyForecast = cardInfo.querySelector(".weekly-forecast");
    if (!weeklyForecast) return;

    const provinciaKey = normalize(provincia);
    const pronosticoData = pronosticoPorProvincia[provinciaKey];

    if (!pronosticoData || pronosticoData.length === 0) {
      weeklyForecast.innerHTML =
        '<div class="section-title">Pronóstico Semanal</div><p style="text-align: center; color: #666; padding: 20px;">No hay pronóstico disponible</p>';
      return;
    }

    // Limpiar y agregar título
    weeklyForecast.innerHTML =
      '<div class="section-title">Pronóstico Semanal</div>';

    const diasSemana = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"];
    const meses = [
      "Ene",
      "Feb",
      "Mar",
      "Abr",
      "May",
      "Jun",
      "Jul",
      "Ago",
      "Sep",
      "Oct",
      "Nov",
      "Dic",
    ];

    pronosticoData.forEach((dia, index) => {
      const dailyItem = document.createElement("div");
      dailyItem.className = "daily-item";

      // Día
      const dayDiv = document.createElement("div");
      dayDiv.className = "day";

      const fecha = new Date(dia.fecha + "T12:00:00");
      const nombreDia = index === 0 ? "Hoy" : diasSemana[fecha.getDay()];
      const diaNum = fecha.getDate();
      const mes = meses[fecha.getMonth()];

      dayDiv.innerHTML = `${nombreDia}<br /><span style="font-size: 12px; color: #999">${mes} ${diaNum}</span>`;

      // Icono
      const iconDiv = document.createElement("div");
      iconDiv.className = "day-icon";
      const iconImg = document.createElement("img");
      iconImg.src = `img/weather/${dia.icon}`;
      iconImg.alt = dia.desc;
      iconImg.width = 40;
      iconImg.height = 40;
      iconDiv.appendChild(iconImg);

      // Temperaturas
      const tempsDiv = document.createElement("div");
      tempsDiv.className = "temps";

      const highSpan = document.createElement("span");
      highSpan.className = "high";
      highSpan.textContent = `${Math.round(dia.temp_high)}°`;

      const lowSpan = document.createElement("span");
      lowSpan.className = "low";
      lowSpan.textContent = `/ ${Math.round(dia.temp_low)}°`;

      tempsDiv.appendChild(highSpan);
      tempsDiv.appendChild(lowSpan);

      dailyItem.appendChild(dayDiv);
      dailyItem.appendChild(iconDiv);
      dailyItem.appendChild(tempsDiv);
      weeklyForecast.appendChild(dailyItem);
    });
  }
  function actualizarDatosProvincia(nombre, clima) {
    const tituloProvincia = cardInfo.querySelector(".titulo-provincia");
    const horaProvincia = cardInfo.querySelector(".hora-provincia");

    if (tituloProvincia) {
      const ahora = new Date();
      const diaSemana = ahora.toLocaleDateString("es-AR", { weekday: "long" });
      tituloProvincia.textContent =
        diaSemana.charAt(0).toUpperCase() + diaSemana.slice(1);
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
        weatherIcon.innerHTML = `<img src="img/weather/${iconFilename}" alt="${
          clima.coco ?? ""
        }" width="85" height="85" class="weather-icon-img">`;
      }

      const humValue = document.getElementById("humValue");
      const windSpeed = document.getElementById("windSpeed");
      const visValue = document.getElementById("visValue");
      const tempValue = document.getElementById("tempValue");
      const precipValue = document.getElementById("precipValue");
      const uvNumber = document.getElementById("uvNumber");

      if (humValue) humValue.textContent = `${clima.humedad}%`;
      if (windSpeed) windSpeed.textContent = `${clima.viento} km/h`;
      if (visValue) visValue.textContent = clima.visibilidad?.toFixed(1) || "0";
      if (tempValue) tempValue.textContent = `${clima.sensacionTermica}°C`;
      if (precipValue)
        precipValue.textContent = `${clima.precipitacion ?? 0} mm`;
      if (uvNumber) uvNumber.textContent = `${clima.uvIndex}`;

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

      const chartImg = cardInfo.querySelector("#temperature-chart");
      if (chartImg) {
        const normalizedName = normalize(nombre);
        chartImg.src = `img/graphs/temp_chart_${normalizedName}.png?cache=${Date.now()}`;
        chartImg.alt = `Gráfico de temperatura de ${nombre}`;
      }

      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          updateVisuals(clima);
        });
      });
    }

    actualizarPronosticoHorario(nombre);
    actualizarPronosticoSemanal(nombre);
    actualizarCarrusel(nombre);
  }

  // EVENTO CLICK EN PROVINCIAS
  const provincias = document.querySelectorAll(
    "#mapa-argentina path[id^='AR']"
  );
  provincias.forEach((provinciaEl) => {
    provinciaEl.addEventListener("click", async () => {
      const nombre = provinciaEl.getAttribute("name");
      const clima = climaPorProvincia[normalize(nombre)];

      window.provinciaActual = nombre;
      localStorage.setItem("selectedProvince", nombre);

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

      // INICIALIZAR GRÁFICOS
      inicializarGraficos();

      // INICIALIZAR CARRUSEL
      actualizarCarrusel(nombre);

      const elapsed = Date.now() - loaderStart;
      const remaining = Math.max(0, 4000 - elapsed);
      setTimeout(() => {
        cardLoader.style.display = "none";
        cardInfo.style.display = "flex";
      }, remaining);
    });
  });

  // RECARGAR PROVINCIA DESDE LOCALSTORAGE
  window.cargarProvinciaActual = async function () {
    if (!window.provinciaActual) return;

    const nombre = window.provinciaActual;
    const key = normalize(nombre);
    const clima = climaPorProvincia[key];

    cardLoader.style.display = "flex";
    cardInfo.style.display = "none";

    await cargarClima();
    await cargarClimaHorario();
    colocarIconos();

    cardInfo.innerHTML = infoHtmlTemplate;
    actualizarDatosProvincia(nombre, clima);

    // GRÁFICOS
    inicializarGraficos();

    // CARRUSEL
    actualizarCarrusel(nombre);

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

      requestAnimationFrame(() => {
        if (window.updateVisuals) {
          window.updateVisuals(clima);
        }
      });
    }, 300);
  };

  // AUTO-UPDATE CADA HORA
  let horaActual = new Date().getHours();
  setInterval(async () => {
    const nuevaHora = new Date().getHours();
    if (nuevaHora !== horaActual) {
      horaActual = nuevaHora;
      console.log("Cambio de hora → recargando datos...");

      await cargarClima();
      await cargarClimaHorario();
      colocarIconos();

      if (cardInfo.style.display === "flex" && window.provinciaActual) {
        const clima = climaPorProvincia[normalize(window.provinciaActual)];
        actualizarDatosProvincia(window.provinciaActual, clima);

        inicializarGraficos();
      }
    }
  }, 60000);

  inicializar();
});

// =======================================================
//    CARRUSEL
// =======================================================

function actualizarCarrusel(provincia) {
  const wrapper = document.getElementById("carouselWrapper");
  const dotsContainer = document.getElementById("carouselDots");

  if (!wrapper || !dotsContainer) {
    console.log("No se encontraron elementos del carrusel");
    return;
  }

  if (!window.carruselPorProvincia) {
    console.log("carruselPorProvincia no está disponible");
    wrapper.innerHTML =
      '<div class="carousel-slide"><p style="text-align:center; padding: 20px;">Cargando datos...</p></div>';
    return;
  }

  const provinciaKey = provincia
    ? provincia
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/\s+/g, "_")
    : null;
  console.log("Buscando carrusel para:", provincia, "-> Key:", provinciaKey);
  console.log("Datos disponibles:", Object.keys(window.carruselPorProvincia));

  const datosCarrusel =
    provinciaKey && window.carruselPorProvincia[provinciaKey];

  // Limpiar contenido previo
  wrapper.innerHTML = "";
  dotsContainer.innerHTML = "";

  if (!datosCarrusel) {
    console.log("No se encontraron datos para:", provinciaKey);
    wrapper.innerHTML =
      '<div class="carousel-slide"><p style="text-align:center; padding: 20px;">No hay datos disponibles</p></div>';
    return;
  }

  console.log("Datos del carrusel encontrados:", datosCarrusel);

  // Crear slides con los 3 datos
  const slides = [
    {
      icon: "💧",
      title: "Probabilidad de Lluvia",
      value: `${datosCarrusel.probabilidad_lluvia}%`,
      detail:
        datosCarrusel.probabilidad_lluvia > 50
          ? "Alta probabilidad"
          : datosCarrusel.probabilidad_lluvia > 20
          ? "Probabilidad moderada"
          : "Baja probabilidad",
    },
    {
      icon: "🌡️",
      title: "Sensación Térmica",
      value: `${datosCarrusel.sensacion_termica}°C`,
      detail: "Temperatura percibida",
    },
    {
      icon: "☁️",
      title: "Nubosidad",
      value: datosCarrusel.nubosidad,
      detail: `${datosCarrusel.nubosidad_porcentaje}% de cobertura`,
    },
  ];

  // Crear HTML de los slides
  slides.forEach((slide) => {
    const slideDiv = document.createElement("div");
    slideDiv.className = "carousel-slide";
    slideDiv.innerHTML = `
      <div class="slide-icon">${slide.icon}</div>
      <h3>${slide.title}</h3>
      <div class="slide-value">${slide.value}</div>
      <p class="slide-detail">${slide.detail}</p>
    `;
    wrapper.appendChild(slideDiv);
  });

  // Crear dots
  for (let i = 0; i < slides.length; i++) {
    const dot = document.createElement("div");
    dot.className = "dot";
    if (i === 0) dot.classList.add("active");
    dotsContainer.appendChild(dot);
  }

  console.log("Carrusel actualizado con", slides.length, "slides");

  // Inicializar carrusel
  inicializarCarrusel();
}

async function inicializarCarrusel() {
  const wrapper = document.getElementById("carouselWrapper");
  const dotsContainer = document.getElementById("carouselDots");

  // Verificar que existen los elementos
  if (!wrapper || !dotsContainer) {
    return;
  }

  const slides = wrapper.querySelectorAll(".carousel-slide");
  let currentSlide = 0;
  const totalSlides = slides.length;

  if (totalSlides === 0) return;

  const dots = dotsContainer.querySelectorAll(".dot");

  function updateCarousel() {
    wrapper.style.transform = `translateX(-${currentSlide * 100}%)`;
    dots.forEach((dot, index) => {
      dot.classList.toggle("active", index === currentSlide);
    });
  }

  function goToSlide(index) {
    currentSlide = index;
    updateCarousel();
  }

  function nextSlide() {
    currentSlide = (currentSlide + 1) % totalSlides;
    updateCarousel();
  }

  function prevSlide() {
    currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
    updateCarousel();
  }

  // Agregar event listeners a los dots
  dots.forEach((dot, index) => {
    dot.addEventListener("click", () => goToSlide(index));
  });

  // Auto-advance (opcional)
  let autoPlay = setInterval(nextSlide, 5000);

  // Pause on hover
  wrapper.addEventListener("mouseenter", () => clearInterval(autoPlay));
  wrapper.addEventListener("mouseleave", () => {
    autoPlay = setInterval(nextSlide, 5000);
  });

  // Touch support
  let touchStartX = 0;
  let touchEndX = 0;

  wrapper.addEventListener("touchstart", (e) => {
    touchStartX = e.changedTouches[0].screenX;
  });

  wrapper.addEventListener("touchend", (e) => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
  });

  function handleSwipe() {
    if (touchStartX - touchEndX > 50) nextSlide();
    if (touchEndX - touchStartX > 50) prevSlide();
  }
}

// =======================================================
//    GRÁFICOS
// =======================================================

function inicializarGraficos() {
  const provincia =
    window.provinciaActual || localStorage.getItem("selectedProvince");
  if (!provincia) return;

  const graphImg = document.getElementById("graph-image");
  if (!graphImg) return;

  const provKey = provincia
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, "_");

  const graphMap = {
    temp_vs_sensacion: `img/graphs/grafico_temp_vs_sensacion_${provKey}.png`,
    precipitacion: `img/graphs/grafico_precipitacion_${provKey}.png`,
    humedad: `img/graphs/grafico_humedad_${provKey}.png`,
    viento: `img/graphs/grafico_velocidad_viento_${provKey}.png`,
    direccion_viento: `img/graphs/grafico_direccion_viento_${provKey}.png`,
  };

  // Inicializa con temperatura
  graphImg.src = graphMap["temp_vs_sensacion"];

  // Marcar tab activo
  document
    .querySelectorAll(".graph-tabs .tab")
    .forEach((btn) => btn.classList.remove("active"));
  document
    .querySelector(`.graph-tabs .tab[data-graph="temp_vs_sensacion"]`)
    ?.classList.add("active");

  // Click en tabs
  document.querySelectorAll(".graph-tabs .tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelector(".tab.active")?.classList.remove("active");
      btn.classList.add("active");
      graphImg.src = graphMap[btn.dataset.graph];
    });
  });
}
