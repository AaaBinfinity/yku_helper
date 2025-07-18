# run.py
from app import create_app
from app.socket_server import socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=12432, debug=True)
