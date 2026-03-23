#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
unisci_db.py - RCS App
======================
Importa i preventivi dal vecchio database nel nuovo database.
I materiali usati nel nuovo DB vengono preservati intatti.

Uso:
    python unisci_db.py [--vecchio VECCHIO_DB] [--nuovo NUOVO_DB]

Esempio:
    python unisci_db.py --vecchio backup/materiali.db --nuovo data/materiali.db

Se non si specificano i percorsi, lo script li chiede interattivamente.
"""

import sys
import os
import json
import shutil
import sqlite3
import argparse
from datetime import datetime


# ──────────────────────────────────────────────────────────────────────────────
# Utilità
# ──────────────────────────────────────────────────────────────────────────────

def _conn(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _backup(path: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = path + f".backup_{ts}"
    shutil.copy2(path, dest)
    return dest


def _colonne(cursor, tabella: str) -> set:
    cursor.execute(f"PRAGMA table_info({tabella})")
    return {r["name"] for r in cursor.fetchall()}


# ──────────────────────────────────────────────────────────────────────────────
# Caricamento dati
# ──────────────────────────────────────────────────────────────────────────────

def _carica_materiali_nuovo(conn_nuovo) -> dict:
    """Restituisce {nome_lower: {id, nome, spessore, prezzo}} dal nuovo DB."""
    cur = conn_nuovo.cursor()
    cur.execute("SELECT id, nome, spessore, prezzo FROM materiali")
    return {r["nome"].lower().strip(): dict(r) for r in cur.fetchall()}


def _carica_preventivi_vecchio(conn_vecchio) -> list:
    """Restituisce tutti i preventivi del vecchio DB come lista di dict."""
    cur = conn_vecchio.cursor()
    # Leggi solo le colonne che esistono in entrambi gli schemi
    cols_disponibili = _colonne(cur, "preventivi")
    cur.execute("SELECT * FROM preventivi ORDER BY id")
    return [dict(r) for r in cur.fetchall()]


def _preventivi_esistenti_nuovo(conn_nuovo) -> set:
    """Restituisce l'insieme di tutti gli id preventivo già nel nuovo DB."""
    cur = conn_nuovo.cursor()
    cur.execute("SELECT id FROM preventivi")
    return {r[0] for r in cur.fetchall()}


# ──────────────────────────────────────────────────────────────────────────────
# Riallineamento materiali nel JSON
# ──────────────────────────────────────────────────────────────────────────────

def _riallinea_materiali_json(mat_json: str, mappa_nuovi: dict) -> tuple:
    """
    Aggiorna il campo materiale_id nel JSON dei materiali usati in un preventivo.

    Ritorna:
        (nuovo_json, lista_problemi)
        problemi = lista di stringhe descrittive per i materiali non trovati
    """
    problemi = []
    try:
        materiali = json.loads(mat_json) if isinstance(mat_json, str) else mat_json
        if not isinstance(materiali, list):
            return mat_json, []
    except (json.JSONDecodeError, TypeError):
        return mat_json, ["JSON non valido nei materiali utilizzati"]

    for mat in materiali:
        nome = str(mat.get("materiale_nome", mat.get("nome", ""))).lower().strip()
        if not nome:
            continue

        if nome in mappa_nuovi:
            mat["materiale_id"] = mappa_nuovi[nome]["id"]
        else:
            # Prova corrispondenza parziale (es. "hs300" vs "HS300 FR")
            candidati = [k for k in mappa_nuovi if nome in k or k in nome]
            if len(candidati) == 1:
                mat["materiale_id"] = mappa_nuovi[candidati[0]]["id"]
                problemi.append(
                    f"  '{mat.get('materiale_nome', nome)}' → corrispondenza parziale "
                    f"con '{mappa_nuovi[candidati[0]]['nome']}' (verifica consigliata)"
                )
            elif len(candidati) > 1:
                mat["materiale_id"] = None
                nomi_candidati = ", ".join(mappa_nuovi[c]["nome"] for c in candidati)
                problemi.append(
                    f"  '{mat.get('materiale_nome', nome)}' → più candidati: {nomi_candidati} "
                    f"(ID azzerato, apri il preventivo per correggere)"
                )
            else:
                mat["materiale_id"] = None
                problemi.append(
                    f"  '{mat.get('materiale_nome', nome)}' → NON TROVATO nel nuovo DB "
                    f"(materiale rimosso o rinominato; i costi salvati restano validi)"
                )

    return json.dumps(materiali), problemi


# ──────────────────────────────────────────────────────────────────────────────
# Colonne standard presenti nel nuovo schema
# ──────────────────────────────────────────────────────────────────────────────

COLONNE_PREVENTIVI = [
    "id", "data_creazione", "numero_revisione", "preventivo_originale_id",
    "nome_cliente", "numero_ordine", "misura", "descrizione", "codice",
    "costo_totale_materiali", "costi_accessori",
    "minuti_taglio", "minuti_avvolgimento", "minuti_pulizia",
    "minuti_rettifica", "minuti_imballaggio",
    "tot_mano_opera", "subtotale", "maggiorazione_25",
    "preventivo_finale", "prezzo_cliente",
    "materiali_utilizzati", "note_revisione", "storico_modifiche",
    "categoria", "sottocategoria",
]


# ──────────────────────────────────────────────────────────────────────────────
# Inserimento
# ──────────────────────────────────────────────────────────────────────────────

def _inserisci_preventivo(cur_nuovo, preventivo: dict, mat_json_aggiornato: str,
                          cols_nuovo: set, id_remap: dict) -> None:
    """
    Inserisce il preventivo nel nuovo DB.
    Rimappa preventivo_originale_id se necessario.
    """
    valori = {}
    for col in COLONNE_PREVENTIVI:
        if col not in cols_nuovo:
            continue
        if col == "materiali_utilizzati":
            valori[col] = mat_json_aggiornato
        elif col == "preventivo_originale_id":
            orig = preventivo.get(col)
            valori[col] = id_remap.get(orig, orig) if orig else None
        else:
            valori[col] = preventivo.get(col)

    # Rimuovi 'id' per far assegnare un nuovo id auto
    valori.pop("id", None)

    cols = list(valori.keys())
    placeholders = ", ".join("?" for _ in cols)
    sql = f"INSERT INTO preventivi ({', '.join(cols)}) VALUES ({placeholders})"
    cur_nuovo.execute(sql, [valori[c] for c in cols])


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def unisci(vecchio_db: str, nuovo_db: str) -> None:
    print(f"\n{'═'*65}")
    print(f"  UNIONE DATABASE")
    print(f"  Vecchio (preventivi): {vecchio_db}")
    print(f"  Nuovo   (materiali) : {nuovo_db}")
    print(f"{'═'*65}\n")

    for path in [vecchio_db, nuovo_db]:
        if not os.path.isfile(path):
            print(f"ERRORE: File non trovato → {path}")
            sys.exit(1)

    # Backup del nuovo DB prima di modificarlo
    bk = _backup(nuovo_db)
    print(f"  Backup nuovo DB: {os.path.basename(bk)}")
    print()

    conn_v = _conn(vecchio_db)
    conn_n = _conn(nuovo_db)

    # Assicura che la migrazione dello schema sia applicata al nuovo DB
    _assicura_schema_nuovo(conn_n)

    mappa_nuovi      = _carica_materiali_nuovo(conn_n)
    preventivi_v     = _carica_preventivi_vecchio(conn_v)
    id_esistenti     = _preventivi_esistenti_nuovo(conn_n)
    cols_nuovo       = _colonne(conn_n.cursor(), "preventivi")

    print(f"  Materiali nel nuovo DB   : {len(mappa_nuovi)}")
    print(f"  Preventivi nel vecchio DB: {len(preventivi_v)}")
    print(f"  Preventivi nel nuovo DB  : {len(id_esistenti)}")
    print()

    cur_n    = conn_n.cursor()
    id_remap = {}   # vecchio_id → nuovo_id

    importati     = 0
    saltati       = 0
    tutti_problemi = {}   # vecchio_id → [problemi]

    for prev in preventivi_v:
        vecchio_id = prev["id"]

        # Se l'id esiste già nel nuovo DB, salta con avviso
        if vecchio_id in id_esistenti:
            print(f"  [SALTO] Preventivo #{vecchio_id} ({prev.get('nome_cliente','')}) "
                  f"già presente nel nuovo DB.")
            saltati += 1
            continue

        # Riallinea materiali
        mat_json = prev.get("materiali_utilizzati") or "[]"
        mat_json_aggiornato, problemi = _riallinea_materiali_json(mat_json, mappa_nuovi)

        if problemi:
            tutti_problemi[vecchio_id] = problemi

        _inserisci_preventivo(cur_n, prev, mat_json_aggiornato, cols_nuovo, id_remap)

        # Recupera il nuovo id assegnato
        nuovo_id = cur_n.lastrowid
        id_remap[vecchio_id] = nuovo_id
        importati += 1

    conn_n.commit()
    conn_v.close()
    conn_n.close()

    # ── Report finale ──────────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print(f"  RISULTATI")
    print(f"{'─'*65}")
    print(f"  Preventivi importati : {importati}")
    if saltati:
        print(f"  Preventivi saltati   : {saltati}  (già presenti)")
    print()

    if tutti_problemi:
        print(f"  DISCREPANZE MATERIALI ({len(tutti_problemi)} preventivi):")
        print(f"  {'─'*60}")
        for vid, probs in tutti_problemi.items():
            nome_c = next(
                (p.get("nome_cliente", "") for p in preventivi_v if p["id"] == vid), ""
            )
            print(f"  Preventivo #{vid}  {nome_c}")
            for p in probs:
                print(f"    {p}")
        print()
        print("  NOTA: I costi e i prezzi salvati restano INVARIATI.")
        print("  I materiali con ID azzerato vanno selezionati di nuovo")
        print("  aprendo il preventivo nell'app.")
    else:
        print("  Nessuna discrepanza: tutti i materiali trovati nel nuovo DB.")

    print(f"\n{'═'*65}")
    print(f"  Completato. Puoi aprire il nuovo DB con l'app.")
    print(f"{'═'*65}\n")


def _assicura_schema_nuovo(conn):
    """Aggiunge colonne mancanti al nuovo DB se necessario."""
    cur = conn.cursor()
    cols = _colonne(cur, "preventivi")
    extra = [
        ("categoria",     "TEXT NOT NULL DEFAULT ''"),
        ("sottocategoria","TEXT NOT NULL DEFAULT ''"),
        ("storico_modifiche", "TEXT DEFAULT '[]'"),
        ("note_revisione", "TEXT DEFAULT ''"),
        ("numero_revisione", "INTEGER NOT NULL DEFAULT 1"),
        ("preventivo_originale_id", "INTEGER"),
    ]
    for col, defn in extra:
        if col not in cols:
            try:
                cur.execute(f"ALTER TABLE preventivi ADD COLUMN {col} {defn}")
            except sqlite3.OperationalError:
                pass

    cols_m = _colonne(cur, "materiali")
    extra_m = [
        ("fornitore",          "TEXT NOT NULL DEFAULT ''"),
        ("prezzo_fornitore",   "REAL NOT NULL DEFAULT 0.0"),
        ("capacita_magazzino", "REAL NOT NULL DEFAULT 0.0"),
        ("giacenza",           "REAL NOT NULL DEFAULT 0.0"),
        ("categoria_id",       "INTEGER"),
    ]
    for col, defn in extra_m:
        if col not in cols_m:
            try:
                cur.execute(f"ALTER TABLE materiali ADD COLUMN {col} {defn}")
            except sqlite3.OperationalError:
                pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categorie_materiale (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            giacenza_minima REAL NOT NULL DEFAULT 0.0,
            giacenza_desiderata REAL NOT NULL DEFAULT 0.0,
            capacita_magazzino REAL NOT NULL DEFAULT 0.0,
            note TEXT DEFAULT ''
        )
    """)
    cur.execute("""
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fornitori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()


def main():
    parser = argparse.ArgumentParser(
        description="Importa i preventivi dal vecchio DB nel nuovo DB"
    )
    parser.add_argument("--vecchio", help="Percorso del vecchio database")
    parser.add_argument("--nuovo",   help="Percorso del nuovo database (verrà modificato)")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))

    if args.vecchio:
        vecchio = args.vecchio
    else:
        default_v = os.path.join(script_dir, "backup", "materiali.db")
        risposta = input(
            f"Percorso del VECCHIO database (quello con i preventivi)\n"
            f"[Invio per: {default_v}]: "
        ).strip()
        vecchio = risposta if risposta else default_v

    if args.nuovo:
        nuovo = args.nuovo
    else:
        default_n = os.path.join(script_dir, "data", "materiali.db")
        risposta = input(
            f"\nPercorso del NUOVO database (quello con i materiali aggiornati)\n"
            f"[Invio per: {default_n}]: "
        ).strip()
        nuovo = risposta if risposta else default_n

    print(f"\nATTENZIONE: Il nuovo database verrà modificato.")
    print(f"Un backup automatico verrà creato prima di qualsiasi modifica.")
    conferma = input("Continuare? [s/N]: ").strip().lower()
    if conferma not in ("s", "si", "sì", "y", "yes"):
        print("Operazione annullata.")
        sys.exit(0)

    unisci(vecchio, nuovo)


if __name__ == "__main__":
    main()
