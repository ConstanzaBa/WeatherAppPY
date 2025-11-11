fetch("header.html")
  .then(response => response.text())
  .then(data => {
    document.getElementById("header").innerHTML = data;

    // === INICIO: Funciones de tema claro/oscuro ===
    function setTheme(isDark) {
      const root = document.documentElement;
      if (isDark) {
        root.classList.add("dark-theme");
        localStorage.setItem("theme", "dark");
      } else {
        root.classList.remove("dark-theme");
        localStorage.setItem("theme", "light");
      }
    }

    function loadSavedTheme() {
      const saved = localStorage.getItem("theme");
      const isDark = saved === "dark";
      setTheme(isDark);

      // sincronizar el estado visual del toggle
      const checkbox = document.querySelector(".theme-switch__checkbox");
      if (checkbox) checkbox.checked = isDark;
    }

    // Cargar tema guardado al insertar el header
    loadSavedTheme();

    // Listener para el toggle
    const themeToggle = document.querySelector(".theme-switch__checkbox");
    if (themeToggle) {
      themeToggle.addEventListener("change", (e) => {
        setTheme(e.target.checked);
      });
    }
    // === FIN: Funciones de tema claro/oscuro ===

    // === HOME ICON ===
    const homeIcon = document.querySelector(".icon");
    if (homeIcon) {
      homeIcon.style.cursor = "pointer";
      homeIcon.addEventListener("click", () => {
        window.location.href = "index.html";
      });
    }

    // === REFRESH BUTTON ===
    const refreshBtn = document.querySelector(".refresh-btn svg");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => {
        refreshBtn.style.transition = "transform 0.6s ease";
        refreshBtn.style.transform = "rotate(360deg)";

        setTimeout(() => {
          refreshBtn.style.transform = "rotate(0deg)";
          // Si existe la función global para refrescar provincia actual → ejecutarla
          if (typeof cargarProvinciaActual === "function") {
            cargarProvinciaActual();
          }
        }, 600);
      });
    }

    // === ACTUALIZAR NOMBRE DE PROVINCIA ===
    window.actualizarNombreProvincia = function (nombreProvincia) {
      const nombreEl = document.querySelector(".nombre-p");
      if (nombreEl) {
        nombreEl.textContent = nombreProvincia || "Argentina";
      }
    };
  })
  .catch(error => console.error("Error al cargar el header:", error));
