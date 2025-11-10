fetch("header.html")
  .then(response => response.text())
  .then(data => {
    document.getElementById("header").innerHTML = data;

    const homeIcon = document.querySelector(".icon");
    if (homeIcon) {
      homeIcon.style.cursor = "pointer";
      homeIcon.addEventListener("click", () => {
        window.location.href = "index.html";
      });
    }

    const refreshBtn = document.querySelector(".refresh-btn svg");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => {
        refreshBtn.style.transition = "transform 0.6s ease";
        refreshBtn.style.transform = "rotate(360deg)";

        setTimeout(() => {
          refreshBtn.style.transform = "rotate(0deg)";
          // si existe la función global para refrescar provincia actual → ejecutarla
          if (typeof cargarProvinciaActual === "function") {
            cargarProvinciaActual();
          }
        }, 600);
      });
    }

    window.actualizarNombreProvincia = function (nombreProvincia) {
      const nombreEl = document.querySelector(".nombre-p");
      if (nombreEl) {
        nombreEl.textContent = nombreProvincia || "Argentina";
      }
    };
  })
  .catch(error => console.error("Error al cargar el header:", error));
