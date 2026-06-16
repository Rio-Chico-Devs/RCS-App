#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RCS - Cruscotto Aziendale (progetto indipendente)
Modulo comune: individua il database del gestionale a partire dal file
config.json di QUESTO strumento. Il database e' sempre aperto in SOLA LETTURA.
"""

import json
import os
import sqlite3
import sys


def base_dir():
    """Cartella dello strumento: accanto all'eseguibile se 'congelato'
    (PyInstaller), altrimenti accanto a questo file."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def carica_config():
    """Legge config.json accanto allo strumento. Ritorna {} se assente o illeggibile."""
    percorso = os.path.join(base_dir(), "config.json")
    if os.path.exists(percorso):
        try:
            with open(percorso, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def trova_db_path(cli=None):
    """Ordine di ricerca del database:
       1. argomento da riga di comando (--db)
       2. config.json -> "db_path"
       3. materiali.db accanto allo strumento
       4. data/materiali.db accanto allo strumento
       Ritorna None se non trova nulla."""
    if cli:
        return cli
    percorso = carica_config().get("db_path")
    if percorso:
        return percorso
    bd = base_dir()
    for cand in (os.path.join(bd, "materiali.db"),
                 os.path.join(bd, "data", "materiali.db")):
        if os.path.exists(cand):
            return cand
    return None


def apri_db_sola_lettura(db_path):
    """Apre il database in SOLA LETTURA. Se manca, spiega come configurarlo."""
    if not db_path or not os.path.exists(db_path):
        raise SystemExit(
            "\nDatabase non trovato.\n\n"
            "Apri il file 'config.json' accanto al programma e imposta 'db_path'\n"
            "con il percorso del database del gestionale. Usa la barra '/'. Esempi:\n\n"
            '    {"db_path": "Z:/RCS/data/materiali.db"}\n'
            '    {"db_path": "//NOMEPC/RCS/data/materiali.db"}\n\n'
            'oppure avvia con:  --db "percorso/materiali.db"\n'
            "(Se config.json non esiste, copia config.example.json in config.json.)\n"
        )
    uri = "file:{}?mode=ro".format(db_path.replace("\\", "/"))
    return sqlite3.connect(uri, uri=True)


def salva_db_path(db_path):
    """Salva/aggiorna 'db_path' in config.json, preservando le altre voci
    (es. la chiave API del notiziario)."""
    cfg = carica_config()
    cfg.pop("_istruzioni", None)
    cfg["db_path"] = db_path
    try:
        with open(os.path.join(base_dir(), "config.json"), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def database_valido(db_path):
    """Verifica che il file sia davvero un database del gestionale,
    controllando la presenza delle tabelle attese. Sola lettura."""
    if not db_path or not os.path.exists(db_path):
        return False
    try:
        uri = "file:{}?mode=ro".format(db_path.replace("\\", "/"))
        conn = sqlite3.connect(uri, uri=True)
        try:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tabelle = {r[0] for r in cur.fetchall()}
        finally:
            conn.close()
        return "preventivi" in tabelle or "materiali" in tabelle
    except Exception:
        return False


def seleziona_db_interattivo():
    """Apre una finestra per scegliere il file del database e lo salva in
    config.json (la scelta viene ricordata). Ritorna il percorso scelto,
    oppure None se l'utente annulla o se l'interfaccia grafica non c'e'."""
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
    except Exception:
        return None  # nessun ambiente grafico: si torna al messaggio testuale

    root = tk.Tk()
    root.withdraw()
    try:
        messagebox.showinfo(
            "Cruscotto Aziendale",
            "Seleziona il file del database del gestionale (di solito 'materiali.db').\n\n"
            "La scelta verra' ricordata: le prossime volte parte da sola.")
        while True:
            scelto = filedialog.askopenfilename(
                title="Seleziona il database del gestionale (materiali.db)",
                filetypes=[("Database SQLite", "*.db"), ("Tutti i file", "*.*")])
            if not scelto:
                return None
            if database_valido(scelto):
                salva_db_path(scelto)
                return scelto
            if not messagebox.askretrycancel(
                    "File non riconosciuto",
                    "Il file scelto non sembra il database del gestionale "
                    "(mancano le tabelle attese).\n\nVuoi sceglierne un altro?"):
                return None
    finally:
        root.destroy()


def assicura_db_path(cli=None):
    """Come trova_db_path, ma se non trova nulla apre la finestra di selezione."""
    percorso = trova_db_path(cli)
    if percorso:
        return percorso
    return seleziona_db_interattivo()
