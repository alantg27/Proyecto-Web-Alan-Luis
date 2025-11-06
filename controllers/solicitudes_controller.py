from flask import render_template, request, redirect, url_for, flash, session, Blueprint
from controllers.main_controller import _require_admin
from models.admin_request import AdminRequest

solicitudes_bp = Blueprint('solicitudes_bp', __name__)

@solicitudes_bp.route("/admin/solicitudes", methods=["GET"])
def admin_solicitudes():
    if not _require_admin():
        return redirect(url_for("main_bp.admin"))
    estado = request.args.get("estado","pendiente")
    items = AdminRequest.listar(estado=estado if estado in ("pendiente","aprobado","rechazado") else "pendiente")
    return render_template("admin_solicitudes.html", items=items, estado=estado)

@solicitudes_bp.route("/admin/solicitudes/<int:id_request>/approve", methods=["POST"])
def admin_solicitud_approve(id_request):
    if not _require_admin():
        return redirect(url_for("main_bp.admin"))
    try:
        AdminRequest.aprobar(id_request, session.get("admin_id"))
        flash("Solicitud aprobada y administrador creado.", "success")
    except ValueError as ex:
        flash(str(ex), "error")
    return redirect(url_for("solicitudes_bp.admin_solicitudes"))

@solicitudes_bp.route("/admin/solicitudes/<int:id_request>/reject", methods=["POST"])
def admin_solicitud_reject(id_request):
    if not _require_admin():
        return redirect(url_for("main_bp.admin"))
    motivo = request.form.get("motivo","").strip() or None
    try:
        AdminRequest.rechazar(id_request, session.get("admin_id"), motivo)
        flash("Solicitud rechazada.", "success")
    except ValueError as ex:
        flash(str(ex), "error")
    return redirect(url_for("solicitudes_bp.admin_solicitudes"))