from flask import Blueprint, jsonify
from db import obtener_municipios

municipios_api = Blueprint("municipios_api", __name__)

@municipios_api.route("/api/municipios", methods=["GET"])
def api_municipios():
    return jsonify(obtener_municipios())
