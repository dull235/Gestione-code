import streamlit as st
import threading
import time
from database import inserisci_ticket, get_notifiche, aggiorna_posizione

# --- Impostazioni pagina e stile ---
st.set_page_config(
    page_title="Autista",
    page_icon="https://raw.githubusercontent.com/dull235/Gestione-code/main/static/icon.png",
    layout="centered"
)

st.markdown("""
<style>
.stApp { 
    background: url("https://raw.githubusercontent.com/dull235/Gestione-code/main/static/sfondo.jpg") no-repeat center center fixed; 
    background-size: cover; 
}
.main > div { 
    background-color: rgba(255, 255, 255, 0.85) !important; 
    padding: 20px; 
    border-radius: 10px; 
    color: black !important; 
}
.notifica { 
    padding: 10px; 
    margin-bottom: 5px; 
    border-left: 4px solid #1f77b4; 
    background-color: #f0f8ff; 
}
</style>
""", unsafe_allow_html=True)

# --- Stato sessione ---
if "modalita" not in st.session_state:
    st.session_state.modalita = "iniziale"
if "ticket_id" not in st.session_state:
    st.session_state.ticket_id = None

# --- Aggiornamento posizione simulata ---
def auto_update_position(ticket_id):
    import random
    while st.session_state.modalita == "notifiche" and st.session_state.ticket_id == ticket_id:
        lat = 45.0 + random.uniform(-0.05, 0.05)
        lon = 9.0 + random.uniform(-0.05, 0.05)
        try:
            aggiorna_posizione(ticket_id, lat, lon)
        except Exception as e:
            print(f"Errore aggiornamento posizione: {e}")
        time.sleep(5)  # aggiorna ogni 5 secondi

# --- Autorefresh per notifiche ---
def st_autorefresh(interval=5000, key=None):
    st.experimental_rerun_timer(interval, key=key)

# --- Schermata iniziale ---
if st.session_state.modalita == "iniziale":
    st.info("Clicca su **Avvia** per creare una nuova richiesta di carico/scarico.")
    if st.button("🚀 Avvia"):
        st.session_state.modalita = "form"
        st.experimental_rerun()

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
                if ticket_id is None:
                    st.error("Errore: impossibile creare il ticket. Controlla il database.")
                else:
                    st.session_state.ticket_id = ticket_id
                    threading.Thread(target=auto_update_position, args=(ticket_id,), daemon=True).start()
                    st.session_state.modalita = "notifiche"
                    st.success("✅ Ticket inviato all'ufficio! Attendi chiamata o aggiornamenti.")
                    st.experimental_rerun()
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
        ultima = notifiche[0]
        testo = ultima.get("Testo") if isinstance(ultima, dict) else ultima[0]
        data = ultima.get("Data") if isinstance(ultima, dict) else ultima[1]
        st.markdown(f"### 🕓 Ultimo aggiornamento: `{data}`")
        st.markdown(f"#### 💬 **{testo}**")
        st.divider()
        st.write("🔁 Storico ultime notifiche:")
        for n in notifiche[1:5]:
            testo_n = n.get("Testo") if isinstance(n, dict) else n[0]
            data_n = n.get("Data") if isinstance(n, dict) else n[1]
            st.markdown(f"<div class='notifica'>🕓 <b>{data_n}</b><br>{testo_n}</div>", unsafe_allow_html=True)
    else:
        st.info("Nessuna notifica disponibile al momento.")

    col1, col2 = st.columns(2)
    if col1.button("🔄 Aggiorna ora"):
        st.experimental_rerun()
    if col2.button("❌ Chiudi ticket locale"):
        st.session_state.ticket_id = None
        st.session_state.modalita = "iniziale"
        st.experimental_rerun()
