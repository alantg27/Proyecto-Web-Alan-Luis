from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from db import Ticket, Catalogo
import re
import random
import io
import string
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
import qrcode
from api.niveles import niveles_api
from api.municipios import municipios_api
from api.asunto import asuntos_api

app = Flask(__name__)
app.secret_key = "clave_secreta_para_flask"

app.register_blueprint(niveles_api)
app.register_blueprint(municipios_api)
app.register_blueprint(asuntos_api)

def generar_captcha_text(length=5):
    chars = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
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


@app.route("/comprobante/<int:id_ticket>", methods=["GET"])
def ticket_comprobante(id_ticket):
    row = Ticket.obtener_por_id(id_ticket)
    if not row:
        flash("Ticket no encontrado.", "error")
        return redirect(url_for("index"))
    pdf_io = generar_pdf_comprobante_row(row)
    filename = f"comprobante_{row.get('curp','CURP')}_{row.get('turno','NA')}.pdf"
    return send_file(pdf_io, mimetype="application/pdf", as_attachment=True, download_name=filename)

def generar_pdf_comprobante_row(row):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4  # 595x842 aprox

    # Marco
    margen = 18 * mm
    c.setLineWidth(2)
    c.rect(margen, margen, width - 2*margen, height - 2*margen)

    # Título
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, height - margen - 10*mm, "Comprobante de Solicitud")

    # Datos
    c.setFont("Helvetica", 11)
    y = height - margen - 25*mm
    line_h = 7*mm

    def draw_kv(k, v):
        nonlocal y
        c.setFont("Helvetica-Bold", 11); c.drawString(margen + 10*mm, y, f"{k}:")
        c.setFont("Helvetica", 11);      c.drawString(margen + 55*mm, y, str(v) if v is not None else "")
        y -= line_h

    draw_kv("ID Ticket", row.get("id_ticket"))
    draw_kv("Turno", row.get("turno", "N/A"))
    draw_kv("Nombre completo", row.get("nombre_completo"))
    draw_kv("CURP", row.get("curp"))
    draw_kv("Nivel", row.get("nivel", ""))
    draw_kv("Municipio", row.get("municipio", ""))
    draw_kv("Asunto", row.get("asunto", ""))
    draw_kv("Estatus", row.get("status", "Pendiente"))
    draw_kv("Fecha de registro", row.get("fecha_generacion"))

    # Nota
    y -= 4*mm
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(margen + 10*mm, y, "Conserva este comprobante. El código QR contiene la CURP del solicitante.")
    y -= 2*mm

    # QR con la CURP
    qr_data = row.get("curp", "")
    # construir QR y convertir a PNG en memoria
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_buf.seek(0)
    qr_reader = ImageReader(qr_buf)
    qr_size = 40 * mm
    # Posicionar QR a la derecha
    c.drawImage(qr_reader, width - margen - qr_size - 10, height - margen - qr_size - 10, qr_size, qr_size, preserveAspectRatio=True, mask='auto')
    c.setFont("Helvetica", 8)
    c.drawRightString(width - margen - 10, height - margen - qr_size - 14, "QR: CURP")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf

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
        return redirect(url_for("ticket_comprobante", id_ticket=t.id_ticket))

    return render_template("ticket.html")

# Formulario para buscar ticket público
@app.route("/modificar_publico", methods=["GET", "POST"])
def modificar_publico():
    if request.method == "POST":
        curp = request.form.get("curp", "").strip().upper()
        turno = request.form.get("turno", "").strip()

        # Buscamos el ticket por CURP y turno
        ticket = Ticket.obtener_por_curp_turno(curp, turno)
        if ticket:
            return redirect(url_for("editar_publico", id_ticket=ticket["id_ticket"]))
        else:
            return render_template("modificar_publico.html", form_data=request.form)

    return render_template("modificar_publico.html")

# Editar ticket público
@app.route("/modificar_publico/editar/<int:id_ticket>", methods=["GET", "POST"])
def editar_publico(id_ticket):
    ticket = Ticket.obtener_por_id(id_ticket)
    if not ticket:
        return redirect(url_for("modificar_publico"))

    if request.method == "POST":
        # Obtenemos los datos del formulario
        nuevos_datos = {
            "nombre_completo": request.form.get("nombreCompleto", "").strip(),
            "curp": ticket["curp"],  # CURP no se puede modificar
            "nombre": request.form.get("nombre", "").strip(),
            "paterno": request.form.get("paterno", "").strip(),
            "materno": request.form.get("materno", "").strip(),
            "telefono": request.form.get("telefono", "").strip(),
            "celular": request.form.get("celular", "").strip(),
            "correo": request.form.get("correo", "").strip(),
            "id_nivel": request.form.get("nivel"),
            "id_municipio": ticket["id_municipio"],  # Municipio no se puede modificar
            "id_asunto": request.form.get("asunto"),
            "status": request.form.get("status", ticket["status"])
        }

        Ticket.actualizar(id_ticket, nuevos_datos)
        ticket = Ticket.obtener_por_id(id_ticket)
        return render_template("ticket_editar_publico.html", ticket=ticket, exito=True, id_ticket=id_ticket)

    return render_template("ticket_editar_publico.html", ticket=ticket)


@app.route("/publico")
def publico():
    return render_template("publico_menu.html")



def _require_admin():
    if not session.get("is_admin"):
        flash("Debes iniciar sesión como administrador.", "error")
        return False
    return True

@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    return redirect(url_for("index"))

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

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
