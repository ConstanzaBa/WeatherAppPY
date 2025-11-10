function visibilidadCard() {
  let visibility = 0;
  const sky = document.getElementById("sky");
  const visValue = document.getElementById("visValue");
  const visStatus = document.getElementById("visStatus");

  function updateVisibility() {
    visibility = Math.random() * 10;
    visValue.textContent = visibility.toFixed(1);

    let status, cloudCount, colorTop, colorBottom;

    if (visibility < 2) {
      status = "Muy baja";
      cloudCount = 22;
      colorTop = "#6b7a8f";
      colorBottom = "#2e3b55";
    } else if (visibility < 5) {
      status = "Reducida";
      cloudCount = 16;
      colorTop = "#5d7cb3";
      colorBottom = "#2a3e73";
    } else if (visibility < 8) {
      status = "Moderada";
      cloudCount = 10;
      colorTop = "#4b6cb7";
      colorBottom = "#182848";
    } else {
      status = "Buena";
      cloudCount = 8;
      colorTop = "#5ba4f0";
      colorBottom = "#1b3c7a";
    }

    visStatus.textContent = status;
    sky.style.background = `linear-gradient(to bottom, ${colorTop}, ${colorBottom})`;

    sky.innerHTML = "";

    const cloudColors = [
      "#ffffff",
      "#f0f8ff",
      "#e6f2ff",
      "#fff5f9",
      "#f2f7ff",
      "#f9f9f9",
    ];

    const cloudShapes = [
      `<svg viewBox="0 0 64 32"><path d="M10 20c2-6 8-10 14-10 4 0 8 2 10 5 2-1 4-1 6-1 6 0 11 4 12 9 1 4-2 7-6 7H16c-5 0-8-4-6-10z"/></svg>`,
      `<svg viewBox="0 0 64 32"><path d="M12 20c1-5 6-8 11-8 3 0 6 1 8 3 2-1 4-1 6-1 5 0 9 3 10 7 1 4-2 6-5 6H18c-4 0-7-3-6-7z"/></svg>`,
      `<svg viewBox="0 0 64 32"><path d="M8 21c2-7 9-11 16-11 5 0 9 3 11 6 2-1 5-1 7-1 7 0 12 5 13 10 1 4-3 7-8 7H18c-6 0-10-4-10-11z"/></svg>`,
    ];

    for (let i = 0; i < cloudCount; i++) {
      const cloud = document.createElement("div");
      cloud.classList.add("cloud");

      const randomShape =
        cloudShapes[Math.floor(Math.random() * cloudShapes.length)];
      const randomColor =
        cloudColors[Math.floor(Math.random() * cloudColors.length)];

      cloud.innerHTML = randomShape;
      const svg = cloud.querySelector("path");
      svg.setAttribute("fill", randomColor);
      svg.setAttribute("opacity", "0.9");

      const size = Math.random() * 80 + 70;
      const top = Math.random() * (sky.clientHeight * 0.7 - 20) + 5;

      cloud.style.width = `${size}px`;
      cloud.style.top = `${top}px`;
      cloud.style.left = `${Math.random() * 280 - 100}px`;
      cloud.style.animationDuration = `${14 + Math.random() * 10}s`;

      sky.appendChild(cloud);
    }
  }

  updateVisibility();
  setInterval(updateVisibility, 10000);
}

function precipitacionCard() {
  const precipitation = 50;
  const maxPrecip = 100;
  const rainWater = document.getElementById("rainWater");
  const raindropsContainer = document.getElementById("raindrops");
  const precipValue = document.getElementById("precipValue");
  const precipStatus = document.getElementById("precipStatus");

  precipValue.textContent = precipitation.toFixed(0);

  const waterHeight = Math.min((precipitation / maxPrecip) * 100, 100);
  rainWater.style.height = waterHeight + "%";

  raindropsContainer.innerHTML = "";
  const numDrops = Math.floor(precipitation * 1.2);

  for (let i = 0; i < numDrops; i++) {
    const drop = document.createElement("div");
    drop.classList.add("raindrop");
    drop.style.left = Math.random() * 100 + "%";
    drop.style.animationDuration = 0.5 + Math.random() * 1 + "s";
    drop.style.animationDelay = Math.random() * 2 + "s";
    raindropsContainer.appendChild(drop);
  }
}

function humedadCard() {
  const humidity = 72;
  const humValue = document.getElementById("humValue");
  const humStatus = document.getElementById("humStatus");
  const progressRing = document.querySelector(".progress-ring");

  humValue.textContent = humidity + "%";

  let status;
  if (humidity < 30) status = "Seco";
  else if (humidity < 60) status = "Moderado";
  else if (humidity < 85) status = "Húmedo";
  else status = "Condensado";

  humStatus.textContent = status;

  const radius = progressRing.r.baseVal.value;
  const circumference = 2 * Math.PI * radius;
  progressRing.style.strokeDasharray = `${circumference} ${circumference}`;
  const offset = circumference - (humidity / 100) * circumference;
  progressRing.style.strokeDashoffset = offset;
}

function sensacionTermicaCard() {
  const actualTemperatura = 25;
  const sensacionTermica = 30;
  const maxTemp = 65;

  const thermoFill = document.getElementById("thermoFill");
  const thermoBulb = document.getElementById("thermoBulb");
  const tempValue = document.getElementById("tempValue");
  const tempStatus = document.getElementById("tempStatus");

  tempValue.textContent = sensacionTermica + "°C";

  const diff = sensacionTermica - actualTemperatura;

  let color, status;

  if (diff <= -5) {
    color = "linear-gradient(to top, #003f7f, #008cff)";
    status = "Mucho más frío";
  } else if (diff < -3) {
    color = "linear-gradient(to top, #5cbcff, #aee4ff)";
    status = "Más frío";
  } else if (diff > 5) {
    color = "linear-gradient(to top, #ff0000, #ff6b6b)";
    status = "Mucho más cálido";
  } else if (diff > 3) {
    color = "linear-gradient(to top, #ffae42, #ff6f00)";
    status = "Más cálido";
  } else {
    color = "linear-gradient(to top, #ffe680, #ffd240)";
    status = "Similar";
  }

  tempStatus.textContent = status;

  const fillHeight = Math.min((sensacionTermica / maxTemp) * 170, 170);
  thermoFill.style.height = fillHeight + "px";
  thermoFill.style.background = color;
  thermoBulb.style.background = color;

  thermoBulb.style.boxShadow =
    diff > 0
      ? "0 0 25px rgba(255,100,50,0.6)"
      : "0 0 25px rgba(100,150,255,0.6)";
}

function vientoCard() {
  const windSpeed = 23;
  const windValue = document.querySelector(".wind-value");
  const windStatus = document.getElementById("windStatus");
  const speedEl = document.getElementById("windSpeed");

  const pathLength = 251;
  windValue.style.strokeDasharray = pathLength;
  windValue.style.strokeDashoffset = pathLength;

  const percent = Math.min(windSpeed / 100, 1);
  const offset = pathLength - percent * pathLength;

  setTimeout(() => {
    windValue.style.strokeDashoffset = offset;
  }, 100);

  let desc;
  if (windSpeed < 5) desc = "Calma";
  else if (windSpeed < 15) desc = "Brisa ligera";
  else if (windSpeed < 30) desc = "Hay brisa";
  else if (windSpeed < 50) desc = "Viento fuerte";
  else desc = "Temporal";

  speedEl.textContent = windSpeed;
  windStatus.textContent = desc;
}

function uvCard() {
  const card = document.querySelector(".uv-card");
  const uvValue = parseFloat(card.dataset.uv) || 0;

  const path = document.querySelector(".uv-value");
  const numberEl = document.getElementById("uvNumber");
  const statusEl = document.getElementById("uvStatus");
  const descEl = document.getElementById("uvDesc");

  const totalLength = 126;
  path.style.strokeDasharray = totalLength;
  path.style.strokeDashoffset = totalLength;

  const progress = Math.min(uvValue / 11, 1);
  const offset = totalLength * (1 - progress);

  setTimeout(() => {
    path.style.strokeDashoffset = offset;
  }, 200);

  let estado, descripcion;
  if (uvValue <= 2) {
    estado = "Bajo 😊";
    descripcion = "El nivel máximo de UV será bajo.";
  } else if (uvValue <= 5) {
    estado = "Moderado 😐";
    descripcion = "El nivel máximo de UV será moderado.";
  } else if (uvValue <= 7) {
    estado = "Alto 😎";
    descripcion = "El nivel máximo de UV de mañana será alto.";
  } else if (uvValue <= 10) {
    estado = "Muy alto 😬";
    descripcion = "El nivel máximo de UV será muy alto.";
  } else {
    estado = "Extremo 😱";
    descripcion = "El nivel máximo de UV será extremo.";
  }

  numberEl.textContent = uvValue;
  statusEl.textContent = estado;
  descEl.textContent = descripcion;
}