import streamlit as st
import threading
from database import inserisci_ticket, aggiorna_posizione, get_notifiche
from datetime import datetime
import random
import time

# --- Configurazione pagina ---
st.set_page_config(
    page_title="Autista",
    page_icon="https://raw.githubusercontent.com/dull235/Gestione-code/main/static/icon.png",
    layout="wide"
)

st.markdown("""
<style>
.stApp { 
    background: url("https://raw.githubusercontent.com/dull235/Gestione-code/main/static/sfondo.jpg") no-repeat center center fixed; 
    background-size: cover; 
}
.main > div { 
    background-color: rgba(255, 255, 255, 0.85) !important; 
    padding: 20px; border-radius: 10px; color: black !important; 
}
</style>
""", unsafe_allow_html=True)

# --- Session state iniziale ---
if "modalita" not in st.session_state:
    st.session_state.modalita = "iniziale"
if "ticket_id" not in st.session_state:
    st.session_state.ticket_id = None
if "reload_flag" not in st.session_state:
    st.session_state.reload_flag = False

# --- Funzione aggiornamento posizione ---
def auto_update_position(ticket_id):
    while st.session_state.modalita == "notifiche":
        lat = 45 + random.random()  # simulazione
        lon = 9 + random.random()   # simulazione
        try:
            aggiorna_posizione(ticket_id, lat, lon)
        except Exception as e:
            print(f"Errore aggiornamento posizione: {e}")
        time.sleep(5)  # ogni 5 secondi

# --- Modalità Iniziale / Invio ticket ---
if st.session_state.modalita == "iniziale":
    st.title("📄 Autista - Inserimento Ticket")

    nome = st.text_input("Nome")
    azienda = st.text_input("Azienda")
    targa = st.text_input("Targa")
    tipo = st.selectbox("Tipo", ["Carico", "Scarico"])
    destinazione = st.text_input("Destinazione")
    produttore = st.text_input("Produttore")
    rimorchio = st.text_input("Rimorchio (numero)", value="0")

    if st.button("📨 Invia Richiesta"):
        if not nome or not azienda or not targa:
            st.error("⚠️ Compila tutti i campi obbligatori prima di inviare.")
        else:
            try:
                ticket_id = inserisci_ticket(
                    nome=nome,
                    azienda=azienda,
                    targa=targa,
                    tipo=tipo,
                    destinazione=destinazione,
                    produttore=produttore,
                    rimorchio=int(rimorchio)
                )
                st.session_state.ticket_id = ticket_id

                # Avvia thread posizione
                threading.Thread(
                    target=auto_update_position,
                    args=(ticket_id,),
                    daemon=True
                ).start()

                # Passa alla modalità notifiche
                st.session_state.modalita = "notifiche"

                # Forza ricarica sicura della pagina
                st.session_state.reload_flag = not st.session_state.reload_flag
            except Exception as e:
                st.error(f"Errore invio ticket: {e}")

# --- Modalità Notifiche ---
elif st.session_state.modalita == "notifiche":
    ticket_id = st.session_state.ticket_id
    if not ticket_id:
        st.warning("Nessun ticket attivo. Torna alla schermata iniziale.")
        st.session_state.modalita = "iniziale"
        st.experimental_rerun = lambda: None  # placeholder compatibilità
    else:
        st.title("🔔 Notifiche Ticket")
        st.write(f"Ticket ID: {ticket_id}")

        try:
            notifiche = get_notifiche(ticket_id)
        except Exception as e:
            st.error(f"Errore recupero notifiche: {e}")
            notifiche = []

        if notifiche:
            for n in notifiche:
                st.info(f"{n['Data']}: {n['Testo']}")
        else:
            st.info("Nessuna notifica al momento.")

        if st.button("🔙 Torna Indietro"):
            st.session_state.modalita = "iniziale"
            st.session_state.ticket_id = None
            st.session_state.reload_flag = not st.session_state.reload_flag
