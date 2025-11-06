import { calcularSensacionTermica } from "./parametros.js";

document.addEventListener("DOMContentLoaded", async () => {
  const cardMapa = document.querySelector(".card.mapa");
  const cardInfo = document.querySelector(".card.info");
  const cardLoader = document.querySelector(".card.loader");
  const provinciaContainer = document.querySelector(".provincia-container");
  const volverBtn = document.getElementById("volver-btn");
  const svgMapa = document.getElementById("mapa-argentina");

  // normalizar nombres de provincias para coincidir con claves del JSON
  const normalize = (str) => str.toLowerCase().replace(/\s+/g, "_");

  // variables principales
  let climaData = []; // guardar datos del clima
  let climaPorProvincia = {}; // objeto por provincia
  let iconos = []; // iconos svg
  let infoHtmlTemplate = ""; // template del info.html

  // Helper para decidir el nombre de archivo del icono a usar
  function getIconFilename(clima) {
    if (!clima) return "clear.svg";
    // Si el JSON ya trae el nombre del archivo, usarlo
    if (clima.icono) return clima.icono;
    // Soporte para campos alternativos (si en el futuro hay códigos)
    const code = Number(clima.cocos ?? clima.coco);
    if (!Number.isNaN(code)) {
      // Si existe un mapeo `weatherIcons` en el futuro, úsalo
      if (typeof weatherIcons !== "undefined" && weatherIcons[code])
        return weatherIcons[code];
    }
    // Fallback
    return "clear.svg";
  }

  // Mapeo para iconos fijos en los .detail-item (puedes ajustar los nombres)
  const detailIconMap = {
    Humedad: "humidity.svg",
    Viento: "wind.svg",
    "Sensación Térmica": "thermometer-sun.svg",
    Precipitación: "umbrella.svg",
    "Radiación UV": "uv-index.svg",
  };

  // función para cargar el template de info.html
  async function cargarTemplateInfo() {
    try {
      const response = await fetch("info.html");
      const html = await response.text();

      const temp = document.createElement("div");
      temp.innerHTML = html;

      // Extraer TODO el contenido del body si existe, o el container
      const container = temp.querySelector(".container");
      if (container) {
        infoHtmlTemplate = container.outerHTML; // CAMBIO: usar outerHTML en lugar de innerHTML
      }
    } catch (error) {
      console.error("Error al cargar info.html:", error);
    }
  }

  // función para cargar los datos del JSON
  async function cargarClima() {
    const climaResponse = await fetch("clima_actual.json?cache=" + Date.now());
    climaData = await climaResponse.json();

    climaPorProvincia = {};
    climaData.forEach((item) => {
      item.sensacionTermica = calcularSensacionTermica(
        item.temperatura,
        item.humedad,
        item.viento
      );

      climaPorProvincia[normalize(item.provincia)] = item;
    });
  }

  async function inicializar() {
    await cargarTemplateInfo(); // Cargar el template primero
    await cargarClima();
    colocarIconos();
  }

  // seleccionar todos los puntos de referencia del SVG
  const labels = document.querySelectorAll("#label_points circle");

  function colocarIconos() {
    // eliminar iconos anteriores para evitar duplicados
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

  // función para actualizar los datos de la provincia en el template
  function actualizarDatosProvincia(nombre, clima) {
    // Actualizar título y hora
    const tituloProvincia = cardInfo.querySelector(".titulo-provincia");
    const horaProvincia = cardInfo.querySelector(".hora-provincia");

    if (tituloProvincia) {
      tituloProvincia.textContent = nombre;
    }

    if (horaProvincia && clima) {
      const ahora = new Date();
      horaProvincia.textContent = ahora.toLocaleTimeString("es-AR", {
        hour: "2-digit",
        minute: "2-digit",
      });
    }

    // Actualizar datos del clima
    if (clima) {
      // Temperatura actual
      const tempActual = cardInfo.querySelector(".temperature");
      if (tempActual) {
        tempActual.textContent = `${clima.temperatura}°`;
      }

      // Condición del clima
      const condition = cardInfo.querySelector(".condition");
      if (condition) {
        condition.textContent = `${clima.condicion}` || "Despejado";
      }

      // Icono del clima
      const weatherIcon = cardInfo.querySelector(".weather-icon");
      if (weatherIcon) {
        const iconFilename = getIconFilename(clima);
        // Si el elemento ya es una <img>, actualizar su src, si no insertar una
        if (
          weatherIcon.tagName &&
          weatherIcon.tagName.toLowerCase() === "img"
        ) {
          weatherIcon.src = `img/weather/${iconFilename}`;
          weatherIcon.alt = `${clima.coco ?? ""}`;
        } else {
          weatherIcon.innerHTML = "";
          const img = document.createElement("img");
          img.src = `img/weather/${iconFilename}`;
          img.alt = `${clima.coco ?? ""}`;
          img.width = 75;
          img.height = 75;
          img.classList.add("weather-icon-img");
          weatherIcon.appendChild(img);
        }
      }

      // Iconos fijos para cada .detail-item (reemplaza emojis por <img>)
      const detailItems = cardInfo.querySelectorAll(".detail-item");
      detailItems.forEach((item) => {
        const labelEl = item.querySelector(".label");
        const iconEl = item.querySelector(".icon");
        if (!labelEl || !iconEl) return;
        const label = labelEl.textContent.trim();
        const iconFilename = detailIconMap[label];
        if (iconFilename) {
          iconEl.innerHTML = "";
          const img = document.createElement("img");
          img.src = `img/weather/${iconFilename}`;
          img.alt = label;
          img.width = 30;
          img.height = 30;
          img.classList.add("detail-icon-img");
          iconEl.appendChild(img);
        }
      });

      // Humedad
      const humidityValue = cardInfo.querySelectorAll(".value")[0];
      if (humidityValue) {
        humidityValue.textContent = `${clima.humedad}%`;
      }

      // Viento
      const vientoValue = cardInfo.querySelectorAll(".value")[1];
      if (vientoValue) {
        vientoValue.textContent = `${clima.viento}km/h`;
      }

      // Visibilidad
      const visibilidadValue = cardInfo.querySelectorAll(".value")[2];
      if (visibilidadValue) {
        visibilidadValue.textContent = `${clima.visibilidad}m`;
      }

      // Sensación Térmica
      const sensacionValue = cardInfo.querySelectorAll(".value")[3];
      if (sensacionValue) {
        sensacionValue.textContent = `${clima.sensacionTermica}°`;
      }

      // Precipitación
      const precipitacionValue = cardInfo.querySelectorAll(".value")[4];
      if (precipitacionValue) {
        precipitacionValue.textContent = `${clima.precipitacion}mm`;
      }

      // Radiación UV
      const uvValue = cardInfo.querySelectorAll(".value")[5];
      if (uvValue) {
        uvValue.textContent = `${clima.uvIndex}`;
      }
    }
  }

  // manejar click en cada provincia
  const provincias = document.querySelectorAll(
    "#mapa-argentina path[id^='AR']"
  );
  provincias.forEach((provinciaEl) => {
    provinciaEl.addEventListener("click", async () => {
      const nombre = provinciaEl.getAttribute("name");
      const clima = climaPorProvincia[normalize(nombre)];

      cardMapa.style.display = "none";
      cardInfo.style.display = "none";
      cardLoader.style.display = "flex";
      const loaderStart = Date.now();

      await cargarClima();
      colocarIconos();

      // Insertar el template
      cardInfo.innerHTML = `
      <div>
        ${infoHtmlTemplate}
      </div>
    `;

      // Actualizar los datos después de insertar el template
      actualizarDatosProvincia(nombre, clima);

      // Crear el botón volver y agregarlo después del weekly-forecast
      const container = cardInfo.querySelector(".container"); // Buscar el container principal

      if (container) {
        const nuevoVolverBtn = document.createElement("button");
        nuevoVolverBtn.id = "volver-btn";
        nuevoVolverBtn.textContent = "Volver al mapa";
        nuevoVolverBtn.addEventListener("click", () => {
          cardInfo.style.display = "none";
          cardLoader.style.display = "none";
          cardMapa.style.display = "flex";
        });

        // Agregar el botón al final del container (después del weekly-forecast)
        container.appendChild(nuevoVolverBtn);
      }

      const elapsed = Date.now() - loaderStart;
      const remaining = Math.max(0, 4000 - elapsed);

      setTimeout(() => {
        cardLoader.style.display = "none";
        cardInfo.style.display = "flex";
      }, remaining);
    });
  });

  // volver al mapa (listener inicial)
  if (volverBtn) {
    volverBtn.addEventListener("click", () => {
      cardInfo.style.display = "none";
      cardLoader.style.display = "none";
      cardMapa.style.display = "flex";
    });
  }

  // actualizar iconos si cambia la hora
  let horaActual = new Date().getHours();
  setInterval(async () => {
    const nuevaHora = new Date().getHours();
    if (nuevaHora !== horaActual) {
      horaActual = nuevaHora;
      console.log("Cambio de hora detectado, recargando datos...");
      await cargarClima();
      colocarIconos();
    }
  }, 60000);

  inicializar();
});
