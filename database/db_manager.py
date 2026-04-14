#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Database Manager per Sistema Preventivi RCS con Sistema di Versioning
Uso riservato esclusivamente a RCS
"""

# type: ignore
# pyright: reportUnknownParameterType=false, reportMissingParameterType=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportAttributeAccessIssue=false
# pyright: reportUnusedVariable=false
# type: ignore
# pyright: reportUnusedImport=false
# type: ignore
# pyright: reportUnknownLambdaType=false

import sqlite3
import os
import sys
import json
import logging
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # Leggi config.json se esiste (percorso db condiviso in rete)
            config_path = os.path.join(base_dir, "config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    db_path = config.get("db_path") or os.path.join(base_dir, "data", "materiali.db")
                except Exception:
                    db_path = os.path.join(base_dir, "data", "materiali.db")
            else:
                db_path = os.path.join(base_dir, "data", "materiali.db")
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
        self._backup_database()

    def _backup_database(self):
        """Crea un backup automatico del database all'avvio. Mantiene gli ultimi 7 backup."""
        try:
            import shutil
            backup_dir = os.path.join(os.path.dirname(self.db_path), "backup")
            os.makedirs(backup_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"materiali_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_name)

            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, backup_path)

            # Mantieni solo gli ultimi 7 backup
            backups = sorted([
                f for f in os.listdir(backup_dir) if f.startswith("materiali_backup_") and f.endswith(".db")
            ])
            while len(backups) > 7:
                os.remove(os.path.join(backup_dir, backups.pop(0)))
        except Exception:
            pass  # Backup non critico, non blocca l'avvio

    def init_database(self):
        """Inizializza il database con le tabelle necessarie"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Tabella materiali (IDENTICA ALL'ORIGINALE)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS materiali (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    spessore REAL NOT NULL,
                    prezzo REAL NOT NULL
                )
            """)

            # Tabella preventivi - AGGIORNATA con campo storico_modifiche e misura
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preventivi (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_creazione TEXT NOT NULL,
                    numero_revisione INTEGER NOT NULL DEFAULT 1,
                    preventivo_originale_id INTEGER,
                    nome_cliente TEXT NOT NULL DEFAULT '',
                    numero_ordine TEXT NOT NULL DEFAULT '',
                    misura TEXT NOT NULL DEFAULT '',
                    descrizione TEXT NOT NULL DEFAULT '',
                    codice TEXT NOT NULL DEFAULT '',
                    finitura TEXT NOT NULL DEFAULT '',
                    costo_totale_materiali REAL,
                    costi_accessori REAL,
                    minuti_taglio REAL,
                    minuti_avvolgimento REAL,
                    minuti_pulizia REAL,
                    minuti_rettifica REAL,
                    minuti_imballaggio REAL,
                    tot_mano_opera REAL,
                    subtotale REAL,
                    maggiorazione_25 REAL,
                    preventivo_finale REAL,
                    prezzo_cliente REAL,
                    materiali_utilizzati TEXT,
                    note_revisione TEXT,
                    storico_modifiche TEXT DEFAULT '[]',
                    FOREIGN KEY (preventivo_originale_id) REFERENCES preventivi(id)
                )
            """)

            # Migrazione automatica per aggiungere le nuove colonne se non esistono
            self._migrate_database(cursor)

            # Inserimento materiali di esempio se la tabella è vuota (IDENTICO ALL'ORIGINALE)
            cursor.execute("SELECT COUNT(*) FROM materiali")
            if cursor.fetchone()[0] == 0:
                materiali_esempio = [
                    ("HS300", 0.3, 20.00),
                    ("HS150", 0.15, 15.00),
                    ("HM 150/40J", 0.15, 42.00),
                    ("IM45", 0.05, 21.00),
                    ("HM 100/64", 0.1, 30.00),
                    ("CC200PL", 0.25, 30.00),
                    ("CC206", 0.23, 30.00),
                    ("GG204", 0.25, 30.00),
                    ("TWILL", 0.25, 30.00),
                    ("CC222", 0.25, 32.00),
                    ("CC631", 0.25, 41.00),
                    ("CC630", 0.25, 41.00),
                    ("GG800T", 0.8, 46.00),
                    ("CBX200", 0.25, 30.00),
                    ("CBX300", 0.33, 30.00),
                    ("STY280", 0.2, 35.00),
                    ("CK204", 0.25, 32.00),
                    ("VV1017", 0.35, 15.00),
                    ("VV1031", 0.25, 12.00),
                    ("VR192", 0.15, 12.00),
                    ("VV116", 0.15, 10.00),
                    ("VV350", 0.37, 15.00),
                    ("VV770", 0.75, 18.00)
                ]
                cursor.executemany(
                    "INSERT INTO materiali (nome, spessore, prezzo) VALUES (?, ?, ?)",
                    materiali_esempio
                )

            conn.commit()

    def _migrate_database(self, cursor):
        """Migrazione automatica per aggiungere i nuovi campi"""
        # Controlla se le nuove colonne esistono già
        cursor.execute("PRAGMA table_info(preventivi)")
        columns = [column[1] for column in cursor.fetchall()]

        # Aggiungi le colonne mancanti
        new_columns = [
            ("nome_cliente", "TEXT NOT NULL DEFAULT ''"),
            ("numero_ordine", "TEXT NOT NULL DEFAULT ''"),
            ("misura", "TEXT NOT NULL DEFAULT ''"),
            ("descrizione", "TEXT NOT NULL DEFAULT ''"),
            ("codice", "TEXT NOT NULL DEFAULT ''"),
            ("finitura", "TEXT NOT NULL DEFAULT ''"),
            ("storico_modifiche", "TEXT DEFAULT '[]'"),
        ]

        for column_name, column_def in new_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE preventivi ADD COLUMN {column_name} {column_def}")
                except sqlite3.OperationalError as e:
                    print(f"[DB migrazione] preventivi.{column_name}: {e}", file=sys.stderr)

        # Migrazione tabella materiali - nuovi campi magazzino
        cursor.execute("PRAGMA table_info(materiali)")
        materiali_columns = [column[1] for column in cursor.fetchall()]

        materiali_new_columns = [
            ("fornitore", "TEXT NOT NULL DEFAULT ''"),
            ("prezzo_fornitore", "REAL NOT NULL DEFAULT 0.0"),
            ("capacita_magazzino", "REAL NOT NULL DEFAULT 0.0"),
            ("giacenza", "REAL NOT NULL DEFAULT 0.0"),
            ("scorta_minima", "REAL NOT NULL DEFAULT 0.0"),
            ("scorta_massima", "REAL NOT NULL DEFAULT 0.0"),
        ]

        for column_name, column_def in materiali_new_columns:
            if column_name not in materiali_columns:
                try:
                    cursor.execute(f"ALTER TABLE materiali ADD COLUMN {column_name} {column_def}")
                except sqlite3.OperationalError as e:
                    print(f"[DB migrazione] materiali.{column_name}: {e}", file=sys.stderr)

        # Tabella movimenti magazzino
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

        # Aggiungi fornitore_nome a movimenti_magazzino se non esiste
        cursor.execute("PRAGMA table_info(movimenti_magazzino)")
        mov_cols = [c[1] for c in cursor.fetchall()]
        if 'fornitore_nome' not in mov_cols:
            try:
                cursor.execute("ALTER TABLE movimenti_magazzino ADD COLUMN fornitore_nome TEXT DEFAULT ''")
            except Exception as e:
                print(f"[DB migrazione] movimenti_magazzino.fornitore_nome: {e}", file=sys.stderr)

        # Tabella multi-fornitore per materiale
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS materiale_fornitori (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                materiale_id INTEGER NOT NULL,
                fornitore_nome TEXT NOT NULL,
                prezzo_fornitore REAL NOT NULL DEFAULT 0.0,
                scorta_minima REAL NOT NULL DEFAULT 0.0,
                scorta_massima REAL NOT NULL DEFAULT 0.0,
                giacenza REAL NOT NULL DEFAULT 0.0,
                FOREIGN KEY (materiale_id) REFERENCES materiali(id),
                UNIQUE (materiale_id, fornitore_nome)
            )
        """)

        # Migrazione: copia dati fornitore esistenti in materiale_fornitori
        cursor.execute("SELECT COUNT(*) FROM materiale_fornitori")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                SELECT id, fornitore, prezzo_fornitore, capacita_magazzino, giacenza
                FROM materiali
                WHERE fornitore IS NOT NULL AND fornitore != ''
            """)
            rows = cursor.fetchall()
            for mat_id, forn, prezzo_forn, cap_mag, giac in rows:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO materiale_fornitori
                        (materiale_id, fornitore_nome, prezzo_fornitore, scorta_massima, giacenza)
                        VALUES (?, ?, ?, ?, ?)
                    """, (mat_id, forn, prezzo_forn, cap_mag, giac))
                except Exception as e:
                    print(f"[DB migrazione] copia fornitore materiale_id={mat_id}: {e}", file=sys.stderr)

        # Tabella fornitori
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fornitori (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE
            )
        """)

        # Pre-popola fornitori di default se vuota
        cursor.execute("SELECT COUNT(*) FROM fornitori")
        if cursor.fetchone()[0] == 0:
            for nome_f in ['CIT', 'FIBERTECH', 'ANGELONI']:
                try:
                    cursor.execute("INSERT INTO fornitori (nome) VALUES (?)", (nome_f,))
                except sqlite3.IntegrityError:
                    pass

        # Tabella clienti
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clienti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                email TEXT DEFAULT '',
                telefono TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)

    # =================== METODI MATERIALI (IDENTICI ALL'ORIGINALE) ===================

    def get_all_materiali(self):
        """Restituisce tutti i materiali disponibili"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome, spessore, prezzo, fornitore, prezzo_fornitore, capacita_magazzino, giacenza, scorta_minima, scorta_massima FROM materiali ORDER BY nome")
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in get_all_materiali: {e}")
            return []

    def get_materiale_by_id(self, materiale_id):
        """Restituisce un materiale specifico tramite ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome, spessore, prezzo, fornitore, prezzo_fornitore, capacita_magazzino, giacenza, scorta_minima, scorta_massima FROM materiali WHERE id = ?", (materiale_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in get_materiale_by_id: {e}")
            return None

    def get_materiale_by_nome(self, nome):
        """Restituisce un materiale specifico tramite nome"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome, spessore, prezzo, fornitore, prezzo_fornitore, capacita_magazzino, giacenza, scorta_minima, scorta_massima FROM materiali WHERE nome = ?", (nome,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in get_materiale_by_nome: {e}")
            return None

    def add_materiale(self, nome, spessore, prezzo, fornitore="", prezzo_fornitore=0.0, capacita_magazzino=0.0, giacenza=0.0):
        """Aggiunge un nuovo materiale"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO materiali (nome, spessore, prezzo, fornitore, prezzo_fornitore, capacita_magazzino, giacenza) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (nome, spessore, prezzo, fornitore, prezzo_fornitore, capacita_magazzino, giacenza)
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return False

    def update_materiale_base(self, materiale_id, nome, spessore, prezzo):
        """Aggiorna solo i campi base di un materiale (senza toccare fornitori/giacenza legacy)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE materiali SET nome = ?, spessore = ?, prezzo = ? WHERE id = ?",
                    (nome, spessore, prezzo, materiale_id)
                )
                conn.commit()
                return cursor.rowcount > 0
            except sqlite3.IntegrityError:
                return False
            except sqlite3.Error as e:
                logging.getLogger('rcs').error(f"DB error in update_materiale_base: {e}")
                return False

    def update_materiale_scorte(self, materiale_id, scorta_minima, scorta_massima):
        """Aggiorna le scorte aggregate (min/max) di un materiale"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE materiali SET scorta_minima = ?, scorta_massima = ? WHERE id = ?",
                    (scorta_minima, scorta_massima, materiale_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in update_materiale_scorte: {e}")
            return False

    def update_materiale(self, materiale_id, nome, spessore, prezzo, fornitore="", prezzo_fornitore=0.0, capacita_magazzino=0.0, giacenza=0.0):
        """Aggiorna un materiale esistente"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE materiali SET nome = ?, spessore = ?, prezzo = ?, fornitore = ?, prezzo_fornitore = ?, capacita_magazzino = ?, giacenza = ? WHERE id = ?",
                    (nome, spessore, prezzo, fornitore, prezzo_fornitore, capacita_magazzino, giacenza, materiale_id)
                )
                conn.commit()
                return cursor.rowcount > 0
            except sqlite3.IntegrityError:
                return False
            except sqlite3.Error as e:
                logging.getLogger('rcs').error(f"DB error in update_materiale: {e}")
                return False

    def update_prezzo_materiale(self, materiale_id, nuovo_prezzo):
        """Aggiorna solo il prezzo di un materiale"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE materiali SET prezzo = ? WHERE id = ?",
                    (nuovo_prezzo, materiale_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in update_prezzo_materiale: {e}")
            return False

    def delete_materiale(self, materiale_id):
        """Elimina un materiale, i suoi movimenti e le sue voci fornitore"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM movimenti_magazzino WHERE materiale_id = ?", (materiale_id,))
                cursor.execute("DELETE FROM materiale_fornitori WHERE materiale_id = ?", (materiale_id,))
                cursor.execute("DELETE FROM materiali WHERE id = ?", (materiale_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in delete_materiale: {e}")
            return False

    # =================== METODI MATERIALE_FORNITORI ===================

    def get_fornitori_per_materiale(self, materiale_id):
        """Restituisce i fornitori di un materiale specifico"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, fornitore_nome, prezzo_fornitore, scorta_minima, scorta_massima, giacenza
                    FROM materiale_fornitori
                    WHERE materiale_id = ?
                    ORDER BY fornitore_nome
                """, (materiale_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in get_fornitori_per_materiale: {e}")
            return []

    def get_fornitori_counts(self):
        """Restituisce dict {materiale_id: n_fornitori} per tutti i materiali"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT materiale_id, COUNT(*) FROM materiale_fornitori GROUP BY materiale_id")
                return {row[0]: row[1] for row in cursor.fetchall()}
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in get_fornitori_counts: {e}")
            return {}

    def add_fornitore_a_materiale(self, materiale_id, fornitore_nome, prezzo_fornitore=0.0, scorta_minima=0.0, scorta_massima=0.0):
        """Aggiunge un fornitore a un materiale"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO materiale_fornitori
                    (materiale_id, fornitore_nome, prezzo_fornitore, scorta_minima, scorta_massima, giacenza)
                    VALUES (?, ?, ?, ?, ?, 0.0)
                """, (materiale_id, fornitore_nome, prezzo_fornitore, scorta_minima, scorta_massima))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return False
            except sqlite3.Error as e:
                logging.getLogger('rcs').error(f"DB error in add_fornitore_a_materiale: {e}")
                return False

    def update_fornitore_materiale(self, mf_id, fornitore_nome, prezzo_fornitore=0.0, scorta_minima=0.0, scorta_massima=0.0):
        """Aggiorna un fornitore di un materiale"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE materiale_fornitori
                    SET fornitore_nome = ?, prezzo_fornitore = ?, scorta_minima = ?, scorta_massima = ?
                    WHERE id = ?
                """, (fornitore_nome, prezzo_fornitore, scorta_minima, scorta_massima, mf_id))
                conn.commit()
                return cursor.rowcount > 0
            except sqlite3.IntegrityError:
                return False
            except sqlite3.Error as e:
                logging.getLogger('rcs').error(f"DB error in update_fornitore_materiale: {e}")
                return False

    def delete_fornitore_materiale(self, mf_id):
        """Elimina un fornitore da un materiale"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM materiale_fornitori WHERE id = ?", (mf_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in delete_fornitore_materiale: {e}")
            return False

    def get_giacenza_totale_materiale(self, materiale_id):
        """Restituisce la giacenza totale di un materiale (somma di tutti i fornitori)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COALESCE(SUM(giacenza), 0)
                    FROM materiale_fornitori
                    WHERE materiale_id = ?
                """, (materiale_id,))
                row = cursor.fetchone()
                if row and row[0] is not None:
                    return row[0]
                # fallback al campo legacy
                cursor.execute("SELECT giacenza FROM materiali WHERE id = ?", (materiale_id,))
                r = cursor.fetchone()
                return r[0] if r else 0.0
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in get_giacenza_totale_materiale: {e}")
            return 0.0

    def get_giacenza_scorta_fornitore(self, materiale_id, fornitore_nome):
        """Restituisce (giacenza, scorta_massima) per un materiale/fornitore specifico."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT giacenza, scorta_massima FROM materiale_fornitori
                    WHERE materiale_id = ? AND fornitore_nome = ?
                """, (materiale_id, fornitore_nome))
                row = cursor.fetchone()
                if row:
                    return float(row[0] or 0), float(row[1] or 0)
                # fallback legacy
                cursor.execute("SELECT giacenza, capacita_magazzino FROM materiali WHERE id = ?", (materiale_id,))
                r = cursor.fetchone()
                return (float(r[0] or 0), float(r[1] or 0)) if r else (0.0, 0.0)
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in get_giacenza_scorta_fornitore: {e}")
            return (0.0, 0.0, 0.0)

    # =================== METODI MAGAZZINO ===================

    def registra_movimento(self, materiale_id, tipo, quantita, note="", preventivo_id=None, fornitore_nome=""):
        """Registra un movimento di magazzino (carico/scarico) e aggiorna giacenza"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO movimenti_magazzino (materiale_id, tipo, quantita, data, note, preventivo_id, fornitore_nome)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (materiale_id, tipo, quantita, datetime.now().isoformat(), note, preventivo_id, fornitore_nome))

                if fornitore_nome:
                    # Aggiorna giacenza in materiale_fornitori
                    if tipo == 'carico':
                        cursor.execute("""
                            UPDATE materiale_fornitori SET giacenza = giacenza + ?
                            WHERE materiale_id = ? AND fornitore_nome = ?
                        """, (quantita, materiale_id, fornitore_nome))
                    elif tipo == 'scarico':
                        cursor.execute("""
                            UPDATE materiale_fornitori SET giacenza = MAX(giacenza - ?, 0)
                            WHERE materiale_id = ? AND fornitore_nome = ?
                        """, (quantita, materiale_id, fornitore_nome))
                else:
                    # Fallback legacy: aggiorna materiali.giacenza
                    if tipo == 'carico':
                        cursor.execute("UPDATE materiali SET giacenza = giacenza + ? WHERE id = ?", (quantita, materiale_id))
                    elif tipo == 'scarico':
                        cursor.execute("UPDATE materiali SET giacenza = MAX(giacenza - ?, 0) WHERE id = ?", (quantita, materiale_id))

                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in registra_movimento: {e}")
            return False

    def get_movimenti_per_materiale(self, materiale_id, limit=100):
        """Restituisce i movimenti di un materiale"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT m.id, m.tipo, m.quantita, m.data, m.note, m.preventivo_id
                    FROM movimenti_magazzino m
                    WHERE m.materiale_id = ?
                    ORDER BY m.data DESC
                    LIMIT ?
                """, (materiale_id, limit))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in get_movimenti_per_materiale: {e}")
            return []

    def get_movimenti_periodo(self, data_inizio, data_fine):
        """Restituisce tutti i movimenti individuali in un periodo (non aggregati)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT mov.id, m.nome, mov.tipo, mov.quantita, mov.data,
                           mov.note, mov.fornitore_nome, mov.materiale_id
                    FROM movimenti_magazzino mov
                    JOIN materiali m ON m.id = mov.materiale_id
                    WHERE mov.data >= ? AND mov.data <= ?
                    ORDER BY mov.data DESC
                """, (data_inizio, data_fine))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in get_movimenti_periodo: {e}")
            return []

    def get_movimento_by_id(self, movimento_id):
        """Restituisce un singolo movimento per id"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, materiale_id, tipo, quantita, data, note, preventivo_id, fornitore_nome
                    FROM movimenti_magazzino WHERE id = ?
                """, (movimento_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in get_movimento_by_id: {e}")
            return None

    def modifica_movimento(self, movimento_id, nuova_quantita, note):
        """Modifica un movimento: reversa il vecchio effetto su giacenza e applica il nuovo"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT materiale_id, tipo, quantita, fornitore_nome FROM movimenti_magazzino WHERE id = ?",
                    (movimento_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return False
                materiale_id, tipo, vecchia_q, fornitore_nome = row

                def _aggiorna_giacenza(cur, mat_id, forn, t, delta):
                    if forn:
                        if t == 'carico':
                            cur.execute("UPDATE materiale_fornitori SET giacenza = giacenza + ? WHERE materiale_id = ? AND fornitore_nome = ?", (delta, mat_id, forn))
                        else:
                            cur.execute("UPDATE materiale_fornitori SET giacenza = MAX(giacenza + ?, 0) WHERE materiale_id = ? AND fornitore_nome = ?", (delta, mat_id, forn))
                    else:
                        if t == 'carico':
                            cur.execute("UPDATE materiali SET giacenza = giacenza + ? WHERE id = ?", (delta, mat_id))
                        else:
                            cur.execute("UPDATE materiali SET giacenza = MAX(giacenza + ?, 0) WHERE id = ?", (delta, mat_id))

                # Reversa vecchio effetto (segno opposto)
                _aggiorna_giacenza(cursor, materiale_id, fornitore_nome, tipo,
                                   -vecchia_q if tipo == 'carico' else vecchia_q)
                # Applica nuovo effetto
                _aggiorna_giacenza(cursor, materiale_id, fornitore_nome, tipo,
                                   nuova_quantita if tipo == 'carico' else -nuova_quantita)

                cursor.execute(
                    "UPDATE movimenti_magazzino SET quantita = ?, note = ? WHERE id = ?",
                    (nuova_quantita, note, movimento_id)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in modifica_movimento: {e}")
            return False

    def elimina_movimento(self, movimento_id):
        """Elimina un movimento e reversa il suo effetto sulla giacenza"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT materiale_id, tipo, quantita, fornitore_nome FROM movimenti_magazzino WHERE id = ?",
                (movimento_id,)
            )
            row = cursor.fetchone()
            if not row:
                return False
            materiale_id, tipo, quantita, fornitore_nome = row

            # Reversa effetto sulla giacenza
            if fornitore_nome:
                if tipo == 'carico':
                    cursor.execute("UPDATE materiale_fornitori SET giacenza = MAX(giacenza - ?, 0) WHERE materiale_id = ? AND fornitore_nome = ?", (quantita, materiale_id, fornitore_nome))
                else:
                    cursor.execute("UPDATE materiale_fornitori SET giacenza = giacenza + ? WHERE materiale_id = ? AND fornitore_nome = ?", (quantita, materiale_id, fornitore_nome))
            else:
                if tipo == 'carico':
                    cursor.execute("UPDATE materiali SET giacenza = MAX(giacenza - ?, 0) WHERE id = ?", (quantita, materiale_id))
                else:
                    cursor.execute("UPDATE materiali SET giacenza = giacenza + ? WHERE id = ?", (quantita, materiale_id))

            cursor.execute("DELETE FROM movimenti_magazzino WHERE id = ?", (movimento_id,))
            conn.commit()
            return True

    def reset_tutte_giacenze(self):
        """Azzera la giacenza di tutti i materiali e fornitori, e cancella tutti i movimenti."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE materiali SET giacenza = 0")
                cursor.execute("UPDATE materiale_fornitori SET giacenza = 0")
                cursor.execute("DELETE FROM movimenti_magazzino")
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in reset_tutte_giacenze: {e}")
            return False

    def get_consumi_periodo(self, data_inizio, data_fine):
        """Restituisce i consumi aggregati per materiale in un periodo"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT mat.id, mat.nome, mat.prezzo_fornitore,
                       COALESCE(SUM(mov.quantita), 0) as totale_consumato
                FROM materiali mat
                LEFT JOIN movimenti_magazzino mov ON mat.id = mov.materiale_id
                    AND mov.tipo = 'scarico'
                    AND mov.data >= ? AND mov.data <= ?
                GROUP BY mat.id, mat.nome, mat.prezzo_fornitore
                HAVING totale_consumato > 0
                ORDER BY totale_consumato DESC
            """, (data_inizio, data_fine))
            return cursor.fetchall()

    def get_scorte(self, ordina_per='giacenza_asc'):
        """Restituisce le scorte di tutti i materiali.
        La giacenza è la somma da materiale_fornitori (se presente) altrimenti dal campo legacy.
        Restituisce: (id, nome, giacenza_totale, scorta_massima, n_fornitori, prezzo_min, scorta_minima)
        La scorta_massima e scorta_minima aggregate vengono lette da m.scorta_massima / m.scorta_minima
        (impostate in gestione materiali). Se non impostate (= 0) si usa il fallback sui fornitori.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if ordina_per == 'giacenza_asc':
                order = "giacenza_totale ASC"
            elif ordina_per == 'giacenza_desc':
                order = "giacenza_totale DESC"
            elif ordina_per == 'n_fornitori_asc':
                order = "n_fornitori ASC, m.nome ASC"
            elif ordina_per == 'n_fornitori_desc':
                order = "n_fornitori DESC, m.nome ASC"
            elif ordina_per == 'fornitore_asc':
                order = "(SELECT MIN(fornitore_nome) FROM materiale_fornitori WHERE materiale_id = m.id) ASC, m.nome ASC"
            else:
                order = "m.nome ASC"

            cursor.execute(f"""
                SELECT m.id, m.nome,
                       COALESCE(SUM(mf.giacenza), m.giacenza) as giacenza_totale,
                       CASE WHEN m.scorta_massima > 0 THEN m.scorta_massima
                            ELSE COALESCE(MAX(mf.scorta_massima), m.capacita_magazzino) END as scorta_massima,
                       COUNT(mf.id) as n_fornitori,
                       COALESCE(MIN(mf.prezzo_fornitore), m.prezzo_fornitore) as prezzo_min,
                       m.scorta_minima as scorta_minima
                FROM materiali m
                LEFT JOIN materiale_fornitori mf ON mf.materiale_id = m.id
                GROUP BY m.id, m.nome
                ORDER BY {order}
            """)
            return cursor.fetchall()

    # =================== METODI PREVENTIVI CON VERSIONING ===================

    def save_preventivo(self, preventivo_data):
        """Salva un preventivo nel database - COMPATIBILITÀ ORIGINALE con nuovi campi"""
        return self.add_preventivo(preventivo_data)

    def add_preventivo(self, preventivo_data):
        """Aggiunge un nuovo preventivo originale con i nuovi campi"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO preventivi (
                    data_creazione, numero_revisione, preventivo_originale_id,
                    nome_cliente, numero_ordine, misura, descrizione, codice, finitura,
                    costo_totale_materiali, costi_accessori, minuti_taglio,
                    minuti_avvolgimento, minuti_pulizia, minuti_rettifica,
                    minuti_imballaggio, tot_mano_opera, subtotale,
                    maggiorazione_25, preventivo_finale, prezzo_cliente,
                    materiali_utilizzati, note_revisione, storico_modifiche
                ) VALUES (?, 1, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '[]')
            """, (
                datetime.now().isoformat(),
                preventivo_data.get('nome_cliente', ''),
                preventivo_data.get('numero_ordine', ''),
                preventivo_data.get('misura', ''),
                preventivo_data.get('descrizione', ''),
                preventivo_data.get('codice', ''),
                preventivo_data.get('finitura', ''),
                preventivo_data['costo_totale_materiali'],
                preventivo_data['costi_accessori'],
                preventivo_data['minuti_taglio'],
                preventivo_data['minuti_avvolgimento'],
                preventivo_data['minuti_pulizia'],
                preventivo_data['minuti_rettifica'],
                preventivo_data['minuti_imballaggio'],
                preventivo_data['tot_mano_opera'],
                preventivo_data['subtotale'],
                preventivo_data['maggiorazione_25'],
                preventivo_data['preventivo_finale'],
                preventivo_data['prezzo_cliente'],
                json.dumps(preventivo_data['materiali_utilizzati']),
                "",
            ))
            conn.commit()
            return cursor.lastrowid

    def update_preventivo(self, preventivo_id, preventivo_data):
        """AGGIORNATO: Aggiorna un preventivo esistente salvando snapshot nello storico"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 1. Prima di aggiornare, salva lo snapshot corrente nello storico
            cursor.execute("SELECT * FROM preventivi WHERE id = ?", (preventivo_id,))
            row = cursor.fetchone()

            if row:
                # Ottieni i nomi delle colonne
                cursor.execute("PRAGMA table_info(preventivi)")
                columns = [col[1] for col in cursor.fetchall()]

                # Crea dizionario con i dati attuali
                preventivo_attuale = dict(zip(columns, row))

                # Carica storico esistente
                storico_json = preventivo_attuale.get('storico_modifiche', '[]')
                try:
                    storico = json.loads(storico_json) if storico_json else []
                except (json.JSONDecodeError, TypeError):
                    storico = []

                # Crea snapshot
                snapshot = {
                    'timestamp': datetime.now().isoformat(),
                    'data': {
                        'nome_cliente': preventivo_attuale.get('nome_cliente', ''),
                        'numero_ordine': preventivo_attuale.get('numero_ordine', ''),
                        'misura': preventivo_attuale.get('misura', ''),
                        'descrizione': preventivo_attuale.get('descrizione', ''),
                        'codice': preventivo_attuale.get('codice', ''),
                        'costo_totale_materiali': preventivo_attuale.get('costo_totale_materiali', 0.0),
                        'costi_accessori': preventivo_attuale.get('costi_accessori', 0.0),
                        'minuti_taglio': preventivo_attuale.get('minuti_taglio', 0.0),
                        'minuti_avvolgimento': preventivo_attuale.get('minuti_avvolgimento', 0.0),
                        'minuti_pulizia': preventivo_attuale.get('minuti_pulizia', 0.0),
                        'minuti_rettifica': preventivo_attuale.get('minuti_rettifica', 0.0),
                        'minuti_imballaggio': preventivo_attuale.get('minuti_imballaggio', 0.0),
                        'tot_mano_opera': preventivo_attuale.get('tot_mano_opera', 0.0),
                        'subtotale': preventivo_attuale.get('subtotale', 0.0),
                        'maggiorazione_25': preventivo_attuale.get('maggiorazione_25', 0.0),
                        'preventivo_finale': preventivo_attuale.get('preventivo_finale', 0.0),
                        'prezzo_cliente': preventivo_attuale.get('prezzo_cliente', 0.0),
                        'materiali_utilizzati': preventivo_attuale.get('materiali_utilizzati', '[]')
                    }
                }

                # Aggiungi snapshot allo storico
                storico.append(snapshot)
                storico_aggiornato = json.dumps(storico)

                # 2. Ora aggiorna il preventivo con i nuovi dati
                cursor.execute("""
                    UPDATE preventivi SET
                        nome_cliente = ?, numero_ordine = ?, misura = ?, descrizione = ?, codice = ?, finitura = ?,
                        costo_totale_materiali = ?, costi_accessori = ?, minuti_taglio = ?,
                        minuti_avvolgimento = ?, minuti_pulizia = ?, minuti_rettifica = ?,
                        minuti_imballaggio = ?, tot_mano_opera = ?, subtotale = ?,
                        maggiorazione_25 = ?, preventivo_finale = ?, prezzo_cliente = ?,
                        materiali_utilizzati = ?, storico_modifiche = ?
                    WHERE id = ?
                """, (
                    preventivo_data.get('nome_cliente', ''),
                    preventivo_data.get('numero_ordine', ''),
                    preventivo_data.get('misura', ''),
                    preventivo_data.get('descrizione', ''),
                    preventivo_data.get('codice', ''),
                    preventivo_data.get('finitura', ''),
                    preventivo_data['costo_totale_materiali'],
                    preventivo_data['costi_accessori'],
                    preventivo_data['minuti_taglio'],
                    preventivo_data['minuti_avvolgimento'],
                    preventivo_data['minuti_pulizia'],
                    preventivo_data['minuti_rettifica'],
                    preventivo_data['minuti_imballaggio'],
                    preventivo_data['tot_mano_opera'],
                    preventivo_data['subtotale'],
                    preventivo_data['maggiorazione_25'],
                    preventivo_data['preventivo_finale'],
                    preventivo_data['prezzo_cliente'],
                    json.dumps(preventivo_data['materiali_utilizzati']),
                    storico_aggiornato,
                    preventivo_id
                ))
                conn.commit()
                return cursor.rowcount > 0

            return False

    def get_storico_modifiche(self, preventivo_id):
        """NUOVO: Ottiene lo storico modifiche di un preventivo"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT storico_modifiche FROM preventivi WHERE id = ?", (preventivo_id,))
            row = cursor.fetchone()

            if row and row[0]:
                try:
                    return json.loads(row[0])
                except (json.JSONDecodeError, TypeError):
                    return []
            return []

    def ripristina_versione_preventivo(self, preventivo_id, timestamp_versione):
        """NUOVO: Ripristina una versione precedente del preventivo"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Ottieni storico
            storico = self.get_storico_modifiche(preventivo_id)

            # Trova la versione da ripristinare
            versione_da_ripristinare = None
            for snapshot in storico:
                if snapshot['timestamp'] == timestamp_versione:
                    versione_da_ripristinare = snapshot['data']
                    break

            if not versione_da_ripristinare:
                return False

            # Prima salva la versione corrente nello storico (come in update_preventivo)
            cursor.execute("SELECT * FROM preventivi WHERE id = ?", (preventivo_id,))
            row = cursor.fetchone()

            if row:
                cursor.execute("PRAGMA table_info(preventivi)")
                columns = [col[1] for col in cursor.fetchall()]
                preventivo_attuale = dict(zip(columns, row))

                # Aggiungi snapshot corrente
                snapshot_corrente = {
                    'timestamp': datetime.now().isoformat(),
                    'data': {
                        'nome_cliente': preventivo_attuale.get('nome_cliente', ''),
                        'numero_ordine': preventivo_attuale.get('numero_ordine', ''),
                        'misura': preventivo_attuale.get('misura', ''),
                        'descrizione': preventivo_attuale.get('descrizione', ''),
                        'codice': preventivo_attuale.get('codice', ''),
                        'costo_totale_materiali': preventivo_attuale.get('costo_totale_materiali', 0.0),
                        'costi_accessori': preventivo_attuale.get('costi_accessori', 0.0),
                        'minuti_taglio': preventivo_attuale.get('minuti_taglio', 0.0),
                        'minuti_avvolgimento': preventivo_attuale.get('minuti_avvolgimento', 0.0),
                        'minuti_pulizia': preventivo_attuale.get('minuti_pulizia', 0.0),
                        'minuti_rettifica': preventivo_attuale.get('minuti_rettifica', 0.0),
                        'minuti_imballaggio': preventivo_attuale.get('minuti_imballaggio', 0.0),
                        'tot_mano_opera': preventivo_attuale.get('tot_mano_opera', 0.0),
                        'subtotale': preventivo_attuale.get('subtotale', 0.0),
                        'maggiorazione_25': preventivo_attuale.get('maggiorazione_25', 0.0),
                        'preventivo_finale': preventivo_attuale.get('preventivo_finale', 0.0),
                        'prezzo_cliente': preventivo_attuale.get('prezzo_cliente', 0.0),
                        'materiali_utilizzati': preventivo_attuale.get('materiali_utilizzati', '[]')
                    }
                }

                storico.append(snapshot_corrente)
                storico_aggiornato = json.dumps(storico)

                # Ripristina la versione selezionata
                cursor.execute("""
                    UPDATE preventivi SET
                        nome_cliente = ?, numero_ordine = ?, misura = ?, descrizione = ?, codice = ?,
                        costo_totale_materiali = ?, costi_accessori = ?, minuti_taglio = ?,
                        minuti_avvolgimento = ?, minuti_pulizia = ?, minuti_rettifica = ?,
                        minuti_imballaggio = ?, tot_mano_opera = ?, subtotale = ?,
                        maggiorazione_25 = ?, preventivo_finale = ?, prezzo_cliente = ?,
                        materiali_utilizzati = ?, storico_modifiche = ?
                    WHERE id = ?
                """, (
                    versione_da_ripristinare['nome_cliente'],
                    versione_da_ripristinare['numero_ordine'],
                    versione_da_ripristinare.get('misura', ''),
                    versione_da_ripristinare['descrizione'],
                    versione_da_ripristinare['codice'],
                    versione_da_ripristinare['costo_totale_materiali'],
                    versione_da_ripristinare['costi_accessori'],
                    versione_da_ripristinare['minuti_taglio'],
                    versione_da_ripristinare['minuti_avvolgimento'],
                    versione_da_ripristinare['minuti_pulizia'],
                    versione_da_ripristinare['minuti_rettifica'],
                    versione_da_ripristinare['minuti_imballaggio'],
                    versione_da_ripristinare['tot_mano_opera'],
                    versione_da_ripristinare['subtotale'],
                    versione_da_ripristinare['maggiorazione_25'],
                    versione_da_ripristinare['preventivo_finale'],
                    versione_da_ripristinare['prezzo_cliente'],
                    versione_da_ripristinare['materiali_utilizzati'],
                    storico_aggiornato,
                    preventivo_id
                ))
                conn.commit()
                return True

            return False

    def add_revisione_preventivo(self, preventivo_originale_id, preventivo_data, note_revisione=""):
        """NUOVO: Aggiunge una revisione a un preventivo esistente con i nuovi campi"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Trova il numero revisione successivo
            cursor.execute("""
                SELECT MAX(numero_revisione) FROM preventivi
                WHERE preventivo_originale_id = ? OR id = ?
            """, (preventivo_originale_id, preventivo_originale_id))

            max_revisione = cursor.fetchone()[0] or 1
            nuovo_numero_revisione = max_revisione + 1

            cursor.execute("""
                INSERT INTO preventivi (
                    data_creazione, numero_revisione, preventivo_originale_id,
                    nome_cliente, numero_ordine, misura, descrizione, codice, finitura,
                    costo_totale_materiali, costi_accessori, minuti_taglio,
                    minuti_avvolgimento, minuti_pulizia, minuti_rettifica,
                    minuti_imballaggio, tot_mano_opera, subtotale,
                    maggiorazione_25, preventivo_finale, prezzo_cliente,
                    materiali_utilizzati, note_revisione, storico_modifiche
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '[]')
            """, (
                datetime.now().isoformat(),
                nuovo_numero_revisione,
                preventivo_originale_id,
                preventivo_data.get('nome_cliente', ''),
                preventivo_data.get('numero_ordine', ''),
                preventivo_data.get('misura', ''),
                preventivo_data.get('descrizione', ''),
                preventivo_data.get('codice', ''),
                preventivo_data.get('finitura', ''),
                preventivo_data['costo_totale_materiali'],
                preventivo_data['costi_accessori'],
                preventivo_data['minuti_taglio'],
                preventivo_data['minuti_avvolgimento'],
                preventivo_data['minuti_pulizia'],
                preventivo_data['minuti_rettifica'],
                preventivo_data['minuti_imballaggio'],
                preventivo_data['tot_mano_opera'],
                preventivo_data['subtotale'],
                preventivo_data['maggiorazione_25'],
                preventivo_data['preventivo_finale'],
                preventivo_data['prezzo_cliente'],
                json.dumps(preventivo_data['materiali_utilizzati']),
                note_revisione,
            ))
            conn.commit()
            return cursor.lastrowid

    def get_all_preventivi(self):
        """Restituisce tutti i preventivi salvati - AGGIORNATO con nuovi campi"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, data_creazione, preventivo_finale, prezzo_cliente,
                           nome_cliente, numero_ordine, descrizione, codice, numero_revisione,
                           storico_modifiche
                    FROM preventivi ORDER BY data_creazione DESC
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in get_all_preventivi: {e}")
            return []

    def get_all_preventivi_latest(self):
        """NUOVO: Restituisce solo l'ultima revisione di ogni preventivo con i nuovi campi"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                WITH latest_preventivi AS (
                    SELECT
                        COALESCE(preventivo_originale_id, id) as gruppo_id,
                        MAX(numero_revisione) as max_revisione
                    FROM preventivi
                    GROUP BY COALESCE(preventivo_originale_id, id)
                )
                SELECT p.id, p.data_creazione, p.preventivo_finale, p.prezzo_cliente,
                       p.nome_cliente, p.numero_ordine, p.descrizione, p.codice,
                       p.numero_revisione,
                       CASE WHEN p.numero_revisione > 1 THEN 'R' ELSE 'O' END as tipo,
                       p.storico_modifiche
                FROM preventivi p
                INNER JOIN latest_preventivi lp ON
                    COALESCE(p.preventivo_originale_id, p.id) = lp.gruppo_id
                    AND p.numero_revisione = lp.max_revisione
                ORDER BY p.data_creazione DESC
            """)
            return cursor.fetchall()

    def get_preventivi_con_modifiche(self):
        """NUOVO: Restituisce solo i preventivi che hanno modifiche nello storico"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, data_creazione, preventivo_finale, prezzo_cliente,
                       nome_cliente, numero_ordine, descrizione, codice, numero_revisione,
                       storico_modifiche
                FROM preventivi
                WHERE storico_modifiche != '[]' AND storico_modifiche IS NOT NULL
                ORDER BY data_creazione DESC
            """)
            return cursor.fetchall()

    def get_preventivo_by_id(self, preventivo_id):
        """Restituisce un preventivo specifico con tutti i dettagli - AGGIORNATO"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM preventivi WHERE id = ?", (preventivo_id,))
                row = cursor.fetchone()
                if row:
                    # Converti il JSON dei materiali utilizzati
                    columns = [description[0] for description in cursor.description]
                    preventivo = dict(zip(columns, row))

                    # Gestisci compatibilità con vecchia struttura
                    materiali_json = preventivo.get('materiali_utilizzati', '[]')
                    if materiali_json:
                        try:
                            preventivo['materiali_utilizzati'] = json.loads(materiali_json)
                        except (json.JSONDecodeError, TypeError):
                            preventivo['materiali_utilizzati'] = []
                    else:
                        preventivo['materiali_utilizzati'] = []

                    # Assicurati che i nuovi campi esistano (compatibilità)
                    for campo in ['nome_cliente', 'numero_ordine', 'misura', 'descrizione', 'codice']:
                        if campo not in preventivo:
                            preventivo[campo] = ''

                    # Gestisci storico modifiche
                    storico_json = preventivo.get('storico_modifiche', '[]')
                    try:
                        preventivo['storico_modifiche'] = json.loads(storico_json) if storico_json else []
                    except (json.JSONDecodeError, TypeError):
                        preventivo['storico_modifiche'] = []

                    return preventivo
                return None
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in get_preventivo_by_id: {e}")
            return None

    def get_revisioni_preventivo(self, preventivo_originale_id):
        """NUOVO: Restituisce tutte le revisioni di un preventivo con i nuovi campi"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, data_creazione, preventivo_finale, prezzo_cliente,
                           nome_cliente, numero_ordine, descrizione, codice,
                           numero_revisione, note_revisione
                    FROM preventivi
                    WHERE preventivo_originale_id = ? OR id = ?
                    ORDER BY numero_revisione DESC
                """, (preventivo_originale_id, preventivo_originale_id))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in get_revisioni_preventivo: {e}")
            return []

    # =================== METODI FORNITORI ===================

    def get_fornitori_nomi_attivi(self):
        """Restituisce i nomi distinti dei fornitori che hanno almeno un materiale"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT fornitore_nome FROM materiale_fornitori ORDER BY fornitore_nome")
            return [row[0] for row in cursor.fetchall()]

    def get_materiali_ids_per_fornitore(self, fornitore_nome):
        """Restituisce gli id dei materiali che hanno un certo fornitore"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT materiale_id FROM materiale_fornitori WHERE fornitore_nome = ?", (fornitore_nome,))
            return {row[0] for row in cursor.fetchall()}

    def get_all_fornitori(self):
        """Restituisce tutti i fornitori"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM fornitori ORDER BY nome")
            return cursor.fetchall()

    def add_fornitore(self, nome):
        """Aggiunge un nuovo fornitore"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO fornitori (nome) VALUES (?)", (nome,))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return False

    def get_scorte_per_fornitore(self, nome_fornitore):
        """Restituisce le scorte dei materiali di un fornitore specifico.
        Considera sia il campo legacy materiali.fornitore sia la tabella materiale_fornitori."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT m.id, m.nome,
                    COALESCE(mf.giacenza, m.giacenza) as giacenza,
                    COALESCE(mf.scorta_massima, m.capacita_magazzino) as capacita_magazzino,
                    ? as fornitore,
                    COALESCE(mf.prezzo_fornitore, m.prezzo_fornitore) as prezzo_fornitore,
                    COALESCE(mf.scorta_minima, 0) as scorta_minima
                FROM materiali m
                LEFT JOIN materiale_fornitori mf
                    ON mf.materiale_id = m.id AND mf.fornitore_nome = ?
                WHERE m.fornitore = ? OR mf.fornitore_nome = ?
                ORDER BY m.nome
            """, (nome_fornitore, nome_fornitore, nome_fornitore, nome_fornitore))
            return cursor.fetchall()

    def rename_fornitore(self, old_nome, new_nome):
        """Rinomina un fornitore aggiornando anche tutti i materiali collegati"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE fornitori SET nome = ? WHERE nome = ?", (new_nome, old_nome))
                if cursor.rowcount == 0:
                    return False
                cursor.execute("UPDATE materiali SET fornitore = ? WHERE fornitore = ?", (new_nome, old_nome))
                cursor.execute("UPDATE materiale_fornitori SET fornitore_nome = ? WHERE fornitore_nome = ?", (new_nome, old_nome))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def assegna_materiali_a_fornitore(self, nome_fornitore, materiale_ids):
        """Assegna i materiali selezionati al fornitore (aggiorna campo fornitore)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for mat_id in materiale_ids:
                cursor.execute("UPDATE materiali SET fornitore = ? WHERE id = ?", (nome_fornitore, mat_id))
            conn.commit()

    def delete_preventivo_e_revisioni(self, preventivo_id):
        """Elimina un preventivo e tutte le sue revisioni se è l'originale,
        oppure solo la revisione se viene passato l'ID di una revisione."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Controlla se è un originale o una revisione
                cursor.execute("""
                    SELECT preventivo_originale_id
                    FROM preventivi WHERE id = ?
                """, (preventivo_id,))

                result = cursor.fetchone()
                if not result:
                    return False

                preventivo_originale_id = result[0]

                if preventivo_originale_id is None:
                    # È un originale: elimina originale + tutte le sue revisioni
                    cursor.execute("""
                        DELETE FROM preventivi
                        WHERE preventivo_originale_id = ? OR id = ?
                    """, (preventivo_id, preventivo_id))
                else:
                    # È una revisione: elimina solo questa revisione
                    cursor.execute("""
                        DELETE FROM preventivi WHERE id = ?
                    """, (preventivo_id,))

                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in delete_preventivo_e_revisioni: {e}")
            return False

    # =================== METODI CLIENTI ===================

    def get_all_clienti(self):
        """Restituisce tutti i clienti con conteggio preventivi, ordinati per nome"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.id, c.nome, COUNT(p.id) as n_preventivi
                    FROM clienti c
                    LEFT JOIN preventivi p ON p.nome_cliente = c.nome
                    GROUP BY c.id, c.nome
                    ORDER BY c.nome
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in get_all_clienti: {e}")
            return []

    def get_cliente_by_id(self, cliente_id):
        """Restituisce un cliente specifico tramite ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM clienti WHERE id = ?", (cliente_id,))
            return cursor.fetchone()

    def add_cliente(self, nome, email="", telefono="", note=""):
        """Aggiunge un nuovo cliente"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO clienti (nome) VALUES (?)", (nome,))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return False
            except sqlite3.Error as e:
                logging.getLogger('rcs').error(f"DB error in add_cliente: {e}")
                return False

    def update_cliente(self, cliente_id, nome, email="", telefono="", note=""):
        """Aggiorna un cliente esistente"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE clienti SET nome = ? WHERE id = ?", (nome, cliente_id))
                conn.commit()
                return cursor.rowcount > 0
            except sqlite3.IntegrityError:
                return False
            except sqlite3.Error as e:
                logging.getLogger('rcs').error(f"DB error in update_cliente: {e}")
                return False

    def delete_cliente(self, cliente_id):
        """Elimina un cliente"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM clienti WHERE id = ?", (cliente_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.getLogger('rcs').error(f"DB error in delete_cliente: {e}")
            return False
