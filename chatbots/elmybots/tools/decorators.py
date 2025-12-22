from aiohttp.web import Request
from elmybots.tools.mylogger import get_logger

LOG = get_logger(__name__)


def log_query(f):
    async def wrapper(req: Request):
        LOG.debug(f"Hit {req.method} request at {req.path} from {req.host}")
        LOG.debug(f"    Headers:\n {req.headers}")
        LOG.debug(f"    Query:\n {req.query_string}")
        LOG.debug(f"    Body:\n {await req.text()}")
        LOG.debug(f"    Client:\n {req.remote}")
        LOG.debug(f"    User-Agent:\n {req.headers.get('User-Agent')}")
        LOG.debug(f"    Content-Type:\n {req.headers.get('Content-Type')}")
        LOG.debug(f"    Accept:\n {req.headers.get('Accept')}")
        return await f(req)

    return wrapper
