# meeting.py

import time
from selenium.webdriver.common.by import By

from libot.logger import logger
from libot.browser import safe_click, take_screenshot
from libot.js_scripts import FILL_INPUT_JS, FIND_AND_CLICK_JS

def _is_in_meeting(driver) -> bool:
    """
    Heurística para saber si ya estamos dentro de una reunión de Teams.
    """
    in_meeting_indicators = [
        "Raise", "Levantar",
        "Chat", "Conversación",
        "React", "Reaccionar",
        "Leave", "Salir",
        "People", "Personas",
    ]
    # 1) Buscar por texto en los botones (sin hacer click)
    for text in in_meeting_indicators:
        try:
            res = driver.execute_script(FIND_AND_CLICK_JS, [text], "button", False)
            if res == "found":
                return True
        except Exception:
            pass

    # 2) IDs / data-tid típicos de controles de llamada
    try:
        if driver.find_elements(By.ID, "hangup-button"):
            return True
        if driver.find_elements(By.CSS_SELECTOR, "[data-tid='call-hangup']"):
            return True
        if driver.find_elements(By.CSS_SELECTOR, "[data-tid='call-controls-panel']"):
            return True
    except Exception:
        pass

    return False


def join_meeting(driver, task_id, max_wait: int = 120) -> bool:
    bot_name = "Scribe!"
    logger.info(f"[{task_id}] 🚀 Intentando unirse a la reunión...")

    JOIN_BUTTONS = [
        "Join now", "Unirse ahora", "Rejoindre maintenant", "Jetzt teilnehmen",
    ]
    NO_AUDIO_BTNS = [
        "Continue without audio or video",
        "Continue without audio",
        "No usar audio",
        "Continuar sin audio",
    ]
    COMPUTER_AUDIO = [
        "Computer audio",
        "Audio del equipo",
        "Audio de l'ordinateur",
    ]
    NAME_FIELDS = [
        "name", "nombre", "nom", "Name",
        "type your name", "escriba su nombre",
    ]
    DISMISS_BTNS = ["Dismiss", "Got it", "Close", "Cerrar"]

    deadline = time.time() + max_wait
    name_filled = False
    audio_selected = False
    join_clicked = False

    while time.time() < deadline:
        url = ""
        try:
            url = driver.current_url
        except Exception:
            pass

        # 1. Login wall
        if "login.microsoft" in (url or ""):
            logger.error(f"[{task_id}] ⛔ Login wall detectado (requiere cuenta).")
            take_screenshot(driver, task_id, "login_wall")
            return False

        # 2. "Continue on this browser"
        if safe_click(driver, "button",
                      ["Continue on this browser", "Continuar en este explorador"], task_id):
            logger.info(f"[{task_id}] Click en 'Continue on this browser'.")
            time.sleep(3)
            continue

        # 3. Popups iniciales (no audio / no vídeo)
        safe_click(driver, "button", NO_AUDIO_BTNS, task_id)

        # 4. Tooltips genéricos que estorban
        safe_click(driver, "button", DISMISS_BTNS, task_id)

        # 5. Rellenar nombre (una sola vez)
        if not name_filled:
            try:
                filled = driver.execute_script(FILL_INPUT_JS, bot_name, NAME_FIELDS)
                if filled:
                    logger.info(f"[{task_id}] Nombre rellenado en el pre-join.")
                    name_filled = True
            except Exception:
                pass

        # 6. Seleccionar audio de equipo (una sola vez)
        if not audio_selected:
            # Intento via botones
            clicked_audio = (
                safe_click(driver, "div", COMPUTER_AUDIO, task_id) or
                safe_click(driver, "span", COMPUTER_AUDIO, task_id) or
                safe_click(driver, "button", COMPUTER_AUDIO, task_id)
            )
            if clicked_audio:
                logger.info(f"[{task_id}] Fuente 'Computer audio' seleccionada.")
                audio_selected = True
                time.sleep(0.5)
            else:
                # Fallback JS
                try:
                    driver.execute_script("""
                        var labels = document.querySelectorAll(
                            'label, div[role="radio"], div[role="checkbox"]'
                        );
                        for (var i=0; i<labels.length; i++) {
                            var txt = (labels[i].innerText || '').toLowerCase();
                            if (txt.includes('computer audio') ||
                                txt.includes('audio del equipo') ||
                                txt.includes('audio de l\\'ordinateur')) {
                                labels[i].click();
                                break;
                            }
                        }
                    """)
                except Exception:
                    pass

        # 7. Click en "Join now" (una sola vez)
        if not join_clicked:
            if safe_click(driver, "button", JOIN_BUTTONS, task_id):
                join_clicked = True
                logger.info(f"[{task_id}] 🤞 Click en 'Join now'.")
                take_screenshot(driver, task_id, "clicked_join")
                # Tiempo para que cargue la reunión
                time.sleep(5)

        # 8. Verificar si ya estamos dentro de la reunión
        try:
            if _is_in_meeting(driver):
                logger.info(f"[{task_id}] ✅ Reunión unida correctamente.")
                take_screenshot(driver, task_id, "joined_success")
                return True
        except Exception:
            pass

        time.sleep(2)

    logger.error(f"[{task_id}] ❌ Timeout intentando unirse (>{max_wait}s).")
    take_screenshot(driver, task_id, "fail_timeout")
    return False
