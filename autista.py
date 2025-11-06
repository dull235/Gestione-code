import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
from database import get_ticket_attivi, get_ticket_storico, aggiorna_posizione, get_notifiche
import random

def main():
    st.set_page_config(
        page_title="Autista",
        page_icon="https://raw.githubusercontent.com/dull235/Gestione-code/main/static/icon.png",
        layout="wide"
    )

    # --- Stile ---
    st.markdown("""
    <style>
    .stApp { background: url("https://raw.githubusercontent.com/dull235/Gestione-code/main/static/sfondo.jpg") no-repeat center center fixed; background-size: cover; }
    .main > div { background-color: rgba(255, 255, 255, 0.85) !important; padding: 20px; border-radius: 10px; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

    st.title("🚚 Dashboard Autista")

    # --- Ticket attivi ---
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

        selected_id = st.selectbox("Seleziona ticket:", df["ID"])

        # --- Notifiche ---
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

        # --- Aggiorna posizione automaticamente ---
        st.subheader("📍 Posizione (aggiornata automaticamente)")
        # Se non ci sono coordinate, simuliamo una posizione vicina
        lat = df.loc[df["ID"] == selected_id, "Lat"].values[0]
        lon = df.loc[df["ID"] == selected_id, "Lon"].values[0]
        if lat is None: lat = 45.0 + random.random()/100
        if lon is None: lon = 9.0 + random.random()/100

        try:
            aggiorna_posizione(selected_id, lat, lon)
        except Exception as e:
            st.error(f"Errore aggiornamento posizione automatica: {e}")

        # --- Mappa ---
        st.subheader("📍 Posizione Ticket")
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
        st.info("Nessun ticket attivo al momento.")

    # --- Storico ticket ---
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
        # Formattazione Durata_servizio
        if "Durata_servizio" in df_s.columns:
            def format_duration(x):
                if pd.isnull(x):
                    return ""
                try:
                    total_minutes = float(x)
                    return f"{int(total_minutes//60)}h {int(total_minutes%60)}m"
                except:
                    return str(x)
            df_s["Durata_servizio"] = df_s["Durata_servizio"].apply(format_duration)
        st.dataframe(df_s[["ID", "Data_creazione", "Data_chiamata", "Data_chiusura", "Durata_servizio", "Ultima_notifica"]], use_container_width=True)
    else:
        st.info("Nessun ticket chiuso nello storico.")

if __name__ == "__main__":
    main()
