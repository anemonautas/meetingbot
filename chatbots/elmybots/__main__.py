from aiohttp import web

from elmybots.config import DefaultConfig
from elmybots.tools.mylogger import get_logger, print_figlet
from elmybots.app import APP

LOG = get_logger(__name__)


def main():
    CONFIG = DefaultConfig()
    print_figlet(CONFIG.BOT_NAME)
    LOG.info(f"Starting chatbot {CONFIG.BOT_NAME} (port: {CONFIG.PORT})")
    web.run_app(APP, host="0.0.0.0", port=CONFIG.PORT, print=None)


if __name__ == "__main__":
    main()
