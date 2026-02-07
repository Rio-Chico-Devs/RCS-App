#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Database Manager per Sistema Preventivi RCS con Sistema di Versioning
Uso riservato esclusivamente a RCS
"""

import sqlite3
import os
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="data/materiali.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()

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
            ("storico_modifiche", "TEXT DEFAULT '[]'")
        ]

        for column_name, column_def in new_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE preventivi ADD COLUMN {column_name} {column_def}")
                    print(f"Aggiunta colonna {column_name} alla tabella preventivi")
                except sqlite3.OperationalError as e:
                    print(f"Errore durante l'aggiunta della colonna {column_name}: {e}")

    # =================== METODI MATERIALI (IDENTICI ALL'ORIGINALE) ===================

    def get_all_materiali(self):
        """Restituisce tutti i materiali disponibili"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, spessore, prezzo FROM materiali ORDER BY nome")
            return cursor.fetchall()

    def get_materiale_by_id(self, materiale_id):
        """Restituisce un materiale specifico tramite ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, spessore, prezzo FROM materiali WHERE id = ?", (materiale_id,))
            return cursor.fetchone()

    def get_materiale_by_nome(self, nome):
        """Restituisce un materiale specifico tramite nome - AGGIUNTO per compatibilità"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, spessore, prezzo FROM materiali WHERE nome = ?", (nome,))
            return cursor.fetchone()

    def add_materiale(self, nome, spessore, prezzo):
        """Aggiunge un nuovo materiale"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO materiali (nome, spessore, prezzo) VALUES (?, ?, ?)",
                    (nome, spessore, prezzo)
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return False

    def update_materiale(self, materiale_id, nome, spessore, prezzo):
        """Aggiorna un materiale esistente - AGGIUNTO per gestione materiali"""
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

    def update_prezzo_materiale(self, materiale_id, nuovo_prezzo):
        """Aggiorna solo il prezzo di un materiale - AGGIUNTO per aggiornamenti prezzi"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE materiali SET prezzo = ? WHERE id = ?",
                (nuovo_prezzo, materiale_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_materiale(self, materiale_id):
        """Elimina un materiale - AGGIUNTO per gestione materiali"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM materiali WHERE id = ?", (materiale_id,))
            conn.commit()
            return cursor.rowcount > 0

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
                    nome_cliente, numero_ordine, misura, descrizione, codice,
                    costo_totale_materiali, costi_accessori, minuti_taglio,
                    minuti_avvolgimento, minuti_pulizia, minuti_rettifica,
                    minuti_imballaggio, tot_mano_opera, subtotale,
                    maggiorazione_25, preventivo_finale, prezzo_cliente,
                    materiali_utilizzati, note_revisione, storico_modifiche
                ) VALUES (?, 1, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '[]')
            """, (
                datetime.now().isoformat(),
                preventivo_data.get('nome_cliente', ''),
                preventivo_data.get('numero_ordine', ''),
                preventivo_data.get('misura', ''),
                preventivo_data.get('descrizione', ''),
                preventivo_data.get('codice', ''),
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
                ""
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
                        nome_cliente = ?, numero_ordine = ?, misura = ?, descrizione = ?, codice = ?,
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
                    nome_cliente, numero_ordine, misura, descrizione, codice,
                    costo_totale_materiali, costi_accessori, minuti_taglio,
                    minuti_avvolgimento, minuti_pulizia, minuti_rettifica,
                    minuti_imballaggio, tot_mano_opera, subtotale,
                    maggiorazione_25, preventivo_finale, prezzo_cliente,
                    materiali_utilizzati, note_revisione, storico_modifiche
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '[]')
            """, (
                datetime.now().isoformat(),
                nuovo_numero_revisione,
                preventivo_originale_id,
                preventivo_data.get('nome_cliente', ''),
                preventivo_data.get('numero_ordine', ''),
                preventivo_data.get('misura', ''),
                preventivo_data.get('descrizione', ''),
                preventivo_data.get('codice', ''),
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
                note_revisione
            ))
            conn.commit()
            return cursor.lastrowid

    def get_all_preventivi(self):
        """Restituisce tutti i preventivi salvati - AGGIORNATO con nuovi campi"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, data_creazione, preventivo_finale, prezzo_cliente,
                       nome_cliente, numero_ordine, descrizione, codice, numero_revisione,
                       storico_modifiche
                FROM preventivi ORDER BY data_creazione DESC
            """)
            return cursor.fetchall()

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

    def get_revisioni_preventivo(self, preventivo_originale_id):
        """NUOVO: Restituisce tutte le revisioni di un preventivo con i nuovi campi"""
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

    def delete_preventivo_e_revisioni(self, preventivo_id):
        """NUOVO: Elimina un preventivo e tutte le sue revisioni"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Trova l'ID originale del preventivo
            cursor.execute("""
                SELECT COALESCE(preventivo_originale_id, id) as gruppo_id
                FROM preventivi WHERE id = ?
            """, (preventivo_id,))

            result = cursor.fetchone()
            if not result:
                return False

            gruppo_id = result[0]

            # Elimina tutte le revisioni del gruppo
            cursor.execute("""
                DELETE FROM preventivi
                WHERE preventivo_originale_id = ? OR id = ?
            """, (gruppo_id, gruppo_id))

            conn.commit()
            return cursor.rowcount > 0
