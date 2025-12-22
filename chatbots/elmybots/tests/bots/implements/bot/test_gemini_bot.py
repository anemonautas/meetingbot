import asyncio
import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ChannelAccount
from google.genai import types

from elmybots.bots.implements.bot.gemini_bot import GeminiBot, GeminiModels
from elmybots.bots.template import TemplateBot, Base64Object


class TestGeminiBot(unittest.TestCase):

    def setUp(self):

        self.system_prompt = "You are a helpful assistant."
        self.model = GeminiModels.BEST_OMNI
        self.vector_stores = ["vs1"]
        self.web_search = False

        self.bot_instance = GeminiBot(
            system_prompt=self.system_prompt,
            model=self.model,
            vector_stores=self.vector_stores,
            web_search=self.web_search,
        )

        self.mock_turn_context = MagicMock(spec=TurnContext)
        self.mock_turn_context.activity = Activity(
            from_property=ChannelAccount(name="test_user"), text="Hello"
        )
        self.mock_turn_context.send_activity = AsyncMock()

    @patch("elmybots.bots.implements.bot.gemini_bot.gemini.models.generate_content")
    def test_generate_response_simple_text(self, mock_generate_content):
        # Arrange
        mock_response_content = types.Content(
            role="model", parts=[types.Part.from_text(text="Hello from the bot!")]
        )

        mock_generate_content.return_value = MagicMock()
        mock_generate_content.return_value.candidates = [MagicMock()]
        mock_generate_content.return_value.candidates[0].content = mock_response_content

        history = []
        base64_images = []
        base64_pdfs = []

        # Act
        asyncio.run(
            self.bot_instance.generate_response(
                self.mock_turn_context, history, base64_images, base64_pdfs
            )
        )

        # Assert
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[1].role, "model")
        self.assertEqual(TemplateBot.book_of_conversations["test_user"], history)

        mock_generate_content.assert_called_once()
        self.mock_turn_context.send_activity.assert_called_once_with(
            "Hello from the bot!"
        )

    @patch("elmybots.bots.implements.bot.gemini_bot.gemini.models.generate_content")
    def test_generate_response_with_image(self, mock_generate_content):
        # Arrange
        mock_response_content = types.Content(
            role="model", parts=[types.Part.from_text(text="I see an image.")]
        )
        mock_generate_content.return_value = MagicMock()
        mock_generate_content.return_value.candidates = [MagicMock()]
        mock_generate_content.return_value.candidates[0].content = mock_response_content

        history = []

        b64 = Base64Object()
        b64.filename = "test.png"
        b64.b64content = "test_image_content".encode("utf-8")

        base64_images = [b64]
        base64_pdfs = []

        # Act
        asyncio.run(
            self.bot_instance.generate_response(
                self.mock_turn_context, history, base64_images, base64_pdfs
            )
        )

        # Assert
        self.assertEqual(len(history), 2)
        user_content = history[0].parts
        self.assertEqual(len(user_content), 2)  # image and text
        self.assertEqual(
            user_content[0],
            types.Part.from_bytes(mime_type="image/png", data=b"test_image_content"),
        )
        self.mock_turn_context.send_activity.assert_called_once_with("I see an image.")

    def test_upload_file_to_vectorstore(self):
        # Arrange
        b64 = Base64Object()
        b64.filename = "test.pdf"
        b64.b64content = b"test_pdf_content"
        base64_pdfs = [b64]

        # Act
        asyncio.run(
            self.bot_instance.upload_file_to_vectorstore(
                self.mock_turn_context, base64_pdfs
            )
        )

        # Assert
        self.assertEqual(self.mock_turn_context.send_activity.call_count, 4)


if __name__ == "__main__":
    unittest.main()
