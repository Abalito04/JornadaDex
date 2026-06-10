const areaSelect = document.getElementById("areaSelect");
const taskSelect = document.getElementById("taskSelect");
const themeToggles = document.querySelectorAll("[data-theme-toggle], #themeToggle");
const previewTabs = document.querySelectorAll("[data-preview-tab]");
const previewPanels = document.querySelectorAll("[data-preview-panel]");
const previewTitle = document.querySelector("[data-preview-title]");
const previewCopy = document.querySelector("[data-preview-copy]");
const smoothLinks = document.querySelectorAll(".landing-menu a[href^='#'], .landing-cta a[href^='#']");
const root = document.documentElement;
const themeStorageKey = "trazalab-theme";

let themePreference = localStorage.getItem(themeStorageKey) || "system";

function applyTheme() {
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const resolvedTheme = themePreference === "system" ? (prefersDark ? "dark" : "light") : themePreference;
  root.dataset.theme = resolvedTheme;

  themeToggles.forEach((themeToggle) => {
    themeToggle.innerHTML = resolvedTheme === "dark" ? '<i data-lucide="sun"></i>' : '<i data-lucide="moon"></i>';
  });

  if (window.lucide) {
    window.lucide.createIcons();
  }
}

if (areaSelect && taskSelect) {
  areaSelect.addEventListener("change", async () => {
    taskSelect.innerHTML = '<option value="">Cargando...</option>';
    if (!areaSelect.value) {
      taskSelect.innerHTML = '<option value="">Seleccionar área primero</option>';
      return;
    }
    const response = await fetch(`/areas/${areaSelect.value}/tasks.json`);
    const tasks = await response.json();
    taskSelect.innerHTML = '<option value="">Seleccionar</option>';
    tasks.forEach((task) => {
      const option = document.createElement("option");
      option.value = task.id;
      option.textContent = task.name;
      taskSelect.appendChild(option);
    });
  });
}

if (previewTabs.length && previewPanels.length) {
  const previewContent = {
    tiempos: {
      title: "32:45hs",
      copy: "Horas registradas por área, con formato 24hs y trazabilidad por tarea.",
    },
    supervision: {
      title: "3 equipos",
      copy: "El supervisor ve avances del equipo y puede revisar registros con contexto.",
    },
    reportes: {
      title: "186 registros",
      copy: "Los reportes resumen empleados, clientes, áreas y registros del período.",
    },
  };

  previewTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const selected = tab.dataset.previewTab;
      previewTabs.forEach((item) => item.classList.toggle("active", item === tab));
      previewPanels.forEach((panel) => {
        panel.classList.toggle("hidden", panel.dataset.previewPanel !== selected);
      });
      if (previewTitle && previewContent[selected]) {
        previewTitle.textContent = previewContent[selected].title;
      }
      if (previewCopy && previewContent[selected]) {
        previewCopy.textContent = previewContent[selected].copy;
      }
      if (window.lucide) {
        window.lucide.createIcons();
      }
    });
  });
}

smoothLinks.forEach((link) => {
  link.addEventListener("click", (event) => {
    const target = document.querySelector(link.getAttribute("href"));
    if (!target) {
      return;
    }
    event.preventDefault();
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

themeToggles.forEach((themeToggle) => {
  themeToggle.addEventListener("click", () => {
    const currentTheme = root.dataset.theme || "light";
    themePreference = currentTheme === "dark" ? "light" : "dark";
    localStorage.setItem(themeStorageKey, themePreference);
    applyTheme();
  });
});

window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if (themePreference === "system") {
    applyTheme();
  }
});

applyTheme();
