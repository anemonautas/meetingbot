import os
import sys
import tempfile
import types
import unittest
from unittest import mock

# Provide a lightweight stub for google.cloud.storage so imports succeed without the
# real dependency installed in the test environment.
storage_stub = types.ModuleType("storage")
storage_stub.Client = mock.MagicMock()
cloud_module = types.ModuleType("google.cloud")
cloud_module.storage = storage_stub
google_module = types.ModuleType("google")
google_module.cloud = cloud_module
sys.modules.setdefault("google", google_module)
sys.modules["google.cloud"] = cloud_module
sys.modules["google.cloud.storage"] = storage_stub

from libot import gcs


class UploadRecordingsToGCSTest(unittest.TestCase):
    def test_skips_upload_when_bucket_missing(self):
        with mock.patch.object(gcs, "GCS_BUCKET", None), \
             mock.patch("libot.gcs.storage.Client") as mock_client:
            with self.assertLogs(gcs.logger, level="WARNING") as log_cm:
                gcs.upload_recordings_to_gcs("task-123", "/tmp/nonexistent.mp4")

            mock_client.assert_not_called()
            self.assertTrue(
                any("Skipping upload" in message for message in log_cm.output),
                msg="Expected warning when GCS_BUCKET is not configured",
            )

    def test_uploads_video_when_bucket_configured(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_path = os.path.join(tmp_dir, "recording.mp4")
            with open(video_path, "w", encoding="utf-8") as video_file:
                video_file.write("dummy data")

            mock_client = mock.MagicMock()
            mock_bucket = mock.MagicMock()
            mock_blob = mock.MagicMock()
            mock_client.bucket.return_value = mock_bucket
            mock_bucket.blob.return_value = mock_blob

            with mock.patch.object(gcs, "GCS_BUCKET", "my-bucket"), \
                 mock.patch.object(gcs, "GCS_PREFIX", "folder"), \
                 mock.patch("libot.gcs.storage.Client", return_value=mock_client):
                with self.assertLogs(gcs.logger, level="INFO") as log_cm:
                    gcs.upload_recordings_to_gcs("task-123", video_path)

            mock_client.bucket.assert_called_once_with("my-bucket")
            mock_bucket.blob.assert_called_once_with("folder/task-123/recording.mp4")
            mock_blob.upload_from_filename.assert_called_once_with(video_path)
            self.assertTrue(
                any("Uploaded file" in message for message in log_cm.output),
                msg="Expected upload confirmation log entry",
            )


if __name__ == "__main__":
    unittest.main()
