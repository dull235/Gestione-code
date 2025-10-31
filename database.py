import sqlite3
import os
from datetime import datetime

# Percorso del database nella cartella dell'app
DB_FILE = os.path.join(os.path.dirname(__file__), "tickets.db")

# --- Inizializzazione database ---
def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
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
        Data_creazione TEXT DEFAULT CURRENT_TIMESTAMP,
        Data_chiamata TEXT,
        Data_chiusura TEXT,
        Durata_servizio TEXT,
        Ultima_notifica TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS notifiche (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Ticket_ID INTEGER,
        Testo TEXT,
        Data TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(Ticket_ID) REFERENCES tickets(ID)
    )
    """)
    conn.commit()
    conn.close()

# Inizializza il DB se non esiste

    init_db()

# --- Funzioni CRUD ---
def inserisci_ticket(nome, azienda, targa, tipo, destinazione="", produttore="", rimorchio=0, lat=None, lon=None):
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        INSERT INTO tickets (Nome, Azienda, Targa, Tipo, Destinazione, Produttore, Rimorchio, Lat, Lon)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nome, azienda, targa, tipo, destinazione, produttore, rimorchio, lat, lon))
    conn.commit()
    ticket_id = c.lastrowid
    conn.close()
    return ticket_id

def aggiorna_posizione(ticket_id, lat, lon):
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("UPDATE tickets SET Lat=?, Lon=? WHERE ID=?", (lat, lon, ticket_id))
    conn.commit()
    conn.close()

def aggiorna_stato(ticket_id, stato, notifica_testo=""):
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("UPDATE tickets SET Stato=? WHERE ID=?", (stato, ticket_id))
    if notifica_testo:
        c.execute("INSERT INTO notifiche (Ticket_ID, Testo) VALUES (?, ?)", (ticket_id, notifica_testo))
        c.execute("UPDATE tickets SET Ultima_notifica=? WHERE ID=?", (notifica_testo, ticket_id))
    conn.commit()
    conn.close()

def get_ticket_attivi():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT * FROM tickets WHERE Attivo=1 ORDER BY ID DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_ticket_storico():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT * FROM tickets WHERE Attivo=0 ORDER BY Data_chiusura DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_notifiche(ticket_id):
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT Testo, Data FROM notifiche WHERE Ticket_ID=? ORDER BY ID DESC", (ticket_id,))
    rows = c.fetchall()
    conn.close()
    return rows

