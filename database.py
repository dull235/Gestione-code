import sqlite3
from datetime import datetime

DB_FILE = "tickets.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Tabella principale ticket
    c.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Nome TEXT,
            Azienda TEXT,
            Targa TEXT,
            Rimorchio INTEGER DEFAULT 0,
            Tipo TEXT,
            Destinazione TEXT,
            Produttore TEXT,
            Stato TEXT DEFAULT 'Nuovo',
            Attivo INTEGER DEFAULT 1,
            Data_creazione TEXT DEFAULT CURRENT_TIMESTAMP,
            Data_chiamata TEXT,
            Data_chiusura TEXT,
            Durata_servizio TEXT,
            Ultima_notifica TEXT,
            Lat REAL,
            Lon REAL
        )
    """)

    # Tabella notifiche (storico)
    c.execute("""
        CREATE TABLE IF NOT EXISTS notifiche (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Ticket_ID INTEGER,
            Testo TEXT,
            Data_invio TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# --- Inserisci nuovo ticket ---
def inserisci_ticket(nome, azienda, targa, tipo, destinazione="", produttore="", rimorchio=0, lat=None, lon=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO tickets (Nome, Azienda, Targa, Tipo, Destinazione, Produttore, Rimorchio, Lat, Lon)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nome, azienda, targa, tipo, destinazione, produttore, rimorchio, lat, lon))
    conn.commit()
    conn.close()

# --- Aggiorna stato e notifica ---
def aggiorna_stato(ticket_id, nuovo_stato, notifica_testo=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if nuovo_stato == "Chiamato":
        c.execute("UPDATE tickets SET Stato=?, Data_chiamata=?, Ultima_notifica=? WHERE ID=?",
                  (nuovo_stato, now, notifica_testo, ticket_id))
    elif nuovo_stato == "Terminato":
        # Calcola durata servizio
        c.execute("SELECT Data_chiamata FROM tickets WHERE ID=?", (ticket_id,))
        start = c.fetchone()[0]
        durata = None
        if start:
            durata = str(datetime.strptime(now, "%Y-%m-%d %H:%M:%S") -
                         datetime.strptime(start, "%Y-%m-%d %H:%M:%S"))
        c.execute("""UPDATE tickets
                     SET Stato=?, Data_chiusura=?, Durata_servizio=?, Attivo=0, Ultima_notifica=?
                     WHERE ID=?""",
                  (nuovo_stato, now, durata, notifica_testo, ticket_id))
    else:
        c.execute("UPDATE tickets SET Stato=?, Ultima_notifica=? WHERE ID=?",
                  (nuovo_stato, notifica_testo, ticket_id))

    # Inserisci notifica nello storico
    if notifica_testo:
        c.execute("INSERT INTO notifiche (Ticket_ID, Testo) VALUES (?, ?)", (ticket_id, notifica_testo))

    conn.commit()
    conn.close()

# --- Recupera ticket ---
def get_ticket_attivi():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM tickets WHERE Attivo=1")
    result = c.fetchall()
    conn.close()
    return result

def get_ticket_storico():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM tickets WHERE Attivo=0")
    result = c.fetchall()
    conn.close()
    return result

def get_notifiche(ticket_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT Testo, Data_invio FROM notifiche WHERE Ticket_ID=? ORDER BY ID DESC", (ticket_id,))
    result = c.fetchall()
    conn.close()
    return result

init_db()
