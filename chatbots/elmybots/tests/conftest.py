import pytest


@pytest.fixture(autouse=True)
def set_api_keys(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy_key")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_key")
