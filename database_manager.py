import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime 

# Carichiamo le chiavi (compatibile con .env locale e Secrets del Cloud)
if os.path.exists(".env"):
    load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def salva_ricordo(audio_path, trascrizione_grezza, testo_pulito, stile, titolo):
    """
    Gestisce il caricamento del file audio e il salvataggio dei testi nel database.
    """
    try:
        # 1. Creiamo un nome file univoco usando il timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(audio_path)[1]
        file_name = f"audio_{timestamp}{file_extension}"
        
        # Caricamento file audio nello Storage
        with open(audio_path, 'rb') as f:
            supabase.storage.from_("audio_ricordi").upload(file_name, f)
        
        # Otteniamo l'URL pubblico del file audio
        res_url = supabase.storage.from_("audio_ricordi").get_public_url(file_name)
        if hasattr(res_url, 'public_url'):
            audio_url = res_url.public_url
        elif isinstance(res_url, dict):
            audio_url = res_url.get('publicURL', res_url)
        else:
            audio_url = str(res_url)
        
        # 2. Inserimento dati nella tabella 'ricordi'
        data = {
            "titolo": titolo,
            "trascrizione_grezza": trascrizione_grezza,
            "diario_pulito": testo_pulito,
            "audio_url": str(audio_url),      
            "stile_usato": stile
        }
        
        supabase.table("ricordi").insert(data).execute()
        
        # Sincronizzazione locale (se siamo sul PC)
        sincronizza_libro_locale()
        
        return True
    except Exception as e:
        print(f"Errore durante il salvataggio: {e}")
        return False

def carica_ricordi():
    """
    Recupera tutti i ricordi ordinati dal più vecchio al più recente.
    """
    try:
        response = supabase.table("ricordi").select("*").order("created_at", desc=False).execute()
        return response.data
    except Exception as e:
        print(f"Errore nel recupero dati: {e}")
        return []

def elimina_ricordo(ricordo_id, audio_url=None):
    """
    Rimuove un ricordo dal database e il relativo file audio dallo storage.
    """
    try:
        # 1. Elimina il testo dal database
        supabase.table("ricordi").delete().eq("id", ricordo_id).execute()
        
        # 2. Elimina il file audio dallo storage se l'URL è presente
        if audio_url:
            try:
                # Estraiamo il nome del file dall'URL pubblico
                file_name = audio_url.split("/")[-1]
                supabase.storage.from_("audio_ricordi").remove([file_name])
            except Exception as e:
                print(f"File audio non trovato o già rimosso: {e}")
        
        return True
    except Exception as e:
        print(f"Errore eliminazione: {e}")
        return False

def aggiorna_ricordo(ricordo_id, nuovo_testo):
    """
    Aggiorna il testo elaborato di un ricordo esistente.
    """
    try:
        supabase.table("ricordi").update({"diario_pulito": nuovo_testo}).eq("id", ricordo_id).execute()
        return True
    except Exception as e:
        print(f"Errore aggiornamento: {e}")
        return False

def sincronizza_libro_locale():
    """
    Crea il file unico sul PC. Ignorato se l'app gira sul Cloud.
    """
    try:
        path_cartella = "D:/Archivio/Desktop/EreditaDigitale"
        path_pc = f"{path_cartella}/Il_Mio_Libro_Digitale.txt"
        
        if os.path.exists(path_cartella):
            ricordi = carica_ricordi()
            with open(path_pc, "w", encoding="utf-8") as f:
                f.write("======= IL MIO DIARIO - EREDITÀ DIGITALE =======\n\n")
                for r in ricordi:
                    data_f = r['created_at'][:10]
                    f.write(f"--- {r['titolo']} ({data_f}) ---\n")
                    f.write(f"{r['diario_pulito']}\n\n")
                    f.write("*" * 40 + "\n\n")
            return path_pc
    except Exception:
        pass
    return None
