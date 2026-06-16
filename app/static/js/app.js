const areaSelect = document.getElementById("areaSelect");
const taskSelect = document.getElementById("taskSelect");
const themeToggles = document.querySelectorAll("[data-theme-toggle], #themeToggle");
const previewTabs = document.querySelectorAll("[data-preview-tab]");
const previewPanels = document.querySelectorAll("[data-preview-panel]");
const previewTitle = document.querySelector("[data-preview-title]");
const previewCopy = document.querySelector("[data-preview-copy]");
const smoothLinks = document.querySelectorAll(".landing-menu a[href^='#'], .landing-cta a[href^='#'], .landing-footer a[href^='#']");
const revealItems = document.querySelectorAll(".landing-copy, .landing-preview, .landing-section, .landing-day, .landing-evidence, .landing-band");
const conditionalToggles = document.querySelectorAll("[data-conditional-toggle]");
const timeBudgetInputs = document.querySelectorAll("[data-time-budget-input]");
const currencyInputs = document.querySelectorAll("[data-currency-input]");
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
      title: "Tareas en curso",
      copy: "Horas registradas por área, con formato 24hs y trazabilidad por tarea.",
    },
    supervision: {
      title: "Supervisión activa",
      copy: "El encargado ve avances del equipo y puede revisar registros con contexto.",
    },
    reportes: {
      title: "Reportes listos",
      copy: "Los reportes resumen colaboradores, clientes, áreas y registros del período.",
    },
  };

  const selectPreviewTab = (tab, shouldRefreshIcons = true) => {
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
    if (shouldRefreshIcons && window.lucide) {
      window.lucide.createIcons();
    }
  };

  let previewAutoIndex = 0;
  let previewAutoTimer = null;
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  previewTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      if (previewAutoTimer) {
        window.clearInterval(previewAutoTimer);
      }
      previewAutoIndex = Array.from(previewTabs).indexOf(tab);
      selectPreviewTab(tab);
    });
  });

  if (!prefersReducedMotion) {
    previewAutoTimer = window.setInterval(() => {
      previewAutoIndex = (previewAutoIndex + 1) % previewTabs.length;
      selectPreviewTab(previewTabs[previewAutoIndex], false);
    }, 4200);
  }
}

conditionalToggles.forEach((toggle) => {
  const target = document.getElementById(toggle.dataset.conditionalToggle);
  if (!target) {
    return;
  }

  const syncConditionalField = () => {
    target.classList.toggle("hidden", toggle.value !== "1");
  };

  toggle.addEventListener("change", syncConditionalField);
  syncConditionalField();
});

timeBudgetInputs.forEach((input) => {
  input.addEventListener("blur", () => {
    const cleanValue = input.value.trim().toLowerCase().replace("hs", "");
    if (!cleanValue) {
      return;
    }
    let hours = 0;
    let minutes = 0;
    if (cleanValue.includes(":")) {
      const parts = cleanValue.split(":");
      hours = Number.parseInt(parts[0] || "0", 10);
      minutes = Number.parseInt(parts[1] || "0", 10);
    } else {
      hours = Number.parseInt(cleanValue || "0", 10);
    }
    if (Number.isNaN(hours) || Number.isNaN(minutes)) {
      return;
    }
    minutes = Math.min(Math.max(minutes, 0), 59);
    input.value = `${String(Math.max(hours, 0)).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
  });
});

currencyInputs.forEach((input) => {
  input.addEventListener("blur", () => {
    const cleanValue = input.value.trim().replace("$", "").replaceAll(" ", "");
    if (!cleanValue) {
      return;
    }
    const normalizedValue = cleanValue.includes(",")
      ? cleanValue.replaceAll(".", "").replace(",", ".")
      : cleanValue.replaceAll(".", "");
    const amount = Number.parseFloat(normalizedValue);
    if (Number.isNaN(amount)) {
      return;
    }
    input.value = `$ ${Math.round(amount).toLocaleString("es-AR")}`;
  });
});

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

if (revealItems.length) {
  if ("IntersectionObserver" in window) {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in-view");
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.14 });

    revealItems.forEach((item) => revealObserver.observe(item));
  } else {
    revealItems.forEach((item) => item.classList.add("in-view"));
  }
}

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
