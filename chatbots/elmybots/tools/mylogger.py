from aiohttp import web
import logging
import sys
import pyfiglet


def get_logger(name=__name__):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.hasHandlers():
        # Console handler for INFO and lower
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.INFO)

        # Console handler for ERROR and higher
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.ERROR)

        # Custom formatter with emojis for log levels
        class EmojiFormatter(logging.Formatter):
            LEVEL_EMOJIS = {
                "DEBUG": "🔧",  # Wrench
                "INFO": "ℹ️",  # Information symbol
                "WARNING": "⚠️",  # Warning sign
                "ERROR": "❌",  # Cross mark
                "CRITICAL": "🚫",  # Prohibited sign
            }

            def format(self, record):
                emoji = self.LEVEL_EMOJIS.get(record.levelname, "")
                record.levelname = f"{emoji} "
                return super().format(record)

        formatter = EmojiFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        stdout_handler.setFormatter(formatter)
        stderr_handler.setFormatter(formatter)

        logger.addHandler(stdout_handler)
        logger.addHandler(stderr_handler)

    return logger


def get_figlet(head: str):
    return pyfiglet.figlet_format(f"{head} \n by elmy", "bulbhead")


def print_figlet(head: str):
    print(get_figlet(head))
