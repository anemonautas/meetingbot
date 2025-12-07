import base64
import importlib
import json
import logging
import os
import sys
import tempfile
import types
import unittest
from unittest import mock


PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/xcAAn8B9Zl+7uEAAAAASUVORK5CYII="


def build_flask_stub():
    flask_stub = types.ModuleType("flask")

    class DummyRequest:
        def __init__(self):
            self._data = None

        def set_json(self, data):
            self._data = data

        def get_json(self):
            return self._data

    request = DummyRequest()

    class DummyBlueprint:
        def __init__(self, name, import_name):
            self.name = name
            self.import_name = import_name

        def route(self, rule, methods=None):
            def decorator(func):
                return func

            return decorator

    def jsonify(payload):
        return payload

    def send_file(path):
        return path

    flask_stub.Blueprint = DummyBlueprint
    flask_stub.request = request
    flask_stub.jsonify = jsonify
    flask_stub.send_file = send_file

    return flask_stub


class TangoRouteTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        env = {"OUTPUT_DIR": self.temp_dir.name}
        self.env_patcher = mock.patch.dict(os.environ, env, clear=False)
        self.env_patcher.start()

        import libot.config as config
        importlib.reload(config)

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        import libot.logger as logger_module
        self.logger_module = importlib.reload(logger_module)

        self.flask_stub = build_flask_stub()
        self.selenium_stub = types.ModuleType("selenium")
        webdriver_stub = types.ModuleType("selenium.webdriver")
        chrome_stub = types.ModuleType("selenium.webdriver.chrome")
        chrome_options_stub = types.ModuleType("selenium.webdriver.chrome.options")
        chrome_service_stub = types.ModuleType("selenium.webdriver.chrome.service")
        common_stub = types.ModuleType("selenium.webdriver.common")
        by_stub = types.ModuleType("selenium.webdriver.common.by")
        google_stub = types.ModuleType("google")
        genai_stub = types.ModuleType("google.genai")
        pydub_stub = types.ModuleType("pydub")

        class Options:
            def add_argument(self, *args, **kwargs):
                return None

            def add_experimental_option(self, *args, **kwargs):
                return None

        class Service:
            def __init__(self, *args, **kwargs):
                return None

        class By:
            ID = "id"

        webdriver_stub.Chrome = lambda *args, **kwargs: mock.MagicMock()
        webdriver_stub.chrome = chrome_stub
        webdriver_stub.common = common_stub
        self.selenium_stub.webdriver = webdriver_stub
        chrome_options_stub.Options = Options
        chrome_service_stub.Service = Service
        by_stub.By = By

        class DummyClient:
            def __init__(self, *args, **kwargs):
                class DummyFiles:
                    def upload(self, *args, **kwargs):
                        return None

                class DummyModels:
                    def generate_content(self, *args, **kwargs):
                        return types.SimpleNamespace(text="")

                self.files = DummyFiles()
                self.models = DummyModels()

        genai_stub.Client = DummyClient
        google_stub.genai = genai_stub

        class DummyAudioSegment:
            def from_file(self, *args, **kwargs):
                return mock.MagicMock()

        pydub_stub.AudioSegment = DummyAudioSegment()

        self.module_patch = mock.patch.dict(
            sys.modules,
            {
                "flask": self.flask_stub,
                "google": google_stub,
                "google.genai": genai_stub,
                "pydub": pydub_stub,
                "selenium": self.selenium_stub,
                "selenium.webdriver": webdriver_stub,
                "selenium.webdriver.chrome": chrome_stub,
                "selenium.webdriver.chrome.options": chrome_options_stub,
                "selenium.webdriver.chrome.service": chrome_service_stub,
                "selenium.webdriver.common": common_stub,
                "selenium.webdriver.common.by": by_stub,
            },
        )
        self.module_patch.start()

        import libot.routes as routes
        self.routes = importlib.reload(routes)
        self.request = self.routes.request

    def tearDown(self):
        for handler in self.logger_module.logger.handlers:
            handler.close()
            self.logger_module.logger.removeHandler(handler)

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        self.module_patch.stop()
        self.env_patcher.stop()
        self.temp_dir.cleanup()

    def test_tango_uploads_valid_image(self):
        payload = {
            "image": PNG_BASE64,
            "mime_type": "image/png",
            "user_id": "user-123",
            "conversation_id": "conv-456",
        }

        self.request.set_json(payload)
        response_data, status_code = self.routes.upload_tango()

        self.assertEqual(status_code, 202)
        self.assertIn("task_id", response_data)

        upload_dir = os.path.join(self.temp_dir.name, response_data["task_id"], "upload")
        self.assertTrue(os.path.isdir(upload_dir))

        image_path = os.path.join(upload_dir, "image.png")
        metadata_path = os.path.join(upload_dir, "metadata.json")

        self.assertTrue(os.path.isfile(image_path))
        self.assertTrue(os.path.isfile(metadata_path))

        with open(image_path, "rb") as image_handle:
            stored_bytes = image_handle.read()
        self.assertEqual(stored_bytes, base64.b64decode(PNG_BASE64))

        with open(metadata_path, "r", encoding="utf-8") as metadata_handle:
            metadata = json.load(metadata_handle)

        self.assertEqual(metadata["mime_type"], "image/png")
        self.assertEqual(metadata["user_id"], "user-123")
        self.assertEqual(metadata["conversation_id"], "conv-456")

    def test_tango_missing_image_returns_400(self):
        self.request.set_json({"mime_type": "image/png"})
        response_data, status_code = self.routes.upload_tango()
        self.assertEqual(status_code, 400)
        self.assertIn("error", response_data)

    def test_tango_unsupported_mime_returns_415(self):
        self.request.set_json({"image": PNG_BASE64, "mime_type": "image/gif"})
        response_data, status_code = self.routes.upload_tango()
        self.assertEqual(status_code, 415)
        self.assertIn("error", response_data)


if __name__ == "__main__":
    unittest.main()
