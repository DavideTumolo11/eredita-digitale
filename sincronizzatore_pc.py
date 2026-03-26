import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. Carichiamo le chiavi dal file .env nella stessa cartella
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("ERRORE: Chiavi non trovate nel file .env!")
    input("Premi Invio per uscire...")
    exit()

supabase: Client = create_client(url, key)

def sincronizza():
    print("Connessione a Supabase in corso...")
    try:
        # Percorso assoluto della cartella
        path_cartella = r"D:\Archivio\Desktop\EreditaDigitale"
        path_pc = os.path.join(path_cartella, "Il_Mio_Libro_Digitale.txt")
        
        # Creiamo la cartella se non esiste
        if not os.path.exists(path_cartella):
            os.makedirs(path_cartella)
            print(f"Cartella creata: {path_cartella}")

        # Scarichiamo i dati
        print("Scaricamento ricordi dal Cloud...")
        response = supabase.table("ricordi").select("*").order("created_at", desc=False).execute()
        ricordi = response.data

        if ricordi:
            print(f"Trovati {len(ricordi)} ricordi. Scrittura file...")
            with open(path_pc, "w", encoding="utf-8") as f:
                f.write("======= IL MIO DIARIO - EREDITA DIGITALE =======\n\n")
                
                for r in ricordi:
                    # Gestione della data (prendiamo i primi 10 caratteri della stringa ISO)
                    data_r = r.get('created_at', 'Data ignota')[:10]
                    titolo = r.get('titolo', 'Senza titolo')
                    testo = r.get('diario_pulito', '[Vuoto]')
                    
                    f.write(f"--- {titolo} ({data_r}) ---\n")
                    f.write(f"{testo}\n\n")
                    f.write("-" * 30 + "\n\n")
            
            print(f"SUCCESSO: Il libro e stato aggiornato in:\n{path_pc}")
        else:
            print("ATTENZIONE: Il database sembra vuoto. Nulla da scrivere.")

    except Exception as e:
        print(f"ERRORE DURANTE LA SINCRONIZZAZIONE: {e}")

if __name__ == "__main__":
    sincronizza()
    print("\nOperazione terminata.")
    input("Premi Invio per chiudere questa finestra...")