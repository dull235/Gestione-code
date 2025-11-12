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

    # --- Sfondo personalizzato ---
    st.markdown("""
    <style>
    .stApp { 
        background: url("https://raw.githubusercontent.com/dull235/Gestione-code/main/static/sfondo.png") 
        no-repeat center center fixed; 
        background-size: container; 
    }
    .main > div { 
        background-color: rgba(255, 255, 255, 0.85) !important; 
        padding: 20px; 
        border-radius: 10px; 
        color: black !important; 
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Aggiornamento automatico ogni 5s ---
    st_autorefresh(interval=5000, key="refresh")

    # --- Login semplice ---
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
                st.rerun()
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

        tickets = [t for t in tickets if t["Stato"] != "Terminato"]

        if tickets:
            df = pd.DataFrame(tickets)
            if "Data_chiamata" not in df.columns:
                df["Data_chiamata"] = ""
            st.dataframe(df, use_container_width=True)

            # --- Mostra elenco rimorchi sotto tabella, se presenti ---
            if "Rimorchio_targa" in df.columns and df["Rimorchio_targa"].notna().any():
                st.write("📄 **Targhe Rimorchi rilevate:**")
                for _, riga in df[df["Rimorchio_targa"].notna()].iterrows():
                    st.markdown(
                        f"- {riga['Nome']} → 🚛 Motrice: `{riga['Targa']}` | Rimorchio: `{riga['Rimorchio_targa']}`"
                    )

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

            # --- Mappa centrata sul primo ticket valido ---
            lat_init, lon_init = 45.5, 9.0
            for t in tickets:
                lat = t.get("Lat")
                lon = t.get("Lon")
                if lat is not None and lon is not None and not math.isnan(lat) and not math.isnan(lon):
                    lat_init, lon_init = lat, lon
                    break

            m = folium.Map(location=[lat_init, lon_init], zoom_start=8)

            # --- Marker aggiornati con colore in base allo stato ---
            for r in tickets:
                lat = r.get("Lat")
                lon = r.get("Lon")
                if lat is None or lon is None or math.isnan(lat) or math.isnan(lon):
                    continue

                popup_text = f"""
                <b>ID:</b> {r['ID']}<br>
                <b>Nome:</b> {r['Nome']}<br>
                <b>Targa Motrice:</b> {r.get('Targa','')}<br>
                """
                if r.get("Rimorchio_targa"):
                    popup_text += f"<b>Rimorchio:</b> {r['Rimorchio_targa']}<br>"
                popup_text += f"""
                <b>Tipo:</b> {r['Tipo']}<br>
                <b>Stato:</b> {r['Stato']}<br>
                <b>Ultima posizione aggiornata:</b> {r.get('Data_chiamata','N/D')}
                """

                color_icon = "blue"
                if r["Stato"] == "Chiamato":
                    color_icon = "green"
                elif r["Stato"] == "Sollecito":
                    color_icon = "orange"
                elif r["Stato"] in ["Annullato", "Non Presentato"]:
                    color_icon = "red"

                folium.Marker(
                    [lat, lon],
                    popup=popup_text,
                    tooltip=f"{r['Nome']} - {r['Tipo']}",
                    icon=folium.Icon(color=color_icon, icon="truck", prefix="fa")
                ).add_to(m)

            st.subheader("📍 Posizione Ticket Autisti")
            st_folium(m, width=1200, height=700)
        else:
            st.info("Nessun ticket attivo al momento.")


if __name__ == "__main__":
    main()

