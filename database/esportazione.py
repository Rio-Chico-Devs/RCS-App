#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Esportazione dei dati in file leggibili con Excel.
Uso riservato esclusivamente a RCS

A cosa serve
------------
I backup sono copie del database: si aprono solo con questo programma. Se un
giorno il programma non partisse piu' (computer nuovo, Windows aggiornato,
file danneggiati), i dati sarebbero comunque li' ma non consultabili subito.

Qui gli stessi dati vengono scritti in file CSV, che si aprono con Excel, con
qualunque foglio di calcolo, e volendo anche con il Blocco note. E' la rete di
sicurezza che non dipende ne' da SQLite ne' da questo programma.

Nessuna libreria aggiuntiva: solo la libreria standard di Python, cosi'
l'eseguibile resta quello che e'.
"""

import csv
import logging
import os
import sqlite3
from datetime import datetime

from database import backup_manager

# Il carattere iniziale (BOM) serve a Excel per riconoscere gli accenti.
CODIFICA = "utf-8-sig"
SEPARATORE = ";"          # Excel in italiano si aspetta il punto e virgola

TABELLE = [
    ("preventivi", "Preventivi"),
    ("clienti", "Clienti"),
    ("materiali", "Materiali"),
    ("fornitori", "Fornitori"),
    ("materiale_fornitori", "Materiali per fornitore"),
    ("movimenti_magazzino", "Movimenti di magazzino"),
    ("categorie_materiale", "Categorie materiale"),
]

GIORNI_TRA_ESPORTAZIONI = 30


def _log():
    return logging.getLogger('rcs')


def cartella_esportazioni(db_path):
    """Le esportazioni stanno accanto ai backup, cosi' si trovano insieme."""
    return os.path.join(os.path.dirname(db_path), "esportazioni")


def _apri_lettura(db_path):
    # Senza questo controllo sqlite3.connect CREEREBBE un database vuoto al
    # posto di segnalare che non c'e': su una cartella di rete irraggiungibile
    # si finirebbe per creare file sparsi invece di accorgersi del problema.
    if not db_path or not os.path.exists(db_path):
        raise FileNotFoundError("database non trovato: {}".format(db_path))
    try:
        conn = sqlite3.connect(backup_manager.uri_sola_lettura(db_path),
                               uri=True, timeout=backup_manager.TIMEOUT_SQLITE)
        conn.execute("PRAGMA schema_version")
        return conn
    except Exception:
        return sqlite3.connect(db_path, timeout=backup_manager.TIMEOUT_SQLITE)


def esporta(db_path, cartella=None):
    """Scrive un file CSV per ogni tabella, in una cartella con la data.

    Ritorna (percorso_cartella, {nome_tabella: righe_scritte}).
    Solleva un'eccezione solo se non si riesce proprio a leggere il database."""
    if not db_path or not os.path.exists(db_path):
        raise FileNotFoundError("database non trovato: {}".format(db_path))

    destinazione = cartella or os.path.join(
        cartella_esportazioni(db_path),
        datetime.now().strftime("%Y-%m-%d_%H%M"))
    os.makedirs(destinazione, exist_ok=True)

    conteggi = {}
    conn = _apri_lettura(db_path)
    try:
        presenti = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}

        for tabella, titolo in TABELLE:
            if tabella not in presenti:
                continue
            try:
                cursore = conn.execute("SELECT * FROM {}".format(tabella))
                intestazioni = [d[0] for d in cursore.description]
                righe = cursore.fetchall()
            except Exception as e:
                _log().error("Esportazione di %s non riuscita: %s", tabella, e)
                continue

            percorso = os.path.join(destinazione, "{}.csv".format(titolo))
            with open(percorso, "w", encoding=CODIFICA, newline="") as f:
                scrittore = csv.writer(f, delimiter=SEPARATORE)
                scrittore.writerow(intestazioni)
                for riga in righe:
                    scrittore.writerow(
                        ["" if v is None else v for v in riga])
            conteggi[tabella] = len(righe)
    finally:
        try:
            conn.close()
        except Exception:
            pass

    _scrivi_riepilogo(destinazione, db_path, conteggi)
    _log().info("Esportazione completata in %s (%s)", destinazione, conteggi)
    return destinazione, conteggi


def _scrivi_riepilogo(destinazione, db_path, conteggi):
    """Un file di testo che spiega cosa c'e' dentro, per chi lo trovera' fra
    anni senza sapere cos'e'."""
    righe = [
        "ESPORTAZIONE DATI - RCS Gestione Preventivi",
        "Data: {}".format(datetime.now().strftime("%d/%m/%Y alle %H:%M")),
        "Database di origine: {}".format(db_path),
        "",
        "Questa cartella contiene una copia dei dati in formato CSV.",
        "Si aprono con Excel (doppio clic) o con qualunque foglio di calcolo.",
        "Non serve il programma gestionale per leggerli.",
        "",
        "CONTENUTO:",
    ]
    for tabella, titolo in TABELLE:
        if tabella in conteggi:
            righe.append("  {}.csv  ->  {} righe".format(titolo, conteggi[tabella]))
    righe += [
        "",
        "NOTA: questi file servono a consultare i dati, non a rimetterli nel",
        "programma. Per ripristinare il funzionamento si usa una copia di",
        "sicurezza dalla schermata 'Impostazioni di archiviazione'.",
    ]
    try:
        with open(os.path.join(destinazione, "LEGGIMI.txt"), "w",
                  encoding="utf-8") as f:
            f.write("\n".join(righe))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Esportazione periodica automatica
# ---------------------------------------------------------------------------

def ultima_esportazione(db_path):
    """Quando e' stata fatta l'ultima esportazione, o None."""
    cartella = cartella_esportazioni(db_path)
    if not os.path.isdir(cartella):
        return None
    date = []
    for nome in os.listdir(cartella):
        try:
            date.append(datetime.strptime(nome[:15], "%Y-%m-%d_%H%M"))
        except Exception:
            continue
    return max(date) if date else None


def serve_esportazione(db_path, giorni=GIORNI_TRA_ESPORTAZIONI):
    ultima = ultima_esportazione(db_path)
    if ultima is None:
        return True
    return (datetime.now() - ultima).days >= giorni


def esporta_se_serve(db_path, giorni=GIORNI_TRA_ESPORTAZIONI):
    """Esportazione automatica, al massimo una volta al mese.

    Non deve mai disturbare l'avvio: se qualcosa va storto lo si annota e si
    prosegue."""
    try:
        if not serve_esportazione(db_path, giorni):
            return None
        destinazione, _conteggi = esporta(db_path)
        return destinazione
    except Exception as e:
        _log().warning("Esportazione automatica non riuscita: %s", e)
        return None
