import streamlit as st
import threading
import time
from streamlit_autorefresh import st_autorefresh
from database import inserisci_ticket, get_notifiche, aggiorna_posizione

def main():
    st.set_page_config(
        page_title="Gestione Code - Autisti",
        page_icon="https://raw.githubusercontent.com/dull235/Gestione-code/main/static/icon.png",
        layout="wide"
    )

    st.title("🚛 Pagina Autisti")

    if "ticket_id" not in st.session_state:
        st.session_state.ticket_id = None
    if "modalita" not in st.session_state:
        st.session_state.modalita = "iniziale"
    if "posizione_attuale" not in st.session_state:
        st.session_state.posizione_attuale = None

    def auto_update_position(ticket_id):
        while True:
            pos = st.session_state.get("posizione_attuale")
            if pos:
                lat, lon = pos
                try:
                    aggiorna_posizione(ticket_id, lat, lon)
                except Exception as e:
                    st.warning(f"Errore aggiornamento posizione: {e}")
            time.sleep(10)

    if st.session_state.modalita == "iniziale":
        st.info("Clicca su **Avvia** per creare una nuova richiesta di carico/scarico.")
        if st.button("🚀 Avvia"):
            st.session_state.modalita = "form"
            st.rerun()

    elif st.session_state.modalita == "form":
        nome = st.text_input("Nome e Cognome")
        azienda = st.text_input("Azienda")
        targa = st.text_input("Targa Motrice")
        tipo = st.radio("Tipo Operazione", ["Carico", "Scarico"])
        destinazione = st.text_input("Destinazione") if tipo=="Carico" else ""
        produttore = st.text_input("Produttore") if tipo=="Scarico" else ""

        if st.button("📨 Invia Richiesta"):
            if not nome or not azienda or not targa:
                st.error("⚠️ Compila tutti i campi obbligatori")
            else:
                ticket_id = inserisci_ticket(
                    nome=nome,
                    azienda=azienda,
                    targa=targa,
                    tipo=tipo,
                    destinazione=destinazione,
                    produttore=produttore,
                    rimorchio=0
                )
                st.session_state.ticket_id = ticket_id
                st.session_state.modalita = "notifiche"

                threading.Thread(
                    target=auto_update_position,
                    args=(ticket_id,),
                    daemon=True
                ).start()
                st.success("✅ Ticket inviato! Attendi notifiche.")
                st.rerun()

    elif st.session_state.modalita == "notifiche":
        ticket_id = st.session_state.ticket_id
        st.success(f"📦 Ticket attivo ID: {ticket_id}")
        st_autorefresh(interval=5000, key="auto_refresh_notifiche")

        # --- Script GPS lato browser ---
        gps_script = """
        <script>
        function sendLocation(pos) {
            const lat = pos.coords.latitude;
            const lon = pos.coords.longitude;
            const payload = {lat: lat, lon: lon};
            fetch("/update_position", {
                method: "POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify(payload)
            });
        }
        navigator.geolocation.watchPosition(sendLocation, console.error, {enableHighAccuracy:true});
        </script>
        """
        st.components.v1.html(gps_script, height=0)

        # --- Notifiche ---
        try:
            notifiche = get_notifiche(ticket_id)
        except Exception:
            notifiche = []

        if notifiche:
            ultima = notifiche[0]
            testo = ultima.get("Testo")
            data = ultima.get("Data")
            st.markdown(f"### 🕓 Ultimo aggiornamento: `{data}`")
            st.markdown(f"#### 💬 **{testo}**")
        else:
            st.info("Nessuna notifica disponibile.")

        if st.button("❌ Chiudi ticket locale"):
            st.session_state.ticket_id = None
            st.session_state.modalita = "iniziale"
            st.rerun()

if __name__ == "__main__":
    main()
