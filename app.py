import streamlit as st
from autista import main as autista_app
from ufficio import main as ufficio_app

st.set_page_config(page_title="Gestione Code", layout="wide")

st.sidebar.title("🚚 Gestione Code")
pagina = st.sidebar.radio("Seleziona la modalità:", ["Autista", "Ufficio"])

if pagina == "Autista":
    autista_app()
else:
    ufficio_app()
