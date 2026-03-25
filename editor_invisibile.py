import os
import requests 
import base64    
from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv()

def pulisci_testo(testo_grezzo, modalita="Standard"):
    gemini_key = os.environ.get("GEMINI_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")
    or_key = os.environ.get("OPENROUTER_API_KEY")

    if modalita == "Cinema":
        prompt = f"Riscrivi in stile evocativo (Interstellar/Notebook): {testo_grezzo}"
    else:
        prompt = f"Agisci come editor invisibile, pulisci il testo parlato senza inventare nulla: {testo_grezzo}"

    # 1. TENTATIVO GEMINI 2.0 FLASH
    if gemini_key:
        try:
            url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
            res = requests.post(url_gemini, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        except:
            pass

    # 2. FALLBACK GROQ
    if groq_key:
        try:
            url_groq = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {groq_key}"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}]
            }
            res = requests.post(url_groq, json=payload, timeout=15)
            return res.json()['choices'][0]['message']['content']
        except:
            pass

    return testo_grezzo

def trascrivi_audio(audio_bytes):
    gemini_key = os.environ.get("GEMINI_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")

    # --- 1. TENTATIVO CON GEMINI 2.0 FLASH ---
    if gemini_key:
        try:
            url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            payload = {
                "contents": [{
                    "parts": [
                        {"text": "Trascrivi parola per parola in italiano:"},
                        {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}}
                    ]
                }]
            }
            res = requests.post(url_gemini, json=payload, timeout=30)
            data = res.json()
            if 'candidates' in data:
                return data['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"Gemini fallito, provo Whisper... {e}")

    # --- 2. FALLBACK CON GROQ WHISPER (Usa la tua chiave Groq esistente) ---
    if groq_key:
        try:
            with open("temp_whisper.wav", "wb") as f:
                f.write(audio_bytes)
            
            url_whisper = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers = {"Authorization": f"Bearer {groq_key}"}
            
            with open("temp_whisper.wav", "rb") as f:
                files = {
                    'file': ('temp_whisper.wav', f),
                    'model': (None, 'whisper-large-v3-turbo'),
                    'language': (None, 'it'),
                    'response_format': (None, 'json')
                }
                res = requests.post(url_whisper, headers=headers, files=files, timeout=30)
            
            os.remove("temp_whisper.wav")
            return res.json().get('text', "Errore: Whisper non ha restituito testo.")
        except Exception as e:
            return f"Errore totale: {str(e)}"

    return "Errore: Nessuna chiave rilevata."
