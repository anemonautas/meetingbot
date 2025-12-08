import os
from flask import Flask
from libot.routes import api
from libot.config import DISPLAY_NUM
from libot.logger import logger

app = Flask(__name__)
app.register_blueprint(api)

os.environ["DISPLAY"] = DISPLAY_NUM
os.environ["PULSE_SERVER"] = "unix:/var/run/pulse/native"


if __name__ == "__main__":

    lock_file = f"/tmp/.X{DISPLAY_NUM.replace(':','')}-lock"
    if os.path.exists(lock_file):
        os.remove(lock_file)

    port = int(os.environ.get("PORT", 8080))
    logger.info("-" * 80)
    logger.info(f"🚀 Service starting on port {port}")
    logger.info("-" * 80)
    app.run(host="0.0.0.0", port=port)
