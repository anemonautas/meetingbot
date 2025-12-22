from abc import ABC, abstractmethod
import base64
import aiohttp, httpx, os

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount, Attachment, Activity
from botbuilder.core.teams import TeamsInfo

from elmybots.tools.mylogger import get_logger
from elmybots.models.base64 import Base64Object

LOG = get_logger(__name__)




BACKEND_SUBSCRIBE_URL = os.getenv(
    "BACKEND_SUBSCRIBE_URL", "http://localhost:8080/subscribe"
)


class TemplateBot(ActivityHandler, ABC):
    """
    A base class for bots that contains shared logic such as handling attachments,
    managing conversation history, and processing reload commands.
    """

    MAX_HISTORY = 75
    book_of_conversations = {}

    async def _download_attachment(self, url: str) -> bytes:
        LOG.debug(f"Downloading attachment from {url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    LOG.debug(f"Downloaded image: HTTP {response.status} from {url}")
                    return await response.read()
                else:
                    LOG.error(f"Failed to download image: HTTP {response.status}")
                    raise Exception(f"Failed to download image: HTTP {response.status}")

    async def get_b64_attachment(
        self, attachment: Attachment, turn_context: TurnContext
    ) -> Base64Object:
        LOG.info(
            f'Handling attachment from [{attachment.name or "unknown"} {attachment.content_type}]'
        )
        LOG.info(f"filename  {attachment.name}")
        response_object = Base64Object()
        response_object.filename = attachment.name

        try:
            if (
                attachment.content is not None
                and attachment.content["downloadUrl"] is not None
            ):
                LOG.debug(
                    f'Downloading attachment from {attachment.content["downloadUrl"]}'
                )
                data = await self._download_attachment(
                    attachment.content["downloadUrl"]
                )
                response_object.b64content = base64.b64encode(data).decode("utf-8")
                return response_object

            elif attachment.content_url is not None:
                LOG.debug(f"Downloading attachment from {attachment.content_url}")
                data = await self._download_attachment(attachment.content_url)
                response_object.b64content = base64.b64encode(data).decode("utf-8")
                return response_object

            else:
                LOG.warning(
                    f"No attachement data found from [{attachment.name or 'unknown'} {attachment.content_type}]"
                )
                return ""

        except Exception as e:
            LOG.error(e)
            await turn_context.send_activity(f"Failed to process the image: {str(e)}")
            return ""

    def _initialize_conversation(self, user_name: str):
        self.book_of_conversations[user_name] = []

    async def _on_reload_command(self, turn_context: TurnContext):
        user_name = turn_context.activity.from_property.name
        LOG.info(f"user:[{user_name}]:REQUEST RELOAD")
        self._initialize_conversation(user_name)
        await turn_context.send_activity("🤖 bip, bip 🤖 on recommence.")

    async def __get_attached_pdf(self, turn_context: TurnContext) -> list[Base64Object]:
        base64_objects: list[Base64Object] = []

        if turn_context.activity.attachments:
            for attachment in turn_context.activity.attachments:
                if (
                    attachment.content_type.startswith("application/pdf")
                    or attachment.content_type
                    == "application/vnd.microsoft.teams.file.download.info"
                    and attachment.content["fileType"] == "pdf"
                ):
                    LOG.debug("user shares pdf documents")
                    pdf = await self.get_b64_attachment(attachment, turn_context)
                    if pdf:
                        base64_objects.append(pdf)

            return base64_objects
        return None

    async def __get_attached_images(
        self, turn_context: TurnContext
    ) -> list[Base64Object]:
        base64_images: list[Base64Object] = []
        if turn_context.activity.attachments:
            LOG.debug("user shares images")

            for attachment in turn_context.activity.attachments:
                if (
                    attachment.content_type.startswith("image/")
                    or attachment.content_type
                    == "application/vnd.microsoft.teams.file.download.info"
                ) and (attachment.content and attachment.content["fileType"] == "png"):
                    img = await self.get_b64_attachment(attachment, turn_context)
                    if img:
                        base64_images.append(img.b64content)
            return base64_images
        return None

    @abstractmethod
    async def upload_file_to_vectorstore(
        self, turn_context: TurnContext, base64_pdfs: list[Base64Object]
    ):
        pass

    @abstractmethod
    async def generate_response(
        self,
        turn_context: TurnContext,
        history: list,
        base64_images: list[Base64Object],
        base64_pdfs: list[Base64Object],
    ):
        """
        Abstract method to generate a response.
        Subclasses must implement this method to integrate with a particular model or API.
        """
        pass

    async def on_message_activity(self, turn_context: TurnContext):

        await turn_context.send_activity(Activity(type="typing"))

        user_name = turn_context.activity.from_property.name
        user_message = (turn_context.activity.text or "").strip().lower()

        if user_message == "reload":
            await self._on_reload_command(turn_context)
            return

        base64_pdfs = await self.__get_attached_pdf(turn_context)
        base64_images = await self.__get_attached_images(turn_context)

        if user_message == "apprend":
            LOG.info(
                f"user:[{user_name}]:REQUEST LEARN FILES {len(base64_pdfs) if base64_pdfs else 0}"
            )
            await self.upload_file_to_vectorstore(turn_context, base64_pdfs)
            return

        if user_message.startswith("transcribe"):
            
            url = user_message.split()[1]    
            meeting_id = None
            cd = turn_context.activity.channel_data or {}

            print(str(cd))

            if isinstance(cd, dict):
                meeting_id = ((cd.get("meeting") or {}).get("id")) or None
                
            if not meeting_id:
                try:
                    info = await TeamsInfo.get_meeting_info(turn_context)
                    # distintos tenants exponen distintos campos
                    details = getattr(info, "details", {}) or {}
                    meeting_id = (
                        details.get("id")
                        or details.get("msMeetingId")
                        or details.get("meetingId")
                    )
                except Exception:
                    pass

            if not meeting_id:
                await turn_context.send_activity(
                    "No veo un onlineMeetingId en este contexto."
                )
                return
            # 3) Llamar a tu backend para crear la suscripción RSC de transcript
            async with httpx.AsyncClient(timeout=20) as cx:
                r = await cx.post(
                    BACKEND_SUBSCRIBE_URL,
                    json={"meetingId": meeting_id, "kind": "transcript"},
                )
                ok = r.status_code < 300

            msg = f"Suscripción {'creada' if ok else 'fallida'} para meetingId={meeting_id}"
            await turn_context.send_activity(msg)
            return

        else:
            history = self.book_of_conversations.get(user_name, [])
            await self.generate_response(
                turn_context, history, base64_images, base64_pdfs
            )

    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Coucou! Comment je peux t'aider? :)")
