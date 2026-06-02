const areaSelect = document.getElementById("areaSelect");
const taskSelect = document.getElementById("taskSelect");

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
