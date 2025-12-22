import os


class DefaultConfig:
    PORT = int(os.environ.get("PORT", "3978"))
    BOT_NAME = os.environ.get("BOT_NAME", "SCRIBE")
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")
    APP_TYPE = "SingleTenant"
    APP_TENANTID = os.environ.get("AppTenant", None)
    CHANNEL_AUTH_TENANT = os.environ.get("AppTenant", None)
