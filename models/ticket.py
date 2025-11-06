from .db import DatabaseConnection

class Ticket:
    def __init__(self, nombre_completo, curp, nombre, paterno, materno,
                 telefono, celular, correo, id_nivel, id_municipio, id_asunto, status="Pendiente"):
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
        self.status = status

    # ---------- CREATE ----------
    def guardar(self):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()

        cursor.execute("SELECT ultimo_turno FROM control_turno WHERE id_municipio=%s", (self.id_municipio,))
        last_turno = cursor.fetchone()[0]
        nuevo_turno = last_turno + 1
        cursor.execute(
            "UPDATE control_turno SET ultimo_turno=%s WHERE id_municipio=%s",
            (nuevo_turno, self.id_municipio)
        )
        self.turno = nuevo_turno

        sql = """
        INSERT INTO ticket (
            nombre_completo, curp, nombre, paterno, materno,
            telefono, celular, correo, id_nivel, id_municipio, id_asunto, status, turno
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        valores = (
            self.nombre_completo, self.curp, self.nombre, self.paterno,
            self.materno, self.telefono, self.celular, self.correo,
            self.id_nivel, self.id_municipio, self.id_asunto, self.status, self.turno
        )
        cursor.execute(sql, valores)
        self.id_ticket = cursor.lastrowid  # id insertado
        conn.commit()

    # ---------- READ ----------
    @staticmethod
    def obtener_todos():
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.*, n.nombre AS nivel, m.nombre AS municipio, a.nombre AS asunto
            FROM ticket t
            LEFT JOIN nivel n ON t.id_nivel = n.id_nivel
            LEFT JOIN municipio m ON t.id_municipio = m.id_municipio
            LEFT JOIN asunto a ON t.id_asunto = a.id_asunto
            ORDER BY fecha_generacion DESC
        """)
        return cursor.fetchall()

    # ---------- UPDATE ----------
    @staticmethod
    def actualizar(id_ticket, nuevos_datos):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()
        sql = """
        UPDATE ticket
        SET nombre_completo=%s, curp=%s, nombre=%s, paterno=%s, materno=%s,
            telefono=%s, celular=%s, correo=%s, id_nivel=%s, id_municipio=%s, id_asunto=%s, status=%s
        WHERE id_ticket=%s
        """
        valores = (
            nuevos_datos["nombre_completo"], nuevos_datos["curp"],
            nuevos_datos["nombre"], nuevos_datos["paterno"], nuevos_datos["materno"],
            nuevos_datos["telefono"], nuevos_datos["celular"], nuevos_datos["correo"],
            nuevos_datos["id_nivel"], nuevos_datos["id_municipio"], nuevos_datos["id_asunto"],
            nuevos_datos["status"], id_ticket
        )
        cursor.execute(sql, valores)
        conn.commit()

    # ---------- DELETE ----------
    @staticmethod
    def eliminar(id_ticket):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ticket WHERE id_ticket = %s", (id_ticket,))
        conn.commit()

    @staticmethod
    def existe_curp(curp):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ticket WHERE curp = %s", (curp,))
        return cursor.fetchone()[0] > 0

    @staticmethod
    def existe_curp_activo(curp):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ticket WHERE curp = %s AND status <> 'Resuelto'", (curp,))
        return cursor.fetchone()[0] > 0

    @staticmethod
    def obtener_por_id(id_ticket):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.*, n.nombre AS nivel, m.nombre AS municipio, a.nombre AS asunto
            FROM ticket t
            LEFT JOIN nivel n ON t.id_nivel = n.id_nivel
            LEFT JOIN municipio m ON t.id_municipio = m.id_municipio
            LEFT JOIN asunto a ON t.id_asunto = a.id_asunto
            WHERE t.id_ticket = %s
        """, (id_ticket,))
        return cursor.fetchone()

    @staticmethod
    def buscar(curp=None, q=None):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor(dictionary=True)
        if curp:
            cursor.execute("""
                SELECT t.*, n.nombre AS nivel, m.nombre AS municipio, a.nombre AS asunto
                FROM ticket t
                LEFT JOIN nivel n ON t.id_nivel = n.id_nivel
                LEFT JOIN municipio m ON t.id_municipio = m.id_municipio
                LEFT JOIN asunto a ON t.id_asunto = a.id_asunto
                WHERE t.curp = %s
                ORDER BY t.fecha_generacion DESC
            """, (curp,))
            return cursor.fetchall()

        if q:
            like = f"%{q}%"
            cursor.execute("""
                SELECT t.*, n.nombre AS nivel, m.nombre AS municipio, a.nombre AS asunto
                FROM ticket t
                LEFT JOIN nivel n ON t.id_nivel = n.id_nivel
                LEFT JOIN municipio m ON t.id_municipio = m.id_municipio
                LEFT JOIN asunto a ON t.id_asunto = a.id_asunto
                WHERE t.nombre_completo LIKE %s OR t.nombre LIKE %s OR t.paterno LIKE %s OR t.materno LIKE %s
                ORDER BY t.fecha_generacion DESC
            """, (like, like, like, like))
            return cursor.fetchall()

        return []

    @staticmethod
    def contar_por_status(id_municipio=None):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()
        if id_municipio:
            cursor.execute(
                "SELECT status, COUNT(*) FROM ticket WHERE id_municipio = %s GROUP BY status",
                (id_municipio,)
            )
        else:
            cursor.execute("SELECT status, COUNT(*) FROM ticket GROUP BY status")

        rows = cursor.fetchall()
        pendientes = 0
        resueltos = 0
        for status, cnt in rows:
            if status == "Pendiente":
                pendientes = cnt
            elif status == "Resuelto":
                resueltos = cnt
        total = pendientes + resueltos
        return {"Pendiente": pendientes, "Resuelto": resueltos, "Total": total}

    @staticmethod
    def obtener_por_curp_turno(curp, turno):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.*, n.nombre AS nivel, m.nombre AS municipio, a.nombre AS asunto
            FROM ticket t
            LEFT JOIN nivel n ON t.id_nivel = n.id_nivel
            LEFT JOIN municipio m ON t.id_municipio = m.id_municipio
            LEFT JOIN asunto a ON t.id_asunto = a.id_asunto
            WHERE t.curp = %s AND t.turno = %s
        """, (curp, turno))
        return cursor.fetchone()
