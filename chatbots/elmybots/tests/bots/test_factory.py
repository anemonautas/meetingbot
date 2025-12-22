from elmybots.bots.implements.bot.oai_bot import OAIBot, OpenAIModels
from elmybots.bots.implements.bot.gemini_bot import GeminiBot, GeminiModels


## Test Bot Instantiation
# Teste la création d'un bot OpenAI avec des paramètres spécifiques.
def test_oai_bot_instantiation():
    bot = OAIBot(
        system_prompt="You are a helpful assistant.",
        model=OpenAIModels.BEST_OF,
        vector_stores=["vs1", "vs2"],
        web_search=True,
    )

    assert bot.system_prompt == "You are a helpful assistant."
    assert bot.model == OpenAIModels.BEST_OF
    assert bot.vector_store == ["vs1", "vs2"]
    assert bot.web_search is True

    tools = bot._get_tools()
    assert len(tools) == 2
    assert tools[0]["type"] == "file_search"
    assert tools[0]["vector_store_ids"] == ["vs1", "vs2"]

    assert tools[1]["type"] == "web_search_preview"
    assert tools[1]["user_location"]["country"] == "FR"
    assert tools[1]["search_context_size"] == "medium"


## Test Gemini Bot Instantiation
# Teste la création d'un bot Gemini.
def test_gemini_bot_instantiation():
    bot = GeminiBot(
        system_prompt="You are a helpful assistant.",
        model=GeminiModels.BEST_OMNI,
        vector_stores=["vs1"],
        web_search=False,
    )
    assert bot.system_prompt == "You are a helpful assistant."
    assert bot.model == GeminiModels.BEST_OMNI
    assert bot.vector_store == ["vs1"]
    assert bot.web_search is False

    tools = bot._get_tools()
    assert len(tools) == 0
