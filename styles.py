import streamlit as st

def apply_styles():
    st.markdown(
        """
        <style>
        /* Sfondo generale color sabbia/pergamena - NIENTE GRIGIO */
        .stApp {
            background-color: #f4ecd8;
            color: #4b3621; /* Marrone scuro per il testo */
        }

        /* Nascondiamo bordi grigi di sistema e widget */
        [data-testid="stHeader"], [data-testid="stToolbar"] {
            background-color: rgba(0,0,0,0);
        }
        
        /* Sidebar color seppia scuro */
        [data-testid="stSidebar"] {
            background-color: #d7ccc8;
            border-right: 1px solid #bcaaa4;
        }

        /* Stile per il titolo (vecchio diario) */
        h1 {
            font-family: 'Georgia', serif;
            color: #5d4037;
            text-align: center;
            border-bottom: 2px solid #d7ccc8;
            padding-bottom: 10px;
            font-variant: small-caps;
        }

        /* Il "Tastone" di registrazione (Bronzo/Marrone) */
        .stButton>button {
            background-color: #8d6e63;
            color: white !important;
            border-radius: 50px;
            border: 2px solid #5d4037;
            padding: 15px 30px;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        }

        .stButton>button:hover {
            background-color: #5d4037;
            transform: scale(1.02);
            box-shadow: 4px 4px 15px rgba(0,0,0,0.2);
        }

        /* Area di testo (Diary Feel) */
        .stTextArea textarea {
            background-color: #fdfaf0 !important;
            color: #4b3621 !important;
            font-family: 'Georgia', serif;
            border: 1px solid #d7ccc8 !important;
            border-radius: 10px;
        }

        /* L'effetto "Parole Offuscate" in background */
        .background-text {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 3rem;
            color: rgba(93, 64, 55, 0.08); /* Molto tenue */
            filter: blur(8px);
            z-index: -1;
            text-align: center;
            width: 80%;
            pointer-events: none;
            font-family: 'Georgia', serif;
            font-style: italic;
            animation: pulse 4s infinite ease-in-out;
        }

        @keyframes pulse {
            0% { opacity: 0.3; transform: translate(-50%, -52%); }
            50% { opacity: 0.7; transform: translate(-50%, -48%); }
            100% { opacity: 0.3; transform: translate(-50%, -52%); }
        }

        /* Rimuoviamo il grigio dai testi delle sezioni espanse */
        .stExpander {
            background-color: rgba(255, 255, 255, 0.2);
            border: 1px solid #d7ccc8 !important;
            border-radius: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )