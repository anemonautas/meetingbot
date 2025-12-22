import os
from pathlib import Path
from pydub import AudioSegment
from libot.compress import compress_audio

import pytest


@pytest.mark.parametrize(
    "filename",
    [
        "input_1.wav",
    ],
)
def test_compress_audio_mono_16khz(
    fixtures_dir: Path,
    tmp_path: Path,
    filename: str,
) -> None:
    input_path = fixtures_dir / filename
    output_path = tmp_path / f"{Path(filename).stem}_compressed.mp3"

    compress_audio(str(input_path), str(output_path), bitrate="128k")

    assert output_path.exists()
    assert output_path.stat().st_size > 0

    result = AudioSegment.from_file(output_path)

    assert result.channels == 1
    assert result.frame_rate == 16000

    original = AudioSegment.from_file(input_path)

    _acceptable_duration_delta_ms = 100
    assert abs(len(result) - len(original)) < _acceptable_duration_delta_ms


@pytest.mark.parametrize(
    "filename",
    [
        "input_1.wav",
    ],
)
def test_compress_audio_bitrate_afecta_tamaño(
    fixtures_dir: Path,
    tmp_path: Path,
    filename: str,
) -> None:
    input_path = fixtures_dir / filename
    out_64k = tmp_path / f"{Path(filename).stem}_64k.mp3"
    out_192k = tmp_path / f"{Path(filename).stem}_192k.mp3"

    compress_audio(str(input_path), str(out_64k), bitrate="64k")
    compress_audio(str(input_path), str(out_192k), bitrate="192k")

    assert out_64k.exists()
    assert out_192k.exists()

    size_64k = os.path.getsize(out_64k)
    size_192k = os.path.getsize(out_192k)

    assert size_64k < size_192k
