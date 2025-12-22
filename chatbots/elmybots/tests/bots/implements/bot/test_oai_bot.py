import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock, mock_open

from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ChannelAccount

from elmybots.bots.implements.bot.oai_bot import OAIBot, OpenAIModels
from elmybots.bots.template import TemplateBot, Base64Object


class TestOAIBot(unittest.TestCase):

    def setUp(self):
        self.system_prompt = "You are a helpful assistant."
        self.model = OpenAIModels.BEST_OMNI
        self.vector_stores = ["vs1"]
        self.web_search = False

        self.bot_instance = OAIBot(
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

    @patch("elmybots.bots.implements.bot.oai_bot.openai_client")
    def test_generate_response_simple_text(self, mock_openai_client):
        # Arrange
        mock_response = MagicMock()
        mock_response.output_text = "Hello from the bot!"
        mock_openai_client.responses.create.return_value = mock_response

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
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"][0]["text"], "test_user: Hello")
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[1]["content"][0]["text"], "Hello from the bot!")
        self.assertEqual(TemplateBot.book_of_conversations["test_user"], history)

        mock_openai_client.responses.create.assert_called_once()
        self.mock_turn_context.send_activity.assert_called_once_with(
            "Hello from the bot!"
        )

    @patch("elmybots.bots.implements.bot.oai_bot.os.remove")
    @patch("elmybots.bots.implements.bot.oai_bot.openai_client")
    @patch("builtins.open", new_callable=mock_open)
    @patch("elmybots.bots.implements.bot.oai_bot.base64.b64decode")
    def test_upload_file_to_vectorstore(
        self, mock_b64decode, mock_file, mock_openai_client, mock_os_remove
    ):
        # Arrange
        b64 = Base64Object()
        b64.filename = "test.pdf"
        b64.b64content = b"test_pdf_content"
        base64_pdfs = [b64]

        mock_file_object = MagicMock()
        mock_file_object.id = "file-123"
        mock_openai_client.files.create.return_value = mock_file_object

        # Act
        asyncio.run(
            self.bot_instance.upload_file_to_vectorstore(
                self.mock_turn_context, base64_pdfs
            )
        )

        # Assert
        mock_b64decode.assert_called_once_with(b"test_pdf_content")
        mock_file.assert_called_once_with("test.pdf", "+wb")
        mock_file().write.assert_called_once_with(mock_b64decode.return_value)
        mock_openai_client.files.create.assert_called_once()
        mock_openai_client.vector_stores.files.create.assert_called_once_with(
            vector_store_id="vs1", file_id="file-123"
        )
        self.assertEqual(self.mock_turn_context.send_activity.call_count, 3)


if __name__ == "__main__":
    unittest.main()
