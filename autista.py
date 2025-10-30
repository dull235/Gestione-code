import streamlit as st
import sqlite3
import threading
import time
from streamlit_autorefresh import st_autorefresh
from database import inserisci_ticket, get_notifiche
import streamlit as st

# --- PWA: collegamento a manifest e service worker ---
st.markdown("""
<link rel="manifest" href="https://raw.githubusercontent.com/dull235/Gestione-code/main/manifest.json">
<meta name="theme-color" content="#2196f3">

<script>
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('static/service-worker.js')
    .then(function() { console.log("Service Worker registrato con successo."); })
    .catch(function(error) { console.log("Errore nella registrazione del Service Worker:", error); });
}
</script>
""", unsafe_allow_html=True)
# --- fine PWA ---

st.title("Gestione Code")


st.set_page_config(page_title="Autista - Carico/Scarico", layout="centered")
st.title("🚚 Benvenuto Autista")

DB_FILE = "tickets.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# --- Variabili di sessione ---
if "ticket_id" not in st.session_state:
    st.session_state.ticket_id = None
if "modalita" not in st.session_state:
    st.session_state.modalita = "iniziale"

# --- Aggiornamento automatico posizione ---
def auto_update_position(ticket_id):
    while True:
        lat, lon = 45.1234, 9.5678  # esempio, sostituire con GPS reale
        c.execute("UPDATE tickets SET Lat=?, Lon=? WHERE ID=?", (lat, lon, ticket_id))
        conn.commit()
        time.sleep(10)

# --- Schermata iniziale ---
if st.session_state.modalita == "iniziale":
    st.info("Clicca su **Avvia** per creare una nuova richiesta di carico/scarico.")
    if st.button("🚀 Avvia"):
        st.session_state.modalita = "form"
        st.rerun()

# --- Schermata form di compilazione ---
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
                inserisci_ticket(
                    nome=nome,
                    azienda=azienda,
                    targa=targa,
                    tipo=tipo,
                    destinazione=destinazione,
                    produttore=produttore,
                    rimorchio=int(rimorchio),
                    lat=45.1234,
                    lon=9.5678
                )
                # Recupera ID nuovo ticket
                c.execute("SELECT MAX(ID) FROM tickets")
                st.session_state.ticket_id = c.fetchone()[0]

                # Avvia thread posizione
                threading.Thread(
                    target=auto_update_position,
                    args=(st.session_state.ticket_id,),
                    daemon=True
                ).start()

                st.session_state.modalita = "notifiche"
                st.success("✅ Ticket inviato all'ufficio! Attendi chiamata o aggiornamenti.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Errore durante l'invio del ticket: {e}")

# --- Schermata notifiche ---
elif st.session_state.modalita == "notifiche":
    ticket_id = st.session_state.ticket_id
    st.success(f"📦 Ticket attivo ID: {ticket_id}")
    st.subheader("📢 Notifiche ricevute")

    # 🔄 Refresh automatico ogni 3 secondi
    st_autorefresh(interval=3000, key="auto_refresh_notifiche")

    notifiche = get_notifiche(ticket_id)

    if notifiche:
        ultima_notifica, ultima_data = notifiche[0]
        st.markdown(f"### 🚨 Ultimo aggiornamento: `{ultima_data}`")
        st.markdown(f"#### 💬 **{ultima_notifica}**")
        st.divider()
        st.write("🔁 Storico ultime notifiche:")
        for testo, data in notifiche[1:5]:
            st.info(f"🕓 {data} — {testo}")
    else:
        st.write("Nessuna notifica al momento.")

    col1, col2 = st.columns(2)
    if col1.button("🔄 Aggiorna ora"):
        st.rerun()

    if col2.button("❌ Chiudi ticket locale"):
        st.session_state.ticket_id = None
        st.session_state.modalita = "iniziale"
        st.rerun()







