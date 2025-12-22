from libot.gcs import fetch_transcriptions_from_gcs
from libot.gemini import make_briefing
from libot.logger import logger
from libot.mailer import send_email
import json

def handle_briefing(task_id):
    # todo: this function is called
    transcription = fetch_transcriptions_from_gcs(task_id)
    briefing_object = make_briefing(task_id, transcript=transcription)
    logger.info(briefing_object)
    briefing = json.loads(briefing_object)
    logger.info(briefing)
    
    send_email(briefing=briefing["htmlBody"], subject=briefing["subject"] )
