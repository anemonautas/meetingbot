import os
from enum import Enum
import base64
from openai import OpenAI
from botbuilder.core import TurnContext
from botbuilder.schema import Activity
from elmybots.bots.template import LOG, TemplateBot, Base64Object

openai_client = OpenAI()


class OpenAIModels(str, Enum):
    BEST_OF = "gpt-5"
    BEST_REASONING = "o3"
    BEST_WRITER = "gpt-4.1"
    BEST_OMNI = "gpt-4o"


class OAIBot(TemplateBot):
    def __init__(
        self,
        system_prompt: str,
        model: OpenAIModels,
        vector_stores: list[str],
        web_search: bool = False,
    ):
        self.system_prompt = system_prompt
        self.model = model
        self.vector_store = vector_stores
        self.web_search = web_search

    def _get_tools(self):
        tools = []
        if len(self.vector_store) > 0:

            tools.append(
                {"type": "file_search", "vector_store_ids": self.vector_store}
            )

        if self.web_search:
            tools.append(
                {
                    "type": "web_search_preview",
                    "user_location": {
                        "type": "approximate",
                        "country": "FR",
                    },
                    "search_context_size": "medium",
                }
            )

        return tools

    async def _get_openai_response(self, history):
        return openai_client.responses.create(
            model=self.model,
            instructions=self.system_prompt,
            input=history,
            text={"format": {"type": "text"}},
            reasoning={},
            include=["file_search_call.results"],
            tools=self._get_tools(),
            temperature=1,
            max_output_tokens=8056,
            top_p=1,
            store=False,
        )

    async def generate_response(
        self,
        turn_context: TurnContext,
        history: list,
        base64_images: list[Base64Object],
        base64_pdfs,
    ):
        user_name = turn_context.activity.from_property.name
        content = [
            {
                "type": "input_text",
                "text": f"{user_name.split(' ')[0]}: {turn_context.activity.text}",
            }
        ]

        if base64_images:
            for image in base64_images:
                content.append(
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{ image.b64content }",
                    }
                )
                LOG.info(f"user {user_name} shared an image - {image.filename}")

        if base64_pdfs:
            for pdf in base64_pdfs:
                content.append(
                    {
                        "type": "input_file",
                        "filename": f"{user_name}_{pdf.filename.split('.')[0]}.pdf",
                        "file_data": f"data:application/pdf;base64,{pdf.b64content}",
                    }
                )
                LOG.info(f"user {user_name} shared a pdf document")

        history.append({"role": "user", "content": content})

        LOG.info(f"user:[{user_name}]:{self.model}:LENGTH_CONV={len(history)}")

        # Request a response from the OpenAI model.
        response = await self._get_openai_response(history)

        response_text = response.output_text

        history.append(
            {
                "role": "assistant",
                "content": [{"type": "output_text", "text": response_text}],
            }
        )

        # Keep conversation history within MAX_HISTORY.
        if len(history) > TemplateBot.MAX_HISTORY:
            history = [history[0]] + history[-TemplateBot.MAX_HISTORY :]
        TemplateBot.book_of_conversations[user_name] = history

        await turn_context.send_activity(response_text)
        return response

    async def upload_file_to_vectorstore(
        self, turn_context: TurnContext, base64_pdfs: list[Base64Object]
    ):

        await turn_context.send_activity(
            Activity(
                type="message",
                text=f"""🤖 bip, bip. Tu as partagé: {len(base64_pdfs)} documents.\n 
        Je vais les ajouter au vector store {self.vector_store}...""",
            )
        )

        for file_to_upload in base64_pdfs:
            with open(f"{file_to_upload.filename}", "+wb") as f:
                f.write(base64.b64decode(file_to_upload.b64content))
                file_object = openai_client.files.create(
                    file=f, purpose="assistants"
                )
                openai_client.vector_stores.files.create(
                    vector_store_id=self.vector_store[0], file_id=file_object.id
                )
                os.remove(f.name)

            await turn_context.send_activity(
                Activity(
                    type="message", text=f"📚 Reading... {file_to_upload.filename}."
                )
            )

        await turn_context.send_activity(
            Activity(
                type="message", text=f"🤖 bip, bip. Des nouvelles ont été ajoutées."
            )
        )

        LOG.info(f"uploading {len(base64_pdfs)} pdfs to vector store")
