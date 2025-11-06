import io
import re
from flask import app, flash, redirect, render_template, request, send_file, url_for
import qrcode
from controllers.ticket_controller import ticket_bp
from models.ticket import Ticket
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from models.catalogos_api import obtener_niveles, obtener_municipios, obtener_asuntos




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