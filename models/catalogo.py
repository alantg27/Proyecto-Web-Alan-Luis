from models.db import DatabaseConnection
import mysql.connector

class Catalogo:
    TIPOS = {
        "asunto": {"tabla": "asunto", "id_col": "id_asunto", "nombre_col": "nombre"},
        "nivel": {"tabla": "nivel", "id_col": "id_nivel", "nombre_col": "nombre"},
        "municipio": {"tabla": "municipio", "id_col": "id_municipio", "nombre_col": "nombre"},
    }

    @staticmethod
    def _cfg(tipo):
        if tipo not in Catalogo.TIPOS:
            raise ValueError("Tipo de catálogo inválido")
        return Catalogo.TIPOS[tipo]

    @staticmethod
    def obtener_todos(tipo):
        cfg = Catalogo._cfg(tipo)
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT {cfg['id_col']} AS id, {cfg['nombre_col']} AS nombre FROM {cfg['tabla']} ORDER BY {cfg['nombre_col']}")
        return cursor.fetchall()

    @staticmethod
    def buscar(tipo, q):
        cfg = Catalogo._cfg(tipo)
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor(dictionary=True)
        like = f"%{q}%"
        cursor.execute(
            f"SELECT {cfg['id_col']} AS id, {cfg['nombre_col']} AS nombre FROM {cfg['tabla']} WHERE {cfg['nombre_col']} LIKE %s ORDER BY {cfg['nombre_col']}",
            (like,)
        )
        return cursor.fetchall()

    @staticmethod
    def obtener_por_id(tipo, id_):
        cfg = Catalogo._cfg(tipo)
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            f"SELECT {cfg['id_col']} AS id, {cfg['nombre_col']} AS nombre FROM {cfg['tabla']} WHERE {cfg['id_col']} = %s",
            (id_,)
        )
        return cursor.fetchone()

    @staticmethod
    def guardar(tipo, nombre):
        cfg = Catalogo._cfg(tipo)
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO {cfg['tabla']} ({cfg['nombre_col']}) VALUES (%s)", (nombre,))
        conn.commit()

    @staticmethod
    def actualizar(tipo, id_, nombre):
        cfg = Catalogo._cfg(tipo)
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {cfg['tabla']} SET {cfg['nombre_col']}=%s WHERE {cfg['id_col']}=%s",
            (nombre, id_,)
        )
        conn.commit()

    @staticmethod
    def eliminar(tipo, id_):
        cfg = Catalogo._cfg(tipo)
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()
        try:
            cursor.execute(f"DELETE FROM {cfg['tabla']} WHERE {cfg['id_col']}=%s", (id_,))
            conn.commit()
            return True
        except mysql.connector.Error:
            return False
