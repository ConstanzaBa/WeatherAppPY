document.addEventListener("DOMContentLoaded", async () => {
  const cardMapa = document.querySelector(".card.mapa");
  const cardInfo = document.querySelector(".card.info");
  const cardLoader = document.querySelector(".card.loader");
  const infoElem = document.getElementById("provincia-info");
  const tituloInfo = document.getElementById("titulo-provincia");
  const volverBtn = document.getElementById("volver-btn");
  const svgMapa = document.getElementById("mapa-argentina");

  // normalizar nombres de provincias para coincidir con claves del JSON
  const normalize = str => str.toLowerCase().replace(/\s+/g, "_");

  // variables principales
  let climaData = [];           // guardar datos del clima
  let climaPorProvincia = {};   // objeto por provincia
  let iconos = [];              // iconos svg

  // función para cargar los datos del JSON
  async function cargarClima() {
    const climaResponse = await fetch("clima_actual.json?cache=" + Date.now());
    climaData = await climaResponse.json();

    climaPorProvincia = {};
    climaData.forEach(item => {
      climaPorProvincia[normalize(item.provincia)] = item;
    });
  }

  async function inicializar() {
    await cargarClima();
    colocarIconos();
  }

  // seleccionar todos los puntos de referencia del SVG
  const labels = document.querySelectorAll("#label_points circle");

  function colocarIconos() {
    // eliminar iconos anteriores para evitar duplicados
    iconos.forEach(icon => icon.remove());
    iconos = [];

    labels.forEach(label => {
      const provincia = normalize(label.getAttribute("data-provincia"));
      const clima = climaPorProvincia[provincia];
      if (!clima) return;

      const svgImage = document.createElementNS("http://www.w3.org/2000/svg", "image");
      svgImage.setAttributeNS(null, "href", `img/weather/${clima.icono}`);
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

  // manejar click en cada provincia
  const provincias = document.querySelectorAll("#mapa-argentina path[id^='AR']");
  provincias.forEach(provinciaEl => {
    provinciaEl.addEventListener("click", async () => {
      const nombre = provinciaEl.getAttribute("name");
      const clima = climaPorProvincia[normalize(nombre)];

      cardMapa.style.display = "none";
      cardInfo.style.display = "none";
      cardLoader.style.display = "flex";
      const loaderStart = Date.now();

      await cargarClima(); // cargar datos si cambia la hora
      colocarIconos();

      // calcular tiempo restante para 5 segundos
      const elapsed = Date.now() - loaderStart;
      const remaining = Math.max(0, 5000 - elapsed);
      setTimeout(() => {
        // ocultar loader y mostrar info
        cardLoader.style.display = "none";
        cardInfo.style.display = "flex";
        tituloInfo.textContent = nombre;

        if (clima) {
          infoElem.innerHTML = `
            <img src="img/weather/${clima.icono}" class="icono-clima" width="64">
            <p><strong>Temperatura:</strong> ${clima.temperatura} °C</p>
            <p><strong>Humedad:</strong> ${clima.humedad} %</p>
            <p><strong>Código:</strong> ${clima.coco}</p>
            <p><em>${clima.fecha_hora}</em></p>
          `;
        } else {
          infoElem.textContent = "Sin datos disponibles.";
        }
      }, remaining);
    });
  });

  // volver al mapa
  volverBtn.addEventListener("click", () => {
    cardInfo.style.display = "none";
    cardLoader.style.display = "none";
    cardMapa.style.display = "flex";
  });

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
