document.addEventListener("DOMContentLoaded", () => {

  // Función genérica para llenar un select
  async function llenarSelect(url, selectId) {
    const select = document.getElementById(selectId);
    const selectedValue = select.dataset.selected || "";

    try {
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`Error al consultar ${url}`);
      const datos = await resp.json();

      // Limpiar opciones anteriores, excepto la primera
      select.innerHTML = '<option value="">Seleccione...</option>';

      datos.forEach(item => {
        const option = document.createElement("option");
        option.value = item.id;
        option.textContent = item.nombre;
        if (item.id == selectedValue) option.selected = true;
        select.appendChild(option);
      });

    } catch (error) {
      console.error(error);
    }
  }

  // Llenar cada select con su API correspondiente
  llenarSelect("/api/niveles", "nivel");
  llenarSelect("/api/municipios", "municipio");
  llenarSelect("/api/asuntos", "asunto");

});
