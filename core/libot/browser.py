import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from libot.logger import logger
from libot.config import OUTPUT_DIR
from libot.js_scripts import FIND_AND_CLICK_JS


def _wait_dom_ready(driver, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        try:
            state = driver.execute_script("return document.readyState")
            if state == "complete":
                return True
        except Exception as e:
            logger.error(f"Error waiting for DOM ready: {e}")
            pass
        time.sleep(0.5)
    return False


def build_driver(task_id: str, avatar_y4m: str | None, task_dir: str):
    opts = Options()
    opts.binary_location = "/usr/bin/google-chrome"

    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--remote-debugging-port=9222")
    opts.add_argument("--window-size=1920,1080")

    opts.add_argument("--autoplay-policy=no-user-gesture-required")
    opts.add_argument("--lang=en-US")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    opts.add_argument("--use-fake-device-for-media-stream")
    opts.add_argument("--use-fake-ui-for-media-stream")

    if avatar_y4m:
        opts.add_argument(f"--use-file-for-fake-video-capture={avatar_y4m}")

    opts.add_argument(f"--user-data-dir=/tmp/profile_{task_id}")

    opts.add_argument("--enable-logging=stderr")
    opts.add_argument("--v=1")

    service = Service(
        "/usr/local/bin/chromedriver",
        log_path=os.path.join(task_dir, "chromedriver.log"),
    )

    return webdriver.Chrome(service=service, options=opts)


def take_screenshot(driver, task_id, name):
    try:
        path = os.path.join(OUTPUT_DIR, task_id, f"{name}.png")
        driver.save_screenshot(path)
    except:
        pass


def safe_click(driver, tag_type, text_options, task_id):
    """
    Attempts to find an element by text and click it using JS.
    Supports list of tags to try if specific tag fails.
    """
    if isinstance(text_options, str):
        text_options = [text_options]

    # If generic 'button' requested, try specific semantic tags used by Teams
    tags_to_try = [tag_type]
    if tag_type == "button":
        tags_to_try = ["button", "div[role='button']", "span[role='button']", "a"]

    for tag in tags_to_try:
        try:
            res = driver.execute_script(FIND_AND_CLICK_JS, text_options, tag, True)
            if res == "clicked":
                logger.info(f"[{task_id}] 🖱️  CLICKED: {text_options[0]} ({tag})")

                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                take_screenshot(driver, task_id, f"click_{text_options[0]}_{timestamp}")
                return True
        except Exception:
            pass
    return False
