from pathlib import Path
import pytest


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """
    Directorio donde están los audios de prueba:
    tests/fixtures/...
    """
    return Path(__file__).resolve().parent / "fixtures"
