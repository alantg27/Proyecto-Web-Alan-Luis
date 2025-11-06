from flask import render_template, request, redirect, url_for, flash, session, send_file, jsonify, Blueprint

from controllers.main_controller import _require_admin
from models.catalogo import Catalogo
from models.ticket import Ticket


dashboard_bp = Blueprint('dashboard_bp', __name__)


@dashboard_bp.route("/admin/dashboard", methods=["GET"])
def admin_dashboard():
    if not _require_admin():
        return redirect(url_for("main_bp.admin"))
    municipios = Catalogo.obtener_todos("municipio")
    selected = request.args.get("municipio", "").strip()
    return render_template("admin_dashboard.html", municipios=municipios, selected=selected)

@dashboard_bp.route("/admin/dashboard/data", methods=["GET"])
def admin_dashboard_data():
    if not _require_admin():
        return jsonify({"error": "unauthorized"}), 401
    m = request.args.get("municipio", "").strip()
    id_municipio = int(m) if m.isdigit() else None
    data = Ticket.contar_por_status(id_municipio=id_municipio)
    return jsonify(data)