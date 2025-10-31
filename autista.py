import streamlit as st
import threading
import time
from streamlit_autorefresh import st_autorefresh
from database import inserisci_ticket, get_notifiche, aggiorna_posizione

# --- Imposta pagina e CSS ---
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
</style>
""", unsafe_allow_html=True)

st.title("Pagina Autisti")
st.write("Gestisci i dati relativi agli autisti e alle code.")

# --- Variabili di sessione ---
if "ticket_id" not in st.session_state:
    st.session_state.ticket_id = None
if "modalita" not in st.session_state:
    st.session_state.modalita = "iniziale"

# --- Aggiornamento automatico posizione ---
def auto_update_position(ticket_id):
    """
    Aggiorna la posizione ogni 10 secondi con lat/lon reale dal browser
    """
    import streamlit_js_eval
    from streamlit_js_eval import get_geolocation

    while True:
        location = get_geolocation()
        if location:
            lat, lon = location['latitude'], location['longitude']
            # usa connessione locale dentro aggiorna_posizione
            aggiorna_posizione(ticket_id, lat, lon)
        time.sleep(10)

# --- Schermata iniziale ---
if st.session_state.modalita == "iniziale":
    st.info("Clicca su **Avvia** per creare una nuova richiesta di carico/scarico.")
    if st.button("🚀 Avvia"):
        st.session_state.modalita = "form"
        st.rerun()

# --- Form di compilazione ---
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
            # Inserimento ticket, ritorna ID
           st.session_state.ticket_id = inserisci_ticket(
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

            st.session_state.modalita = "notifiche"
            st.success("✅ Ticket inviato all'ufficio! Attendi chiamata o aggiornamenti.")
            time.sleep(1)
            st.rerun()

# --- Notifiche ticket ---
elif st.session_state.modalita == "notifiche":
    ticket_id = st.session_state.ticket_id
    st.success(f"📦 Ticket attivo ID: {ticket_id}")
    st.subheader("📢 Notifiche ricevute")

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


