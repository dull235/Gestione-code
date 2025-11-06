import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from database import get_ticket_attivi, aggiorna_stato
import math
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

def main():
    st.set_page_config(
        page_title="Ufficio Carico/Scarico",
        page_icon="https://raw.githubusercontent.com/dull235/Gestione-code/main/static/icon.png",
        layout="wide"
    )

    st.markdown("""
    <style>
    .stApp { background: url("https://raw.githubusercontent.com/dull235/Gestione-code/main/static/sfondo.jpg") no-repeat center center fixed; background-size: cover; }
    .main > div { background-color: rgba(255, 255, 255, 0.85) !important; padding: 20px; border-radius: 10px; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

    # Autorefresh automatico ogni 5 secondi
    st_autorefresh(interval=5000, key="refresh")

    # Login semplice
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.subheader("🔑 Login Ufficio")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Accedi"):
            if username == "admin" and password == "1234":
                st.session_state.logged_in = True
                st.success("Login effettuato!")
                st.rerun()  # solo per login
            else:
                st.error("Username o password errati")
        return

    st.sidebar.title("📋 Menu")
    view = st.sidebar.radio("Seleziona vista:", ["Ticket Aperti"])

    st.title("🏢 Gestione Ticket Ufficio")

    notifiche_testi = {
        "Chiamata": "È il tuo turno. Sei pregato di recarti in pesa.",
        "Sollecito": "Sollecito: È il tuo turno. Recati in pesa.",
        "Annulla": "Attività annullata. Rivolgiti all’ufficio.",
        "Non Presentato": "Attività annullata per assenza.",
        "Termina Servizio": "Grazie per la visita."
    }

    if view == "Ticket Aperti":
        try:
            tickets = get_ticket_attivi()
        except Exception as e:
            st.error(f"Errore caricamento ticket: {e}")
            tickets = []

        # Filtra solo i ticket non terminati
        tickets = [t for t in tickets if t["Stato"] != "Terminato"]

        if tickets:
            df = pd.DataFrame(tickets)

            # Popola Data_chiamata se non presente
            if "Data_chiamata" not in df.columns:
                df["Data_chiamata"] = ""

            st.dataframe(df, use_container_width=True)

            selected_id = st.selectbox("Seleziona ticket:", df["ID"])

            col1, col2, col3, col4, col5 = st.columns(5)
            if col1.button("CHIAMATA"):
                ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                aggiorna_stato(selected_id, "Chiamato", notifiche_testi["Chiamata"], data_chiamata=ora)
                st.rerun()
            if col2.button("SOLLECITO"):
                aggiorna_stato(selected_id, "Sollecito", notifiche_testi["Sollecito"])
                st.rerun()
            if col3.button("ANNULLA"):
                aggiorna_stato(selected_id, "Annullato", notifiche_testi["Annulla"])
                st.rerun()
            if col4.button("NON PRESENTATO"):
                aggiorna_stato(selected_id, "Non Presentato", notifiche_testi["Non Presentato"])
                st.rerun()
            if col5.button("TERMINA SERVIZIO"):
                aggiorna_stato(selected_id, "Terminato", notifiche_testi["Termina Servizio"])
                st.rerun()

            # Mappa Folium
            st.subheader("📍 Posizione Ticket")
            m = folium.Map(location=[45.5, 9.0], zoom_start=8)
            for r in tickets:
                lat = r.get("Lat")
                lon = r.get("Lon")
                if lat is None or lon is None or math.isnan(lat) or math.isnan(lon):
                    continue
                folium.Marker(
                    [lat, lon],
                    popup=f"{r['Nome']} - {r['Tipo']}",
                    tooltip=r["Stato"]
                ).add_to(m)
            st_data = st_folium(m, width=700, height=500)
        else:
            st.info("Nessun ticket attivo al momento.")

if __name__ == "__main__":
    main()


