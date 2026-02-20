import os
import sys
import wave
import subprocess
import traceback

# Add src to path
current_dir = os.getcwd()
if os.path.basename(current_dir) == 'src':
    sys.path.append(current_dir)
else:
    sys.path.append(os.path.join(current_dir, 'src'))

try:
    from vaaniverse import voice_translator
    print("Import successful.")
except ImportError:
    print("Import failed.")
    sys.exit(1)

def create_dummy_wav(filename):
    with wave.open(filename, 'wb') as wav_file:
        # Set parameters: 1 channel, 2 bytes per sample, 44100 Hz, 0 frames
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(44100)
        # Write some silence
        wav_file.writeframes(b'\x00\x00' * 44100) # 1 second of silence

def convert_wav_to_mp3(wav_file, mp3_file):
    # Try to find ffmpeg
    ffmpeg_cmd = "ffmpeg"
    if os.path.exists("ffmpeg.exe"):
        ffmpeg_cmd = ".\\ffmpeg.exe"
    elif os.path.exists("..\\ffmpeg.exe"):
        ffmpeg_cmd = "..\\ffmpeg.exe"
    
    # Simple conversion
    cmd = [ffmpeg_cmd, "-y", "-i", wav_file, mp3_file]
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)

try:
    print("Creating test.wav...")
    create_dummy_wav("test.wav")
    
    print("Converting test.wav to test.mp3 using ffmpeg cli...")
    convert_wav_to_mp3("test.wav", "test.mp3")
    
    print("Attempting to transcribe test.mp3 (via voice_translator)...")
    # This triggers the pydub conversion path in voice_translator (MP3 -> WAV)
    text = voice_translator.transcribe_audio("test.mp3")
    print("Transcription successful (result might be empty string for silence).")
    
except subprocess.CalledProcessError as e:
    print(f"FFmpeg CLI failed: {e}")
except Exception:
    traceback.print_exc()
finally:
    # Cleanup
    if os.path.exists("test.wav"): os.remove("test.wav")
    if os.path.exists("test.mp3"): os.remove("test.mp3")
    # pydub might create a wav file? voice_translator cleans it up?
    # voice_translator does NOT clean up the converted wav file in the current code?
    # let's check.
    # It says: wav_path = str(path.with_suffix('.wav'))
    # It does NOT delete it.
