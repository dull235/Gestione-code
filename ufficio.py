import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from database import get_ticket_attivi, get_ticket_storico, aggiorna_stato

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

    # --- Login ---
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
    else:
        st.sidebar.title("📋 Menu")
        view = st.sidebar.radio("Seleziona vista:", ["Ticket Aperti", "Storico Ticket"])

        st.title("🏢 Gestione Ticket Ufficio")

        notifiche_testi = {
            "Chiamata": "È il tuo turno. Sei pregato di recarti in pesa.",
            "Sollecito": "Sollecito: È il tuo turno. Recati in pesa.",
            "Annulla": "Attività annullata. Rivolgiti all’ufficio.",
            "Non Presentato": "Attività annullata per assenza.",
            "Termina Servizio": "Grazie per la visita."
        }

        # --- Ticket Aperti ---
        if view == "Ticket Aperti":
            try:
                tickets = get_ticket_attivi()
            except Exception as e:
                st.error(f"Errore caricamento ticket: {e}")
                tickets = []

            if tickets:
                df = pd.DataFrame(tickets, columns=[
                    "ID", "Nome", "Azienda", "Targa", "Rimorchio", "Tipo", "Destinazione",
                    "Produttore", "Stato", "Attivo", "Data_creazione", "Data_chiamata",
                    "Data_chiusura", "Durata_servizio", "Ultima_notifica", "Lat", "Lon"
                ])
                st.dataframe(df, use_container_width=True)

                selected_id = st.selectbox("Seleziona ticket:", df["ID"])

                col1, col2, col3, col4, col5 = st.columns(5)
                if col1.button("CHIAMATA"):
                    try:
                        aggiorna_stato(selected_id, "Chiamato", notifiche_testi["Chiamata"])
                        st.success("Notifica CHIAMATA inviata.")
                    except Exception as e:
                        st.error(f"Errore invio notifica: {e}")

                if col2.button("SOLLECITO"):
                    try:
                        aggiorna_stato(selected_id, "Sollecito", notifiche_testi["Sollecito"])
                        st.success("Notifica SOLLECITO inviata.")
                    except Exception as e:
                        st.error(f"Errore invio notifica: {e}")

                if col3.button("ANNULLA"):
                    try:
                        aggiorna_stato(selected_id, "Annullato", notifiche_testi["Annulla"])
                        st.warning("Ticket annullato.")
                    except Exception as e:
                        st.error(f"Errore invio notifica: {e}")

                if col4.button("NON PRESENTATO"):
                    try:
                        aggiorna_stato(selected_id, "Non Presentato", notifiche_testi["Non Presentato"])
                        st.error("Segnalato come non presentato.")
                    except Exception as e:
                        st.error(f"Errore invio notifica: {e}")

                if col5.button("TERMINA SERVIZIO"):
                    try:
                        aggiorna_stato(selected_id, "Terminato", notifiche_testi["Termina Servizio"])
                        st.success("Ticket terminato.")
                    except Exception as e:
                        st.error(f"Errore invio notifica: {e}")

                # --- Mappa ---
                st.subheader("📍 Posizione Ticket Attivi")
                avg_lat = df["Lat"].mean() if not df["Lat"].isna().all() else 45.0
                avg_lon = df["Lon"].mean() if not df["Lon"].isna().all() else 9.0
                m = folium.Map(location=[avg_lat, avg_lon], zoom_start=6)
                for _, r in df.iterrows():
                    if r["Lat"] and r["Lon"]:
                        folium.Marker(
                            [r["Lat"], r["Lon"]],
                            popup=f"{r['Nome']} - {r['Tipo']}",
                            tooltip=r["Stato"]
                        ).add_to(m)
                st_folium(m, height=500, width='100%')
            else:
                st.info("Nessun ticket aperto al momento.")

        # --- Storico Ticket ---
        else:
            st.subheader("📜 Storico Ticket")
            try:
                storico = get_ticket_storico()
            except Exception as e:
                st.error(f"Errore caricamento storico: {e}")
                storico = []

            if storico:
                df_s = pd.DataFrame(storico, columns=[
                    "ID", "Nome", "Azienda", "Targa", "Rimorchio", "Tipo", "Destinazione",
                    "Produttore", "Stato", "Attivo", "Data_creazione", "Data_chiamata",
                    "Data_chiusura", "Durata_servizio", "Ultima_notifica", "Lat", "Lon"
                ])
                st.dataframe(df_s, use_container_width=True)
            else:
                st.info("Nessun ticket chiuso nello storico.")

if __name__ == "__main__":
    main()
