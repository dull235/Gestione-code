import streamlit as st
from autista import main as autista_app
from ufficio import main as ufficio_app

st.set_page_config(page_title="Gestione Code", layout="wide")

st.sidebar.title("🚚 Gestione Code")
page = st.sidebar.radio("Seleziona la sezione:", ["Autista", "Ufficio"])

if page == "Autista":
    autista_app()
elif page == "Ufficio":
    ufficio_app()
