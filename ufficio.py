import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
from database import get_ticket_attivi, get_ticket_storico, aggiorna_stato

st.set_page_config(page_title="Ufficio Carico/Scarico", layout="wide")

st.sidebar.title("📋 Menu")
view = st.sidebar.radio("Seleziona vista:", ["Ticket Aperti", "Storico Ticket"])

st.title("🏢 Gestione Ticket Ufficio")

notifiche_testi = {
    "Chiamata": "È il tuo turno. Sei pregato di recarti in pesa con il tuo automezzo.",
    "Sollecito": "Sollecito: È il tuo turno. Sei pregato di recarti in pesa con il tuo automezzo.",
    "Annulla": "Attività di Carico/Scarico Annullata. Per favore recati all'ufficio pesa per ulteriori informazioni.",
    "Non Presentato": "Attività di Carico/Scarico Annullata a causa della tua assenza.",
    "Termina Servizio": "Grazie mille per la sua visita."
}

# --- Aggiornamento automatico ogni 5 secondi ---
st_autorefresh(interval=5000, key="refresh_ufficio")

if view == "Ticket Aperti":
    tickets = get_ticket_attivi()
    if tickets:
        df = pd.DataFrame(tickets, columns=[
            "ID", "Nome", "Azienda", "Targa", "Rimorchio", "Tipo", "Destinazione",
            "Produttore", "Stato", "Attivo", "Data_creazione", "Data_chiamata",
            "Data_chiusura", "Durata_servizio", "Ultima_notifica", "Lat", "Lon"
        ])
        st.dataframe(df, use_container_width=True)

        selected_id = st.selectbox("Seleziona ticket:", df["ID"])
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("CHIAMATA"):
                aggiorna_stato(selected_id, "Chiamato", notifiche_testi["Chiamata"])
                st.success("Notifica CHIAMATA inviata.")
        with col2:
            if st.button("SOLLECITO"):
                aggiorna_stato(selected_id, "Sollecito", notifiche_testi["Sollecito"])
                st.success("Notifica SOLLECITO inviata.")
        with col3:
            if st.button("ANNULLA"):
                aggiorna_stato(selected_id, "Annullato", notifiche_testi["Annulla"])
                st.warning("Ticket annullato.")
        with col4:
            if st.button("NON PRESENTATO"):
                aggiorna_stato(selected_id, "Non Presentato", notifiche_testi["Non Presentato"])
                st.error("Segnalato come non presentato.")
        with col5:
            if st.button("TERMINA SERVIZIO"):
                aggiorna_stato(selected_id, "Terminato", notifiche_testi["Termina Servizio"])
                st.success("Ticket terminato.")

        # --- Mappa in tempo reale ---
        st.subheader("📍 Posizione Ticket Attivi")
        if df["Lat"].notna().any() and df["Lon"].notna().any():
            avg_lat = df["Lat"].mean()
            avg_lon = df["Lon"].mean()
        else:
            avg_lat, avg_lon = 45.0, 9.0  # default

        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=6)
        for _, r in df.iterrows():
            if pd.notna(r["Lat"]) and pd.notna(r["Lon"]):
                folium.Marker(
                    [r["Lat"], r["Lon"]],
                    popup=f"{r['Nome']} - {r['Tipo']}",
                    tooltip=f"{r['Stato']} - {r['Targa']}"
                ).add_to(m)
        st_folium(m, height=500, width='100%')
    else:
        st.info("Nessun ticket aperto al momento.")

else:
    st.subheader("📜 Storico Ticket")
    storico = get_ticket_storico()
    if storico:
        df_s = pd.DataFrame(storico, columns=[
            "ID", "Nome", "Azienda", "Targa", "Rimorchio", "Tipo", "Destinazione",
            "Produttore", "Stato", "Attivo", "Data_creazione", "Data_chiamata",
            "Data_chiusura", "Durata_servizio", "Ultima_notifica", "Lat", "Lon"
        ])
        st.dataframe(df_s, use_container_width=True)
        csv = df_s.to_csv(index=False).encode("utf-8")
        st.download_button("📤 Esporta Storico CSV", csv, "storico_tickets.csv", "text/csv")
    else:
        st.info("Nessun ticket chiuso presente nello storico.")
