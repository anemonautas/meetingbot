import os
from libot.logger import logger
from libot.config import OUTPUT_DIR
from libot.js_scripts import FIND_AND_CLICK_JS


def take_screenshot(driver, task_id, name):
    try:
        path = os.path.join(OUTPUT_DIR, task_id, f"{name}.png")
        driver.save_screenshot(path)
    except: pass

def safe_click(driver, tag_type, text_options, task_id):
    """
    Attempts to find an element by text and click it using JS.
    Supports list of tags to try if specific tag fails.
    """
    if isinstance(text_options, str): text_options = [text_options]
    
    # If generic 'button' requested, try specific semantic tags used by Teams
    tags_to_try = [tag_type]
    if tag_type == "button":
        tags_to_try = ["button", "div[role='button']", "span[role='button']", "a"]

    for tag in tags_to_try:
        try:
            res = driver.execute_script(FIND_AND_CLICK_JS, text_options, tag, True)
            if res == "clicked":
                logger.info(f"[{task_id}] 🖱️  CLICKED: {text_options[0]} ({tag})")
                return True
        except Exception:
            pass
    return False
