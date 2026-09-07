#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test della logica delle Impostazioni di archiviazione: elenco delle copie,
lettura del contenuto e ripristino.

Il ripristino è l'operazione più delicata dell'applicazione (sovrascrive il
database in uso), quindi qui si verifica soprattutto che sia SEMPRE
reversibile e che non parta mai da una copia danneggiata.

Esegui con:  python -m unittest tests.test_archivio -v
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import archivio
from database import backup_manager as bm


def crea_db(percorso, preventivi=3, clienti=2):
    conn = sqlite3.connect(percorso)
    conn.execute("CREATE TABLE preventivi (id INTEGER PRIMARY KEY, data_creazione TEXT, nota TEXT)")
    conn.execute("CREATE TABLE clienti (id INTEGER PRIMARY KEY, nome TEXT)")
    conn.execute("CREATE TABLE materiali (id INTEGER PRIMARY KEY, nome TEXT)")
    conn.executemany("INSERT INTO preventivi (data_creazione, nota) VALUES (?, ?)",
                     [("2026-09-0{}T10:00:00".format(i % 9 + 1), "riga " * 40) for i in range(preventivi)])
    conn.executemany("INSERT INTO clienti (nome) VALUES (?)",
                     [("Cliente {}".format(i),) for i in range(clienti)])
    conn.commit()
    conn.close()
    return percorso


def corrompi(percorso):
    with open(percorso, "r+b") as f:
        f.seek(4096)
        f.write(b"\xff" * 4096)


class BaseArchivio(unittest.TestCase):
    def setUp(self):
        bm._esito_avvio_cache.clear()
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "materiali.db")
        self.backup_dir = os.path.join(self.tmp, "backup")
        os.makedirs(self.backup_dir, exist_ok=True)
        crea_db(self.db, preventivi=10, clienti=4)
        # niente mirror sul disco dell'ambiente di test
        self._orig_app = bm.cartella_app
        bm.cartella_app = lambda: self.tmp

    def tearDown(self):
        bm.cartella_app = self._orig_app
        bm._esito_avvio_cache.clear()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _crea_backup(self, quando=None, preventivi=5, cartella=None, prefisso=None):
        quando = quando or datetime.now()
        prefisso = prefisso or bm.PREFISSO_BACKUP
        cartella = cartella or self.backup_dir
        os.makedirs(cartella, exist_ok=True)
        nome = prefisso + quando.strftime(bm.FORMATO_TIMESTAMP) + ".db"
        percorso = os.path.join(cartella, nome)
        crea_db(percorso, preventivi=preventivi, clienti=2)
        return percorso


# ---------------------------------------------------------------------------
# Elenco e dettagli
# ---------------------------------------------------------------------------

class TestElencoBackup(BaseArchivio):

    def test_elenco_vuoto(self):
        self.assertEqual(archivio.elenco_backup(self.db), [])

    def test_ordine_dal_piu_recente(self):
        self._crea_backup(datetime.now() - timedelta(days=3))
        recente = self._crea_backup(datetime.now() - timedelta(hours=1))
        voci = archivio.elenco_backup(self.db)
        self.assertEqual(len(voci), 2)
        self.assertEqual(voci[0]["percorso"], recente)

    def test_riconosce_i_tipi_di_copia(self):
        self._crea_backup()
        self._crea_backup(cartella=os.path.join(self.backup_dir, "sicurezza"),
                          prefisso=bm.PREFISSO_SICUREZZA)
        self._crea_backup(cartella=os.path.join(self.backup_dir, "corrotti"),
                          prefisso=bm.PREFISSO_CORROTTO)
        tipi = {v["tipo"] for v in archivio.elenco_backup(self.db)}
        self.assertEqual(tipi, {"automatico", "protetto", "danneggiato"})

    def test_dettagli_contenuto(self):
        percorso = self._crea_backup(preventivi=7)
        dettagli = archivio.dettagli_backup(percorso)
        self.assertTrue(dettagli["integro"])
        self.assertEqual(dettagli["conteggi"]["preventivi"], 7)
        self.assertIn("7 preventivi", archivio.descrivi_contenuto(dettagli))

    def test_dettagli_copia_danneggiata(self):
        percorso = self._crea_backup()
        corrompi(percorso)
        dettagli = archivio.dettagli_backup(percorso)
        self.assertFalse(dettagli["integro"])
        self.assertIn("danneggiata", archivio.descrivi_contenuto(dettagli))


# ---------------------------------------------------------------------------
# Ripristino
# ---------------------------------------------------------------------------

class TestRipristino(BaseArchivio):

    def _conta_preventivi(self, percorso):
        conn = sqlite3.connect(percorso)
        try:
            return conn.execute("SELECT COUNT(*) FROM preventivi").fetchone()[0]
        finally:
            conn.close()

    def test_ripristino_riuscito(self):
        backup = self._crea_backup(preventivi=42)
        self.assertEqual(self._conta_preventivi(self.db), 10)

        riuscito, messaggio, copia = archivio.ripristina_backup(self.db, backup)

        self.assertTrue(riuscito, messaggio)
        self.assertEqual(self._conta_preventivi(self.db), 42,
                         "il database deve ora contenere i dati della copia")
        self.assertIn("42 preventivi", messaggio)

    def test_il_database_precedente_viene_conservato(self):
        """Il ripristino deve essere sempre reversibile."""
        backup = self._crea_backup(preventivi=42)
        _riuscito, _messaggio, copia = archivio.ripristina_backup(self.db, backup)

        self.assertIsNotNone(copia)
        self.assertTrue(os.path.exists(copia))
        self.assertEqual(self._conta_preventivi(copia), 10,
                         "la copia messa da parte deve contenere i dati di prima")

    def test_rifiuta_una_copia_danneggiata(self):
        backup = self._crea_backup(preventivi=42)
        corrompi(backup)

        riuscito, messaggio, copia = archivio.ripristina_backup(self.db, backup)

        self.assertFalse(riuscito)
        self.assertIn("danneggiata", messaggio)
        self.assertIsNone(copia, "non deve nemmeno iniziare")
        self.assertEqual(self._conta_preventivi(self.db), 10,
                         "il database in uso non deve essere stato toccato")

    def test_copia_inesistente(self):
        riuscito, messaggio, _copia = archivio.ripristina_backup(
            self.db, os.path.join(self.backup_dir, "non_esiste.db"))
        self.assertFalse(riuscito)
        self.assertIn("non esiste", messaggio)
        self.assertEqual(self._conta_preventivi(self.db), 10)

    def test_ripristino_su_database_gia_danneggiato(self):
        """Il caso reale: il database in uso è rotto e si ripristina una copia
        buona. Anche il file rotto va conservato: può contenere dati recenti."""
        backup = self._crea_backup(preventivi=42)
        corrompi(self.db)

        riuscito, _messaggio, copia = archivio.ripristina_backup(self.db, backup)

        self.assertTrue(riuscito)
        self.assertEqual(self._conta_preventivi(self.db), 42)
        self.assertTrue(os.path.exists(copia),
                        "anche il database danneggiato va conservato: "
                        "potrebbe contenere dati recuperabili")

    def test_torna_indietro_se_il_risultato_non_e_valido(self):
        """Se dopo il ripristino il database non è valido, deve tornare da solo
        alla situazione precedente."""
        backup = self._crea_backup(preventivi=42)

        # la copia passa la verifica iniziale, ma si rovina durante la copia
        originale_copy2 = shutil.copy2
        stato = {"chiamate": 0}

        def copy2_che_rovina(sorgente, destinazione, *a, **k):
            stato["chiamate"] += 1
            originale_copy2(sorgente, destinazione, *a, **k)
            # la seconda chiamata è quella che scrive sul database in uso
            if stato["chiamate"] == 2:
                corrompi(destinazione)

        shutil.copy2 = copy2_che_rovina
        try:
            riuscito, messaggio, copia = archivio.ripristina_backup(self.db, backup)
        finally:
            shutil.copy2 = originale_copy2

        self.assertFalse(riuscito)
        self.assertIn("rimesso al suo posto", messaggio)
        self.assertEqual(self._conta_preventivi(self.db), 10,
                         "deve essere tornato al database di prima")


# ---------------------------------------------------------------------------
# Riepilogo dello stato
# ---------------------------------------------------------------------------

class TestRiepilogoStato(BaseArchivio):

    def test_database_sano(self):
        self._crea_backup(datetime.now() - timedelta(days=2))
        self._crea_backup(datetime.now() - timedelta(hours=2))

        stato = archivio.riepilogo_stato(self.db)
        self.assertTrue(stato["integro"])
        self.assertEqual(stato["numero_backup"], 2)
        self.assertIsNotNone(stato["backup_piu_recente"])

    def test_database_danneggiato_segnalato(self):
        corrompi(self.db)
        stato = archivio.riepilogo_stato(self.db)
        self.assertFalse(stato["integro"])
        testo = archivio.testo_riepilogo(stato)
        self.assertIn("ATTENZIONE", testo)
        self.assertIn("danneggiato", testo)

    def test_le_copie_danneggiate_non_contano_come_backup(self):
        self._crea_backup()
        self._crea_backup(cartella=os.path.join(self.backup_dir, "corrotti"),
                          prefisso=bm.PREFISSO_CORROTTO)
        stato = archivio.riepilogo_stato(self.db)
        self.assertEqual(stato["numero_backup"], 1,
                         "una copia danneggiata non è un backup utilizzabile")
        self.assertEqual(stato["copie_danneggiate"], 1)

    def test_testo_comprensibile(self):
        self._crea_backup()
        testo = archivio.testo_riepilogo(archivio.riepilogo_stato(self.db))
        for atteso in ["DATABASE IN USO", "COPIE DI SICUREZZA",
                       "ULTIMO AVVIO", "ALTRI COMPUTER COLLEGATI ADESSO"]:
            self.assertIn(atteso, testo)
        self.assertIn("nessun problema rilevato", testo)

    def test_segnala_altri_pc_collegati(self):
        bm._scrivi_sessioni(bm._percorso_sessioni(self.db), {
            "PC-UFFICIO|mario": {"avvio": datetime.now().isoformat(timespec="seconds")},
        })
        stato = archivio.riepilogo_stato(self.db)
        self.assertIn("PC-UFFICIO|mario", stato["altri_pc"])
        self.assertIn("PC-UFFICIO", archivio.testo_riepilogo(stato))


if __name__ == "__main__":
    unittest.main(verbosity=2)
