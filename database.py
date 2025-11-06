import os
from supabase import create_client, Client
from datetime import datetime

# --- Connessione a Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Helper: controlla se esiste attributo .error oppure gestisci eccezione ---
def _execute_query(query):
    try:
        response = query.execute()
        # Compatibilità vecchia libreria
        if hasattr(response, "error") and response.error:
            raise Exception(response.error.message)
        return response.data
    except Exception as e:
        raise Exception(str(e))

# --- Funzioni CRUD per i ticket ---
def inserisci_ticket(nome, azienda, targa, tipo, destinazione="", produttore="", rimorchio=0, lat=None, lon=None):
    data = {
        "Nome": nome,
        "Azienda": azienda,
        "Targa": targa,
        "Tipo": tipo,
        "Destinazione": destinazione,
        "Produttore": produttore,
        "Rimorchio": rimorchio,
        "Lat": lat,
        "Lon": lon,
        "Stato": "Nuovo",
        "Attivo": True,
        "Data_creazione": datetime.utcnow().isoformat()
    }

    response = _execute_query(supabase.table("tickets").insert(data))
    if response and isinstance(response[0], dict):
        return response[0].get("ID") or response[0].get("id")
    return None

def aggiorna_posizione(ticket_id, lat, lon):
    _execute_query(
        supabase.table("tickets").update({"Lat": lat, "Lon": lon}).eq("ID", ticket_id)
    )

def aggiorna_stato(ticket_id, stato, notifica_testo="", data_chiamata=None):
    """
    Aggiorna lo stato di un ticket.
    Se lo stato è 'Terminato', calcola la durata del servizio e aggiorna Data_chiusura.
    Invia una notifica se specificata.
    """
    # Recupera il ticket per calcolare la durata
    ticket = _execute_query(
        supabase.table("tickets").select("*").eq("ID", ticket_id)
    )
    if not ticket or not isinstance(ticket, list):
        raise Exception(f"Ticket {ticket_id} non trovato")
    
    ticket = ticket[0]
    
    update_data = {"Stato": stato}
    
    if data_chiamata:
        update_data["Data_chiamata"] = data_chiamata
    
    if stato == "Terminato":
        data_creazione_str = ticket.get("Data_creazione")
        if data_creazione_str:
            # converte in datetime
            data_creazione = datetime.fromisoformat(data_creazione_str)
            data_chiusura = datetime.utcnow()
            durata_minuti = (data_chiusura - data_creazione).total_seconds() / 60
            update_data["Data_chiusura"] = data_chiusura.isoformat()
            update_data["Durata_servizio"] = round(durata_minuti, 2)  # salva come numero
    
    # Aggiorna il ticket
    _execute_query(
        supabase.table("tickets").update(update_data).eq("ID", ticket_id)
    )

    # Inserisci notifica se fornita
    if notifica_testo:
        _execute_query(
            supabase.table("notifiche").insert({
                "Ticket_id": ticket_id,
                "Testo": notifica_testo,
                "Data": datetime.utcnow().isoformat()
            })
        )
        # Aggiorna anche ultima notifica nel ticket
        _execute_query(
            supabase.table("tickets").update({"Ultima_notifica": notifica_testo}).eq("ID", ticket_id)
        )

def get_ticket_attivi():
    return _execute_query(
        supabase.table("tickets").select("*").eq("Attivo", True).order("ID", desc=True)
    )

def get_ticket_storico():
    return _execute_query(
        supabase.table("tickets").select("*").eq("Attivo", False).order("Data_chiusura", desc=True)
    )

def get_notifiche(ticket_id):
    return _execute_query(
        supabase.table("notifiche").select("Testo, Data").eq("Ticket_id", ticket_id).order("ID", desc=True)
    )

