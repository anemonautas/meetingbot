# tests/test_compress_audio_golden.py

import hashlib
from pathlib import Path

import pytest
from pydub import AudioSegment

# Ajusta este import al módulo real donde tengas la función
# por ejemplo: from my_project.audio import compress_audio
from libot.compress import compress_audio


# Nombres de los ficheros en tests/fixtures
INPUT_FILENAME = "input_1.wav"  # cámbialo por el nombre real
EXPECTED_OUTPUT_FILENAME = "output.mp3"  # este es tu golden file


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def test_compress_audio_matches_golden(fixtures_dir: Path, tmp_path: Path) -> None:
    input_path = fixtures_dir / INPUT_FILENAME
    expected_path = fixtures_dir / EXPECTED_OUTPUT_FILENAME
    actual_path = fixtures_dir / "output.mp3"

    # 2) Comprobación extra de propiedades por si algún día cambias la implementación
    expected_audio = AudioSegment.from_file(expected_path)
    actual_audio = AudioSegment.from_file(actual_path)

    assert actual_audio.channels == expected_audio.channels == 1
    assert actual_audio.frame_rate == expected_audio.frame_rate == 16000
    assert abs(len(actual_audio) - len(expected_audio)) < 50

    compress_audio(str(input_path), str(actual_path), "128k")

    # 1) Comparación estricta de bytes (golden file)
    assert _md5(actual_path) == _md5(expected_path)


def test_compress_audio(fixtures_dir: Path, tmp_path: Path) -> None:
    input_path = fixtures_dir / 'audio_000.wav'
    expected_path = fixtures_dir / EXPECTED_OUTPUT_FILENAME
    actual_path = tmp_path / "output.mp3"
    compress_audio(str(input_path), str(actual_path), "128k")
    assert actual_path.exists()
    assert actual_path.stat().st_size > 0