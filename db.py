import mysql.connector



#LUIS   CAMBIO DE CONEXION A LA BASE DE DATOS A SINGLETON AQUI POR SI CREAS LLAMADOS NUEVOS
class DatabaseConnection:
    _instance = None

    def __init__(self):
        self.conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="ticket_turno"
        )

    @classmethod
    def get_instance(cls):
        if cls._instance is None or not cls._instance.conn.is_connected():
            cls._instance = DatabaseConnection()
        return cls._instance.conn


# ------------------------------
# CLASE MODELO: Ticket
# ------------------------------
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
        conn.commit()
        conn.close()

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
        datos = cursor.fetchall()
        conn.close()
        return datos

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
        conn.close()

    # ---------- DELETE ----------
    @staticmethod
    def eliminar(id_ticket):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ticket WHERE id_ticket = %s", (id_ticket,))
        conn.commit()
        conn.close()


    # ---------- VERIFICAR DUPLICADO DE CURP ----------
    @staticmethod
    def existe_curp(curp):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ticket WHERE curp = %s", (curp,))
        existe = cursor.fetchone()[0] > 0
        conn.close()
        return existe

    @staticmethod
    def existe_curp_activo(curp):
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ticket WHERE curp = %s AND status <> 'Resuelto'", (curp,))
        existe = cursor.fetchone()[0] > 0
        conn.close()
        return existe

    # ---------- OBTENER POR ID ----------
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
        row = cursor.fetchone()
        conn.close()
        return row

    # ---------- BUSCAR (por CURP exacto o por nombre parcial) ----------
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
                ORDER BY fecha_generacion DESC
            """, (curp,))
            rows = cursor.fetchall()
        elif q:
            like = f"%{q}%"
            cursor.execute("""
                SELECT t.*, n.nombre AS nivel, m.nombre AS municipio, a.nombre AS asunto
                FROM ticket t
                LEFT JOIN nivel n ON t.id_nivel = n.id_nivel
                LEFT JOIN municipio m ON t.id_municipio = m.id_municipio
                LEFT JOIN asunto a ON t.id_asunto = a.id_asunto
                WHERE t.nombre_completo LIKE %s OR t.nombre LIKE %s OR t.paterno LIKE %s OR t.materno LIKE %s
                ORDER BY fecha_generacion DESC
            """, (like, like, like, like))
            rows = cursor.fetchall()
        else:
            rows = []
        conn.close()
        return rows
    
    # ---------- CONTAR POR STATUS ----------
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
        conn.close()

        pendientes = 0
        resueltos = 0
        for status, cnt in rows:
            if status == "Pendiente":
                pendientes = cnt
            elif status == "Resuelto":
                resueltos = cnt
        total = pendientes + resueltos
        return {"Pendiente": pendientes, "Resuelto": resueltos, "Total": total}
    
    # ---------- OBTENER POR CURP Y TURNO ----------
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
        row = cursor.fetchone()
        conn.close()
        return row

# ------------------------------
# CLASE CATALOGO
# ------------------------------
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
        rows = cursor.fetchall()
        conn.close()
        return rows

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
        rows = cursor.fetchall()
        conn.close()
        return rows

    @staticmethod
    def obtener_por_id(tipo, id_):
        cfg = Catalogo._cfg(tipo)
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            f"SELECT {cfg['id_col']} AS id, {cfg['nombre_col']} AS nombre FROM {cfg['tabla']} WHERE {cfg['id_col']} = %s",
            (id_,)
        )
        row = cursor.fetchone()
        conn.close()
        return row

    @staticmethod
    def guardar(tipo, nombre):
        cfg = Catalogo._cfg(tipo)
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO {cfg['tabla']} ({cfg['nombre_col']}) VALUES (%s)", (nombre,))
        conn.commit()
        conn.close()

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
        conn.close()

    @staticmethod
    def eliminar(tipo, id_):
        cfg = Catalogo._cfg(tipo)
        conn = DatabaseConnection.get_instance()
        cursor = conn.cursor()
        try:
            cursor.execute(f"DELETE FROM {cfg['tabla']} WHERE {cfg['id_col']}=%s", (id_,))
            conn.commit()
            ok = True
        except mysql.connector.Error:
            ok = False
        finally:
            conn.close()
        return ok
