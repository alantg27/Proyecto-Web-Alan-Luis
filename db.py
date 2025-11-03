import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",          # usuario por defecto en XAMPP
        password="",          # sin contraseña
        database="ticket_turno"  # el nombre de tu base de datos
    )

# ------------------------------
# CLASE MODELO: Ticket
# ------------------------------
class Ticket:
    def __init__(self, nombre_completo, curp, nombre, paterno, materno,
                 telefono, celular, correo, id_nivel, id_municipio, id_asunto):
        self.nombre_completo = nombre_completo
        self.curp = curp
        self.nombre = nombre
        self.paterno = paterno
        self.materno = materno
        self.telefono = telefono
        self.celular = celular
        self.correo = correo
        self.id_nivel = id_nivel
        self.id_municipio = id_municipio
        self.id_asunto = id_asunto

    # ---------- CREATE ----------
    def guardar(self):
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
        INSERT INTO ticket (
            nombre_completo, curp, nombre, paterno, materno,
            telefono, celular, correo, id_nivel, id_municipio, id_asunto
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        valores = (
            self.nombre_completo, self.curp, self.nombre, self.paterno,
            self.materno, self.telefono, self.celular, self.correo,
            self.id_nivel, self.id_municipio, self.id_asunto
        )
        cursor.execute(sql, valores)
        conn.commit()
        conn.close()

    # ---------- READ ----------
    @staticmethod
    def obtener_todos():
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.*, n.nombre AS nivel, m.nombre AS municipio, a.nombre AS asunto
            FROM ticket t
            LEFT JOIN nivel n ON t.id_nivel = n.id_nivel
            LEFT JOIN municipio m ON t.id_municipio = m.id_municipio
            LEFT JOIN asunto a ON t.id_asunto = a.id_asunto
            ORDER BY fecha_generacion DESC
        """)
        datos = cursor.fetchall()
        conn.close()
        return datos

    # ---------- UPDATE ----------
    @staticmethod
    def actualizar(id_ticket, nuevos_datos):
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
        UPDATE ticket
        SET nombre_completo=%s, curp=%s, nombre=%s, paterno=%s, materno=%s,
            telefono=%s, celular=%s, correo=%s, id_nivel=%s, id_municipio=%s, id_asunto=%s
        WHERE id_ticket=%s
        """
        valores = (
            nuevos_datos["nombre_completo"], nuevos_datos["curp"],
            nuevos_datos["nombre"], nuevos_datos["paterno"], nuevos_datos["materno"],
            nuevos_datos["telefono"], nuevos_datos["celular"], nuevos_datos["correo"],
            nuevos_datos["id_nivel"], nuevos_datos["id_municipio"], nuevos_datos["id_asunto"],
            id_ticket
        )
        cursor.execute(sql, valores)
        conn.commit()
        conn.close()

    # ---------- DELETE ----------
    @staticmethod
    def eliminar(id_ticket):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ticket WHERE id_ticket = %s", (id_ticket,))
        conn.commit()
        conn.close()


    # ---------- VERIFICAR DUPLICADO DE CURP ----------
    @staticmethod
    def existe_curp(curp):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ticket WHERE curp = %s", (curp,))
        existe = cursor.fetchone()[0] > 0
        conn.close()
        return existe
