import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

# --- Carica variabili dal file .env ---
load_dotenv()

DB_HOST = os.getenv("SUPABASE_DB_URL")
DB_USER = os.getenv("SUPABASE_DB_USER")
DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")
DB_NAME = os.getenv("SUPABASE_DB_NAME")
DB_PORT = os.getenv("SUPABASE_DB_PORT", 5432)

# --- Connessione ---
def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME,
        port=DB_PORT
    )

# --- Inizializzazione database ---
def init_db():
    conn = get_conn()
    c = conn.cursor()
    # Tabella tickets
    c.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ID SERIAL PRIMARY KEY,
            Nome TEXT,
            Azienda TEXT,
            Targa TEXT,
            Tipo TEXT,
            Destinazione TEXT,
            Produttore TEXT,
            Rimorchio INTEGER DEFAULT 0,
            Lat REAL,
            Lon REAL,
            Stato TEXT DEFAULT 'Nuovo',
            Attivo INTEGER DEFAULT 1,
            Data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            Data_chiamata TIMESTAMP,
            Data_chiusura TIMESTAMP,
            Durata_servizio TEXT,
            Ultima_notifica TEXT
        )
    """)
    # Tabella notifiche
    c.execute("""
        CREATE TABLE IF NOT EXISTS notifiche (
            ID SERIAL PRIMARY KEY,
            Ticket_ID INTEGER REFERENCES tickets(ID),
            Testo TEXT,
            Data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Inizializza DB se non esiste
init_db()

# --- Funzioni CRUD ---
def inserisci_ticket(nome, azienda, targa, tipo, destinazione="", produttore="", rimorchio=0, lat=None, lon=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO tickets (Nome, Azienda, Targa, Tipo, Destinazione, Produttore, Rimorchio, Lat, Lon)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING ID
    """, (nome, azienda, targa, tipo, destinazione, produttore, rimorchio, lat, lon))
    ticket_id = c.fetchone()[0]
    conn.commit()
    conn.close()
    return ticket_id

def aggiorna_posizione(ticket_id, lat, lon):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE tickets SET Lat=%s, Lon=%s WHERE ID=%s", (lat, lon, ticket_id))
    conn.commit()
    conn.close()

def aggiorna_stato(ticket_id, stato, notifica_testo=""):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE tickets SET Stato=%s WHERE ID=%s", (stato, ticket_id))
    if notifica_testo:
        c.execute("INSERT INTO notifiche (Ticket_ID, Testo) VALUES (%s, %s)", (ticket_id, notifica_testo))
        c.execute("UPDATE tickets SET Ultima_notifica=%s WHERE ID=%s", (notifica_testo, ticket_id))
    conn.commit()
    conn.close()

def get_ticket_attivi():
    conn = get_conn()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT * FROM tickets WHERE Attivo=1 ORDER BY ID DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_ticket_storico():
    conn = get_conn()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT * FROM tickets WHERE Attivo=0 ORDER BY Data_chiusura DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_notifiche(ticket_id):
    conn = get_conn()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT Testo, Data FROM notifiche WHERE Ticket_ID=%s ORDER BY ID DESC", (ticket_id,))
    rows = c.fetchall()
    conn.close()
    return rows
