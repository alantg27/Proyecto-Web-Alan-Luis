document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    let valido = true;

    form.querySelectorAll(".error").forEach(el => el.remove());
    form.querySelectorAll(".input-error").forEach(el => el.classList.remove("input-error"));

    const campos = form.querySelectorAll("input, select");

    campos.forEach(campo => {
      if (campo.type !== "submit") {
        const valor = campo.value.trim();
        let mensajeError = "";

        if (valor === "") {
          if (campo.tagName === "SELECT") {
            mensajeError = "Debe seleccionar una opción.";
          } else {
            mensajeError = "Este campo es obligatorio.";
          }
        } else if (campo.id === "correo") {
          const regexCorreo = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
          if (!regexCorreo.test(valor)) {
            mensajeError = "Ingrese un correo válido.";
          }
        } else if (campo.id === "curp") {
          const regexCurp = /^[A-Z0-9]{18}$/i;
          if (!regexCurp.test(valor)) {
            mensajeError = "La CURP debe tener 18 caracteres alfanuméricos.";
          }
        } else if (campo.id === "telefono" || campo.id === "celular") {
          const regexTel = /^[0-9]{10}$/;
          if (!regexTel.test(valor)) {
            mensajeError = "Debe tener 10 dígitos numéricos.";
          }
        }

        if (mensajeError !== "") {
          valido = false;
          campo.classList.add("input-error");

          const errorMsg = document.createElement("span");
          errorMsg.classList.add("error");
          errorMsg.textContent = mensajeError;
          campo.insertAdjacentElement("afterend", errorMsg);
        }
      }
    });

    if (valido) {
      form.submit();
    }
  });
});
