import os
import requests 
import base64    
from dotenv import load_dotenv

load_dotenv()

# Recupero chiavi (compatibile con PC e Streamlit Cloud)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def pulisci_testo(testo_grezzo, modalita="Standard"):
    """
    Sistema a cascata: Prova Gemini -> Fallback su Groq -> Fallback su OpenRouter.
    """
    
    # --- DEFINIZIONE PROMPT ---
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
    try:
        url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url_gemini, json=payload, timeout=10)
        data = res.json()
        if 'candidates' in data:
            return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Gemini fallito, provo Groq... ({e})")

    # --- 2. FALLBACK CON GROQ (Se Gemini fallisce o è occupato) ---
    if GROQ_API_KEY:
        try:
            url_groq = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
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

    # --- 3. FALLBACK CON OPENROUTER (Ultima risorsa) ---
    if OPENROUTER_API_KEY:
        try:
            url_or = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
            payload_or = {
                "model": "google/gemini-2.0-flash-001", # Usa gemini tramite OpenRouter
                "messages": [{"role": "user", "content": prompt}]
            }
            res = requests.post(url_or, json=payload_or, timeout=10)
            data = res.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"Tutti i modelli AI hanno fallito: {e}")

    return testo_grezzo

def trascrivi_audio(audio_bytes):
    """
    Trascrizione audio usando Gemini-2.0-flash.
    """
    if not GEMINI_API_KEY:
        return "Errore: Manca la chiave API Gemini per la trascrizione."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
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
            return f"Errore trascrizione: {data.get('error', {}).get('message', 'Risposta non valida')}"
    except Exception as e:
        return f"Errore tecnico trascrizione: {str(e)}"