fetch("header.html")
  .then(response => response.text())
  .then(data => {
    document.getElementById("header").innerHTML = data;

    // =============================
    //       TEMA CLARO / OSCURO
    // =============================
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

      // Sincronizar el checkbox visualmente
      const checkbox = document.querySelector(".theme-switch__checkbox");
      if (checkbox) checkbox.checked = isDark;
    }

    // Ejecutar apenas se inserta el header
    loadSavedTheme();

    // Listener del toggle
    const themeToggle = document.querySelector(".theme-switch__checkbox");
    if (themeToggle) {
      themeToggle.addEventListener("change", (e) => {
        setTheme(e.target.checked);

        // Si hay clima cargado y una función visual, actualizar
        if (window.provinciaActual && typeof updateVisuals === "function") {
          const provKey = window.provinciaActual.toLowerCase()
            .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
            .replace(/\s+/g, "_");

          const clima = window.climaPorProvincia?.[provKey];
          if (clima) updateVisuals(clima);
        }
      });
    }

    // =============================
    //            HOME
    // =============================
    const homeIcon = document.querySelector(".icon");
    if (homeIcon) {
      homeIcon.style.cursor = "pointer";
      homeIcon.addEventListener("click", () => {
        window.location.href = "index.html";
      });
    }

    // =============================
    //            REFRESH
    // =============================
    const refreshBtn = document.querySelector(".refresh-btn svg");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => {
        refreshBtn.style.transition = "transform 0.6s ease";
        refreshBtn.style.transform = "rotate(360deg)";

        setTimeout(() => {
          refreshBtn.style.transform = "rotate(0deg)";

          // Si la página tiene función para refrescar clima
          if (typeof cargarProvinciaActual === "function") {
            cargarProvinciaActual();
          }
        }, 600);
      });
    }

    // =============================
    //   ACTUALIZAR NOMBRE PROVINCIA
    // =============================
    window.actualizarNombreProvincia = function (nombreProvincia) {
      const nombreEl = document.querySelector(".nombre-p");
      if (nombreEl) {
        nombreEl.textContent = nombreProvincia || "Argentina";
      }
    };
  })
  .catch(error => console.error("Error al cargar el header:", error));
