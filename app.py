from flask import Flask
from config import Config
from extensions import db, bcrypt, jwt
from auth.routes import auth_bp
from lawyers.routes import lawyers_bp
from infohub import infohub_bp
from appointments.routes import appointments_bp
from flask_migrate import Migrate

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # init extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(lawyers_bp)
    app.register_blueprint(infohub_bp)
    app.register_blueprint(appointments_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
