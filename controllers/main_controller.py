from tkinter import Image
from flask import Blueprint, session
from flask import render_template, request, redirect, url_for, flash, session, send_file, jsonify, Blueprint
import random
import io
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from models.ticket import Ticket



main_bp = Blueprint('main_bp', __name__)


def generar_captcha_text(length=5):
    chars = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(chars) for _ in range(length))

@main_bp.route("/captcha_image")
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



@main_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")




@main_bp.route("/admin", methods=["GET", "POST"])
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
        session.pop("captcha_text", None)
        session["is_admin"] = True
        return redirect(url_for("ticket_bp.admin_panel"))
    else:
        flash("Usuario o contraseña inválidos.", "error")
        session["captcha_text"] = generar_captcha_text()
        return render_template("admin_login.html")
    


@main_bp.route("/publico")
def publico():
    return render_template("publico_menu.html")



def _require_admin():
    if not session.get("is_admin"):
        flash("Debes iniciar sesión como administrador.", "error")
        return False
    return True


@main_bp.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    return redirect(url_for("main_bp.index"))


@main_bp.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response