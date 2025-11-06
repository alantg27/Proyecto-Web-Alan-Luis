from flask import Blueprint, jsonify
from db import obtener_asuntos

asuntos_api = Blueprint("asuntos_api", __name__)

@asuntos_api.route("/api/asuntos", methods=["GET"])
def api_asuntos():
    return jsonify(obtener_asuntos())
