from werkzeug.security import generate_password_hash
from .db import DatabaseConnection
from .admin import Admin
import mysql.connector

class AdminRequest:
    @staticmethod
    def create(username: str, password_plain: str, nombre: str = None, email: str = None):
        pwd_hash = generate_password_hash(password_plain)
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM admin_user WHERE username=%s", (username,))
        if cursor.fetchone():
            raise ValueError("El usuario ya existe.")
        cursor.execute("SELECT 1 FROM admin_signup_request WHERE username=%s AND estado='pendiente'", (username,))
        if cursor.fetchone():
            raise ValueError("Ya existe una solicitud pendiente con ese usuario.")
        if email:
            cursor.execute("SELECT 1 FROM admin_user WHERE email=%s", (email,))
            if cursor.fetchone():
                raise ValueError("El correo ya está registrado.")
            cursor.execute("SELECT 1 FROM admin_signup_request WHERE email=%s AND estado='pendiente'", (email,))
            if cursor.fetchone():
                raise ValueError("Ya existe una solicitud pendiente con ese correo.")

        cursor.execute(
            "INSERT INTO admin_signup_request (username, password_hash, nombre, email) VALUES (%s, %s, %s, %s)",
            (username, pwd_hash, nombre, email)
        )
        conn.commit()
        return cursor.lastrowid

    @staticmethod
    def listar(estado: str = "pendiente"):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor(dictionary=True)
        if estado:
            cursor.execute("SELECT * FROM admin_signup_request WHERE estado=%s ORDER BY creado_en DESC", (estado,))
        else:
            cursor.execute("SELECT * FROM admin_signup_request ORDER BY creado_en DESC")
        return cursor.fetchall()

    @staticmethod
    def obtener(id_request: int):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_signup_request WHERE id_request=%s", (id_request,))
        return cursor.fetchone()

    @staticmethod
    def aprobar(id_request: int, id_admin_actual: int):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_signup_request WHERE id_request=%s FOR UPDATE", (id_request,))
        row = cursor.fetchone()
        if not row:
            raise ValueError("Solicitud no encontrada.")
        if row["estado"] != "pendiente":
            raise ValueError("La solicitud ya fue resuelta.")

        c2 = conn.cursor()
        c2.execute("SELECT 1 FROM admin_user WHERE username=%s", (row["username"],))
        if c2.fetchone():
            raise ValueError("El usuario ya existe como administrador.")

        c2.execute(
            "INSERT INTO admin_user (username, password_hash, nombre, email, activo) VALUES (%s, %s, %s, %s, 1)",
            (row["username"], row["password_hash"], row.get("nombre"), row.get("email"))
        )
        c2.execute(
            "UPDATE admin_signup_request SET estado='aprobado', resuelto_en=NOW(), resuelto_por=%s WHERE id_request=%s",
            (id_admin_actual, id_request)
        )
        conn.commit()
        return True

    @staticmethod
    def rechazar(id_request: int, id_admin_actual: int, motivo: str = None):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE admin_signup_request SET estado='rechazado', motivo_rechazo=%s, resuelto_en=NOW(), resuelto_por=%s WHERE id_request=%s AND estado='pendiente'",
            (motivo, id_admin_actual, id_request)
        )
        if cursor.rowcount == 0:
            raise ValueError("Solicitud no encontrada o ya resuelta.")
        conn.commit()
        return True