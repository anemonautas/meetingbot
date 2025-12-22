import resend
import os 

resend.api_key = os.getenv("SENDER_API_KEY")

def send_email(briefing: str, subject: str):
    params: resend.Emails.SendParams = {
    "from": "Tango <scribe@mailer.anemonautas.eu>",
    "to": ["eolo+meetings@anemonautas.eu"],
    "subject": f"CR {subject}",
    "html": briefing
    }

    email = resend.Emails.send(params)
    print(email)

