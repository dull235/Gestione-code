import streamlit as st
import threading
import time
from datetime import datetime
from database import inserisci_ticket, get_notifiche, aggiorna_posizione
from streamlit_autorefresh import st_autorefresh

# --- Configurazione pagina ---
st.set_page_config(
    page_title="Gestione Code - Autisti",
    page_icon="https://raw.githubusercontent.com/dull235/Gestione-code/main/static/icon.png",
    layout="wide"
)

# --- CSS personalizzato + sfondo ---
st.markdown("""
<style>
.stApp {
    background: url("https://raw.githubusercontent.com/dull235/Gestione-code/main/static/sfondo.jpg") 
    no-repeat center center fixed;
    background-size: cover;
}
.main > div {
    background-color: rgba(255, 255, 255, 0.85) !important;
    padding: 20px;
    border-radius: 10px;
    color: black !important;
}
.stButton button {
    background-color: #1976d2;
    color: white;
    border-radius: 8px;
    border: none;
}
.notifica {
    background-color: rgba(255, 255, 255, 0.9);
    padding: 10px 15px;
    border-left: 6px solid #1976d2;
    margin-bottom: 10px;
    border-radius: 6px;
}
</style>
""", unsafe_allow_html=True)

st.title("🚛 Pagina Autisti")
st.write("Compila i tuoi dati e ricevi aggiornamenti dall'ufficio in tempo reale.")

# --- Stato sessione ---
if "ticket_id" not in st.session_state:
    st.session_state.ticket_id = None
if "modalita" not in st.session_state:
    st.session_state.modalita = "iniziale"
if "posizione_attuale" not in st.session_state:
    st.session_state.posizione_attuale = (0, 0)

# --- Thread per aggiornamento posizione ---
def auto_update_position(ticket_id):
    while True:
        lat, lon = st.session_state.posizione_attuale
        if lat != 0 and lon != 0 and ticket_id is not None:
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

# --- Form inserimento ticket ---
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
                st.session_state.modalita = "notifiche"
                st.success("✅ Ticket inviato all'ufficio! Attendi notifiche.")

                # Avvia thread aggiornamento posizione
                threading.Thread(
                    target=auto_update_position,
                    args=(ticket_id,),
                    daemon=True
                ).start()

                st.rerun()
            except Exception as e:
                st.error(f"Errore invio ticket: {e}")

# --- Schermata notifiche e posizione ---
elif st.session_state.modalita == "notifiche":
    ticket_id = st.session_state.ticket_id
    st.success(f"📦 Ticket attivo ID: {ticket_id}")
    st.subheader("📢 Notifiche ricevute")
    st_autorefresh(interval=5000, key="auto_refresh_notifiche")
    st.markdown("<hr>", unsafe_allow_html=True)

    # --- Script JS per aggiornamento GPS lato browser ---
    gps_script = """
    <script>
    function updatePosition() {
        navigator.geolocation.getCurrentPosition(
            function(pos) {
                const lat = pos.coords.latitude;
                const lon = pos.coords.longitude;
                const inputLat = document.getElementById('lat_hidden');
                const inputLon = document.getElementById('lon_hidden');
                if(inputLat && inputLon){
                    inputLat.value = lat;
                    inputLon.value = lon;
                    inputLat.dispatchEvent(new Event('change'));
                    inputLon.dispatchEvent(new Event('change'));
                }
            },
            function(err) {
                console.warn("Errore GPS: " + err.message);
            }
        );
    }
    setInterval(updatePosition, 5000);
    updatePosition();
    </script>
    """
    st.markdown(gps_script, unsafe_allow_html=True)

    # --- Campi hidden per GPS ---
    lat_input = st.number_input("lat_hidden", value=st.session_state.posizione_attuale[0], key="lat_hidden", step=0.000001)
    lon_input = st.number_input("lon_hidden", value=st.session_state.posizione_attuale[1], key="lon_hidden", step=0.000001)

    # Aggiorna session_state quando cambiano
    st.session_state.posizione_attuale = (lat_input, lon_input)

    # --- Mostra notifiche ---
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
        st.rerun()
    if col2.button("❌ Chiudi ticket locale"):
        st.session_state.ticket_id = None
        st.session_state.modalita = "iniziale"
        st.rerun()
