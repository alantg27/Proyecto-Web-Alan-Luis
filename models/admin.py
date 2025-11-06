from werkzeug.security import generate_password_hash
from .db import DatabaseConnection

class Admin:
    @staticmethod
    def get_by_username(username: str):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_user WHERE username=%s AND activo=1", (username,))
        return cursor.fetchone()

    @staticmethod
    def create(username: str, password_plain: str, nombre: str = None, email: str = None):
        pwd_hash = generate_password_hash(password_plain)
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO admin_user (username, password_hash, nombre, email) VALUES (%s, %s, %s, %s)",
            (username, pwd_hash, nombre, email)
        )
        conn.commit()
        return cursor.lastrowid