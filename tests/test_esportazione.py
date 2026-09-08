#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test dell'esportazione dei dati e della segnalazione tecnica.

L'esportazione e' la rete di sicurezza di ultima istanza: i backup sono copie
del database e si aprono solo con questo programma, mentre i file CSV si
leggono con Excel anche fra dieci anni, senza il gestionale.

Esegui con:  python -m unittest tests.test_esportazione -v
"""

import csv
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import backup_manager as bm
from database import esportazione
from database.db_manager import DatabaseManager
from utils import segnalazione


def preventivo(indice, cliente="Bianchi SpA"):
    return {
        'nome_cliente': cliente, 'numero_ordine': f'ORD-{indice}',
        'misura': '1200 mm', 'descrizione': 'Tubo carbonio', 'codice': f'TC-{indice}',
        'finitura': 'Lucida', 'costo_totale_materiali': 100.0, 'costi_accessori': 10.0,
        'minuti_taglio': 15.0, 'minuti_avvolgimento': 40.0, 'minuti_pulizia': 10.0,
        'minuti_rettifica': 5.0, 'minuti_imballaggio': 8.0, 'tot_mano_opera': 78.0,
        'subtotale': 188.0, 'maggiorazione_25': 47.0, 'preventivo_finale': 235.0,
        'prezzo_cliente': 300.0, 'materiali_utilizzati': [{'materiale_nome': 'Fibra'}],
    }


class BaseEsportazione(unittest.TestCase):
    def setUp(self):
        bm._esito_avvio_cache.clear()
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "materiali.db")
        self._orig_app = bm.cartella_app
        bm.cartella_app = lambda: self.tmp
        self.gestore = DatabaseManager(db_path=self.db)

    def tearDown(self):
        bm.cartella_app = self._orig_app
        bm._esito_avvio_cache.clear()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _leggi_csv(self, percorso):
        with open(percorso, encoding=esportazione.CODIFICA, newline="") as f:
            return list(csv.reader(f, delimiter=esportazione.SEPARATORE))


class TestEsportazione(BaseEsportazione):

    def test_crea_un_file_per_tabella(self):
        self.gestore.add_preventivo(preventivo(1))
        cartella, conteggi = esportazione.esporta(self.db)

        self.assertTrue(os.path.isdir(cartella))
        file_creati = sorted(os.listdir(cartella))
        self.assertIn("Preventivi.csv", file_creati)
        self.assertIn("Clienti.csv", file_creati)
        self.assertIn("Materiali.csv", file_creati)
        self.assertIn("LEGGIMI.txt", file_creati)
        self.assertEqual(conteggi["preventivi"], 1)

    def test_il_contenuto_e_corretto(self):
        self.gestore.add_preventivo(preventivo(7, "Verdi Srl"))
        cartella, _c = esportazione.esporta(self.db)

        righe = self._leggi_csv(os.path.join(cartella, "Preventivi.csv"))
        intestazioni, dati = righe[0], righe[1:]
        self.assertIn("nome_cliente", intestazioni)
        self.assertIn("prezzo_cliente", intestazioni)
        self.assertEqual(len(dati), 1)

        colonna = intestazioni.index("nome_cliente")
        self.assertEqual(dati[0][colonna], "Verdi Srl")

    def test_gli_accenti_restano_leggibili(self):
        """Excel deve mostrare 'Società' e non caratteri strani."""
        self.gestore.add_preventivo(preventivo(1, "Società Àèìòù & Figli"))
        cartella, _c = esportazione.esporta(self.db)

        percorso = os.path.join(cartella, "Preventivi.csv")
        with open(percorso, "rb") as f:
            self.assertTrue(f.read(3) == b"\xef\xbb\xbf",
                            "manca il contrassegno che Excel usa per gli accenti")

        righe = self._leggi_csv(percorso)
        colonna = righe[0].index("nome_cliente")
        self.assertEqual(righe[1][colonna], "Società Àèìòù & Figli")

    def test_separatore_adatto_a_excel_italiano(self):
        self.gestore.add_preventivo(preventivo(1))
        cartella, _c = esportazione.esporta(self.db)
        with open(os.path.join(cartella, "Preventivi.csv"),
                  encoding=esportazione.CODIFICA) as f:
            prima_riga = f.readline()
        self.assertIn(";", prima_riga)

    def test_database_vuoto_non_e_un_errore(self):
        cartella, conteggi = esportazione.esporta(self.db)
        self.assertTrue(os.path.isdir(cartella))
        self.assertEqual(conteggi.get("preventivi"), 0)

    def test_i_valori_assenti_diventano_celle_vuote(self):
        """Le celle vuote sono corrette; la parola 'None' nel foglio no."""
        self.gestore.add_preventivo(preventivo(1))
        cartella, _c = esportazione.esporta(self.db)
        righe = self._leggi_csv(os.path.join(cartella, "Preventivi.csv"))
        for riga in righe[1:]:
            self.assertNotIn("None", riga)

    def test_il_leggimi_spiega_il_contenuto(self):
        self.gestore.add_preventivo(preventivo(1))
        cartella, _c = esportazione.esporta(self.db)
        with open(os.path.join(cartella, "LEGGIMI.txt"), encoding="utf-8") as f:
            testo = f.read()
        self.assertIn("Excel", testo)
        self.assertIn("Preventivi.csv", testo)


class TestEsportazionePeriodica(BaseEsportazione):

    def test_la_prima_volta_serve_sempre(self):
        self.assertTrue(esportazione.serve_esportazione(self.db))

    def test_non_si_ripete_subito(self):
        esportazione.esporta(self.db)
        self.assertFalse(esportazione.serve_esportazione(self.db),
                         "non deve rifarla a ogni apertura del programma")

    def test_si_ripete_dopo_un_mese(self):
        cartella = esportazione.cartella_esportazioni(self.db)
        vecchia = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d_%H%M")
        os.makedirs(os.path.join(cartella, vecchia), exist_ok=True)
        self.assertTrue(esportazione.serve_esportazione(self.db))

    def test_esporta_se_serve_non_solleva_mai_eccezioni(self):
        esito = esportazione.esporta_se_serve("/percorso/inesistente/x.db")
        self.assertIsNone(esito)

    def test_avvio_del_programma_produce_lesportazione(self):
        """All'avvio, se e' passato il tempo, l'esportazione parte da sola."""
        self.gestore.add_preventivo(preventivo(1))
        bm._esito_avvio_cache.clear()
        DatabaseManager(db_path=self.db)

        cartella = esportazione.cartella_esportazioni(self.db)
        self.assertTrue(os.path.isdir(cartella),
                        "l'esportazione automatica deve essere partita")
        self.assertTrue(os.listdir(cartella))


class TestSegnalazione(BaseEsportazione):

    def test_crea_il_pacchetto(self):
        self.gestore.add_preventivo(preventivo(1))
        percorso = segnalazione.prepara(self.db, os.path.join(self.tmp, "s.zip"))
        self.assertTrue(os.path.exists(percorso))

        with zipfile.ZipFile(percorso) as z:
            nomi = z.namelist()
            self.assertIn("informazioni.json", nomi)
            self.assertIn("backup_presenti.json", nomi)
            self.assertIn("LEGGIMI.txt", nomi)

    def test_non_contiene_dati_aziendali(self):
        """Il punto piu' importante: si invia all'assistenza, quindi non deve
        contenere il database né i nomi dei clienti."""
        self.gestore.add_preventivo(preventivo(1, "Bianchi SpA Riservato"))
        percorso = segnalazione.prepara(self.db, os.path.join(self.tmp, "s.zip"))

        with zipfile.ZipFile(percorso) as z:
            for nome in z.namelist():
                self.assertFalse(nome.endswith(".db"),
                                 f"il pacchetto non deve contenere database: {nome}")
                contenuto = z.read(nome).decode("utf-8", "replace")
                self.assertNotIn("Bianchi SpA Riservato", contenuto,
                                 f"nome cliente trovato dentro {nome}")

    def test_contiene_le_informazioni_utili(self):
        percorso = segnalazione.prepara(self.db, os.path.join(self.tmp, "s.zip"))
        import json
        with zipfile.ZipFile(percorso) as z:
            info = json.loads(z.read("informazioni.json"))
        for chiave in ("computer", "sistema", "percorso_database",
                       "database_su_rete", "integrita"):
            self.assertIn(chiave, info)
        self.assertTrue(info["integrita"]["integro"])

    def test_funziona_anche_senza_registri(self):
        percorso = segnalazione.prepara(self.db, os.path.join(self.tmp, "s.zip"))
        self.assertTrue(zipfile.is_zipfile(percorso))


if __name__ == "__main__":
    unittest.main(verbosity=2)
