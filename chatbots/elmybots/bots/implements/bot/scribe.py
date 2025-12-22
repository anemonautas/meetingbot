from botbuilder.core import TurnContext
from botbuilder.schema import Activity

from elmybots.bots.template import LOG
from elmybots.bots.implements.bot.oai_bot import OAIBot, OpenAIModels
from elmybots.bots.botonality.selector import getBotonality

class ScribeBotOAI(OAIBot):
    def __init__(self):
        super().__init__(
            system_prompt=getBotonality("SCRIBE"),
            model=OpenAIModels.BEST_OF,
            vector_stores=["vs_68c81264d59c81919de17b1e4a83f58b"],
            web_search=True,
        )
        LOG.info("init ScribeBotOAI")

