from models.db import DatabaseConnection
from models.admin import Admin

if __name__ == "__main__":
    # Inicializa la conexión
    DatabaseConnection.get_instance()
    # Crear admin
    admin_id = Admin.create(
        username="admin",
        password_plain="admin123",
        nombre="Administrador",
        email="admin@gmail.com"
    )
    print(f"Admin creado con id: {admin_id}")