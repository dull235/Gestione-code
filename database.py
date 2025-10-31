import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime

# --- Carica variabili da .env ---
load_dotenv()

# --- Connessione al DB ---
def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

# --- Funzioni CRUD ---
def inserisci_ticket(nome, azienda, targa, tipo, destinazione="", produttore="", rimorchio=False, lat=None, lon=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tickets (Nome, Azienda, Targa, Tipo, Destinazione, Produttore, Rimorchio, Lat, Lon)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING ID
    """, (nome, azienda, targa, tipo, destinazione, produttore, int(rimorchio), lat, lon))
    ticket_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return ticket_id

def aggiorna_posizione(ticket_id, lat, lon):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tickets SET Lat=%s, Lon=%s WHERE ID=%s", (lat, lon, ticket_id))
    conn.commit()
    cur.close()
    conn.close()

def aggiorna_stato(ticket_id, stato, notifica_testo=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tickets SET Stato=%s WHERE ID=%s", (stato, ticket_id))
    if notifica_testo:
        cur.execute("INSERT INTO notifiche (Ticket_ID, Testo) VALUES (%s, %s)", (ticket_id, notifica_testo))
        cur.execute("UPDATE tickets SET Ultima_notifica=%s WHERE ID=%s", (notifica_testo, ticket_id))
    conn.commit()
    cur.close()
    conn.close()

def get_ticket_attivi():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM tickets WHERE Attivo=1 ORDER BY ID DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_ticket_storico():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM tickets WHERE Attivo=0 ORDER BY Data_chiusura DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_notifiche(ticket_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT Testo, Data FROM notifiche WHERE Ticket_ID=%s ORDER BY ID DESC", (ticket_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# --- Inizializzazione tabelle se non esistono ---
def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        ID SERIAL PRIMARY KEY,
        Nome TEXT,
        Azienda TEXT,
        Targa TEXT,
        Tipo TEXT,
        Destinazione TEXT,
        Produttore TEXT,
        Rimorchio INTEGER DEFAULT 0,
        Lat DOUBLE PRECISION,
        Lon DOUBLE PRECISION,
        Stato TEXT DEFAULT 'Nuovo',
        Attivo INTEGER DEFAULT 1,
        Data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        Data_chiamata TIMESTAMP,
        Data_chiusura TIMESTAMP,
        Durata_servizio TEXT,
        Ultima_notifica TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notifiche (
        ID SERIAL PRIMARY KEY,
        Ticket_ID INTEGER REFERENCES tickets(ID),
        Testo TEXT,
        Data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    cur.close()
    conn.close()

# Inizializza le tabelle
init_db()
