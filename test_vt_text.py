import requests
import urllib.parse

BASE_URL = "http://127.0.0.1:8000"

def test_text_voice_translate():
    print("Testing /voice-translate (Text -> Speech)...")
    try:
        data = {
            'text': 'Hello, how are you?',
            'src_lang': 'en',
            'tgt_lang': 'hi',
            'gender': 'female'
        }
        res = requests.post(f"{BASE_URL}/voice-translate", data=data)
        if res.status_code == 200:
            print("✅ /voice-translate success!")
            print(f"Content-Type: {res.headers.get('content-type')}")
            translated_header = res.headers.get('X-Translated-Text')
            print(f"X-Translated-Text (raw): {translated_header}")
            if translated_header:
                try:
                    decoded = urllib.parse.unquote(translated_header)
                    print(f"X-Translated-Text (decoded): {decoded}")
                except:
                    print("Could not decode header")
            
            with open("test_vt_text.mp3", "wb") as f:
                f.write(res.content)
        else:
            print(f"❌ /voice-translate failed: {res.status_code} {res.text}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_text_voice_translate()
