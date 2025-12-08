import importlib
import logging
import os
import tempfile
import unittest
from unittest import mock


class ConfigModuleTest(unittest.TestCase):
    def tearDown(self):
        # Restore the config module to reflect the real environment
        import libot.config as config

        importlib.reload(config)

    def test_output_dir_created_and_prefix_stripped(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = os.path.join(tmp_dir, "nested", "out")
            env = {"OUTPUT_DIR": output_dir, "GCS_PREFIX": "folder/prefix///"}

            with mock.patch.dict(os.environ, env, clear=False):
                import libot.config as config

                reloaded_config = importlib.reload(config)

            self.assertTrue(os.path.isdir(output_dir))
            self.assertEqual(reloaded_config.OUTPUT_DIR, output_dir)
            self.assertEqual(reloaded_config.GCS_PREFIX, "folder/prefix")

    def test_exit_on_finish_respects_environment_flag(self):
        with mock.patch.dict(os.environ, {"EXIT_ON_FINISH": "0"}, clear=False):
            import libot.config as config

            reloaded_config = importlib.reload(config)

        self.assertFalse(reloaded_config.EXIT_ON_FINISH)


class LoggerModuleTest(unittest.TestCase):
    def tearDown(self):
        import libot.config as config
        import libot.logger as logger

        # Close handlers to avoid leaking file descriptors across tests
        for handler in logger.logger.handlers:
            handler.close()
            logger.logger.removeHandler(handler)

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        importlib.reload(config)
        importlib.reload(logger)

    def test_logger_writes_to_output_directory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = os.path.join(tmp_dir, "logs")
            env = {"OUTPUT_DIR": output_dir}

            with mock.patch.dict(os.environ, env, clear=False):
                import libot.config as config

                importlib.reload(config)

                # Reset root handlers so logger.basicConfig can set up fresh handlers
                for handler in logging.root.handlers[:]:
                    logging.root.removeHandler(handler)

                import libot.logger as logger

                reloaded_logger = importlib.reload(logger)

            reloaded_logger.logger.info("hello log")
            for handler in reloaded_logger.logger.handlers:
                handler.flush()

            log_file = os.path.join(output_dir, "service.log")
            self.assertTrue(os.path.isfile(log_file))

            with open(log_file, "r", encoding="utf-8") as log_handle:
                contents = log_handle.read()

            self.assertIn("hello log", contents)


class CompressModuleTest(unittest.TestCase):
    def test_compress_audio_invokes_pydub_pipeline(self):
        import sys
        import types

        mock_segment = mock.MagicMock()
        mock_after_channels = mock.MagicMock()
        mock_after_frame_rate = mock.MagicMock()

        mock_segment.set_channels.return_value = mock_after_channels
        mock_after_channels.set_frame_rate.return_value = mock_after_frame_rate

        audio_segment_mock = mock.MagicMock()
        audio_segment_mock.from_file.return_value = mock_segment
        pydub_stub = types.ModuleType("pydub")
        pydub_stub.AudioSegment = audio_segment_mock

        sys.modules.pop("libot.compress", None)

        with mock.patch.dict(sys.modules, {"pydub": pydub_stub}):
            from libot import compress

            compress.compress_audio("input.wav", "output.mp3", bitrate="64k")

        audio_segment_mock.from_file.assert_called_once_with("input.wav")
        mock_segment.set_channels.assert_called_once_with(1)
        mock_after_channels.set_frame_rate.assert_called_once_with(16000)
        mock_after_frame_rate.export.assert_called_once_with(
            "output.mp3", format="mp3", bitrate="64k"
        )


if __name__ == "__main__":
    unittest.main()
