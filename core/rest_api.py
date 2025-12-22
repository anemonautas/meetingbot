import os
from flask import Flask
from libot.routes import api
from libot.config import DISPLAY_NUM
from libot.logger import logger

os.environ["DISPLAY"] = DISPLAY_NUM
os.environ["PULSE_SERVER"] = "unix:/var/run/pulse/native"


app = Flask(__name__)
app.register_blueprint(api)


def setup_lock():
    lock_file = f"/tmp/.X{DISPLAY_NUM.replace(':','')}-lock"
    if os.path.exists(lock_file):
        os.remove(lock_file)


def start_app():
    PORT = int(os.environ.get("PORT", 8080))
    logger.info("-" * 80)
    logger.info(f"🚀 Service starting on port {PORT}")
    logger.info("-" * 80)
    app.run(host="0.0.0.0", port=PORT)


if __name__ == "__main__":

    setup_lock()
    start_app()
