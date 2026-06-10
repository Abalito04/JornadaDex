const areaSelect = document.getElementById("areaSelect");
const taskSelect = document.getElementById("taskSelect");
const themeToggles = document.querySelectorAll("[data-theme-toggle], #themeToggle");
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
      taskSelect.innerHTML = '<option value="">Seleccionar area primero</option>';
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
