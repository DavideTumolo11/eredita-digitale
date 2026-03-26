import os
import subprocess
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime 

# Carichiamo le chiavi
if os.path.exists(".env"):
    load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def salva_ricordo(audio_path, trascrizione_grezza, testo_pulito, stile, titolo):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(audio_path)[1]
        file_name = f"audio_{timestamp}{file_extension}"
        
        with open(audio_path, 'rb') as f:
            supabase.storage.from_("audio_ricordi").upload(file_name, f)
        
        res_url = supabase.storage.from_("audio_ricordi").get_public_url(file_name)
        if hasattr(res_url, 'public_url'):
            audio_url = res_url.public_url
        elif isinstance(res_url, dict):
            audio_url = res_url.get('publicURL', res_url)
        else:
            audio_url = str(res_url)
        
        data = {
            "titolo": titolo,
            "trascrizione_grezza": trascrizione_grezza,
            "diario_pulito": testo_pulito,
            "audio_url": str(audio_url),      
            "stile_usato": stile
        }
        
        supabase.table("ricordi").insert(data).execute()
        
        # Sincronizzazione silente dopo il salvataggio
        sincronizza_libro_locale()
        
        return True
    except Exception as e:
        print(f"Errore durante il salvataggio: {e}")
        return False

def carica_ricordi():
    try:
        response = supabase.table("ricordi").select("*").order("created_at", desc=False).execute()
        return response.data
    except Exception as e:
        print(f"Errore nel recupero dati: {e}")
        return []

def elimina_ricordo(ricordo_id, audio_url=None):
    try:
        supabase.table("ricordi").delete().eq("id", ricordo_id).execute()
        if audio_url:
            try:
                file_name = audio_url.split("/")[-1]
                supabase.storage.from_("audio_ricordi").remove([file_name])
            except Exception:
                pass
        return True
    except Exception as e:
        print(f"Errore eliminazione: {e}")
        return False

def aggiorna_ricordo(ricordo_id, nuovo_testo):
    try:
        supabase.table("ricordi").update({"diario_pulito": nuovo_testo}).eq("id", ricordo_id).execute()
        return True
    except Exception as e:
        print(f"Errore aggiornamento: {e}")
        return False

def sincronizza_libro_locale():
    """
    Scrive il libro come testo fluido sul disco D.
    """
    try:
        path_cartella = r"D:\Archivio\Desktop\EreditaDigitale"
        path_pc = os.path.join(path_cartella, "Il_Mio_Libro_Digitale.txt")
        
        if not os.path.exists(path_cartella):
            return None

        ricordi = carica_ricordi()
        
        if ricordi:
            # Creiamo il flusso di testo unendo tutti i pezzi salvati
            libro_fluido = " ".join([r['diario_pulito'] for r in ricordi])
            
            with open(path_pc, "w", encoding="utf-8") as f:
                f.write("======= IL MIO DIARIO DIGITALE =======\n\n")
                f.write(libro_fluido)
                f.write("\n\n" + "=" * 30)
            return path_pc
    except Exception as e:
        print(f"Errore scrittura file locale: {e}")
    return None
