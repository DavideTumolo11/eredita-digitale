import streamlit as st
import os  
from styles import apply_styles
from streamlit_mic_recorder import mic_recorder
from editor_invisibile import trascrivi_audio, pulisci_testo
from database_manager import salva_ricordo, carica_ricordi, elimina_ricordo, aggiorna_ricordo, sincronizza_libro_locale
from datetime import datetime 

# Configurazione pagina
st.set_page_config(page_title="Eredità Digitale", layout="centered")
apply_styles()

st.markdown("<h1>Eredità Digitale</h1>", unsafe_allow_html=True)

# Inizializzazione contatore per resettare il widget audio
if 'reset_counter' not in st.session_state:
    st.session_state['reset_counter'] = 0

def reset_totale():
    for k in ['testo_pulito_cache', 'testo_grezzo_cache', 'last_audio_id', 'audio_bytes_cache']:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state['reset_counter'] += 1
    st.rerun()

# Recupero della lista ricordi
lista_ricordi = carica_ricordi()

# Preparazione del testo fluido (Libro Digitale)
testo_libro_fluido = ""
if lista_ricordi:
    testo_libro_fluido = " ".join([r['diario_pulito'] for r in lista_ricordi])

# --- SIDEBAR: STATO, LIBRO E SINCRONIZZAZIONE ---
with st.sidebar:
    st.markdown("### Stato Sistema")
    st.write("Database: Collegato")
    st.write("AI: Selezione Automatica (Multi-AI)")
    
    st.markdown("---")
    st.markdown("### Impostazioni Scrittura")
    stile_editing = st.radio("Stile del Diario:", ["Standard", "Cinema"])
    
    st.markdown("---")
    # PULSANTE SINCRONIZZAZIONE
    if st.button("Sincronizza Libro su PC"):
        with st.spinner("Lancio sincronizzazione locale..."):
            if sincronizza_libro_locale():
                st.success("File .txt aggiornato sul tuo PC!")
            else:
                st.info("Sincronizzazione Cloud completata. Se sei su PC, verifica che Python sia nel PATH.")

    st.markdown("---")
    # VISUALIZZAZIONE LIBRO NELLA SIDEBAR (Anteprima fluida)
    st.markdown("### Anteprima Libro")
    if testo_libro_fluido:
        st.text_area("Flusso narrativo:", value=testo_libro_fluido, height=300, disabled=True, key="sidebar_book")
    else:
        st.write("Inizia a registrare per comporre il libro.")

# --- AREA DI REGISTRAZIONE ---
st.write("")
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    audio_record = mic_recorder(
        start_prompt="AVVIA REGISTRAZIONE",
        stop_prompt="STOP (ELABORA)",
        key=f"recorder_{st.session_state['reset_counter']}",
        use_container_width=True
    )

    if audio_record:
        if 'last_audio_id' not in st.session_state or st.session_state.get('last_audio_id') != audio_record['id']:
            with st.spinner("L'IA sta leggendo il libro e collegando i pensieri..."):
                testo_grezzo = trascrivi_audio(audio_record['bytes'])
                
                # Recuperiamo le ultime 300 battute per dare contesto all'IA
                contesto_recente = testo_libro_fluido[-300:] if testo_libro_fluido else ""
                
                # Passiamo il contesto alla funzione pulisci_testo
                st.session_state['testo_pulito_cache'] = pulisci_testo(testo_grezzo, modalita=stile_editing, contesto=contesto_recente)
                st.session_state['testo_grezzo_cache'] = testo_grezzo
                st.session_state['last_audio_id'] = audio_record['id']
                st.session_state['audio_bytes_cache'] = audio_record['bytes']

        if 'testo_pulito_cache' in st.session_state:
            st.markdown("### Nuova aggiunta al Libro")
            testo_finale = st.text_area("Modifica o conferma l'unione:", value=st.session_state['testo_pulito_cache'], height=250)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("SALVA NEL DIARIO"):
                    temp_fs = "temp_save.wav"
                    with open(temp_fs, "wb") as f: f.write(st.session_state['audio_bytes_cache'])
                    titolo_auto = f"Ricordo del {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                    if salva_ricordo(temp_fs, st.session_state['testo_grezzo_cache'], testo_finale, stile_editing, titolo_auto):
                        if os.path.exists(temp_fs): os.remove(temp_fs)
                        reset_totale()
            with c2:
                if st.button("SCARTA"):
                    reset_totale()

# --- IL MIO LIBRO DIGITALE (VISUALIZZAZIONE HOME) ---
st.markdown("---")
st.markdown("## 📖 Il Mio Libro Digitale")
if testo_libro_fluido:
    # Mostra il libro come un unico grande blocco di testo leggibile
    st.markdown(f"""
    <div style="background-color: #fdf5e6; padding: 30px; border-radius: 10px; border: 1px solid #d2b48c; font-family: 'Georgia', serif; line-height: 1.6; color: #3e2723;">
        {testo_libro_fluido}
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("Il tuo libro è ancora bianco. Registra il primo pensiero per iniziare.")

# --- GESTIONE CAPITOLI ---
st.markdown("---")
st.markdown("## Gestione Capitoli")
if lista_ricordi:
    for ricordo in lista_ricordi:
        with st.expander(f"{ricordo['titolo']}"):
            nuovo_testo = st.text_area("Contenuto:", value=ricordo.get('diario_pulito', ''), key=f"edit_{ricordo['id']}", height=150)
            col_a, col_b = st.columns([3, 1])
            with col_a:
                if st.button("Salva Modifica", key=f"btn_up_{ricordo['id']}"):
                    if aggiorna_ricordo(ricordo['id'], nuovo_testo):
                        st.success("Modificato.")
                        st.rerun()
            with col_b:
                if st.button("Elimina", key=f"btn_del_book_{ricordo['id']}"):
                    if elimina_ricordo(ricordo['id'], ricordo.get('audio_url')):
                        st.rerun()

# --- ARCHIVIO AUDIO ---
st.markdown("---")
st.markdown("### Archivio Audio")
if lista_ricordi:
    for ricordo in reversed(lista_ricordi):
        with st.expander(f"Audio: {ricordo['titolo']}"):
            st.audio(ricordo['audio_url'])
            if st.button("Elimina audio", key=f"btn_del_arc_{ricordo['id']}"):
                if elimina_ricordo(ricordo['id'], ricordo.get('audio_url')):
                    st.rerun()
