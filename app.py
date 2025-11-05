from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from db import Ticket, Catalogo
import re
import random
import io
import string
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = Flask(__name__)
app.secret_key = "clave_secreta_para_flask"

def generar_captcha_text(length=5):
    chars = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # evitar O,0,I,1 confusos
    return "".join(random.choice(chars) for _ in range(length))

@app.route("/captcha_image")
def captcha_image():
    texto = session.get("captcha_text")
    if not texto:
        texto = generar_captcha_text()
        session["captcha_text"] = texto

    width, height = 200, 70
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    for i in range(6):
        start = (random.randint(0, width), random.randint(0, height))
        end = (random.randint(0, width), random.randint(0, height))
        color = tuple(random.randint(100, 180) for _ in range(3))
        draw.line([start, end], fill=color, width=2)

    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except Exception:
        font = ImageFont.load_default()

    x = 10
    for ch in texto:
        y = random.randint(5, 20)
        fg = tuple(random.randint(0, 100) for _ in range(3))
        draw.text((x, y), ch, font=font, fill=fg)
        x += 34

    for _ in range(200):
        xy = (random.randint(0, width), random.randint(0, height))
        draw.point(xy, fill=tuple(random.randint(0, 255) for _ in range(3)))

    image = image.filter(ImageFilter.SMOOTH)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

def generar_captcha():
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    op = random.choice(['+', '-', '*'])
    if op == '+':
        resp = a + b
    elif op == '-':
        resp = a - b
    else:
        resp = a * b
    pregunta = f"{a} {op} {b} = ?"
    return pregunta, str(resp)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "GET" or "captcha_text" not in session:
        texto = generar_captcha_text()
        session["captcha_text"] = texto
        return render_template("admin_login.html")

    usuario = request.form.get("usuario", "").strip()
    contrasena = request.form.get("contrasena", "")
    captcha_input = request.form.get("captcha", "").strip()

    if not usuario or not contrasena or not captcha_input:
        flash("Todos los campos son obligatorios.", "error")
        session["captcha_text"] = generar_captcha_text()
        return render_template("admin_login.html")

    if captcha_input.lower() != session.get("captcha_text", "").lower():
        flash("Captcha incorrecto.", "error")
        session["captcha_text"] = generar_captcha_text()
        return render_template("admin_login.html")

    # credenciales de ejemplo (temporal, reemplazar por BDD cuando esté disponible)
    ADMIN_USER = "admin"
    ADMIN_PASS = "admin123"

    if usuario == ADMIN_USER and contrasena == ADMIN_PASS:
        #flash("Acceso de administrador concedido.", "success")
        # limpiar captcha de sesión por seguridad
        session.pop("captcha_text", None)
        session["is_admin"] = True
        return redirect(url_for("admin_panel"))
    else:
        flash("Usuario o contraseña inválidos.", "error")
        session["captcha_text"] = generar_captcha_text()
        return render_template("admin_login.html")


@app.route("/ticket", methods=["GET", "POST"])
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


        if Ticket.existe_curp_activo(curp):
            flash("Ya existe un ticket pendiente con esa CURP. Solo puedes crear otro cuando esté resuelto.", "error")
            return render_template("ticket.html", form_data=request.form)
        
#        if Ticket.existe_curp(curp):
#            flash("El CURP ingresado ya se encuentra registrado. No puede duplicar el ticket.", "error")
#            return render_template("ticket.html", form_data=request.form)

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
            id_asunto=id_asunto,
            status="Pendiente"  # por defecto
        )
        t.guardar()

        flash("Formulario enviado y ticket registrado correctamente", "success")
        return redirect(url_for("ticket"))

    return render_template("ticket.html")

def _require_admin():
    if not session.get("is_admin"):
        flash("Debes iniciar sesión como administrador.", "error")
        return False
    return True

@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    #flash("Sesión de administrador cerrada.", "success")
    return redirect(url_for("index"))

# PANEL: listar y buscar
@app.route("/admin/panel", methods=["GET"])
def admin_panel():
    if not _require_admin():
        return redirect(url_for("admin"))
    curp = request.args.get("curp", "").strip().upper()
    q = request.args.get("q", "").strip()
    if curp:
        tickets = Ticket.buscar(curp=curp)
    elif q:
        tickets = Ticket.buscar(q=q)
    else:
        tickets = Ticket.obtener_todos()
    return render_template("admin_panel.html", mode="list", tickets=tickets, form_data=None)

# CREAR
@app.route("/admin/ticket/new", methods=["GET", "POST"])
def admin_ticket_new():
    if not _require_admin():
        return redirect(url_for("admin"))
    if request.method == "GET":
        return render_template("admin_panel.html", mode="new", tickets=[], form_data={})

    # POST crear
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
    status = request.form.get("status", "Pendiente")
    if status not in ("Pendiente", "Resuelto"):
        status = "Pendiente"

    errores = []
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
    if Ticket.existe_curp(curp):
        errores.append("El CURP ingresado ya se encuentra registrado.")

    if errores:
        for e in errores:
            flash(e, "error")
        return render_template("admin_panel.html", mode="new", tickets=[], form_data=request.form)

    t = Ticket(
        nombre_completo=nombre_completo, curp=curp,
        nombre=nombre, paterno=paterno, materno=materno,
        telefono=telefono, celular=celular, correo=correo,
        id_nivel=id_nivel, id_municipio=id_municipio, id_asunto=id_asunto,
        status=status
    )
    t.guardar()
    flash("Ticket creado correctamente.", "success")
    return redirect(url_for("admin_panel"))

# EDITAR
@app.route("/admin/ticket/<int:id_ticket>/edit", methods=["GET", "POST"])
def admin_ticket_edit(id_ticket):
    if not _require_admin():
        return redirect(url_for("admin"))
    if request.method == "GET":
        row = Ticket.obtener_por_id(id_ticket)
        if not row:
            flash("Ticket no encontrado.", "error")
            return redirect(url_for("admin_panel"))
        # Adaptamos nombres para el formulario
        form_data = {
            "nombreCompleto": row.get("nombre_completo", ""),
            "curp": row.get("curp", ""),
            "nombre": row.get("nombre", ""),
            "paterno": row.get("paterno", ""),
            "materno": row.get("materno", ""),
            "telefono": row.get("telefono", ""),
            "celular": row.get("celular", ""),
            "correo": row.get("correo", ""),
            "nivel": str(row.get("id_nivel") or ""),
            "municipio": str(row.get("id_municipio") or ""),
            "asunto": str(row.get("id_asunto") or ""),
            "status": row.get("status", "Pendiente"),
        }
        return render_template("admin_panel.html", mode="edit", tickets=[], form_data=form_data, id_ticket=id_ticket)

    # POST actualizar
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
    status = request.form.get("status", "Pendiente")
    if status not in ("Pendiente", "Resuelto"):
        status = "Pendiente"

    errores = []
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

    # Evitar CURP duplicado de otro registro
    row_actual = Ticket.obtener_por_id(id_ticket)
    if not row_actual:
        flash("Ticket no encontrado.", "error")
        return redirect(url_for("admin_panel"))
    if curp != (row_actual.get("curp") or "") and Ticket.existe_curp_activo(curp):
        errores.append("El CURP ingresado ya se encuentra registrado en otro ticket pendiente.")

    if errores:
        for e in errores:
            flash(e, "error")
        return render_template("admin_panel.html", mode="edit", tickets=[], form_data=request.form, id_ticket=id_ticket)

    nuevos = {
        "nombre_completo": nombre_completo,
        "curp": curp,
        "nombre": nombre,
        "paterno": paterno,
        "materno": materno,
        "telefono": telefono,
        "celular": celular,
        "correo": correo,
        "id_nivel": id_nivel,
        "id_municipio": id_municipio,
        "id_asunto": id_asunto,
        "status": status
    }
    Ticket.actualizar(id_ticket, nuevos)
    flash("Ticket actualizado correctamente.", "success")
    return redirect(url_for("admin_panel"))

# ELIMINAR
@app.route("/admin/ticket/<int:id_ticket>/delete", methods=["POST"])
def admin_ticket_delete(id_ticket):
    if not _require_admin():
        return redirect(url_for("admin"))
    Ticket.eliminar(id_ticket)
    flash("Ticket eliminado.", "success")
    return redirect(url_for("admin_panel"))

def _catalogo_display_name(tipo):
    return {"asunto": "Asuntos", "nivel": "Niveles", "municipio": "Municipios"}.get(tipo, tipo)

@app.route("/admin/catalogos/<tipo>", methods=["GET"])
def admin_catalog_list(tipo):
    if not _require_admin():
        return redirect(url_for("admin"))
    try:
        q = request.args.get("q", "").strip()
        items = Catalogo.buscar(tipo, q) if q else Catalogo.obtener_todos(tipo)
        return render_template("admin_catalogs.html", tipo=tipo, titulo=_catalogo_display_name(tipo), mode="list", items=items, form_data=None, q=q)
    except ValueError:
        flash("Catálogo inválido.", "error")
        return redirect(url_for("admin_panel"))

@app.route("/admin/catalogos/<tipo>/new", methods=["GET", "POST"])
def admin_catalog_new(tipo):
    if not _require_admin():
        return redirect(url_for("admin"))
    try:
        if request.method == "GET":
            return render_template("admin_catalogs.html", tipo=tipo, titulo=_catalogo_display_name(tipo), mode="new", items=[], form_data={})
        nombre = request.form.get("nombre", "").strip()
        if not nombre:
            flash("El nombre es obligatorio.", "error")
            return render_template("admin_catalogs.html", tipo=tipo, titulo=_catalogo_display_name(tipo), mode="new", items=[], form_data=request.form)
        if len(nombre) > 50:
            flash("El nombre no debe exceder 50 caracteres.", "error")
            return render_template("admin_catalogs.html", tipo=tipo, titulo=_catalogo_display_name(tipo), mode="new", items=[], form_data=request.form)
        Catalogo.guardar(tipo, nombre)
        flash("Registro creado correctamente.", "success")
        return redirect(url_for("admin_catalog_list", tipo=tipo))
    except ValueError:
        flash("Catálogo inválido.", "error")
        return redirect(url_for("admin_panel"))

@app.route("/admin/catalogos/<tipo>/<int:id_item>/edit", methods=["GET", "POST"])
def admin_catalog_edit(tipo, id_item):
    if not _require_admin():
        return redirect(url_for("admin"))
    try:
        if request.method == "GET":
            row = Catalogo.obtener_por_id(tipo, id_item)
            if not row:
                flash("Registro no encontrado.", "error")
                return redirect(url_for("admin_catalog_list", tipo=tipo))
            return render_template("admin_catalogs.html", tipo=tipo, titulo=_catalogo_display_name(tipo), mode="edit", id_item=id_item, items=[], form_data={"nombre": row.get("nombre","")})
        # POST
        nombre = request.form.get("nombre", "").strip()
        if not nombre:
            flash("El nombre es obligatorio.", "error")
            return render_template("admin_catalogs.html", tipo=tipo, titulo=_catalogo_display_name(tipo), mode="edit", id_item=id_item, items=[], form_data=request.form)
        if len(nombre) > 50:
            flash("El nombre no debe exceder 50 caracteres.", "error")
            return render_template("admin_catalogs.html", tipo=tipo, titulo=_catalogo_display_name(tipo), mode="edit", id_item=id_item, items=[], form_data=request.form)
        Catalogo.actualizar(tipo, id_item, nombre)
        flash("Registro actualizado correctamente.", "success")
        return redirect(url_for("admin_catalog_list", tipo=tipo))
    except ValueError:
        flash("Catálogo inválido.", "error")
        return redirect(url_for("admin_panel"))

@app.route("/admin/catalogos/<tipo>/<int:id_item>/delete", methods=["POST"])
def admin_catalog_delete(tipo, id_item):
    if not _require_admin():
        return redirect(url_for("admin"))
    try:
        ok = Catalogo.eliminar(tipo, id_item)
        if ok:
            flash("Registro eliminado.", "success")
        else:
            flash("No es posible eliminar: existe información relacionada (tickets).", "error")
        return redirect(url_for("admin_catalog_list", tipo=tipo))
    except ValueError:
        flash("Catálogo inválido.", "error")
        return redirect(url_for("admin_panel"))

@app.route("/admin/dashboard", methods=["GET"])
def admin_dashboard():
    if not _require_admin():
        return redirect(url_for("admin"))
    municipios = Catalogo.obtener_todos("municipio")
    selected = request.args.get("municipio", "").strip()
    return render_template("admin_dashboard.html", municipios=municipios, selected=selected)

@app.route("/admin/dashboard/data", methods=["GET"])
def admin_dashboard_data():
    if not _require_admin():
        return jsonify({"error": "unauthorized"}), 401
    m = request.args.get("municipio", "").strip()
    id_municipio = int(m) if m.isdigit() else None
    data = Ticket.contar_por_status(id_municipio=id_municipio)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
