import os
import requests 
import base64    
from dotenv import load_dotenv

# Carica .env solo se esiste (per test locali)
if os.path.exists(".env"):
    load_dotenv()

def pulisci_testo(testo_grezzo, modalita="Standard"):
    """
    Sistema a cascata: Prova Gemini -> Fallback su Groq -> Fallback su OpenRouter.
    """
    # Recupero dinamico delle chiavi dai Secrets/Ambiente
    gemini_key = os.environ.get("GEMINI_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")
    or_key = os.environ.get("OPENROUTER_API_KEY")

    if modalita == "Cinema":
        prompt = f"""
        Riscrivi questo ricordo in uno stile narrativo ed evocativo, 
        ispirandoti a film come 'Interstellar', 'Il Curioso Caso di Benjamin Button' e 'The Notebook'. 
        Mantieni i fatti reali e le persone citate, ma rendi l'atmosfera profonda, 
        malinconica e senza tempo. Usa un linguaggio poetico ma autentico.
        Testo da elaborare: {testo_grezzo}
        """
    else:
        prompt = f"""
        Agisci come un editor invisibile. Pulisci questo testo parlato dai difetti 
        tipici (ripetizioni, "ehm", inciampi, frasi interrotte). 
        NON aggiungere parole che non ho detto. NON inventare fatti. 
        Mantieni la mia voce autentica. Riorganizza solo la punteggiatura e la fluidità.
        Testo da elaborare: {testo_grezzo}
        """

    # --- 1. TENTATIVO CON GEMINI ---
    if gemini_key:
        try:
            url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url_gemini, json=payload, timeout=10)
            data = res.json()
            if 'candidates' in data:
                return data['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"Gemini fallito, provo Groq... ({e})")

    # --- 2. FALLBACK CON GROQ ---
    if groq_key:
        try:
            url_groq = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload_groq = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}]
            }
            res = requests.post(url_groq, json=payload_groq, timeout=10)
            data = res.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"Groq fallito, provo OpenRouter... ({e})")

    # --- 3. FALLBACK CON OPENROUTER ---
    if or_key:
        try:
            url_or = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"}
            payload_or = {
                "model": "google/gemini-2.0-flash-001", 
                "messages": [{"role": "user", "content": prompt}]
            }
            res = requests.post(url_or, json=payload_or, timeout=10)
            data = res.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content']
        except Exception:
            pass

    return testo_grezzo

def trascrivi_audio(audio_bytes):
    """
    Trascrizione audio usando Gemini-2.0-flash.
    """
    # Recupero dinamico della chiave
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    if not gemini_key:
        return "Errore: La chiave GEMINI_API_KEY non è stata rilevata dal sistema Cloud."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

    payload = {
        "contents": [{
            "parts": [
                {"text": "Trascrivi accuratamente questo audio in lingua italiana, parola per parola. Non saltare nulla."},
                {
                    "inline_data": {
                        "mime_type": "audio/wav", 
                        "data": audio_b64
                    }
                }
            ]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()
        if 'candidates' in data and len(data['candidates']) > 0:
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Errore trascrizione: {data.get('error', {}).get('message', 'Risposta API non valida')}"
    except Exception as e:
        return f"Errore tecnico trascrizione: {str(e)}"
