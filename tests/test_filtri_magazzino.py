#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filtri dello storico movimenti di magazzino.

Perche' servono
---------------
Nati da un caso vero: di un materiale risultavano a sistema 46,9 m2 mentre
sullo scaffale ce n'erano 6,9. Per capire da dove venisse la differenza
bisognava leggere tutti i movimenti uno per uno.

Con i filtri la stessa domanda si fa in tre clic: tipo di movimento,
fornitore, materiale - piu' il periodo. I tre filtri si combinano.

Cosa si verifica qui
--------------------
Che i filtri filtrino davvero, che si combinino, e che il riepilogo dica
caricato, scaricato E saldo: e' il confronto che rende visibile una
differenza, mentre il solo totale scaricato la nascondeva.

Esegui con:  python -m unittest tests.test_filtri_magazzino -v
"""

import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RADICE)
sys.path.insert(0, os.path.join(RADICE, "tests"))

import finto_qt
finto_qt.installa()

from database import backup_manager as bm
from database.db_manager import DatabaseManager
from ui.magazzino_window import MagazzinoWindow


class BaseMagazzino(unittest.TestCase):
    """Un magazzino con due materiali, due fornitori, carichi e scarichi."""

    def setUp(self):
        bm._esito_avvio_cache.clear()
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "materiali.db")
        self._orig_app = bm.cartella_app
        bm.cartella_app = lambda: self.tmp
        import database.db_manager as modulo_db
        self._orig_risolvi = modulo_db.risolvi_percorso_db
        modulo_db.risolvi_percorso_db = lambda: (self.db, {})

        self.gestore = DatabaseManager(db_path=self.db)
        # CK204 e TWILL sono gia' nel catalogo predefinito: si recuperano i
        # loro identificativi invece di ricrearli (add_materiale rifiuta i
        # nomi doppi e risponde False, non un identificativo).
        self.ck = self._id_materiale("CK204")
        self.tw = self._id_materiale("TWILL")
        self.gestore.registra_movimento(self.ck, 'carico', 69.0,
                                        note="rotolo", fornitore_nome="FIBERTECH")
        self.gestore.registra_movimento(self.ck, 'scarico', 21.9,
                                        note="jantex", fornitore_nome="FIBERTECH")
        self.gestore.registra_movimento(self.tw, 'carico', 62.5,
                                        note="rotolo pieno", fornitore_nome="CIT")
        self.gestore.registra_movimento(self.tw, 'scarico', 4.8,
                                        note="bnp", fornitore_nome="CIT")
        self.gestore.registra_movimento(self.tw, 'scarico', 1.2,
                                        note="prova", fornitore_nome="FIBERTECH")

        self.finestra = MagazzinoWindow(self.gestore)
        self.finestra.combo_periodo.scegli("tutto")

    def _id_materiale(self, nome):
        with self.gestore._connessione() as conn:
            riga = conn.execute("SELECT id FROM materiali WHERE nome = ?", (nome,)).fetchone()
        self.assertIsNotNone(riga, "materiale %s non trovato nel catalogo" % nome)
        return riga[0]

    def tearDown(self):
        bm.cartella_app = self._orig_app
        import database.db_manager as modulo_db
        modulo_db.risolvi_percorso_db = self._orig_risolvi
        bm._esito_avvio_cache.clear()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def righe_mostrate(self):
        return self.finestra.tabella_consumi.rowCount()

    def riepilogo(self):
        return self.finestra.lbl_riepilogo_consumi.text()


class TestElenchiDeiFiltri(BaseMagazzino):

    def test_le_tendine_si_riempiono_con_quello_che_c_e(self):
        fornitori = [self.finestra.combo_fornitore_mov.itemData(i)
                     for i in range(self.finestra.combo_fornitore_mov.count())]
        materiali = [self.finestra.combo_materiale_mov.itemData(i)
                     for i in range(self.finestra.combo_materiale_mov.count())]
        self.assertEqual(fornitori[0], None, "la prima voce deve essere 'tutti'")
        self.assertIn("FIBERTECH", fornitori)
        self.assertIn("CIT", fornitori)
        self.assertIn("CK204", materiali)
        self.assertIn("TWILL", materiali)

    def test_compaiono_anche_i_fornitori_non_piu_in_anagrafica(self):
        """Un fornitore con cui non si lavora piu' deve restare nel filtro,
        altrimenti i suoi movimenti di due anni fa diventano irraggiungibili -
        ed e' proprio quando un filtro serve."""
        elenco = self.gestore.fornitori_nei_movimenti()
        self.assertIn("FIBERTECH", elenco)
        self.assertIn("CIT", elenco)


class TestIFiltriFiltrano(BaseMagazzino):

    def test_senza_filtri_si_vede_tutto(self):
        self.assertEqual(self.righe_mostrate(), 5)

    def test_solo_carichi(self):
        self.finestra.combo_tipo_mov.scegli("carico")
        self.assertEqual(self.righe_mostrate(), 2)
        self.assertIn("caricato 131.50", self.riepilogo())

    def test_solo_scarichi(self):
        self.finestra.combo_tipo_mov.scegli("scarico")
        self.assertEqual(self.righe_mostrate(), 3)

    def test_per_fornitore(self):
        self.finestra.combo_fornitore_mov.scegli("CIT")
        self.assertEqual(self.righe_mostrate(), 2)

    def test_per_materiale(self):
        self.finestra.combo_materiale_mov.scegli("CK204")
        self.assertEqual(self.righe_mostrate(), 2)

    def test_i_tre_filtri_si_combinano(self):
        """La domanda vera: 'tutti gli scarichi di TWILL fatti da FIBERTECH'.
        Ce n'e' uno solo, ed e' quello che senza filtri non si troverebbe."""
        self.finestra.combo_tipo_mov.scegli("scarico")
        self.finestra.combo_fornitore_mov.scegli("FIBERTECH")
        self.finestra.combo_materiale_mov.scegli("TWILL")
        self.assertEqual(self.righe_mostrate(), 1)

    def test_azzera_filtri_rimette_tutto(self):
        self.finestra.combo_tipo_mov.scegli("carico")
        self.finestra.combo_materiale_mov.scegli("CK204")
        self.assertEqual(self.righe_mostrate(), 1)

        self.finestra.azzera_filtri_movimenti()
        self.assertEqual(self.righe_mostrate(), 5)
        self.assertIsNone(self.finestra.combo_tipo_mov.currentData())
        self.assertIsNone(self.finestra.combo_materiale_mov.currentData())


class TestRiepilogo(BaseMagazzino):

    def test_dice_caricato_scaricato_e_saldo(self):
        """Prima mostrava solo il totale scaricato: con quello non si poteva
        vedere se entrato e uscito tornassero."""
        testo = self.riepilogo()
        for atteso in ("caricato", "scaricato", "saldo"):
            self.assertIn(atteso, testo, "manca '%s' nel riepilogo: %r" % (atteso, testo))

    def test_il_saldo_e_giusto(self):
        self.finestra.combo_materiale_mov.scegli("CK204")
        self.assertIn("saldo +47.10", self.riepilogo())   # 69,0 - 21,9

    def test_il_riepilogo_nomina_i_filtri_attivi(self):
        self.finestra.combo_materiale_mov.scegli("CK204")
        self.assertIn("CK204", self.riepilogo(),
                      "chi guarda deve sapere che sta vedendo un sottoinsieme")

    def test_se_i_filtri_non_trovano_nulla_lo_spiega(self):
        """Zero righe con i filtri attivi non deve far pensare che il periodo
        sia vuoto: va detto quanti movimenti ci sono senza filtri."""
        self.finestra.combo_tipo_mov.scegli("carico")
        self.finestra.combo_fornitore_mov.scegli("FIBERTECH")
        self.finestra.combo_materiale_mov.scegli("TWILL")

        self.assertEqual(self.righe_mostrate(), 0)
        testo = self.riepilogo()
        self.assertIn("nessun movimento con questi filtri", testo)
        self.assertIn("5", testo, "deve dire quanti ce ne sono senza filtri")


class TestPeriodi(BaseMagazzino):

    def test_tutto_lo_storico_prende_anche_i_movimenti_vecchi(self):
        vecchio = (datetime.now() - timedelta(days=400)).isoformat()
        with self.gestore._connessione() as conn:
            conn.execute("""INSERT INTO movimenti_magazzino
                            (materiale_id, tipo, quantita, data, note, fornitore_nome)
                            VALUES (?, 'carico', 10.0, ?, 'vecchio', 'CIT')""",
                         (self.ck, vecchio))
            conn.commit()

        self.finestra.combo_periodo.scegli("ultimi_3_mesi")
        recenti = self.righe_mostrate()
        self.finestra.combo_periodo.scegli("tutto")
        tutti = self.righe_mostrate()

        self.assertEqual(tutti, recenti + 1,
                         "'Tutto lo storico' deve comprendere anche il movimento "
                         "di piu' di un anno fa")

    def test_ogni_periodo_produce_date_valide(self):
        for i in range(self.finestra.combo_periodo.count()):
            chiave = self.finestra.combo_periodo.itemData(i)
            with self.subTest(periodo=chiave):
                inizio, fine = self.finestra._calcola_date_periodo(chiave)
                self.assertLessEqual(inizio, fine,
                                     "l'inizio non puo' essere dopo la fine")
                datetime.fromisoformat(inizio)
                datetime.fromisoformat(fine)


if __name__ == "__main__":
    unittest.main(verbosity=2)
