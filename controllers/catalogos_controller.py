from flask import render_template, request, redirect, url_for, flash, Blueprint

from controllers.main_controller import _require_admin
from models.catalogo import Catalogo


catalogos_bp = Blueprint('catalogos_bp', __name__)


def _catalogo_display_name(tipo):
    return {"asunto": "Asuntos", "nivel": "Niveles", "municipio": "Municipios"}.get(tipo, tipo)

@catalogos_bp.route("/admin/catalogos/<tipo>", methods=["GET"])
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

@catalogos_bp.route("/admin/catalogos/<tipo>/new", methods=["GET", "POST"])
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

@catalogos_bp.route("/admin/catalogos/<tipo>/<int:id_item>/edit", methods=["GET", "POST"])
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

@catalogos_bp.route("/admin/catalogos/<tipo>/<int:id_item>/delete", methods=["POST"])
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