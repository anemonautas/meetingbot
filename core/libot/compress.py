from pydub import AudioSegment


def compress_audio(input_path: str, output_path: str, bitrate: str = "128k") -> None:
    # Load WAV (or other format)
    audio = AudioSegment.from_file(input_path)

    # Optionally downsample to mono and lower sample rate
    audio = audio.set_channels(1)  # mono
    audio = audio.set_frame_rate(16000)  # 16 kHz

    # Export as MP3 with chosen bitrate (lower = more compression)
    audio.export(output_path, format="mp3", bitrate=bitrate)
