if view == "Ticket Aperti":
    try:
        tickets = get_ticket_attivi()
    except Exception as e:
        st.error(f"Errore caricamento ticket: {e}")
        tickets = []

    # Filtra i ticket terminati così spariscono dalla pagina principale
    tickets = [t for t in tickets if t.get("Stato") != "Terminato"]

    if tickets:
        df = pd.DataFrame(tickets)

        # --- FORMATTARE LE DATE ---
        date_cols = ["Data_chiamata", "Data_apertura", "Data_chiusura"]
        for col in date_cols:
            if col in df.columns:
                def format_date(x):
                    if pd.isna(x) or x in ["", None]:
                        return "-"
                    try:
                        return pd.to_datetime(x, errors='coerce').strftime("%d/%m/%Y %H:%M")
                    except:
                        return str(x)
                df[col] = df[col].apply(format_date)
            else:
                df[col] = "-"

        st.dataframe(df, use_container_width=True)

        selected_id = st.selectbox("Seleziona ticket:", df["ID"])

        col1, col2, col3, col4, col5 = st.columns(5)
        if col1.button("CHIAMATA"):
            aggiorna_stato(selected_id, "Chiamato", notifiche_testi["Chiamata"])
        if col2.button("SOLLECITO"):
            aggiorna_stato(selected_id, "Sollecito", notifiche_testi["Sollecito"])
        if col3.button("ANNULLA"):
            aggiorna_stato(selected_id, "Annullato", notifiche_testi["Annulla"])
        if col4.button("NON PRESENTATO"):
            aggiorna_stato(selected_id, "Non Presentato", notifiche_testi["Non Presentato"])
        if col5.button("TERMINA SERVIZIO"):
            aggiorna_stato(selected_id, "Terminato", notifiche_testi["Termina Servizio"])

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
