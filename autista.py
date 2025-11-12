import streamlit as st
import time
from database import inserisci_ticket, get_notifiche, aggiorna_posizione

# Compatibilità Streamlit vecchie versioni
if not hasattr(st, "rerun"):
    st.rerun = st.experimental_rerun

def main():
    st.set_page_config(
        page_title="Gestione Code - Autisti",
        page_icon="https://raw.githubusercontent.com/dull235/Gestione-code/main/static/icon.png",
        layout="wide"
    )

    # --- Stile CSS personalizzato ---
    st.markdown("""
    <style>
    .stApp {
        background: url("https://raw.githubusercontent.com/dull235/Gestione-code/main/static/sfondo.jpg")
        no-repeat center center fixed;
        background-size: container;
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
        st.session_state.posizione_attuale = (0.0, 0.0)
    if "last_refresh_time" not in st.session_state:
        st.session_state.last_refresh_time = 0

    # --- Ottieni lat/lon dalla query string (gps_sender.html) ---
    params = st.query_params
    if "lat" in params and "lon" in params:
        try:
            lat = float(params["lat"])
            lon = float(params["lon"])
            st.session_state.posizione_attuale = (lat, lon)
        except Exception:
            pass

    # --- Refresh automatico ogni 10 secondi ---
    refresh_interval = 10
    if time.time() - st.session_state.last_refresh_time > refresh_interval:
        st.session_state.last_refresh_time = time.time()
        st.rerun()

    # --- Se la posizione non è ancora disponibile ---
    if st.session_state.posizione_attuale == (0.0, 0.0):
        gps_url = "https://dull235.github.io/gps-sender/gps_sender.html"
        st.warning("📡 Posizione non rilevata.")
        st.markdown(f"[👉 Clicca qui per attivare il GPS]({gps_url})", unsafe_allow_html=True)

    else:
        lat, lon = st.session_state.posizione_attuale
        st.markdown(f"**📍 Posizione attuale:** Lat {lat:.6f}, Lon {lon:.6f}")
        # Aggiorna posizione nel DB se ticket attivo
        if st.session_state.ticket_id:
            try:
                aggiorna_posizione(st.session_state.ticket_id, lat, lon)
            except Exception as e:
                st.warning(f"Errore aggiornamento posizione: {e}")

    # --- Modalità iniziale ---
    if st.session_state.modalita == "iniziale":
        st.info("Clicca su **Avvia** per creare una nuova richiesta di carico/scarico.")
        if st.button("🚀 Avvia"):
            st.session_state.modalita = "form"
            st.rerun()

    # --- Form per invio ticket ---
    elif st.session_state.modalita == "form":
        st.subheader("📋 Compila i tuoi dati")

        # --- Campi salvati in sessione ---
        nome = st.text_input("Nome e Cognome", value=st.session_state.get("nome", ""), key="nome")
        azienda = st.text_input("Azienda", value=st.session_state.get("azienda", ""), key="azienda")
        targa = st.text_input("Targa Motrice", value=st.session_state.get("targa", ""), key="targa")

        # --- Rimorchio ---
        rimorchio = st.checkbox("Hai un rimorchio?", value=st.session_state.get("rimorchio", False), key="rimorchio")
        if rimorchio:
            targa_rim = st.text_input("Targa Rimorchio", value=st.session_state.get("targa_rim", ""), key="targa_rim")
        else:
            st.session_state["targa_rim"] = ""

        # --- Tipo Operazione ---
        tipo = st.radio("Tipo Operazione", ["Carico", "Scarico"], key="tipo")

        if tipo == "Carico":
            destinazione = st.text_input("Destinazione", value=st.session_state.get("destinazione", ""), key="destinazione")
            st.session_state["produttore"] = ""
        else:
            produttore = st.text_input("Produttore", value=st.session_state.get("produttore", ""), key="produttore")
            st.session_state["destinazione"] = ""

        # --- Pulsante invio ---
        if st.button("📨 Invia Richiesta"):
            if not st.session_state.nome or not st.session_state.azienda or not st.session_state.targa:
                st.error("⚠️ Compila tutti i campi obbligatori prima di inviare.")
            else:
                try:
                    ticket_id = inserisci_ticket(
                        nome=st.session_state.nome,
                        azienda=st.session_state.azienda,
                        targa=st.session_state.targa,
                        tipo=st.session_state.tipo,
                        destinazione=st.session_state.get("destinazione", ""),
                        produttore=st.session_state.get("produttore", ""),
                        rimorchio=int(st.session_state.rimorchio),
                        lat=st.session_state.posizione_attuale[0],
                        lon=st.session_state.posizione_attuale[1]
                    )
                    st.session_state.ticket_id = ticket_id
                    st.session_state.modalita = "notifiche"
                    st.success("✅ Ticket inviato all'ufficio! Attendi notifiche.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore invio ticket: {e}")

    # --- Modalità notifiche ---
    elif st.session_state.modalita == "notifiche":
        ticket_id = st.session_state.ticket_id
        st.success(f"📦 Ticket attivo ID: {ticket_id}")
        st.subheader("📢 Notifiche ricevute")

        st.markdown("<hr>", unsafe_allow_html=True)

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


if __name__ == "__main__":
    main()

