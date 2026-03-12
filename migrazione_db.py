#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script di migrazione database - RCS App
Converte un vecchio database al formato della nuova versione.

Uso:
    python migrazione_db.py [percorso_vecchio_db]
    oppure esegui senza argomenti e verrà chiesto il percorso.
"""

import sys
import os
import json
import shutil
import sqlite3
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# Mapping vecchio → nuovo formato per i materiali dentro i preventivi
# ─────────────────────────────────────────────────────────────────────────────

def _converti_materiale_vecchio(mat):
    """
    Converte un dizionario materiale dal vecchio formato al nuovo.
    Campi che non esistono nel vecchio formato vengono impostati a default.
    """
    # Se ha già il campo 'diametro' (nuovo formato) non lo tocchiamo
    if 'diametro' in mat and 'materiale_nome' in mat:
        return mat

    nuovo = {
        # Geometria
        'diametro':               mat.get('diametro_interno', mat.get('diametro', 0.0)),
        'lunghezza':              mat.get('lunghezza', 0.0),           # non esisteva → 0
        'giri':                   mat.get('giri', 0),
        'spessore':               mat.get('spessore', 0.0),
        'diametro_finale':        mat.get('diametro_finale', 0.0),

        # Sviluppo
        'sviluppo':               mat.get('sviluppo', mat.get('stratifica', 0.0)),
        'arrotondamento_manuale': mat.get('arrotondamento_manuale', 0.0),

        # Materiale
        'materiale_id':           mat.get('materiale_id', None),
        'materiale_nome':         mat.get('nome', mat.get('materiale_nome', '')),

        # Costi
        'costo_materiale':        mat.get('costo_al_kg', mat.get('costo_materiale', 0.0)),
        'lunghezza_utilizzata':   mat.get('lunghezza_utilizzata', 0.0),
        'costo_totale':           mat.get('costo_totale', 0.0),
        'maggiorazione':          mat.get('maggiorazione', round(mat.get('costo_totale', 0.0) * 1.1, 4)),

        # Conicità
        'is_conica':              mat.get('is_conica', False),
        'sezioni_coniche':        mat.get('sezioni_coniche', []),
        'conicita_lato':          mat.get('conicita_lato', 'sinistra'),
        'conicita_altezza_mm':    mat.get('conicita_altezza_mm', 0.0),
        'conicita_lunghezza_mm':  mat.get('conicita_lunghezza_mm', 0.0),
        'scarto_mm2':             mat.get('scarto_mm2', 0.0),

        # Orientamento
        'orientamento':           mat.get('orientamento', {'rotation': 0, 'flip_h': False, 'flip_v': False}),
    }
    return nuovo


def _aggiorna_schema(cursor):
    """
    Aggiunge le colonne mancanti alle tabelle esistenti
    (stesso comportamento di DatabaseManager._migrate_database).
    """
    # ── preventivi ──
    cursor.execute("PRAGMA table_info(preventivi)")
    cols = {r[1] for r in cursor.fetchall()}

    aggiunte_preventivi = [
        ("nome_cliente",     "TEXT NOT NULL DEFAULT ''"),
        ("numero_ordine",    "TEXT NOT NULL DEFAULT ''"),
        ("misura",           "TEXT NOT NULL DEFAULT ''"),
        ("descrizione",      "TEXT NOT NULL DEFAULT ''"),
        ("codice",           "TEXT NOT NULL DEFAULT ''"),
        ("storico_modifiche","TEXT DEFAULT '[]'"),
        ("note_revisione",   "TEXT DEFAULT ''"),
        ("numero_revisione", "INTEGER NOT NULL DEFAULT 1"),
        ("preventivo_originale_id", "INTEGER"),
    ]
    for col, defn in aggiunte_preventivi:
        if col not in cols:
            try:
                cursor.execute(f"ALTER TABLE preventivi ADD COLUMN {col} {defn}")
            except sqlite3.OperationalError:
                pass

    # ── materiali ──
    cursor.execute("PRAGMA table_info(materiali)")
    cols = {r[1] for r in cursor.fetchall()}

    aggiunte_materiali = [
        ("fornitore",          "TEXT NOT NULL DEFAULT ''"),
        ("prezzo_fornitore",   "REAL NOT NULL DEFAULT 0.0"),
        ("capacita_magazzino", "REAL NOT NULL DEFAULT 0.0"),
        ("giacenza",           "REAL NOT NULL DEFAULT 0.0"),
        ("categoria_id",       "INTEGER"),
    ]
    for col, defn in aggiunte_materiali:
        if col not in cols:
            try:
                cursor.execute(f"ALTER TABLE materiali ADD COLUMN {col} {defn}")
            except sqlite3.OperationalError:
                pass

    # ── nuove tabelle ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorie_materiale (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            giacenza_minima REAL NOT NULL DEFAULT 0.0,
            giacenza_desiderata REAL NOT NULL DEFAULT 0.0,
            capacita_magazzino REAL NOT NULL DEFAULT 0.0,
            note TEXT DEFAULT ''
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimenti_magazzino (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            materiale_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            quantita REAL NOT NULL,
            data TEXT NOT NULL,
            note TEXT DEFAULT '',
            preventivo_id INTEGER,
            FOREIGN KEY (materiale_id) REFERENCES materiali(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fornitori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)
    # Fornitori di default
    for nome_f in ['CIT', 'FIBERTECH', 'ANGELONI']:
        try:
            cursor.execute("INSERT INTO fornitori (nome) VALUES (?)", (nome_f,))
        except sqlite3.IntegrityError:
            pass


def migra(percorso_db: str) -> None:
    print(f"\n{'─'*60}")
    print(f"  Migrazione: {percorso_db}")
    print(f"{'─'*60}")

    if not os.path.isfile(percorso_db):
        print(f"ERRORE: File non trovato → {percorso_db}")
        sys.exit(1)

    # ── 1. Backup ──────────────────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = percorso_db + f".backup_{timestamp}"
    shutil.copy2(percorso_db, backup_path)
    print(f"  Backup creato: {os.path.basename(backup_path)}")

    with sqlite3.connect(percorso_db) as conn:
        cursor = conn.cursor()

        # ── 2. Schema ──────────────────────────────────────────────────────
        print("  Aggiornamento schema tabelle...")
        _aggiorna_schema(cursor)
        conn.commit()

        # ── 3. Migrazione JSON preventivi ──────────────────────────────────
        cursor.execute("SELECT id, materiali_utilizzati FROM preventivi")
        preventivi = cursor.fetchall()
        print(f"  Preventivi trovati: {len(preventivi)}")

        migrati = 0
        gia_nuovi = 0
        errori = 0

        for prev_id, mat_json in preventivi:
            if not mat_json:
                continue
            try:
                materiali = json.loads(mat_json) if isinstance(mat_json, str) else mat_json
                if not isinstance(materiali, list) or len(materiali) == 0:
                    continue

                # Controlla se è già in formato nuovo
                primo = materiali[0]
                if 'materiale_nome' in primo and 'diametro' in primo:
                    gia_nuovi += 1
                    continue

                # Converti ogni materiale
                materiali_nuovi = [_converti_materiale_vecchio(m) for m in materiali]
                nuovo_json = json.dumps(materiali_nuovi)

                cursor.execute(
                    "UPDATE preventivi SET materiali_utilizzati = ? WHERE id = ?",
                    (nuovo_json, prev_id)
                )
                migrati += 1

            except Exception as e:
                print(f"    ATTENZIONE preventivo #{prev_id}: {e}")
                errori += 1

        conn.commit()

        print(f"\n  Risultati migrazione preventivi:")
        print(f"    Convertiti al nuovo formato : {migrati}")
        print(f"    Già in formato nuovo        : {gia_nuovi}")
        if errori:
            print(f"    Errori (non modificati)     : {errori}")

        # ── 4. Riepilogo materiali ─────────────────────────────────────────
        cursor.execute("SELECT COUNT(*) FROM materiali")
        n_mat = cursor.fetchone()[0]
        print(f"\n  Materiali nel catalogo: {n_mat}")

    print(f"\n  Migrazione completata.")
    print(f"  NOTA: I campi 'lunghezza rotolo' dei vecchi preventivi")
    print(f"        sono stati impostati a 0. Per ricalcolare i costi")
    print(f"        aprire il preventivo e aggiornare il campo 'Lunghezza'.")
    print(f"{'─'*60}\n")


def main():
    if len(sys.argv) > 1:
        percorso = sys.argv[1]
    else:
        # Prova percorso di default relativo a questo script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default = os.path.join(script_dir, "data", "materiali.db")
        risposta = input(
            f"\nPercorso del database vecchio\n"
            f"[Invio per usare il default: {default}]: "
        ).strip()
        percorso = risposta if risposta else default

    migra(percorso)


if __name__ == "__main__":
    main()
