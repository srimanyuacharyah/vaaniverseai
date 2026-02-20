import os
import shutil
from pydub import AudioSegment

print("Checking ffmpeg availability...")
ffmpeg_path = shutil.which("ffmpeg")
ffprobe_path = shutil.which("ffprobe")

print(f"ffmpeg path: {ffmpeg_path}")
print(f"ffprobe path: {ffprobe_path}")

print("Path environment variable:")
print(os.environ["PATH"])

try:
    AudioSegment.converter = "ffmpeg"
    print("AudioSegment.converter set to 'ffmpeg'")
    # Create a dummy silent audio segment
    silent = AudioSegment.silent(duration=1000)
    print("Created silent audio segment successfully.")
except Exception as e:
    print(f"Error initializing AudioSegment: {e}")
