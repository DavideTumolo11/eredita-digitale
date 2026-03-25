import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime 

# Carichiamo le chiavi (compatibile con .env locale e Secrets del Cloud)
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
        # Nota: .get_public_url su alcune versioni torna un oggetto, su altre una stringa
        res_url = supabase.storage.from_("audio_ricordi").get_public_url(file_name)
        audio_url = res_url if isinstance(res_url, str) else res_url.get('publicURL', res_url)
        
        # 2. Inserimento dati nella tabella 'ricordi'
        data = {
            "titolo": titolo,
            "trascrizione_grezza": trascrizione_grezza,
            "diario_pulito": testo_pulito,
            "audio_url": str(audio_url),       
            "stile_usato": stile
        }
        
        supabase.table("ricordi").insert(data).execute()
        
        # Aggiornamento automatico del "Libro" locale se siamo sul PC
        sincronizza_libro_locale()
        
        return True
    except Exception as e:
        print(f"Errore durante il salvataggio: {e}")
        return False

def carica_ricordi():
    """
    Recupera tutti i ricordi salvati dal database, ordinati dal più vecchio al più recente 
    per formare il "Libro" cronologico.
    """
    try:
        # Ordiniamo per created_at ASC per avere la storia che prosegue nel tempo
        response = supabase.table("ricordi").select("*").order("created_at", desc=False).execute()
        return response.data
    except Exception as e:
        print(f"Errore nel recupero dati: {e}")
        return []

def sincronizza_libro_locale():
    """
    Questa funzione scarica tutto e crea il file unico sul PC.
    Viene ignorata se l'app gira sul Cloud (iPhone).
    """
    try:
        # Percorso del tuo file sul PC (modificalo se necessario)
        path_pc = "D:/Archivio/Desktop/EreditaDigitale/Il_Mio_Libro_Digitale.txt"
        
        # Controlliamo se siamo sul PC (se esiste il percorso della cartella)
        if os.path.exists("D:/Archivio/Desktop/EreditaDigitale"):
            ricordi = carica_ricordi()
            with open(path_pc, "w", encoding="utf-8") as f:
                f.write("======= IL MIO DIARIO - EREDITÀ DIGITALE =======\n\n")
                for r in ricordi:
                    data_f = r['created_at'][:10] # Prende solo YYYY-MM-DD
                    f.write(f"--- {r['titolo']} ({data_f}) ---\n")
                    f.write(f"{r['diario_pulito']}\n\n")
                    f.write("*" * 40 + "\n\n")
            print("Libro locale aggiornato con successo.")
    except Exception as e:
        # In cloud fallirà silenziosamente perché il percorso D:/ non esiste
        pass