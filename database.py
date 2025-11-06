import os
from supabase import create_client, Client
from datetime import datetime

# --- Connessione a Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Helper per esecuzione query ---
def _execute_query(query):
    try:
        response = query.execute()
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

def aggiorna_stato(ticket_id, stato, notifica_testo=""):
    now = datetime.utcnow().isoformat()

    update_data = {"Stato": stato}

    # Aggiorna le date automaticamente in base allo stato
    if stato == "Chiamato":
        update_data["Data_chiamata"] = now
    elif stato == "Terminato":
        update_data["Data_chiusura"] = now
        # Calcola durata se Data_chiamata esiste
        ticket = supabase.table("tickets").select("Data_chiamata").eq("ID", ticket_id).single().execute()
        data_chiamata = ticket.data.get("Data_chiamata") if ticket.data else None
        if data_chiamata:
            fmt = "%Y-%m-%dT%H:%M:%S.%f"
            durata = datetime.strptime(now, fmt) - datetime.strptime(data_chiamata, fmt)
            update_data["Durata_servizio"] = str(durata)

    _execute_query(supabase.table("tickets").update(update_data).eq("ID", ticket_id))

    # Inserisci notifica
    if notifica_testo:
        _execute_query(
            supabase.table("notifiche").insert({
                "Ticket_id": ticket_id,
                "Testo": notifica_testo,
                "Data": now
            })
        )
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
    # Attenzione alle maiuscole: Testo e Data devono essere così come in Supabase
    return _execute_query(
        supabase.table("notifiche").select("Testo, Data").eq("Ticket_id", ticket_id).order("ID", desc=True)
    )

