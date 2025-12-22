import pytest
from unittest.mock import MagicMock, AsyncMock

from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ChannelAccount

from elmybots.bots.template import TemplateBot


class MockTemplateBot(TemplateBot):
    def __init__(self):
        super().__init__()
        self.response_generator = None

    async def upload_file_to_vectorstore(
        self, turn_context: TurnContext, base64_pdfs: list
    ):
        pass

    async def generate_response(
        self,
        turn_context: TurnContext,
        history: list,
        base64_images: list,
        base64_pdfs: list,
    ):
        if self.response_generator:
            await self.response_generator(
                turn_context, history, base64_images, base64_pdfs
            )


@pytest.mark.asyncio
async def test_conversation_history():
    # Ce test valide la gestion de l'historique de conversation dans le TemplateBot.

    bot = MockTemplateBot()

    # Simule le contexte d'un tour de conversation.
    turn_context = MagicMock(spec=TurnContext)
    turn_context.activity = Activity(
        from_property=ChannelAccount(name="test_user"), text="Hello", type="message"
    )
    turn_context.send_activity = AsyncMock()

    # --- Étape 1: Premier message de l'utilisateur ---
    # Définit un générateur de réponse pour vérifier l'historique après le premier message.
    async def response_generator_1(tc, history, images, pdfs):
        # L'historique doit contenir le message de l'utilisateur et la réponse (simulée) du bot.
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"][0]["text"] == "test_user: Hello"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"][0]["text"] == "Hello from the bot!"

    bot.response_generator = response_generator_1
    await bot.on_message_activity(turn_context)

    # --- Étape 2: Deuxième message et enrichissement manuel de l'historique ---
    # Ajoute manuellement des messages à l'historique pour simuler une conversation plus longue.
    bot.book_of_conversations["test_user"].append({"role": "user", "content": "Hello"})
    bot.book_of_conversations["test_user"].append(
        {"role": "assistant", "content": "Hi there!"}
    )
    turn_context.activity.text = "How are you?"

    # Définit un nouveau générateur pour vérifier que l'historique s'est correctement enrichi.
    async def response_generator_2(tc, history, images, pdfs):
        assert len(history) == 4
        assert history[2]["content"] == "Hello"
        assert history[3]["content"] == "Hi there!"

    bot.response_generator = response_generator_2
    await bot.on_message_activity(turn_context)

    # --- Étape 3: Commande de rechargement ---
    # Simule l'envoi de la commande 'reload' pour réinitialiser la conversation.
    turn_context.activity.text = "reload"
    await bot.on_message_activity(turn_context)
    # Vérifie que l'historique de l'utilisateur est bien vide.
    assert len(bot.book_of_conversations["test_user"]) == 0

    # --- Étape 4: Message après rechargement ---
    # Simule un nouveau message après la réinitialisation.
    turn_context.activity.text = "New conversation"

    # Définit un générateur pour s'assurer que l'historique est vide avant ce nouveau message.
    async def response_generator_3(tc, history, images, pdfs):
        assert len(history) == 0

    bot.response_generator = response_generator_3
    await bot.on_message_activity(turn_context)
