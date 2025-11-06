from flask import Blueprint, jsonify
from models.catalogos_api import obtener_niveles, obtener_municipios, obtener_asuntos

api_bp = Blueprint("api_bp", __name__)

@api_bp.route("/api/niveles")
def api_niveles():
    return jsonify(obtener_niveles())

@api_bp.route("/api/municipios")
def api_municipios():
    return jsonify(obtener_municipios())

@api_bp.route("/api/asuntos")
def api_asuntos():
    return jsonify(obtener_asuntos())
