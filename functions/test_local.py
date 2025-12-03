import os
import sys
from unittest.mock import MagicMock, patch

# Mock dependencies before importing main
mock_ff = MagicMock()
# Make the cloud_event decorator pass through the function
mock_ff.cloud_event = lambda f: f
sys.modules["functions_framework"] = mock_ff

sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.storage"] = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = MagicMock()

# Now import main
import main

# Mock CloudEvent
class MockCloudEvent:
    def __init__(self, data):
        self.data = data
    
    def __getitem__(self, key):
        return {
            "id": "test-event-id",
            "type": "google.cloud.storage.object.v1.finalized"
        }.get(key)

@patch("main.storage.Client")
@patch("main.genai.Client")
def test_expose_to_gemini(mock_genai_client, mock_storage_client):
    # Setup mocks
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_storage_client.return_value.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    
    mock_files_client = MagicMock()
    mock_genai_client.return_value.files = mock_files_client
    
    mock_file_response = MagicMock()
    mock_file_response.display_name = "test_file.txt"
    mock_file_response.uri = "https://generativeai.google.com/files/123"
    mock_file_response.state = "PROCESSING"
    mock_files_client.upload.return_value = mock_file_response

    # Test data
    data = {
        "bucket": "test-bucket",
        "name": "test_folder/test_file.txt"
    }
    
    # Run function
    print("Running test_expose_to_gemini...")
    main.expose_to_gemini(MockCloudEvent(data))
    
    # Verify interactions
    mock_storage_client.assert_called_once()
    mock_bucket.blob.assert_called_with("test_folder/test_file.txt")
    mock_blob.download_to_filename.assert_called()
    mock_genai_client.assert_called_with(api_key="dummy_key")
    mock_files_client.upload.assert_called()
    print("Test passed successfully!")

if __name__ == "__main__":
    # Set dummy API key for test
    os.environ["GEMINI_API_KEY"] = "dummy_key"
    test_expose_to_gemini()
