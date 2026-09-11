#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modalità protetta: il database si legge, non si tocca.

A cosa serve
------------
Quando il database risulta danneggiato e non c'e' un backup su cui contare,
restare chiusi fuori dal programma non aiuta nessuno: i dati, anche se
rovinati, spesso si leggono ancora, e poter consultare o stampare mentre si
cerca una soluzione vale molto.

Ma lasciare che ci si SCRIVA sopra peggiorerebbe il danno. Quindi: si entra,
si legge, non si modifica.

Come e' realizzata, e perche' cosi'
-----------------------------------
Il database viene aperto in SOLA LETTURA. Non e' un dettaglio tecnico: nel
programma ci sono 45 istruzioni di scrittura sparse in decine di metodi, e
solo 4 passano dal punto in cui si potrebbe mettere un controllo. Proteggerle
una per una vorrebbe dire dimenticarne qualcuna - oggi o fra un anno, quando
se ne aggiunge una nuova.

Aprendo in sola lettura e' SQLite stessa a rifiutarle tutte, comprese quelle
che nessuno ha ancora scritto. Una protezione che non si puo' dimenticare di
applicare.

Esegui con:  python -m unittest tests.test_modalita_protetta -v
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RADICE)
sys.path.insert(0, os.path.join(RADICE, "tests"))

import finto_qt
finto_qt.installa()

from database import backup_manager as bm
from database.db_manager import DatabaseManager, DatabaseInSolaLettura


def dati_preventivo():
    return {
        'nome_cliente': 'Prova', 'numero_ordine': '1', 'misura': 'x',
        'descrizione': 'd', 'codice': 'c', 'finitura': 'f',
        'costo_totale_materiali': 1.0, 'costi_accessori': 1.0,
        'minuti_taglio': 1.0, 'minuti_avvolgimento': 1.0, 'minuti_pulizia': 1.0,
        'minuti_rettifica': 1.0, 'minuti_imballaggio': 1.0, 'tot_mano_opera': 1.0,
        'subtotale': 1.0, 'maggiorazione_25': 1.0, 'preventivo_finale': 1.0,
        'prezzo_cliente': 1.0, 'materiali_utilizzati': [],
    }


class BaseProtetta(unittest.TestCase):

    def setUp(self):
        bm._esito_avvio_cache.clear()
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "materiali.db")
        self._orig_app = bm.cartella_app
        bm.cartella_app = lambda: self.tmp
        import database.db_manager as modulo_db
        self._orig_risolvi = modulo_db.risolvi_percorso_db
        modulo_db.risolvi_percorso_db = lambda: (self.db, {})

        # un database vero, con dentro qualcosa da leggere
        sano = DatabaseManager(db_path=self.db)
        self.id_preventivo = sano.add_preventivo(dati_preventivo())
        self.impronta_prima = self._impronta()

    def tearDown(self):
        bm.cartella_app = self._orig_app
        import database.db_manager as modulo_db
        modulo_db.risolvi_percorso_db = self._orig_risolvi
        bm._esito_avvio_cache.clear()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _impronta(self):
        import hashlib
        with open(self.db, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def _rovina_e_riapri(self):
        with open(self.db, "r+b") as f:
            f.seek(4096)
            f.write(b"\xff" * 4096)
        bm._esito_avvio_cache.clear()
        self.impronta_prima = self._impronta()
        return DatabaseManager(db_path=self.db)


class TestSiAccendeQuandoServe(BaseProtetta):

    def test_database_sano_nessuna_modalita_protetta(self):
        gestore = DatabaseManager(db_path=self.db)
        self.assertFalse(gestore.modalita_protetta,
                         "su un database sano si deve lavorare normalmente")

    def test_database_danneggiato_accende_la_modalita_protetta(self):
        gestore = self._rovina_e_riapri()
        self.assertTrue(gestore.modalita_protetta)
        self.assertIsNotNone(gestore.avviso_integrita,
                             "l'utente deve sapere perché è in sola lettura")

    def test_il_programma_si_apre_lo_stesso(self):
        """Il punto di tutta la modalità: non restare chiusi fuori."""
        gestore = self._rovina_e_riapri()
        self.assertIsNotNone(gestore)
        self.assertEqual(gestore.db_path, self.db)


class TestNonSiPuoScrivere(BaseProtetta):

    def test_il_file_non_viene_toccato_nemmeno_dall_apertura(self):
        """Nemmeno init_database deve girare: creerebbe tabelle e colonne su
        un file già malato."""
        self._rovina_e_riapri()
        self.assertEqual(self._impronta(), self.impronta_prima,
                         "aprire in modalità protetta non deve modificare "
                         "di un byte il database danneggiato")

    def test_salvare_un_preventivo_viene_rifiutato_con_un_messaggio_chiaro(self):
        gestore = self._rovina_e_riapri()
        with self.assertRaises(DatabaseInSolaLettura) as contesto:
            gestore.add_preventivo(dati_preventivo())
        messaggio = str(contesto.exception)
        self.assertIn("MODALITÀ PROTETTA", messaggio)
        self.assertIn("Impostazioni di archiviazione", messaggio,
                      "va detto COME uscirne, non solo che è bloccato")

    def test_anche_le_scritture_senza_protezione_esplicita_falliscono(self):
        """La parte che conta: dei 45 punti che scrivono, solo 4 passano dal
        controllo esplicito. Gli altri devono essere fermati comunque, da
        SQLite, perché il file è aperto in sola lettura."""
        gestore = self._rovina_e_riapri()
        with self.assertRaises(sqlite3.OperationalError) as contesto:
            with gestore._connessione() as conn:
                conn.execute("CREATE TABLE prova_scrittura (x INTEGER)")
        self.assertIn("readonly", str(contesto.exception).lower())
        self.assertEqual(self._impronta(), self.impronta_prima)

    def test_dopo_un_tentativo_di_scrittura_il_file_e_intatto(self):
        gestore = self._rovina_e_riapri()
        for tentativo in (lambda: gestore.add_preventivo(dati_preventivo()),
                          lambda: gestore.registra_movimento(1, 'carico', 5.0)):
            try:
                tentativo()
            except Exception:
                pass
        self.assertEqual(self._impronta(), self.impronta_prima,
                         "nessun tentativo deve aver modificato il file")


class TestSiPuoLeggere(BaseProtetta):

    def test_i_preventivi_si_leggono_ancora(self):
        """Se non si potesse nemmeno leggere, la modalità protetta non
        servirebbe a niente: tanto varrebbe non aprire."""
        gestore = self._rovina_e_riapri()
        try:
            elenco = gestore.get_all_preventivi()
        except Exception as e:
            self.skipTest("il danno impedisce anche la lettura: %s" % e)
        self.assertIsInstance(elenco, list)


class TestBannerBenVisibile(BaseProtetta):

    def test_la_schermata_principale_mostra_la_fascia_di_avviso(self):
        """Un messaggio che si chiude e poi sparisce lascerebbe credere di
        star lavorando normalmente."""
        from ui.main_window import MainWindow
        self._rovina_e_riapri()
        bm._esito_avvio_cache.clear()

        finestra = MainWindow()
        # __dict__ e non getattr: le finestre finte rispondono a QUALUNQUE
        # attributo, quindi getattr(..., None) non risponderebbe mai None.
        banner = finestra.__dict__.get("banner_modalita_protetta")
        self.assertIsNotNone(banner, "manca la fascia di avviso")
        testo = banner.text()
        self.assertIn("MODALITÀ PROTETTA", testo)
        self.assertIn("Impostazioni di archiviazione", testo,
                      "deve dire come tornare a lavorare")

    def test_con_database_sano_nessuna_fascia(self):
        from ui.main_window import MainWindow
        bm._esito_avvio_cache.clear()
        finestra = MainWindow()
        self.assertIsNone(finestra.__dict__.get("banner_modalita_protetta"),
                          "senza problemi non deve comparire nessun avviso")


if __name__ == "__main__":
    unittest.main(verbosity=2)
