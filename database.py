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
    from datetime import datetime

    aggiornamenti = {"Stato": stato}

    if stato == "Chiamato":
        aggiornamenti["Data_chiamata"] = datetime.utcnow().isoformat()
    elif stato in ["Annullato", "Non Presentato", "Terminato"]:
        aggiornamenti["Data_chiusura"] = datetime.utcnow().isoformat()
        aggiornamenti["Attivo"] = False

        # Calcola durata se disponibile
        ticket = _execute_query(
            supabase.table("tickets").select("Data_creazione, Data_chiamata").eq("ID", ticket_id)
        )
        if ticket and isinstance(ticket, list) and len(ticket) > 0:
            t = ticket[0]
            inizio = t.get("Data_chiamata") or t.get("Data_creazione")
            if inizio:
                try:
                    da = datetime.fromisoformat(inizio.replace("Z", ""))
                    durata = datetime.utcnow() - da
                    ore = int(durata.total_seconds() // 3600)
                    minuti = int((durata.total_seconds() % 3600) // 60)
                    aggiornamenti["Durata_servizio"] = f"{ore}h {minuti}m"
                except Exception:
                    aggiornamenti["Durata_servizio"] = str(durata)

    _execute_query(
        supabase.table("tickets").update(aggiornamenti).eq("ID", ticket_id)
    )

    # Inserisci notifica
    if notifica_testo:
        _execute_query(
            supabase.table("notifiche").insert({
                "Ticket_id": ticket_id,
                "Testo": notifica_testo,
                "Data": datetime.utcnow().isoformat()
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


