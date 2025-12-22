from aiohttp.web import Request, Response, json_response
from botbuilder.schema import Activity
from elmybots.bot_setup import ADAPTER, BOT
from elmybots.tools.decorators import log_query


@log_query
async def messages(req: Request) -> Response:
    if req.method == "OPTIONS":
        return Response(status=200)

    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return Response(status=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    ## It could be declined here for given another service.
    response = await ADAPTER.process_activity(auth_header, activity, BOT.on_turn)

    if response:
        return json_response(data=response.body, status=response.status)
    return Response(status=201)
