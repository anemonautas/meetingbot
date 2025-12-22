from elmybots.bots.selector import get_bot


def test_selector():
    bot = get_bot("MARTY")()
    assert type(bot).__name__ == "MartyBotOAI"

    bot = get_bot("DOC")()
    assert type(bot).__name__ == "DocBotOAI"

    bot = get_bot("GEMMA")()
    assert type(bot).__name__ == "GemmaBotGAI"

    bot = get_bot("PETITAGREG")()
    assert type(bot).__name__ == "PetiteAgregBotOAI"

    bot = get_bot("BRIFFEUR_XC")()
    assert type(bot).__name__ == "BriffBotOAI"

    bot = get_bot("COMMERCE")()
    assert type(bot).__name__ == "TapisBotOAI"
