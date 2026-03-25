import streamlit as st
import os  
from styles import apply_styles
from streamlit_mic_recorder import mic_recorder
from editor_invisibile import trascrivi_audio, pulisci_testo
from database_manager import salva_ricordo, carica_ricordi, sincronizza_libro_locale
from datetime import datetime 

# Configurazione pagina
st.set_page_config(page_title="Eredità Digitale", layout="centered")

# Applicazione dello stile personalizzato (Sabbia/Seppia)
apply_styles()

# Titolo in stile antico
st.markdown("<h1>Eredità Digitale</h1>", unsafe_allow_html=True)

# Recupero della lista ricordi all'avvio per popolare le sezioni
lista_ricordi = carica_ricordi()

# Sidebar con Stato Sistema e Impostazioni
with st.sidebar:
    st.markdown("### Stato Sistema")
    st.write("Database: Collegato")
    st.write("AI: Selezione Automatica (Multi-AI)")
    
    st.markdown("---")
    st.markdown("### Impostazioni Scrittura")
    stile_editing = st.radio(
        "Stile del Diario:",
        ["Standard", "Cinema"],
        index=0,
        help="Standard: Editor invisibile. Cinema: Stile Interstellar/Benjamin Button."
    )
    
    st.markdown("---")
    # TASTO SINCRONIZZAZIONE LOCALE
    if st.button("Sincronizza Libro su PC"):
        with st.spinner("Aggiornamento file locale in corso..."):
            path = sincronizza_libro_locale()
            if path:
                st.success(f"Sincronizzato su: {path}")
            else:
                st.info("Sincronizzazione completata (Cloud mode).")

# Area Principale di Registrazione
st.write("")
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    audio_record = mic_recorder(
        start_prompt="AVVIA REGISTRAZIONE",
        stop_prompt="STOP (ELABORA)",
        key='recorder',
        use_container_width=True
    )

    if audio_record:
        # Effetto visivo parole offuscate durante l'elaborazione
        st.markdown(
            f'<div class="background-text">Le tue parole stanno diventando memoria...</div>', 
            unsafe_allow_html=True
        )
        
        # Gestione cache per evitare ricaricamenti inutili dell'AI
        if 'testo_pulito_cache' not in st.session_state or st.session_state.get('last_audio_id') != audio_record['id']:
            with st.spinner("L'IA sta ascoltando il tuo racconto..."):
                testo_grezzo = trascrivi_audio(audio_record['bytes'])
                st.session_state['testo_pulito_cache'] = pulisci_testo(testo_grezzo, modalita=stile_editing)
                st.session_state['testo_grezzo_cache'] = testo_grezzo
                st.session_state['last_audio_id'] = audio_record['id']
            
        st.markdown("### Il tuo Racconto")
        
        testo_finale = st.text_area("Versione elaborata:", 
                                    value=st.session_state['testo_pulito_cache'], 
                                    height=250)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("SALVA NEL DIARIO"):
                with st.spinner("Archiviazione in corso..."):
                    temp_filename = "temp_audio_to_save.wav"
                    with open(temp_filename, "wb") as f:
                        f.write(audio_record['bytes'])
                    
                    titolo_auto = f"Ricordo del {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                    
                    successo = salva_ricordo(
                        audio_path=temp_filename,
                        trascrizione_grezza=st.session_state['testo_grezzo_cache'],
                        testo_pulito=testo_finale,
                        stile=stile_editing,
                        titolo=titolo_auto
                    )
                    
                    if successo:
                        st.success("Archiviato per sempre.")
                        # Rimosso st.balloons() perché contiene emoji/animazioni grafiche non richieste
                        st.rerun()
                        if os.path.exists(temp_filename): 
                            os.remove(temp_filename)
                    else:
                        st.error("Errore durante il salvataggio.")
        
        with col_btn2:
            if st.button("SCARTA"):
                st.warning("Registrazione eliminata.")
                st.rerun()

# --- SEZIONE: IL LIBRO (DIARIO COMPLETO) ---
st.markdown("---")
st.markdown("## Il Mio Libro")
if lista_ricordi:
    with st.container():
        testo_completo = ""
        for ricordo in lista_ricordi:
            data_r = ricordo.get('created_at', '')[:10]
            testo_completo += f"**{ricordo['titolo']}** ({data_r})\n\n{ricordo.get('diario_pulito', '')}\n\n---\n\n"
        
        st.markdown(testo_completo)
else:
    st.write("Il libro è ancora bianco. Inizia a raccontare.")

# --- SEZIONE CRONOLOGIA (ARCHIVIO AUDIO) ---
st.markdown("---")
st.markdown("### Archivio Audio")

if lista_ricordi:
    for ricordo in reversed(lista_ricordi):
        with st.expander(f"Rec: {ricordo['titolo']} ({ricordo.get('stile_usato', 'N/A')})"):
            st.audio(ricordo['audio_url'])
            st.write(f"**Trascrizione originale:** {ricordo.get('trascrizione_grezza', 'Non disponibile')}")