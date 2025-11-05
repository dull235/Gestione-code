import streamlit as st
import pandas as pd
from database import get_ticket_attivi, get_notifiche, aggiorna_posizione
from datetime import datetime

def main():
    st.set_page_config(
        page_title="Autista Carico/Scarico",
        page_icon="https://raw.githubusercontent.com/dull235/Gestione-code/main/static/icon.png",
        layout="wide"
    )

    st.markdown("""
    <style>
    .stApp { background: url("https://raw.githubusercontent.com/dull235/Gestione-code/main/static/sfondo.jpg") no-repeat center center fixed; background-size: cover; }
    .main > div { background-color: rgba(255, 255, 255, 0.85) !important; padding: 20px; border-radius: 10px; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

    st.title("🚚 Ticket Autista")

    # --- Login Autista ---
    if "logged_in_autista" not in st.session_state:
        st.session_state.logged_in_autista = False

    if not st.session_state.logged_in_autista:
        st.subheader("🔑 Login Autista")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Accedi"):
            if username == "autista" and password == "1234":
                st.session_state.logged_in_autista = True
                st.success("Login effettuato!")
                st.rerun()
            else:
                st.error("Username o password errati")
        return

    # --- Ticket Attivi ---
    try:
        tickets = get_ticket_attivi()
    except Exception as e:
        st.error(f"Errore caricamento ticket: {e}")
        tickets = []

    if tickets:
        df = pd.DataFrame(tickets)
        st.subheader("🟢 Ticket Attivi")
        st.dataframe(df, use_container_width=True)

        selected_id = st.selectbox("Seleziona ticket:", df["ID"])

        # --- Notifiche del ticket selezionato ---
        st.subheader("🔔 Notifiche")
        try:
            notifiche = get_notifiche(selected_id)
        except Exception as e:
            st.error(f"Errore recupero notifiche: {e}")
            notifiche = []

        if notifiche:
            df_n = pd.DataFrame(notifiche)
            df_n = df_n.rename(columns={"Testo": "Messaggio"})
            st.table(df_n)
        else:
            st.info("Nessuna notifica per questo ticket.")

        # --- Aggiornamento posizione ---
        st.subheader("📍 Aggiorna Posizione")
        lat = st.number_input("Latitudine", value=0.0, format="%.6f")
        lon = st.number_input("Longitudine", value=0.0, format="%.6f")
        if st.button("Aggiorna Posizione"):
            try:
                aggiorna_posizione(selected_id, lat, lon)
                st.success("Posizione aggiornata!")
            except Exception as e:
                st.error(f"Errore aggiornamento posizione: {e}")

    else:
        st.info("Nessun ticket attivo al momento.")

if __name__ == "__main__":
    main()
