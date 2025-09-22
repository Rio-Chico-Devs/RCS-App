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
            
            # Tabella preventivi - AGGIORNATA con colonne per revisioni
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preventivi (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_creazione TEXT NOT NULL,
                    numero_revisione INTEGER NOT NULL DEFAULT 1,
                    preventivo_originale_id INTEGER,
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
                    FOREIGN KEY (preventivo_originale_id) REFERENCES preventivi(id)
                )
            """)
            
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
    
    # =================== METODI PREVENTIVI (ORIGINALI + REVISIONI) ===================
    
    def save_preventivo(self, preventivo_data):
        """Salva un preventivo nel database - COMPATIBILITÀ ORIGINALE"""
        return self.add_preventivo(preventivo_data)
    
    def add_preventivo(self, preventivo_data):
        """Aggiunge un nuovo preventivo originale"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO preventivi (
                    data_creazione, numero_revisione, preventivo_originale_id,
                    costo_totale_materiali, costi_accessori, minuti_taglio,
                    minuti_avvolgimento, minuti_pulizia, minuti_rettifica,
                    minuti_imballaggio, tot_mano_opera, subtotale,
                    maggiorazione_25, preventivo_finale, prezzo_cliente,
                    materiali_utilizzati, note_revisione
                ) VALUES (?, 1, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
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
    
    def add_revisione_preventivo(self, preventivo_originale_id, preventivo_data, note_revisione=""):
        """NUOVO: Aggiunge una revisione a un preventivo esistente"""
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
                    costo_totale_materiali, costi_accessori, minuti_taglio,
                    minuti_avvolgimento, minuti_pulizia, minuti_rettifica,
                    minuti_imballaggio, tot_mano_opera, subtotale,
                    maggiorazione_25, preventivo_finale, prezzo_cliente,
                    materiali_utilizzati, note_revisione
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                nuovo_numero_revisione,
                preventivo_originale_id,
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
        """Restituisce tutti i preventivi salvati - COMPATIBILITÀ ORIGINALE"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, data_creazione, preventivo_finale, prezzo_cliente
                FROM preventivi ORDER BY data_creazione DESC
            """)
            return cursor.fetchall()
    
    def get_all_preventivi_latest(self):
        """NUOVO: Restituisce solo l'ultima revisione di ogni preventivo"""
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
                SELECT p.* FROM preventivi p
                INNER JOIN latest_preventivi lp ON 
                    COALESCE(p.preventivo_originale_id, p.id) = lp.gruppo_id 
                    AND p.numero_revisione = lp.max_revisione
                ORDER BY p.data_creazione DESC
            """)
            return cursor.fetchall()
    
    def get_preventivo_by_id(self, preventivo_id):
        """Restituisce un preventivo specifico con tutti i dettagli - COMPATIBILITÀ ORIGINALE"""
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
                
                return preventivo
            return None
    
    def get_revisioni_preventivo(self, preventivo_originale_id):
        """NUOVO: Restituisce tutte le revisioni di un preventivo"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM preventivi 
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