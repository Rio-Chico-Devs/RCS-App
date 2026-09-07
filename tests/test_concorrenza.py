#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del comportamento quando due computer scrivono sul database nello stesso
momento (situazione normale con il database su cartella di rete condivisa).

Esegui con:  python -m unittest tests.test_concorrenza -v
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import backup_manager as bm
from database import db_manager as dbm
from database.db_manager import DatabaseManager, DatabaseOccupato


def _dati_preventivo():
    return {
        'nome_cliente': 'Prova', 'numero_ordine': '1', 'misura': 'x',
        'descrizione': 'd', 'codice': 'c', 'finitura': 'f',
        'costo_totale_materiali': 1.0, 'costi_accessori': 1.0,
        'minuti_taglio': 1.0, 'minuti_avvolgimento': 1.0, 'minuti_pulizia': 1.0,
        'minuti_rettifica': 1.0, 'minuti_imballaggio': 1.0, 'tot_mano_opera': 1.0,
        'subtotale': 1.0, 'maggiorazione_25': 1.0, 'preventivo_finale': 1.0,
        'prezzo_cliente': 1.0, 'materiali_utilizzati': [],
    }


class BaseDb(unittest.TestCase):
    def setUp(self):
        bm._esito_avvio_cache.clear()
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "materiali.db")
        self.gestore = DatabaseManager(db_path=self.db)

    def tearDown(self):
        bm._esito_avvio_cache.clear()
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestAttesaConfigurata(BaseDb):

    def test_timeout_piu_lungo_del_predefinito(self):
        """Il valore della libreria (5 s) è troppo basso su cartella di rete."""
        self.assertGreater(dbm.TIMEOUT_CONNESSIONE, 5.0)

    def test_connessione_usa_il_timeout(self):
        conn = self.gestore._connessione()
        try:
            self.assertIsInstance(conn, sqlite3.Connection)
        finally:
            conn.close()


class TestRiprovaSeOccupato(BaseDb):

    def test_salvataggio_riesce_dopo_una_attesa_breve(self):
        """Un altro computer tiene occupato il database per un istante: il
        salvataggio deve riuscire da solo, senza disturbare l'utente."""
        # check_same_thread=False: il blocco viene rilasciato da un altro thread,
        # che è proprio ciò che simula "l'altro computer ha finito di salvare".
        blocco = sqlite3.connect(self.db, check_same_thread=False)
        blocco.execute("BEGIN EXCLUSIVE")

        def rilascia_dopo_poco():
            time.sleep(0.4)
            blocco.rollback()
            blocco.close()

        threading.Thread(target=rilascia_dopo_poco, daemon=True).start()

        # timeout basso per non far attendere il test: deve comunque riuscire
        originale = dbm.TIMEOUT_CONNESSIONE
        dbm.TIMEOUT_CONNESSIONE = 0.1
        try:
            nuovo_id = self.gestore.add_preventivo(_dati_preventivo())
        finally:
            dbm.TIMEOUT_CONNESSIONE = originale

        self.assertIsNotNone(nuovo_id, "il salvataggio deve riuscire dopo l'attesa")
        self.assertEqual(len(self.gestore.get_all_preventivi()), 1)

    def test_errore_comprensibile_se_resta_occupato(self):
        """Se il database resta occupato, l'utente deve leggere un messaggio in
        italiano, non un errore tecnico."""
        blocco = sqlite3.connect(self.db)
        blocco.execute("BEGIN EXCLUSIVE")

        originale_timeout = dbm.TIMEOUT_CONNESSIONE
        originale_attesa = dbm.ATTESA_TRA_TENTATIVI
        dbm.TIMEOUT_CONNESSIONE = 0.05
        dbm.ATTESA_TRA_TENTATIVI = 0.01
        try:
            with self.assertRaises(DatabaseOccupato) as contesto:
                self.gestore.add_preventivo(_dati_preventivo())
        finally:
            dbm.TIMEOUT_CONNESSIONE = originale_timeout
            dbm.ATTESA_TRA_TENTATIVI = originale_attesa
            blocco.rollback()
            blocco.close()

        messaggio = str(contesto.exception)
        self.assertIn("Un altro computer sta salvando", messaggio)
        self.assertIn("non sono andati persi", messaggio)
        self.assertNotIn("locked", messaggio.lower(),
                         "niente gergo tecnico nel messaggio all'utente")

    def test_gli_altri_errori_non_vengono_ritentati(self):
        """Un errore diverso dal 'database occupato' deve emergere subito."""
        def esplode(*_a, **_k):
            raise sqlite3.OperationalError("no such table: preventivi")

        originale = self.gestore._connessione
        self.gestore._connessione = esplode
        try:
            with self.assertRaises(sqlite3.OperationalError) as contesto:
                self.gestore.add_preventivo(_dati_preventivo())
            self.assertIn("no such table", str(contesto.exception))
        finally:
            self.gestore._connessione = originale

    def test_conflitto_registrato_nel_diario(self):
        """Ogni conflitto va annotato: serve a sapere quanto spesso capita."""
        annotazioni = []
        from utils import diagnostica
        originale = diagnostica.registra_scrittura
        diagnostica.registra_scrittura = lambda *a, **k: annotazioni.append(a)

        blocco = sqlite3.connect(self.db)
        blocco.execute("BEGIN EXCLUSIVE")
        originale_timeout = dbm.TIMEOUT_CONNESSIONE
        originale_attesa = dbm.ATTESA_TRA_TENTATIVI
        dbm.TIMEOUT_CONNESSIONE = 0.05
        dbm.ATTESA_TRA_TENTATIVI = 0.01
        try:
            with self.assertRaises(DatabaseOccupato):
                self.gestore.add_preventivo(_dati_preventivo())
        finally:
            dbm.TIMEOUT_CONNESSIONE = originale_timeout
            dbm.ATTESA_TRA_TENTATIVI = originale_attesa
            diagnostica.registra_scrittura = originale
            blocco.rollback()
            blocco.close()

        self.assertTrue(annotazioni, "il conflitto deve finire nel registro")
        testo = " ".join(str(a) for a in annotazioni)
        self.assertIn("add_preventivo", testo)
        self.assertIn("occupato", testo)

    def test_nessun_doppio_inserimento_dopo_i_tentativi(self):
        """Ritentare non deve creare preventivi duplicati."""
        # check_same_thread=False: il blocco viene rilasciato da un altro thread,
        # che è proprio ciò che simula "l'altro computer ha finito di salvare".
        blocco = sqlite3.connect(self.db, check_same_thread=False)
        blocco.execute("BEGIN EXCLUSIVE")

        def rilascia():
            time.sleep(0.3)
            blocco.rollback()
            blocco.close()

        threading.Thread(target=rilascia, daemon=True).start()
        originale = dbm.TIMEOUT_CONNESSIONE
        dbm.TIMEOUT_CONNESSIONE = 0.1
        try:
            self.gestore.add_preventivo(_dati_preventivo())
        finally:
            dbm.TIMEOUT_CONNESSIONE = originale

        self.assertEqual(len(self.gestore.get_all_preventivi()), 1,
                         "deve esserci un solo preventivo, non uno per tentativo")


if __name__ == "__main__":
    unittest.main(verbosity=2)
