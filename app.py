import streamlit as st
import autista
import ufficio

# --- Impostazioni pagina ---
st.set_page_config(
    page_title="Gestione Code",
    page_icon="https://raw.githubusercontent.com/dull235/Gestione-code/main/static/icon.png",
    layout="wide"
)

# --- Sidebar principale ---
st.sidebar.title("🚚 Gestione Code")
page = st.sidebar.radio("Seleziona vista:", ["Autista", "Ufficio"])

# --- Routing tra le due app ---
if page == "Autista":
    # Se autista.py ha una funzione main()
    if hasattr(autista, "main"):
        autista.main()
    else:
        st.write("⚙️ Caricamento pagina Autista...")
        autista  # fallback
elif page == "Ufficio":
    if hasattr(ufficio, "main"):
        ufficio.main()
    else:
        st.write("⚙️ Caricamento pagina Ufficio...")
        ufficio  # fallback
