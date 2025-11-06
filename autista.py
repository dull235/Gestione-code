import streamlit as st
import threading
import time
from streamlit_autorefresh import st_autorefresh
from database import inserisci_ticket, get_notifiche, aggiorna_posizione
import random

# --- Funzione per simulare posizione se GPS non disponibile ---
def get_simulated_location():
    # Coordinate casuali vicino a Milano per simulazione
    lat = 45.4642 + random.uniform(-0.01, 0.01)
    lon = 9.19 + random.uniform(-0.01, 0.01)
    return lat, lon

def main():
    st.set_page_config(
        page_title="Gestione Code - Autisti",
        page_icon="https://raw.githubusercontent.com/dull235/Gestione-code/main/static/icon.png",
        layout="wide"
    )

    st.markdown("""
    <style>
    .stApp { background: url("https://raw.githubusercontent.com/dull235/Gestione-code/main/static/sfondo.jpg") no-repeat center center fixed; background-size: contain; }
    .main > div { background-color: rgba(255, 255, 255, 0.8) !important; padding: 20px; border-radius: 10px; color: black !important; }
    .stTextInput input, .stSelectbox select, .stRadio input + label, .stCheckbox input + label { color: black !important; background-color: rgba(144, 238, 144, 0.9) !important; }
    .stButton button { background-color: #1976d2; color: white; border-radius: 8px; border: none; }
    .notifica { background-color: rgba(255, 255, 255, 0.9); padding: 10px 15px; border-left: 6px solid #1976d2; margin-bottom: 10px; border-radius: 6px; }
    </style>
    """, unsafe_allow_html=True)

    st.title("🚛 Pagina Autisti")
    st.write("Ricevi aggiornamenti in tempo reale dall'ufficio.")

    # --- Variabili di sessione ---
    if "ticket_id" not in st.session_state:
        st.session_state.ticket_id = None
    if "modalita" not in st.session_state:
        st.session_state.modalita = "iniziale"

    # --- Funzione per aggiornamento posizione ---
    def auto_update_position(ticket_id):
        try:
            from streamlit_js_eval import get_geolocation
        except ImportError:
            get_geolocation = None

        while True:
            if get_geolocation:
                loc = get_geolocation()
                if loc:
                    lat, lon = loc["latitude"], loc["longitude"]
                else:
                    lat, lon = get_simulated_location()
            else:
                lat, lon = get_simulated_location()

            try:
                aggiorna_posizione(ticket_id, lat, lon)
            except Exception as e:
                st.warning(f"Errore aggiornamento posizione: {e}")
            time.sleep(10)  # ogni 10 secondi

    # --- Schermata iniziale ---
    if st.session_state.modalita == "iniziale":
        st.info("Clicca su **Avvia** per creare una nuova richiesta di carico/scarico.")
        if st.button("🚀 Avvia"):
            st.session_state.modalita = "form"
            st.rerun()

    # --- Form di inserimento ---
    elif st.session_state.modalita == "form":
        st.subheader("📋 Compila i tuoi dati")
        nome = st.text_input("Nome e Cognome")
        azienda = st.text_input("Azienda")
        targa = st.text_input("Targa Motrice")
        rimorchio = st.checkbox("Hai un rimorchio?")
        targa_rim = st.text_input("Targa Rimorchio") if rimorchio else ""
        tipo = st.radio("Tipo Operazione", ["Carico", "Scarico"])
        destinazione = produttore = ""
        if tipo == "Carico":
            destinazione = st.text_input("Destinazione")
        else:
            produttore = st.text_input("Produttore")

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
                    threading.Thread(target=auto_update_position, args=(ticket_id,), daemon=True).start()

                    st.session_state.modalita = "notifiche"
                    st.success("✅ Ticket inviato all'ufficio! Attendi notifiche.")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore invio ticket: {e}")

    # --- Schermata notifiche ---
    elif st.session_state.modalita == "notifiche":
        ticket_id = st.session_state.ticket_id
        st.success(f"📦 Ticket attivo ID: {ticket_id}")
        st.subheader("📢 Notifiche ricevute")

        st_autorefresh(interval=5000, key="auto_refresh_notifiche")

        try:
            notifiche = get_notifiche(ticket_id)
        except Exception as e:
            st.error(f"Errore recupero notifiche: {e}")
            notifiche = []

        if notifiche:
            for n in notifiche[:5]:
                testo = n.get("Testo") if isinstance(n, dict) else n[0]
                data = n.get("Data") if isinstance(n, dict) else n[1]
                st.markdown(f"<div class='notifica'>🕓 <b>{data}</b><br>{testo}</div>", unsafe_allow_html=True)
        else:
            st.info("Nessuna notifica disponibile al momento.")

        col1, col2 = st.columns(2)
        if col1.button("🔄 Aggiorna ora"):
            st.rerun()

        if col2.button("❌ Chiudi ticket locale"):
            st.session_state.ticket_id = None
            st.session_state.modalita = "iniziale"
            st.rerun()


if __name__ == "__main__":
    main()
