import mysql.connector
from mysql.connector import pooling

class DatabaseConnection:
    _instance = None

    def __init__(self):
        # Creamos un pool de conexiones
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=32,
            host="localhost",
            user="root",
            password="",
            database="ticket_turno"
        )

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DatabaseConnection()
        # Devuelve directamente una conexión del pool
        return cls._instance.pool.get_connection()

