from elmybots.bots.implements.bot.scribe import ScribeBotOAI

IMPLEMENTED_BOTS = {
    "SCRIBE": ScribeBotOAI,
}


def get_bot(bot_name: str):
    """Retrieves a bot class from the implemented bots."""
    bot_class = IMPLEMENTED_BOTS.get(bot_name)
    if bot_class is None:
        raise KeyError(f'Bot "{bot_name}" is not implemented or not found.')
    return bot_class
