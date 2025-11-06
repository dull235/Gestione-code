import streamlit as st
from database import get_ticket_attivi, get_notifiche, aggiorna_posizione
import time

def main():
    st.set_page_config(
        page_title="Autista",
        page_icon="https://raw.githubusercontent.com/dull235/Gestione-code/main/static/icon.png",
        layout="wide"
    )

    st.markdown("""
    <style>
    .stApp { background: url("https://raw.githubusercontent.com/dull235/Gestione-code/main/static/sfondo.jpg") no-repeat center center fixed; background-size: cover; }
    .main > div { background-color: rgba(255, 255, 255, 0.85) !important; padding: 20px; border-radius: 10px; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

    st.title("🚚 Dashboard Autista")

    try:
        tickets = get_ticket_attivi()
    except Exception as e:
        st.error(f"Errore caricamento ticket: {e}")
        tickets = []

    if tickets:
        ticket_ids = [t["ID"] for t in tickets]
        selected_id = st.selectbox("Seleziona ticket:", ticket_ids)

        # Mostra notifiche
        st.subheader("🔔 Notifiche")
        try:
            notifiche = get_notifiche(selected_id)
        except Exception as e:
            st.error(f"Errore caricamento notifiche: {e}")
            notifiche = []

        if notifiche:
            for n in notifiche:
                st.markdown(f"🕓 {n['Data']} — {n['Testo']}")
        else:
            st.info("Nessuna notifica per questo ticket.")

        # --- Aggiornamento automatico posizione ---
        st.subheader("📍 Posizione automatica")
        st.info("La posizione viene aggiornata automaticamente ogni 10 secondi.")
        
        # Usare JavaScript per geolocalizzazione
        location_js = """
        <script>
        function getLocation(){
            if(navigator.geolocation){
                navigator.geolocation.getCurrentPosition(function(position){
                    document.getElementById('lat').value = position.coords.latitude;
                    document.getElementById('lon').value = position.coords.longitude;
                });
            }
        }
        setInterval(getLocation, 10000);
        </script>
        <input type="hidden" id="lat">
        <input type="hidden" id="lon">
        """
        st.components.v1.html(location_js)

        # Aggiornamento continuo
        if 'lat' not in st.session_state:
            st.session_state.lat = 0.0
            st.session_state.lon = 0.0

        # Legge valori da JS ogni 10 secondi e aggiorna DB
        while True:
            try:
                lat = float(st.session_state.get('lat', 0))
                lon = float(st.session_state.get('lon', 0))
                if lat != 0 and lon != 0:
                    aggiorna_posizione(selected_id, lat, lon)
            except Exception as e:
                st.error(f"Errore aggiornamento posizione: {e}")
            time.sleep(10)
    else:
        st.info("Nessun ticket attivo al momento.")

if __name__ == "__main__":
    main()
