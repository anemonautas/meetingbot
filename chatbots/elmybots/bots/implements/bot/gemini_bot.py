import os
from enum import Enum
from google import genai
from google.genai import types
from botbuilder.core import TurnContext, ActivityHandler
from botbuilder.schema import Activity
from elmybots.bots.template import LOG, TemplateBot, Base64Object

gemini = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


class GeminiModels(str, Enum):
    BEST_REASONING = "gemini-2.5-pro"
    BEST_WRITER = "gemini-2.5-pro"
    BEST_OMNI = "gemini-2.5-pro"


class GeminiBot(TemplateBot):
    def __init__(
        self,
        system_prompt: str,
        model: GeminiModels,
        vector_stores: list[str] = [],
        web_search: bool = False,
    ):
        self.system_prompt = system_prompt
        self.model = model
        self.vector_store = vector_stores
        self.web_search = web_search

    def _get_tools(self):
        tools = []
        return tools

    async def generate_response(
        self,
        turn_context: TurnContext,
        history: list,
        base64_images: list[Base64Object],
        base64_pdfs: list[Base64Object],
    ):
        user_name = turn_context.activity.from_property.name

        generate_content_config = types.GenerateContentConfig(
            response_mime_type="text/plain",
            system_instruction=[
                types.Part.from_text(text=self.system_prompt),
            ],
        )

        __input_message = f"{user_name.split(' ')[0]}: {turn_context.activity.text}"

        contents: list[types.Part] = []

        if base64_images:
            LOG.info(f"user {user_name} shared {len(base64_images)} images")
            for image in base64_images:
                contents.append(
                    types.Part.from_bytes(
                        mime_type="image/png", data=image.b64content
                    )
                )
                LOG.info(f"user {user_name} shared an image - {image.filename}")

        if base64_pdfs:
            LOG.info(f"user {user_name} shared {len(base64_pdfs)} pdfs")
            for pdf in base64_pdfs:
                contents.append(
                    types.Part.from_bytes(
                        mime_type="application/pdf", data=pdf.b64content
                    )
                )
                LOG.info(f"user {user_name} shared a pdf document")

        contents.append(types.Part.from_text(text=__input_message))

        history.append(
            types.Content(
                role="user",
                parts=contents,
            )
        )

        LOG.info(f"user:[{user_name}]:{self.model}:LENGTH_CONV={len(history)}")

        res = gemini.models.generate_content(
            model=self.model, contents=history, config=generate_content_config
        )

        response_content = res.candidates[0].content

        try:
            history.append(response_content)
            # Keep conversation history within MAX_HISTORY.
            if len(history) > TemplateBot.MAX_HISTORY:
                history = [history[0]] + history[-TemplateBot.MAX_HISTORY :]
            TemplateBot.book_of_conversations[user_name] = history
        except Exception as e:
            LOG.info(f"error: {e}")

        await turn_context.send_activity(response_content.parts[0].text)

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
            await turn_context.send_activity(
                Activity(
                    type="message", text=f"📚 Reading... {file_to_upload.filename}."
                )
            )

            # ## PLACEHOLDER for uploading to somewhere...
            # with open(f"{file_to_upload.filename}", "+wb") as f:
            #     f.write(base64.b64decode(file_to_upload.b64content))
            #     ## Do action
            #     os.remove(f.name)
            await turn_context.send_activity(
                Activity(
                    type="message", text=f"📚 Finished: {file_to_upload.filename}."
                )
            )

        await turn_context.send_activity(
            Activity(
                type="message", text=f"🤖 bip, bip. Des nouvelles ont été ajoutées."
            )
        )

        LOG.info(f"uploading {len(base64_pdfs)} pdfs to vector store")
