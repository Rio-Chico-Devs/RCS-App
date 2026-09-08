#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test dei percorsi di rete di Windows.

Il database dell'azienda sta su una cartella condivisa, quindi il percorso puo'
essere della forma '\\\\NOMEPC\\RCS\\materiali.db' oppure 'Z:\\RCS\\materiali.db'.

Tradotto ingenuamente, il primo diventa 'file://NOMEPC/RCS/materiali.db' e
SQLite lo RIFIUTA, perche' legge 'NOMEPC' come nome di host
("invalid uri authority"). Dove non c'era un ripiego, ogni copia di backup
sarebbe risultata "danneggiata" e il ripristino impossibile.

Esegui con:  python -m unittest tests.test_percorsi_rete -v
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import archivio
from database import backup_manager as bm


class TestIndirizzoSolaLettura(unittest.TestCase):

    def test_percorso_windows_normale(self):
        self.assertEqual(bm.uri_sola_lettura(r"C:\RCS\materiali.db"),
                         "file:C:/RCS/materiali.db?mode=ro")

    def test_unita_di_rete_mappata(self):
        self.assertEqual(bm.uri_sola_lettura(r"Z:\RCS\materiali.db"),
                         "file:Z:/RCS/materiali.db?mode=ro")

    def test_percorso_di_rete_con_barre_rovesciate(self):
        """La forma che SQLite rifiutava."""
        indirizzo = bm.uri_sola_lettura(r"\\NOMEPC\RCS\materiali.db")
        self.assertEqual(indirizzo, "file:////NOMEPC/RCS/materiali.db?mode=ro")
        self.assertNotEqual(indirizzo, "file://NOMEPC/RCS/materiali.db?mode=ro")

    def test_percorso_di_rete_con_barre_normali(self):
        """E' la forma suggerita dal messaggio del Cruscotto."""
        indirizzo = bm.uri_sola_lettura("//NOMEPC/RCS/materiali.db")
        self.assertEqual(indirizzo, "file:////NOMEPC/RCS/materiali.db?mode=ro")

    def test_sqlite_accetta_la_forma_corretta_e_rifiuta_quella_sbagliata(self):
        """Verifica sul motore vero, non solo sulla stringa."""
        tmp = tempfile.mkdtemp()
        try:
            db = os.path.join(tmp, "materiali.db")
            sqlite3.connect(db).execute("CREATE TABLE preventivi (id INTEGER)")

            # forma sbagliata: nome di computer letto come host
            with self.assertRaises(sqlite3.OperationalError) as contesto:
                sqlite3.connect("file://NOMEPC/qualcosa.db?mode=ro",
                                uri=True).execute("SELECT 1")
            self.assertIn("authority", str(contesto.exception).lower())

            # forma corretta: host vuoto, il percorso viene usato tale e quale
            conn = sqlite3.connect(bm.uri_sola_lettura(db), uri=True)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM preventivi").fetchone()[0], 0)
            conn.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_resta_in_sola_lettura(self):
        """L'indirizzo deve continuare a impedire le scritture."""
        tmp = tempfile.mkdtemp()
        try:
            db = os.path.join(tmp, "materiali.db")
            sqlite3.connect(db).execute("CREATE TABLE preventivi (id INTEGER)")
            conn = sqlite3.connect(bm.uri_sola_lettura(db), uri=True)
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute("INSERT INTO preventivi (id) VALUES (1)")
            conn.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestRipiegoDettagliBackup(unittest.TestCase):
    """Se l'indirizzo in sola lettura non fosse utilizzabile, la copia NON deve
    essere dichiarata danneggiata: si legge comunque."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.copia = os.path.join(self.tmp, "materiali_backup_20260101_120000.db")
        conn = sqlite3.connect(self.copia)
        conn.execute("CREATE TABLE preventivi (id INTEGER PRIMARY KEY, data_creazione TEXT)")
        conn.execute("CREATE TABLE clienti (id INTEGER PRIMARY KEY, nome TEXT)")
        conn.executemany("INSERT INTO preventivi (data_creazione) VALUES (?)",
                         [("2026-01-0%d" % (i + 1),) for i in range(5)])
        conn.execute("INSERT INTO clienti (nome) VALUES ('Prova')")
        conn.commit()
        conn.close()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_lettura_normale(self):
        dettagli = archivio.dettagli_backup(self.copia)
        self.assertTrue(dettagli["integro"])
        self.assertEqual(dettagli["conteggi"]["preventivi"], 5)

    def test_se_lindirizzo_fallisce_si_legge_lo_stesso(self):
        """Simula un indirizzo non utilizzabile (come succedeva sui percorsi
        di rete): la copia deve comunque risultare leggibile e integra."""
        originale = bm.uri_sola_lettura
        bm.uri_sola_lettura = lambda p: "file://HOST-NON-VALIDO/x.db?mode=ro"
        try:
            dettagli = archivio.dettagli_backup(self.copia)
        finally:
            bm.uri_sola_lettura = originale

        self.assertTrue(dettagli["integro"],
                        "senza ripiego ogni copia risulterebbe danneggiata "
                        "e il ripristino sarebbe impossibile")
        self.assertEqual(dettagli["conteggi"]["preventivi"], 5)
        self.assertIn("5 preventivi", archivio.descrivi_contenuto(dettagli))


class TestCruscottoPercorsiRete(unittest.TestCase):
    """Lo stesso difetto era nel Cruscotto, che apre il database di rete in
    sola lettura ed e' il caso d'uso per cui e' nato."""

    def setUp(self):
        sys.path.insert(0, os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "CruscottoAziendale"))

    def test_indirizzo_di_rete(self):
        import config_db
        self.assertEqual(config_db.uri_sola_lettura("//NOMEPC/RCS/materiali.db"),
                         "file:////NOMEPC/RCS/materiali.db?mode=ro")
        self.assertEqual(config_db.uri_sola_lettura(r"\\NOMEPC\RCS\materiali.db"),
                         "file:////NOMEPC/RCS/materiali.db?mode=ro")

    def test_apertura_reale(self):
        import config_db
        tmp = tempfile.mkdtemp()
        try:
            db = os.path.join(tmp, "materiali.db")
            conn = sqlite3.connect(db)
            conn.execute("CREATE TABLE preventivi (id INTEGER)")
            conn.commit()
            conn.close()

            self.assertTrue(config_db.database_valido(db))
            aperto = config_db.apri_db_sola_lettura(db)
            self.assertEqual(
                aperto.execute("SELECT COUNT(*) FROM preventivi").fetchone()[0], 0)
            aperto.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
