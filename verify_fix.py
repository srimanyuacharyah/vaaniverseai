import sys
import os
# Add src to path to allow imports
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from vaaniverse import voice_translator
    print("Successfully imported voice_translator")
except ImportError as e:
    print(f"Failed to import voice_translator: {e}")
    sys.exit(1)

import shutil
if shutil.which("ffmpeg"):
    print(f"ffmpeg found at: {shutil.which('ffmpeg')}")
else:
    print("ffmpeg NOT found in PATH")

print("Verification script finished.")
