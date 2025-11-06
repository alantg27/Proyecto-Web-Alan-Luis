import mysql.connector

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
