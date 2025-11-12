elif st.session_state.modalita == "form":
    st.subheader("📋 Compila i tuoi dati")

    # --- Campi salvati in sessione ---
    nome = st.text_input("Nome e Cognome", value=st.session_state.get("nome", ""), key="nome")
    azienda = st.text_input("Azienda", value=st.session_state.get("azienda", ""), key="azienda")
    targa = st.text_input("Targa Motrice", value=st.session_state.get("targa", ""), key="targa")

    # --- Rimorchio ---
    rimorchio = st.checkbox("Hai un rimorchio?", value=st.session_state.get("rimorchio", False), key="rimorchio")
    if rimorchio:
        targa_rim = st.text_input("Targa Rimorchio", value=st.session_state.get("targa_rim", ""), key="targa_rim")
    else:
        st.session_state["targa_rim"] = ""

    # --- Tipo Operazione ---
    tipo = st.radio("Tipo Operazione", ["Carico", "Scarico"], key="tipo")

    if tipo == "Carico":
        destinazione = st.text_input("Destinazione", value=st.session_state.get("destinazione", ""), key="destinazione")
        st.session_state["produttore"] = ""
    else:
        produttore = st.text_input("Produttore", value=st.session_state.get("produttore", ""), key="produttore")
        st.session_state["destinazione"] = ""

    # --- Pulsante invio ---
    if st.button("📨 Invia Richiesta"):
        if not st.session_state.nome or not st.session_state.azienda or not st.session_state.targa:
            st.error("⚠️ Compila tutti i campi obbligatori prima di inviare.")
        else:
            try:
                ticket_id = inserisci_ticket(
                    nome=st.session_state.nome,
                    azienda=st.session_state.azienda,
                    targa=st.session_state.targa,
                    tipo=st.session_state.tipo,
                    destinazione=st.session_state.get("destinazione", ""),
                    produttore=st.session_state.get("produttore", ""),
                    rimorchio=int(st.session_state.rimorchio),
                    lat=st.session_state.posizione_attuale[0],
                    lon=st.session_state.posizione_attuale[1]
                )
                st.session_state.ticket_id = ticket_id
                st.session_state.modalita = "notifiche"
                st.success("✅ Ticket inviato all'ufficio! Attendi notifiche.")
                st.rerun()
            except Exception as e:
                st.error(f"Errore invio ticket: {e}")
