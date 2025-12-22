from pydub import AudioSegment

def _ensure_whole_frames(audio: AudioSegment) -> AudioSegment:
    """
    Trim trailing bytes so that the length of the raw data
    is a whole number of frames for the current sample_width * channels.
    This avoids audioop.error: not a whole number of frames.
    """
    frame_size = audio.sample_width * audio.channels  # bytes per frame
    if frame_size == 0:
        return audio  # defensive

    remainder = len(audio._data) % frame_size
    if remainder:
        trimmed_data = audio._data[:-remainder]
        audio = audio._spawn(trimmed_data)

    return audio


def compress_audio(input_path: str, output_path: str, bitrate: str = "128k") -> None:
    audio = AudioSegment.from_file(input_path)
    audio = _ensure_whole_frames(audio)
    audio = audio.set_channels(1)  # mono
    audio = audio.set_frame_rate(16000)  # 16 kHz
    audio.export(output_path, format="mp3", bitrate=bitrate)
