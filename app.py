from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = "clave_secreta_para_flask"

    # === IMPORTS DE BLUEPRINTS ===
    from controllers.main_controller import main_bp
    from controllers.ticket_controller import ticket_bp
    from controllers.catalogos_controller import catalogos_bp
    from controllers.dashboard_controller import dashboard_bp

    # === REGISTRO ===
    app.register_blueprint(main_bp)
    app.register_blueprint(ticket_bp)
    app.register_blueprint(catalogos_bp)
    app.register_blueprint(dashboard_bp)

    # === INICIALIZAR DB UNA VEZ ===
    from models.db import DB
    DB.get_instance()  # esto asegura que cree la conexión singleton

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

