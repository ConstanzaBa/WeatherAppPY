// Actualizar visuales (gráficos/animaciones) usando los valores del JSON
function updateVisuals(clima) {
  if (!clima) return;

  // VISIBILIDAD
  try {
    const visibility = Number(clima.visibilidad ?? clima.visibilidad_km) || 0;
    const sky = document.getElementById('sky');
    const visValue = document.getElementById('visValue');
    const visStatus = document.getElementById('visStatus');
    
    if (visValue) visValue.textContent = visibility.toFixed(1);

    if (sky && visStatus) {
      let status, cloudCount, colorTop, colorBottom;
      if (visibility < 2) {
        status = 'Muy baja'; cloudCount = 22; colorTop = '#6b7a8f'; colorBottom = '#2e3b55';
      } else if (visibility < 5) {
        status = 'Reducida'; cloudCount = 16; colorTop = '#5d7cb3'; colorBottom = '#2a3e73';
      } else if (visibility < 8) {
        status = 'Moderada'; cloudCount = 10; colorTop = '#4b6cb7'; colorBottom = '#182848';
      } else {
        status = 'Buena'; cloudCount = 8; colorTop = '#5ba4f0'; colorBottom = '#1b3c7a';
      }
      visStatus.textContent = status;
      sky.style.background = `linear-gradient(to bottom, ${colorTop}, ${colorBottom})`;

      // generar nubes proporcionalmente
      sky.innerHTML = '';
      const cloudColors = ['#ffffff','#f0f8ff','#e6f2ff','#fff5f9','#f2f7ff','#f9f9f9'];
      const cloudShapes = [
        `<svg viewBox="0 0 64 32"><path d="M10 20c2-6 8-10 14-10 4 0 8 2 10 5 2-1 4-1 6-1 6 0 11 4 12 9 1 4-2 7-6 7H16c-5 0-8-4-6-10z"/></svg>`,
        `<svg viewBox="0 0 64 32"><path d="M12 20c1-5 6-8 11-8 3 0 6 1 8 3 2-1 4-1 6-1 5 0 9 3 10 7 1 4-2 6-5 6H18c-4 0-7-3-6-7z"/></svg>`,
        `<svg viewBox="0 0 64 32"><path d="M8 21c2-7 9-11 16-11 5 0 9 3 11 6 2-1 5-1 7-1 7 0 12 5 13 10 1 4-3 7-8 7H18c-6 0-10-4-10-11z"/></svg>`
      ];
      for (let i = 0; i < cloudCount; i++) {
        const cloud = document.createElement('div');
        cloud.classList.add('cloud');
        const randomShape = cloudShapes[Math.floor(Math.random()*cloudShapes.length)];
        const randomColor = cloudColors[Math.floor(Math.random()*cloudColors.length)];
        cloud.innerHTML = randomShape;
        const path = cloud.querySelector('path');
        if (path) { path.setAttribute('fill', randomColor); path.setAttribute('opacity','0.9'); }
        const size = Math.random()*80 + 70;
        const top = Math.random() * (Math.max(sky.clientHeight, 100) * 0.7 - 20) + 5;
        cloud.style.width = `${size}px`;
        cloud.style.top = `${top}px`;
        cloud.style.left = `${Math.random()*280 - 100}px`;
        cloud.style.animationDuration = `${14 + Math.random()*10}s`;
        sky.appendChild(cloud);
      }
    }
  } catch (e) { console.warn('updateVisuals visibilidad error', e); }

  // PRECIPITACIÓN
  try {
    const hasNumericPrecip = clima.precipitacion != null || clima.precip_mm != null || clima.precip != null;
    const precipitation = Number(clima.precipitacion ?? clima.precip_mm ?? clima.precip) || 0;
    const maxPrecip = 100;
    const rainWater = document.getElementById('rainWater');
    const raindropsContainer = document.getElementById('raindrops');
    const precipValue = document.getElementById('precipValue');

    if (precipValue) {
      if (hasNumericPrecip) {
        precipValue.textContent = precipitation.toFixed(0);
      } else if (clima.prob_precipitacion != null) {
        precipValue.textContent = `${clima.prob_precipitacion}%`;
      } else {
        precipValue.textContent = '—';
      }
    }

    if (rainWater) {
      const waterHeight = hasNumericPrecip ? Math.min((precipitation / maxPrecip) * 100, 100) : 0;
      rainWater.style.height = waterHeight + '%';
    }

    if (raindropsContainer) {
      raindropsContainer.innerHTML = '';
      const numDrops = hasNumericPrecip ? Math.floor((precipitation / Math.max(1, maxPrecip)) * 60) : 0;
      for (let i = 0; i < numDrops; i++) {
        const drop = document.createElement('div');
        drop.classList.add('raindrop');
        drop.style.left = Math.random() * 100 + '%';
        drop.style.animationDuration = 0.5 + Math.random() * 1 + 's';
        drop.style.animationDelay = Math.random() * 2 + 's';
        raindropsContainer.appendChild(drop);
      }
    }
  } catch (e) { console.warn('updateVisuals precipitacion error', e); }

  // HUMEDAD
  try {
    const humidity = Number(clima.humedad ?? clima.hum ?? clima.humidity);
    const humValue = document.getElementById('humValue');
    const humStatus = document.getElementById('humStatus');
    const progressRing = document.querySelector('.progress-ring');
    if (!Number.isNaN(humidity)) {
      if (humValue) humValue.textContent = `${humidity}%`;
      let status;
      if (humidity < 30) status = 'Seco';
      else if (humidity < 60) status = 'Moderado';
      else if (humidity < 85) status = 'Húmedo';
      else status = 'Condensado';
      if (humStatus) humStatus.textContent = status;
      if (progressRing) {
        const radius = progressRing.r.baseVal.value;
        const circumference = 2 * Math.PI * radius;
        progressRing.style.strokeDasharray = `${circumference} ${circumference}`;
        const offset = circumference - (humidity / 100) * circumference;
        progressRing.style.strokeDashoffset = offset;
      }
    }
  } catch(e){ console.warn('updateVisuals humedad error', e); }

  // SENSACIÓN TÉRMICA
  try {
    const actualTemp = Number(clima.temperatura ?? clima.temp ?? clima.t);
    const sensacion = Number(clima.sensacionTermica ?? clima.sensacion ?? clima.feels_like ?? clima.therm);
    const thermoFill = document.getElementById('thermoFill');
    const thermoBulb = document.getElementById('thermoBulb');
    const tempValue = document.getElementById('tempValue');
    const tempStatus = document.getElementById('tempStatus');
    if (!Number.isNaN(sensacion)) {
      if (tempValue) tempValue.textContent = `${sensacion}°C`;
      const diff = sensacion - (actualTemp || sensacion);
      let color, status;
      if (diff <= -5) { color = 'linear-gradient(to top, #003f7f, #008cff)'; status = 'Mucho más frío'; }
      else if (diff < -3) { color = 'linear-gradient(to top, #5cbcff, #aee4ff)'; status = 'Más frío'; }
      else if (diff > 5) { color = 'linear-gradient(to top, #ff0000, #ff6b6b)'; status = 'Mucho más cálido'; }
      else if (diff > 3) { color = 'linear-gradient(to top, #ffae42, #ff6f00)'; status = 'Más cálido'; }
      else { color = 'linear-gradient(to top, #ffe680, #ffd240)'; status = 'Similar'; }
      if (tempStatus) tempStatus.textContent = status;
      const maxTemp = 65;
      if (thermoFill) {
        thermoFill.style.height = Math.min((sensacion / maxTemp) * 170, 170) + 'px';
        thermoFill.style.background = color;
      }
      if (thermoBulb) {
        thermoBulb.style.background = color;
        thermoBulb.style.boxShadow = diff > 0 ? '0 0 25px rgba(255,100,50,0.6)' : '0 0 25px rgba(100,150,255,0.6)';
      }
    }
  } catch(e){ console.warn('updateVisuals sensacion error', e); }

  // VIENTO
  try {
    const windSpeed = Number(clima.viento ?? clima.wind ?? clima.wind_kph ?? clima.wind_km);
    const windValue = document.querySelector('.wind-value');
    const windStatus = document.getElementById('windStatus');
    const speedEl = document.getElementById('windSpeed');
    if (!Number.isNaN(windSpeed)) {
      const pathLength = 251;
      if (windValue) { 
        windValue.style.strokeDasharray = pathLength; 
        windValue.style.strokeDashoffset = pathLength; 
      }
      const percent = Math.min(windSpeed / 100, 1);
      const offset = pathLength - percent * pathLength;
      setTimeout(() => { if (windValue) windValue.style.strokeDashoffset = offset; }, 100);
      let desc;
      if (windSpeed < 5) desc = 'Calma'; 
      else if (windSpeed < 15) desc = 'Brisa ligera'; 
      else if (windSpeed < 30) desc = 'Hay brisa'; 
      else if (windSpeed < 50) desc = 'Viento fuerte'; 
      else desc = 'Temporal';
      if (speedEl) speedEl.textContent = windSpeed;
      if (windStatus) windStatus.textContent = desc;
    }
  } catch(e){ console.warn('updateVisuals viento error', e); }

  // UV
  try {
    const uvVal = Number(clima.uvIndex ?? clima.uv ?? clima.uv_value);
    const uvCardEl = document.querySelector('.uv-card');
    if (!Number.isNaN(uvVal) && uvCardEl) {
      uvCardEl.dataset.uv = uvVal;
      const path = document.querySelector('.uv-value');
      const numberEl = document.getElementById('uvNumber');
      const statusEl = document.getElementById('uvStatus');
      const descEl = document.getElementById('uvDesc');

      if (path && numberEl) {
        const totalLength = 126;
        path.style.strokeDasharray = totalLength;
        path.style.strokeDashoffset = totalLength;
        const progress = Math.min(uvVal / 11, 1);
        const offset = totalLength * (1 - progress);
        setTimeout(() => { path.style.strokeDashoffset = offset; }, 200);

        let estado, descripcion;
        if (uvVal <= 2) { estado = 'Bajo 😊'; descripcion = 'El nivel máximo de UV será bajo.'; }
        else if (uvVal <= 5) { estado = 'Moderado 😐'; descripcion = 'El nivel máximo de UV será moderado.'; }
        else if (uvVal <= 7) { estado = 'Alto 😎'; descripcion = 'El nivel máximo de UV será alto.'; }
        else if (uvVal <= 10) { estado = 'Muy alto 😬'; descripcion = 'El nivel máximo de UV será muy alto.'; }
        else { estado = 'Extremo 😱'; descripcion = 'El nivel máximo de UV será extremo.'; }

        numberEl.textContent = uvVal;
        if (statusEl) statusEl.textContent = estado;
        if (descEl) descEl.textContent = descripcion;
      }
    }
  } catch(e){ console.warn('updateVisuals uv error', e); }
}