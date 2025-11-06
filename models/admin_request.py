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
        
        # Verificar si existe alguna solicitud con ese username
        cursor.execute("SELECT estado, id_request FROM admin_signup_request WHERE username=%s", (username,))
        existing_request = cursor.fetchone()
        if existing_request:
            estado = existing_request[0]
            id_request = existing_request[1]
            if estado == 'pendiente':
                raise ValueError("Ya existe una solicitud pendiente con ese usuario.")
            elif estado == 'rechazado':
                # Actualizar solicitud rechazada a pendiente
                cursor.execute(
                    "UPDATE admin_signup_request SET estado='pendiente', password_hash=%s, nombre=%s, email=%s, creado_en=NOW(), resuelto_en=NULL, resuelto_por=NULL, motivo_rechazo=NULL WHERE id_request=%s",
                    (pwd_hash, nombre, email, id_request)
                )
                conn.commit()
                return id_request
            else:  # aprobado
                raise ValueError(f"Ya existe una solicitud {estado} con ese usuario.")
        
        if email:
            cursor.execute("SELECT 1 FROM admin_user WHERE email=%s", (email,))
            if cursor.fetchone():
                raise ValueError("El correo ya está registrado.")
            # Verificar correo en solicitudes también
            cursor.execute("SELECT estado, id_request FROM admin_signup_request WHERE email=%s", (email,))
            existing_email = cursor.fetchone()
            if existing_email:
                estado = existing_email[0]
                id_request = existing_email[1]
                if estado == 'pendiente':
                    raise ValueError("Ya existe una solicitud pendiente con ese correo.")
                elif estado == 'rechazado':
                    # Actualizar solicitud rechazada a pendiente
                    cursor.execute(
                        "UPDATE admin_signup_request SET estado='pendiente', password_hash=%s, nombre=%s, email=%s, username=%s, creado_en=NOW(), resuelto_en=NULL, resuelto_por=NULL, motivo_rechazo=NULL WHERE id_request=%s",
                        (pwd_hash, nombre, email, username, id_request)
                    )
                    conn.commit()
                    return id_request
                else:  # aprobado
                    raise ValueError(f"Ya existe una solicitud {estado} con ese correo.")

        try:
            cursor.execute(
                "INSERT INTO admin_signup_request (username, password_hash, nombre, email) VALUES (%s, %s, %s, %s)",
                (username, pwd_hash, nombre, email)
            )
            conn.commit()
            return cursor.lastrowid
        except mysql.connector.errors.IntegrityError as e:
            # Manejo de errores de integridad no capturados previamente
            if 'uq_req_username' in str(e):
                raise ValueError("El usuario ya existe en el sistema.")
            elif 'email' in str(e):
                raise ValueError("El correo ya existe en el sistema.")
            else:
                raise ValueError(f"Error de integridad en la base de datos: {str(e)}")

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

    @staticmethod
    def get_by_username(username: str):
        """Obtener solicitud por username"""
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_signup_request WHERE username=%s", (username,))
        return cursor.fetchone()