from flask import Blueprint, jsonify
from db import obtener_niveles

niveles_api = Blueprint("niveles_api", __name__)

@niveles_api.route("/api/niveles", methods=["GET"])
def api_niveles():
    return jsonify(obtener_niveles())