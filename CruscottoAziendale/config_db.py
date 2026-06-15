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
