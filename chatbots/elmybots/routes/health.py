from aiohttp.web import Request, Response
from elmybots.tools.mylogger import get_logger
from elmybots.tools.decorators import log_query

LOG = get_logger(__name__)


@log_query
async def healthz(req: Request) -> Response:
    LOG.debug(f"Hit {req.method} {req.path} {req.host}")
    return Response(status=200)
