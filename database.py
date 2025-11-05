import os
from supabase import create_client, Client
from datetime import datetime

# --- Connessione a Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    response = supabase.table("tickets").insert(data).execute()
    if response.error:
        raise Exception(f"Errore inserimento ticket: {response.error.message}")
    return response.data[0]["id"]

def aggiorna_posizione(ticket_id, lat, lon):
    response = supabase.table("tickets").update({"Lat": lat, "Lon": lon}).eq("id", ticket_id).execute()
    if response.error:
        raise Exception(f"Errore aggiornamento posizione: {response.error.message}")

def aggiorna_stato(ticket_id, stato, notifica_testo=""):
    updates = {"Stato": stato}
    response = supabase.table("tickets").update(updates).eq("id", ticket_id).execute()
    if response.error:
        raise Exception(f"Errore aggiornamento stato: {response.error.message}")
    
    if notifica_testo:
        supabase.table("notifiche").insert({
            "Ticket_ID": ticket_id,
            "Testo": notifica_testo,
            "Data": datetime.utcnow().isoformat()
        }).execute()
        supabase.table("tickets").update({"Ultima_notifica": notifica_testo}).eq("id", ticket_id).execute()

def get_ticket_attivi():
    response = supabase.table("tickets").select("*").eq("Attivo", True).order("id", desc=True).execute()
    if response.error:
        raise Exception(f"Errore caricamento ticket attivi: {response.error.message}")
    return response.data

def get_ticket_storico():
    response = supabase.table("tickets").select("*").eq("Attivo", False).order("Data_chiusura", desc=True).execute()
    if response.error:
        raise Exception(f"Errore caricamento storico ticket: {response.error.message}")
    return response.data

def get_notifiche(ticket_id):
    response = supabase.table("notifiche").select("Testo, Data").eq("Ticket_ID", ticket_id).order("ID", desc=True).execute()
    if response.error:
        raise Exception(f"Errore caricamento notifiche: {response.error.message}")
    return response.data
