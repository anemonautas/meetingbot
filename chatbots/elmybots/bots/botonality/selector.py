from importlib.resources import read_text


def getBotonality(BOT_NAME: str):
    try:
        return read_text("elmybots.bots.botonality", f"{BOT_NAME}.txt")

    except FileNotFoundError:
        raise Exception(f"Botonality file for [{BOT_NAME}] not found.")
