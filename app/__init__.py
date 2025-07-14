from flask import Flask
from .routes import main
from .socket_server import socketio
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(main)
    socketio.init_app(app)
    return app
