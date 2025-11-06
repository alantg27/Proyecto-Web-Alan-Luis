from .db import DatabaseConnection

def obtener_niveles():
    conn = DatabaseConnection.get_instance()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_nivel AS id, nombre FROM nivel ORDER BY id_nivel")
    rows = cursor.fetchall()
    conn.close()
    return rows

def obtener_municipios():
    conn = DatabaseConnection.get_instance()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_municipio AS id, nombre FROM municipio ORDER BY id_municipio")
    rows = cursor.fetchall()
    conn.close()
    return rows

def obtener_asuntos():
    conn = DatabaseConnection.get_instance()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_asunto AS id, nombre FROM asunto ORDER BY id_asunto")
    rows = cursor.fetchall()
    conn.close()
    return rows