import os
import sys
import asyncio

# Ensure src is in path
sys.path.insert(0, os.path.abspath('src'))

from vaaniverse import song_generator

async def verify_ai_singing():
    print("--- Starting AI Singing Verification ---")
    try:
        # We use a short 2-line version for speed
        song = await song_generator.generate_song_audio_async(
            theme='nature', 
            lang='en', 
            lines=2, 
            gender='female',
            genre='lofi'
        )
        
        audio_path = song.get("audio_path")
        print(f"Generated Audio Path: {audio_path}")
        
        if audio_path and os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            print(f"✅ Success: Audio file exists ({file_size} bytes)")
            
            # Additional check: Is it an MP3?
            if audio_path.endswith('.mp3'):
                print("✅ Success: File format is MP3")
            
            if song.get('lyrics'):
                print(f"✅ Lyrics generated: {song['lyrics'][:50]}...")
            
            return True
        else:
            print("❌ Failure: Audio file was not created.")
            if 'audio_error' in song:
                print(f"Error detail: {song['audio_error']}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(verify_ai_singing())
    sys.exit(0 if success else 1)
