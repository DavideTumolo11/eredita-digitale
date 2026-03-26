import streamlit as st
import os  
from styles import apply_styles
from streamlit_mic_recorder import mic_recorder
from editor_invisibile import trascrivi_audio, pulisci_testo
from database_manager import salva_ricordo, carica_ricordi, elimina_ricordo, aggiorna_ricordo, sincronizza_libro_locale
from datetime import datetime 
from fpdf import FPDF # Libreria per il PDF

# Configurazione pagina
st.set_page_config(page_title="Eredità Digitale", layout="centered")
apply_styles()

# --- FUNZIONE GENERAZIONE PDF ---
def genera_pdf(testo_completo):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    # Usiamo un font standard che supporta bene i caratteri latini
    pdf.set_font("Times", size=12)
    
    # Titolo del libro nel PDF
    pdf.set_font("Times", style="B", size=16)
    pdf.cell(200, 10, txt="IL MIO DIARIO DIGITALE", ln=True, align='C')
    pdf.ln(10)
    
    # Corpo del testo
    pdf.set_font("Times", size=12)
    # multi_cell gestisce automaticamente l'andata a capo
    pdf.multi_cell(0, 10, txt=testo_completo)
    
    return pdf.output(dest='S') # Restituisce i bytes del PDF

# --- AGGIORNAMENTO: GESTIONE PAGINA ATTIVA ---
if 'pagina_attiva' not in st.session_state:
    st.session_state['pagina_attiva'] = "Scrittura"

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

# --- LOGICA FLUSSO TEMPORALE ---
testo_libro_fluido = ""
if lista_ricordi:
    testo_sezionato = []
    ultima_data = None
    
    for r in lista_ricordi:
        data_corrente = r.get('created_at', datetime.now().isoformat())[:10] 
        testo = r['diario_pulito'].strip()
        
        if ultima_data is None:
            testo_sezionato.append(testo)
        elif data_corrente == ultima_data:
            testo_sezionato.append(" " + testo)
        else:
            testo_sezionato.append("\n\n" + testo)
            
        ultima_data = data_corrente
    
    testo_libro_fluido = "".join(testo_sezionato)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### Navigazione")
    st.session_state['pagina_attiva'] = st.radio("Vai a:", ["Scrittura", "Lettura Libro"])
    st.markdown("---")
    st.markdown("### Stato Sistema")
    st.write("Database: Collegato")
    st.write("AI: Selezione Automatica")
    st.markdown("---")
    
    # --- PULSANTI DI ESPORTAZIONE ---
    st.markdown("### Esporta Libro")
    if st.button("Sincronizza Libro su PC"):
        with st.spinner("Sincronizzazione..."):
            if sincronizza_libro_locale():
                st.success("File .txt aggiornato!")
    
    if testo_libro_fluido:
        pdf_bytes = genera_pdf(testo_libro_fluido)
        st.download_button(
            label="Scarica File PDF",
            data=pdf_bytes,
            file_name="Il_Mio_Libro_Digitale.pdf",
            mime="application/pdf"
        )
    
    st.markdown("---")
    st.markdown("### Impostazioni Scrittura")
    stile_editing = st.radio("Stile del Diario:", ["Standard", "Cinema"])

# --- LOGICA DI VISUALIZZAZIONE ---

if st.session_state['pagina_attiva'] == "Scrittura":
    st.markdown("<h1>Eredità Digitale</h1>", unsafe_allow_html=True)
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
                with st.spinner("L'IA sta elaborando..."):
                    testo_grezzo = trascrivi_audio(audio_record['bytes'])
                    contesto_recente = testo_libro_fluido[-300:] if testo_libro_fluido else ""
                    st.session_state['testo_pulito_cache'] = pulisci_testo(testo_grezzo, modalita=stile_editing, contesto=contesto_recente)
                    st.session_state['testo_grezzo_cache'] = testo_grezzo
                    st.session_state['last_audio_id'] = audio_record['id']
                    st.session_state['audio_bytes_cache'] = audio_record['bytes']

            if 'testo_pulito_cache' in st.session_state:
                st.markdown("### Nuova aggiunta")
                testo_finale = st.text_area("Conferma:", value=st.session_state['testo_pulito_cache'], height=250)
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
                    if st.button("SCARTA"): reset_totale()

    st.markdown("---")
    st.markdown("## Gestione Capitoli")
    if lista_ricordi:
        for ricordo in lista_ricordi:
            with st.expander(f"{ricordo['titolo']}"):
                nuovo_testo = st.text_area("Contenuto:", value=ricordo.get('diario_pulito', ''), key=f"edit_{ricordo['id']}", height=150)
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    if st.button("Salva Modifica", key=f"btn_up_{ricordo['id']}"):
                        if aggiorna_ricordo(ricordo['id'], nuovo_testo): st.rerun()
                with col_b:
                    if st.button("Elimina", key=f"btn_del_book_{ricordo['id']}"):
                        if elimina_ricordo(ricordo['id'], ricordo.get('audio_url')): st.rerun()

    st.markdown("---")
    st.markdown("### Archivio Audio")
    if lista_ricordi:
        for ricordo in reversed(lista_ricordi):
            with st.expander(f"Audio: {ricordo['titolo']}"):
                st.audio(ricordo['audio_url'])

else:
    # --- PAGINA LETTURA (IL LIBRO VERO) ---
    st.markdown("<h1>Il Mio Libro Digitale</h1>", unsafe_allow_html=True)
    
    with st.expander("Chiedi all'Editor (Ricerca Vocale o Testuale)"):
        c_testo, c_audio = st.columns([3, 1])
        domanda_vocal = None
        
        with c_audio:
            audio_search = mic_recorder(start_prompt="Chiedi a voce", stop_prompt="Analizza...", key="search_mic")
            if audio_search:
                domanda_vocal = trascrivi_audio(audio_search['bytes'])
                st.write(f"Hai chiesto: *{domanda_vocal}*")
        
        with c_testo:
            domanda_txt = st.text_input("Oppure scrivi qui:", value=domanda_vocal if domanda_vocal else "")
        
        domanda_finale = domanda_txt if domanda_txt else domanda_vocal
        
        if domanda_finale and st.button("Interroga il Libro"):
            with st.spinner("L'IA sta cercando..."):
                risposta_ia = pulisci_testo(f"Trova nel libro: {domanda_finale}", contesto=testo_libro_fluido)
                st.info(risposta_ia)

    if testo_libro_fluido:
        limite_caratteri = 2500
        pagine = [testo_libro_fluido[i:i+limite_caratteri] for i in range(0, len(testo_libro_fluido), limite_caratteri)]
        
        if len(pagine) > 1:
            num_pag = st.select_slider("Sfoglia le pagine", options=range(1, len(pagine) + 1))
        else:
            num_pag = 1
        
        st.markdown(f"""
        <div style="
            background-color: #fdf5e6; 
            padding: 50px; 
            border-radius: 5px; 
            border: 1px solid #d2b48c; 
            font-family: 'Georgia', serif; 
            line-height: 2; 
            color: #3e2723;
            word-wrap: break-word;
            min-height: 600px;
            position: relative;
        ">
            <div style="white-space: pre-wrap;">{pagine[num_pag-1]}</div>
            <div style="
                position: absolute; 
                bottom: 20px; 
                right: 30px; 
                font-size: 0.9em; 
                color: #8b4513;
                font-style: italic;
            ">
                Pagina {num_pag}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Libro vuoto.")
