#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test della riapertura dei preventivi non salvati.

Dopo uno spegnimento improvviso le schermate vengono riaperte GIA' COMPILATE,
riusando lo stesso percorso con cui l'applicazione carica un preventivo dal
database (_popola_da_dati). PyQt5 non e' installabile in sviluppo, quindi qui
si verifica cio' che si puo' verificare davvero: che la bozza salvata contenga
TUTTI i dati che quella funzione andra' a leggere.

E' il controllo che conta: se manca una chiave, il preventivo si riaprirebbe
con un campo vuoto e l'utente non se ne accorgerebbe.

Esegui con:  python -m unittest tests.test_recupero_bozze -v
"""

import ast
import json
import os
import shutil
import sys
import tempfile
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RADICE)

from models.preventivo import Preventivo
from models.materiale import MaterialeCalcolato
from utils import bozze


def chiavi_lette_da(nome_funzione, percorso_file, nome_parametro):
    """Ricava dal codice quali chiavi legge una funzione dal suo parametro.

    Si analizza il codice invece di elencarle a mano: cosi' se un domani la
    funzione leggera' un campo in piu', il test se ne accorge da solo."""
    with open(percorso_file, encoding="utf-8") as f:
        albero = ast.parse(f.read(), percorso_file)

    chiavi = set()
    for nodo in ast.walk(albero):
        if not isinstance(nodo, ast.FunctionDef) or nodo.name != nome_funzione:
            continue
        for sotto in ast.walk(nodo):
            # forma:  parametro.get('chiave', ...)
            if (isinstance(sotto, ast.Call)
                    and isinstance(sotto.func, ast.Attribute)
                    and sotto.func.attr == "get"
                    and isinstance(sotto.func.value, ast.Name)
                    and sotto.func.value.id == nome_parametro
                    and sotto.args
                    and isinstance(sotto.args[0], ast.Constant)):
                chiavi.add(sotto.args[0].value)
            # forma:  parametro['chiave']
            if (isinstance(sotto, ast.Subscript)
                    and isinstance(sotto.value, ast.Name)
                    and sotto.value.id == nome_parametro
                    and isinstance(sotto.slice, ast.Constant)):
                chiavi.add(sotto.slice.value)
    return chiavi


def preventivo_realistico():
    """Costruisce un preventivo come lo produrrebbe la schermata."""
    preventivo = Preventivo()
    preventivo.costi_accessori = 30.0
    preventivo.minuti_taglio = 15.0
    preventivo.minuti_avvolgimento = 40.0
    preventivo.minuti_pulizia = 10.0
    preventivo.minuti_rettifica = 5.0
    preventivo.minuti_imballaggio = 8.0
    preventivo.prezzo_cliente = 1250.0

    materiale = MaterialeCalcolato()
    materiale.diametro = 40.0
    materiale.lunghezza = 1200.0
    materiale.materiale_id = 3
    materiale.materiale_nome = "Fibra carbonio 200g"
    materiale.giri = 6
    materiale.spessore = 0.25
    materiale.costo_totale = 180.0
    materiale.maggiorazione = 10.0
    preventivo.materiali_calcolati.append(materiale)

    dati = preventivo.to_dict()
    dati.update({
        "nome_cliente": "Bianchi SpA", "numero_ordine": "ORD-77",
        "descrizione": "Tubo carbonio", "codice": "TC-1",
        "misura": "1200 mm", "finitura": "Lucida",
    })
    return dati


class TestCompatibilitaBozza(unittest.TestCase):
    """La bozza deve contenere tutto cio' che serve a riaprire la schermata."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._orig = bozze.cartella_bozze
        bozze.cartella_bozze = lambda: self.tmp

    def tearDown(self):
        bozze.cartella_bozze = self._orig
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_la_bozza_contiene_i_campi_del_preventivo(self):
        richieste = chiavi_lette_da(
            "_popola_da_dati", os.path.join(RADICE, "ui/preventivo_window.py"),
            "preventivo_data")
        self.assertTrue(richieste, "il test deve aver trovato le chiavi lette")

        dati = preventivo_realistico()
        # 'preventivo_originale_id' riguarda solo le revisioni salvate a database
        richieste.discard("preventivo_originale_id")

        mancanti = sorted(c for c in richieste if c not in dati)
        self.assertEqual(mancanti, [],
                         f"la bozza non contiene: {mancanti} -> alla riapertura "
                         f"quei campi resterebbero vuoti")

    def test_la_bozza_sopravvive_al_salvataggio_su_file(self):
        """Passando da JSON i dati non devono cambiare forma."""
        originale = preventivo_realistico()
        bozze.salva_bozza("prova", originale)
        riletta = bozze.elenca_bozze()[0]["dati"]

        self.assertEqual(riletta["nome_cliente"], "Bianchi SpA")
        self.assertEqual(riletta["minuti_avvolgimento"], 40.0)
        self.assertEqual(len(riletta["materiali_utilizzati"]), 1)
        self.assertEqual(riletta["materiali_utilizzati"][0]["materiale_nome"],
                         "Fibra carbonio 200g")
        self.assertEqual(riletta["materiali_utilizzati"][0]["giri"], 6)

    def test_i_materiali_mantengono_i_campi_che_servono(self):
        """La riapertura ricostruisce i materiali campo per campo."""
        richieste = chiavi_lette_da(
            "_popola_da_dati", os.path.join(RADICE, "ui/preventivo_window.py"),
            "mat_data")
        self.assertTrue(richieste, "il test deve aver trovato le chiavi dei materiali")

        bozze.salva_bozza("prova", preventivo_realistico())
        materiale = bozze.elenca_bozze()[0]["dati"]["materiali_utilizzati"][0]

        # 'stratifica' è solo un vecchio nome alternativo di 'sviluppo'
        richieste.discard("stratifica")
        mancanti = sorted(c for c in richieste if c not in materiale)
        self.assertEqual(mancanti, [],
                         f"i materiali della bozza non contengono: {mancanti}")

    def test_bozza_vuota_non_rompe_la_riapertura(self):
        """Una bozza appena creata, senza materiali, deve restare gestibile."""
        bozze.salva_bozza("vuota", {"nome_cliente": "", "materiali_utilizzati": []})
        dati = bozze.elenca_bozze()[0]["dati"]
        self.assertEqual(dati["materiali_utilizzati"], [])

    def test_eliminazione_dopo_la_riapertura(self):
        """Riaperto il preventivo, la bozza va tolta: da quel momento e' la
        schermata a tenerne una propria."""
        bozze.salva_bozza("prova", preventivo_realistico())
        voce = bozze.elenca_bozze()[0]
        self.assertTrue(bozze.elimina_bozza_da_file(voce))
        self.assertEqual(bozze.elenca_bozze(), [])

    def test_eliminazione_di_una_voce_senza_file(self):
        self.assertFalse(bozze.elimina_bozza_da_file({}))
        self.assertFalse(bozze.elimina_bozza_da_file(None))


class TestEsitoAvvioRicordato(unittest.TestCase):
    """La finestra principale legge l'esito dell'avvio piu' tardi, quando
    l'interfaccia esiste: deve restare disponibile."""

    def setUp(self):
        from utils import diagnostica
        self.diagnostica = diagnostica
        self.tmp = tempfile.mkdtemp()
        self._orig = diagnostica.cartella_locale
        diagnostica.cartella_locale = lambda: self.tmp

    def tearDown(self):
        self.diagnostica.cartella_locale = self._orig
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_esito_disponibile_dopo(self):
        self.diagnostica.segna_avvio("/rete/materiali.db")
        self.diagnostica.segna_avvio("/rete/materiali.db")   # chiusura anomala

        esito = self.diagnostica.esito_avvio_precedente()
        self.assertFalse(esito["chiusura_precedente_regolare"],
                         "la finestra principale deve poter sapere che la "
                         "chiusura precedente e' stata anomala")

    def test_chiusura_regolare_non_propone_recuperi(self):
        self.diagnostica.segna_avvio()
        self.diagnostica.segna_chiusura_regolare()
        self.diagnostica.segna_avvio()
        self.assertTrue(
            self.diagnostica.esito_avvio_precedente()["chiusura_precedente_regolare"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
