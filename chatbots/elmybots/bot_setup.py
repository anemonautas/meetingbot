import os
import traceback
from botbuilder.core import  BotFrameworkAdapterSettings, TurnContext
from botbuilder.integration.aiohttp import (
    CloudAdapter,
    ConfigurationBotFrameworkAuthentication,
)
from elmybots.bots.selector import get_bot
from elmybots.config import DefaultConfig
from elmybots.tools.mylogger import get_logger

LOG = get_logger(__name__)

CONFIG = DefaultConfig(
    
)
 
ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(CONFIG))
 

async def on_error(context: TurnContext, error: Exception):
    LOG.critical(f"\n [on_turn_error] unhandled error: {error}")
    LOG.critical(error.with_traceback(None))
    LOG.critical(traceback.format_exc())

    await context.send_activity(f"The bot encountered an error or bug. {error}")
    await context.send_activity(
        "To continue to run this bot, please fix the bot source code."
    )


ADAPTER.on_turn_error = on_error

BOT = get_bot(CONFIG.BOT_NAME)()
