from aiohttp import web
from botbuilder.core.integration import aiohttp_error_middleware
from elmybots.routes.health import healthz
from elmybots.routes.messages import messages
from elmybots.tools.mylogger import get_logger
from elmybots.tools.mylogger import print_figlet

LOG = get_logger(__name__)

APP = web.Application(middlewares=[aiohttp_error_middleware])

APP.router.add_get("/healthz", healthz)
APP.router.add_options("/api/messages", messages)
APP.router.add_post("/api/messages", messages)

LOG.info("Starting chatbot DOC (port: 3000)")
print_figlet("Chatbot")
web.run_app(APP, port=3000)
