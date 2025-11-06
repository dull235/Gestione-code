import streamlit as st
import threading
import time
from streamlit_autorefresh import st_autorefresh
from database import inserisci_ticket, get_notifiche, aggiorna_posizione

def main():
    # --- Imposta pagina e CSS ---
    st.set_page_config(
        page_title="Gestione Code - Autisti",
        page_icon="https://raw.githubusercontent.com/dull235/Gestione-code/main/static/icon.png",
        layout="wide"
    )

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

    if "ticket_id" not in st.session_state:
        st.session_state.ticket_id = None
    if "modalita" not in st.session_state:
        st.session_state.modalita = "iniziale"

    # --- Aggiornamento posizione automatico tramite thread ---
    def auto_update_position(ticket_id):
        while True:
            posizione = st.session_state.get("posizione_attuale")
            if posizione:
                lat, lon = posizione
                try:
                    aggiorna_posizione(ticket_id, lat, lon)
                except Exception as e:
                    st.warning(f"Errore aggiornamento posizione: {e}")
            time.sleep(10)

    # --- Schermata iniziale ---
    if st.session_state.modalita == "iniziale":
        st.info("Clicca su **Avvia** per creare una nuova richiesta di carico/scarico.")
        if st.button("🚀 Avvia"):
            st.session_state.modalita = "form"
            st.rerun()

    # --- Form di inserimento ticket ---
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

                    st.session_state.posizione_attuale = None
                    st.write("🔹 Attendi il prompt per la geolocalizzazione del browser e consenti l'accesso.")

                    threading.Thread(
                        target=auto_update_position,
                        args=(ticket_id,),
                        daemon=True
                    ).start()

                    st.rerun()
                except Exception as e:
                    st.error(f"Errore invio ticket: {e}")

    # --- Schermata notifiche ---
    elif st.session_state.modalita == "notifiche":
        ticket_id = st.session_state.ticket_id
        st.success(f"📦 Ticket attivo ID: {ticket_id}")
        st.subheader("📢 Notifiche ricevute")
        st_autorefresh(interval=5000, key="auto_refresh_notifiche")

        # ==========================
        # 🔹 BLOCCO GPS DIAGNOSTICO
        # ==========================
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### 📍 Posizione GPS (Browser)")
        st.info("📡 Tentativo di lettura posizione GPS dal browser...")

        gps_script = """
        <script>
        function inviaPosizione(){
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (pos) => {
                        const lat = pos.coords.latitude;
                        const lon = pos.coords.longitude;
                        console.log("✅ Posizione letta dal browser:", lat, lon);
                        const streamlitInput = window.parent.document.querySelector('input[data-testid="stTextInput"][aria-label="gps_input"]');
                        if(streamlitInput){
                            streamlitInput.value = lat + "," + lon;
                            streamlitInput.dispatchEvent(new Event("input", { bubbles: true }));
                        } else {
                            console.warn("⚠️ Campo gps_input non trovato da JS");
                        }
                    },
                    (err) => { 
                        console.error("❌ Errore GPS:", err.message);
                        alert("Errore GPS: " + err.message);
                    }
                );
            } else {
                alert("❌ Geolocalizzazione non supportata su questo dispositivo");
            }
        }
        inviaPosizione();
        </script>
        """
        st.markdown(gps_script, unsafe_allow_html=True)

        # campo nascosto per ricevere coordinate
        gps_input = st.text_input("gps_input", value="", label_visibility="collapsed")

        if gps_input:
            try:
                lat, lon = map(float, gps_input.split(","))
                st.session_state.posizione_attuale = (lat, lon)
                aggiorna_posizione(ticket_id, lat, lon)
                st.success(f"📍 Posizione aggiornata: {lat:.5f}, {lon:.5f}")
            except Exception as e:
                st.warning(f"Errore aggiornamento posizione: {e}")
        else:
            st.info("⏳ In attesa del consenso GPS dal browser...")

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


if __name__ == "__main__":
    main()
