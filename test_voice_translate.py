import requests
import time
import os

BASE_URL = "http://127.0.0.1:8000"

def test_auto_translate_tts():
    print("Testing Auto-Translate TTS (/speak-age)...")
    try:
        data = {
            'text': 'Hello my friend, how are you doing today?', 
            'lang': 'hi', 
            'gender': 'female', 
            'age_preset': 'adult',
            'auto_translate': 'on'
        }
        res = requests.post(f"{BASE_URL}/speak-age", data=data)
        if res.status_code == 200 and res.headers.get('content-type') == 'audio/mpeg':
            print("✅ /speak-age success! Received audio/mpeg")
            with open("test_age_translated.mp3", "wb") as f:
                f.write(res.content)
        else:
            print(f"❌ /speak-age failed: {res.status_code} {res.text}")
    except Exception as e:
        print(f"❌ /speak-age error: {str(e)}")

    print("Testing Auto-Translate Legendary (/speak-legendary)...")
    try:
        # Assuming 'modi' voice exists and maps to Hindi
        data = {
            'voice_id': 'modi', 
            'text': 'India is a great country with rich culture.', 
            'auto_translate': 'on'
        }
        res = requests.post(f"{BASE_URL}/speak-legendary", data=data)
        if res.status_code == 200 and res.headers.get('content-type') == 'audio/mpeg':
            print("✅ /speak-legendary success! Received audio/mpeg")
            with open("test_legendary_translated.mp3", "wb") as f:
                f.write(res.content)
        else:
            print(f"❌ /speak-legendary failed: {res.status_code} {res.text}")
    except Exception as e:
        print(f"❌ /speak-legendary error: {str(e)}")

def test_speech_to_speech():
    print("Testing Speech-to-Speech (/voice-translate-audio)...")
    
    # 1. Generate input audio using standard TTS
    print("-> Generating input audio...")
    try:
        tts_data = {'text': 'This is a test message for translation.', 'lang': 'en', 'gender': 'female', 'backend': 'edge-tts'}
        input_res = requests.post(f"{BASE_URL}/speak", data=tts_data)
        if input_res.status_code != 200:
            print("❌ Failed to generate input audio")
            return
        
        with open("test_input.mp3", "wb") as f:
            f.write(input_res.content)
        print("-> Input audio generated.")
    except Exception as e:
        print(f"❌ Input generation error: {str(e)}")
        return

    # 2. Upload for translation
    print("-> Uploading for speech-to-speech translation...")
    try:
        with open("test_input.mp3", "rb") as f:
            files = {'file': ('test_input.mp3', f, 'audio/mpeg')}
            data = {'src_lang': 'en', 'tgt_lang': 'hi', 'gender': 'female'}
            res = requests.post(f"{BASE_URL}/voice-translate-audio", files=files, data=data)
            
            if res.status_code == 200:
                print("✅ /voice-translate-audio success!")
                transcribed = res.headers.get('X-Transcribed-Text')
                translated = res.headers.get('X-Translated-Text')
                print(f"   Transcribed: {transcribed}")
                print(f"   Translated: {translated}")
                with open("test_s2s_result.mp3", "wb") as out:
                    out.write(res.content)
            else:
                 print(f"❌ /voice-translate-audio failed: {res.status_code} {res.text}")

    except Exception as e:
        print(f"❌ /voice-translate-audio error: {str(e)}")
    
    # Cleanup
    if os.path.exists("test_input.mp3"): os.remove("test_input.mp3")

if __name__ == "__main__":
    test_auto_translate_tts()
    test_speech_to_speech()
