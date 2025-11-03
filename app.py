from flask import Flask, render_template, request, redirect, url_for, flash
from db import Ticket
import re

app = Flask(__name__)
app.secret_key = "clave_secreta_para_flask"


@app.route("/", methods=["GET", "POST"])
def ticket():
    if request.method == "POST":
        errores = []

        nombre_completo = request.form.get("nombreCompleto", "").strip()
        curp = request.form.get("curp", "").strip().upper()
        nombre = request.form.get("nombre", "").strip()
        paterno = request.form.get("paterno", "").strip()
        materno = request.form.get("materno", "").strip()
        telefono = request.form.get("telefono", "").strip()
        celular = request.form.get("celular", "").strip()
        correo = request.form.get("correo", "").strip()
        id_nivel = request.form.get("nivel")
        id_municipio = request.form.get("municipio")
        id_asunto = request.form.get("asunto")

        if not nombre_completo or not curp or not correo:
            errores.append("Los campos Nombre completo, CURP y Correo son obligatorios.")

        if not re.match(r"^[A-Z0-9]{18}$", curp):
            errores.append("La CURP debe tener 18 caracteres alfanuméricos.")

        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", correo):
            errores.append("El correo electrónico no es válido.")

        if telefono and not re.match(r"^[0-9]{10}$", telefono):
            errores.append("El teléfono debe tener 10 dígitos numéricos.")
        if celular and not re.match(r"^[0-9]{10}$", celular):
            errores.append("El celular debe tener 10 dígitos numéricos.")

        if not id_nivel or not id_municipio or not id_asunto:
            errores.append("Debe seleccionar nivel, municipio y asunto.")

        if errores:
            for e in errores:
                flash(e, "error")
            return redirect(url_for("ticket"))

        if Ticket.existe_curp(curp):
            flash("El CURP ingresado ya se encuentra registrado. No puede duplicar el ticket.", "error")
            return render_template("ticket.html", form_data=request.form)

        t = Ticket(
            nombre_completo=nombre_completo,
            curp=curp,
            nombre=nombre,
            paterno=paterno,
            materno=materno,
            telefono=telefono,
            celular=celular,
            correo=correo,
            id_nivel=id_nivel,
            id_municipio=id_municipio,
            id_asunto=id_asunto
        )
        t.guardar()

        flash("Formulario enviado y ticket registrado correctamente ✅", "success")
        return redirect(url_for("ticket"))

    return render_template("ticket.html")

if __name__ == "__main__":
    app.run(debug=True)
