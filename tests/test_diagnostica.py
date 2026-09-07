#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test di diagnostica (marcatore di sessione, registro scritture) e bozze.
Esegui con:  python -m unittest tests.test_diagnostica -v
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import bozze, diagnostica


class BaseCartellaFinta(unittest.TestCase):
    """Dirotta le cartelle locali dei moduli su una temporanea."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._orig_diag = diagnostica.cartella_locale
        self._orig_bozze = bozze.cartella_bozze
        cartella_log = os.path.join(self.tmp, "logs")
        cartella_bozze = os.path.join(self.tmp, "logs", "bozze")
        os.makedirs(cartella_bozze, exist_ok=True)
        diagnostica.cartella_locale = lambda: cartella_log
        bozze.cartella_bozze = lambda: cartella_bozze

    def tearDown(self):
        diagnostica.cartella_locale = self._orig_diag
        bozze.cartella_bozze = self._orig_bozze
        shutil.rmtree(self.tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Marcatore di sessione
# ---------------------------------------------------------------------------

class TestMarcatoreSessione(BaseCartellaFinta):

    def test_primo_avvio_in_assoluto(self):
        esito = diagnostica.segna_avvio("/percorso/db.db")
        self.assertIsNone(esito["chiusura_precedente_regolare"],
                          "al primissimo avvio non si può dire nulla")

    def test_chiusura_regolare_riconosciuta(self):
        diagnostica.segna_avvio()
        diagnostica.segna_chiusura_regolare()
        esito = diagnostica.segna_avvio()
        self.assertTrue(esito["chiusura_precedente_regolare"])

    def test_chiusura_anomala_riconosciuta(self):
        """Scenario reale: PC spento da Windows Update con l'app aperta.
        Il marcatore resta sul disco e al riavvio viene rilevato."""
        diagnostica.segna_avvio("/rete/materiali.db")
        # NESSUNA chiusura regolare: simula lo spegnimento improvviso
        esito = diagnostica.segna_avvio("/rete/materiali.db")

        self.assertFalse(esito["chiusura_precedente_regolare"])
        self.assertIsNotNone(esito["sessione_precedente"])
        self.assertIn("avvio", esito["sessione_precedente"])
        self.assertEqual(esito["sessione_precedente"]["database"], "/rete/materiali.db")

    def test_riepilogo_leggibile(self):
        diagnostica.segna_avvio()
        esito = diagnostica.segna_avvio()
        testo = diagnostica.riepilogo_avvio(
            esito, ["01/01/2026 - Il PC si è riavviato senza essere spento correttamente"])
        self.assertIn("NON è stata chiusa", testo)
        self.assertIn("riavviato", testo)


# ---------------------------------------------------------------------------
# Registro delle scritture
# ---------------------------------------------------------------------------

class TestRegistroScritture(BaseCartellaFinta):

    def test_registra_e_rilegge(self):
        diagnostica.registra_scrittura("add_preventivo", "id 108", "ok", 42.0)
        righe = diagnostica.ultime_scritture()
        self.assertEqual(len(righe), 1)
        self.assertIn("add_preventivo", righe[0])
        self.assertIn("id 108", righe[0])
        self.assertIn("42 ms", righe[0])

    def test_registra_problema(self):
        diagnostica.registra_scrittura("add_preventivo", "id 109", "DATABASE DANNEGGIATO")
        righe = diagnostica.ultime_scritture()
        self.assertIn("DATABASE DANNEGGIATO", righe[-1])

    def test_ordine_e_limite(self):
        for i in range(20):
            diagnostica.registra_scrittura("add_preventivo", f"id {i}")
        righe = diagnostica.ultime_scritture(5)
        self.assertEqual(len(righe), 5)
        self.assertIn("id 19", righe[-1], "l'ultima riga deve essere la più recente")

    def test_non_solleva_mai_eccezioni(self):
        diagnostica.cartella_locale = lambda: "/percorso/che/non/esiste/xyz"
        try:
            diagnostica.registra_scrittura("prova")   # non deve sollevare
        except Exception as e:
            self.fail(f"il registro non deve mai far fallire un salvataggio: {e}")


# ---------------------------------------------------------------------------
# Bozze dei preventivi aperti
# ---------------------------------------------------------------------------

def _dati_preventivo(cliente="Rossi Srl", prezzo=1234.5):
    return {
        "nome_cliente": cliente,
        "numero_ordine": "ORD-77",
        "descrizione": "Tubo in carbonio",
        "prezzo_cliente": prezzo,
        "materiali_utilizzati": [{"nome": "fibra"}, {"nome": "resina"}],
    }


class TestBozze(BaseCartellaFinta):

    def test_salva_e_rilegge(self):
        self.assertTrue(bozze.salva_bozza("finestra1", _dati_preventivo()))
        elenco = bozze.elenca_bozze()
        self.assertEqual(len(elenco), 1)
        self.assertEqual(elenco[0]["dati"]["nome_cliente"], "Rossi Srl")

    def test_tre_finestre_aperte(self):
        """Lo scenario chiesto: tre schede preventivo aperte quando il PC si spegne."""
        for i in range(3):
            bozze.salva_bozza(f"finestra{i}", _dati_preventivo(cliente=f"Cliente {i}"))
        elenco = bozze.elenca_bozze()
        self.assertEqual(len(elenco), 3, "devono essere recuperabili tutte e tre")
        nomi = {b["dati"]["nome_cliente"] for b in elenco}
        self.assertEqual(nomi, {"Cliente 0", "Cliente 1", "Cliente 2"})

    def test_bozza_eliminata_dopo_salvataggio(self):
        bozze.salva_bozza("finestra1", _dati_preventivo())
        bozze.elimina_bozza("finestra1")
        self.assertEqual(bozze.elenca_bozze(), [],
                         "salvato il preventivo, la bozza non serve più")

    def test_descrizione_comprensibile(self):
        bozze.salva_bozza("f1", _dati_preventivo())
        testo = bozze.descrivi_bozza(bozze.elenca_bozze()[0])
        self.assertIn("Rossi Srl", testo)
        self.assertIn("ORD-77", testo)
        self.assertIn("2 materiali", testo)
        self.assertIn("1234.50", testo)

    def test_descrizione_senza_cliente(self):
        bozze.salva_bozza("f1", {"materiali_utilizzati": []})
        testo = bozze.descrivi_bozza(bozze.elenca_bozze()[0])
        self.assertIn("cliente non indicato", testo)

    def test_pulizia_vecchie(self):
        bozze.salva_bozza("recente", _dati_preventivo())
        # Bozza vecchia, scritta a mano con data superata
        vecchia = os.path.join(bozze.cartella_bozze(), "bozza_vecchia.json")
        with open(vecchia, "w", encoding="utf-8") as f:
            json.dump({"salvata_il": (datetime.now() - timedelta(days=60)).isoformat(),
                       "dati": {}}, f)

        bozze.pulisci_vecchie(giorni=30)
        rimaste = bozze.elenca_bozze()
        self.assertEqual(len(rimaste), 1)
        self.assertFalse(os.path.exists(vecchia))

    def test_chiave_con_caratteri_strani(self):
        self.assertTrue(bozze.salva_bozza("../../fuori/posto", _dati_preventivo()))
        for percorso in os.listdir(bozze.cartella_bozze()):
            self.assertTrue(percorso.startswith("bozza_"),
                            "il nome file non deve uscire dalla cartella prevista")


class TestFileRecupero(BaseCartellaFinta):
    """Il foglio che permette di ricompilare i preventivi persi."""

    def _bozza_completa(self, cliente="Bianchi SpA"):
        return {
            "nome_cliente": cliente, "numero_ordine": "ORD-77",
            "descrizione": "Tubo carbonio", "codice": "TC-1",
            "misura": "1200 mm", "finitura": "Lucida",
            "costo_totale_materiali": 250.0, "costi_accessori": 30.0,
            "tot_mano_opera": 120.5, "minuti_taglio": 15, "minuti_avvolgimento": 40,
            "minuti_pulizia": 10, "minuti_rettifica": 5, "minuti_imballaggio": 8,
            "subtotale": 400.0, "maggiorazione_25": 100.0,
            "preventivo_finale": 500.0, "prezzo_cliente": 1250.75,
            "materiali_utilizzati": [
                {"materiale_nome": "Fibra 200g", "diametro": 40, "lunghezza": 1200,
                 "giri": 6, "spessore": 0.25, "maggiorazione": 10,
                 "costo_totale": 180.0, "is_conica": False},
            ],
        }

    def test_nessuna_bozza_nessun_file(self):
        self.assertIsNone(bozze.genera_file_recupero())

    def test_contiene_tutti_i_dati_per_ricompilare(self):
        bozze.salva_bozza("f1", self._bozza_completa())
        percorso = bozze.genera_file_recupero()
        self.assertIsNotNone(percorso)
        with open(percorso, encoding="utf-8") as f:
            testo = f.read()

        for atteso in ["Bianchi SpA", "ORD-77", "Tubo carbonio", "TC-1",
                       "1200 mm", "Lucida", "Fibra 200g"]:
            self.assertIn(atteso, testo, f"manca '{atteso}' nel foglio di recupero")

        # importi e minuti servono per ricostruire il preventivo
        self.assertIn("1.250,75", testo, "il prezzo al cliente deve esserci")
        self.assertIn("15 min", testo)
        self.assertIn("40 min", testo)

    def test_piu_pagine_aperte_finiscono_tutte_nel_file(self):
        """Lo scenario delle 'più pagine aperte'."""
        for i, nome in enumerate(["Bianchi SpA", "Verdi Srl", "Neri & Co"]):
            bozze.salva_bozza(f"f{i}", self._bozza_completa(nome))

        percorso = bozze.genera_file_recupero()
        with open(percorso, encoding="utf-8") as f:
            testo = f.read()

        for nome in ["Bianchi SpA", "Verdi Srl", "Neri & Co"]:
            self.assertIn(nome, testo)
        self.assertIn("PREVENTIVO NON SALVATO n. 1", testo)
        self.assertIn("PREVENTIVO NON SALVATO n. 3", testo)
        self.assertIn("c'erano 3 preventivi", testo)

    def test_bozza_quasi_vuota_non_rompe_il_file(self):
        bozze.salva_bozza("f1", {"materiali_utilizzati": []})
        percorso = bozze.genera_file_recupero()
        with open(percorso, encoding="utf-8") as f:
            testo = f.read()
        self.assertIn("(non indicato)", testo)
        self.assertIn("nessun materiale", testo)

    def test_numeri_in_formato_italiano(self):
        bozze.salva_bozza("f1", self._bozza_completa())
        percorso = bozze.genera_file_recupero()
        with open(percorso, encoding="utf-8") as f:
            testo = f.read()
        self.assertIn("0,25 mm", testo, "i decimali usano la virgola")
        self.assertIn("€ 180,00", testo)

    def test_materiale_malformato_non_blocca_tutto(self):
        dati = self._bozza_completa()
        dati["materiali_utilizzati"] = ["non è un dizionario", {"materiale_nome": "Buono"}]
        bozze.salva_bozza("f1", dati)
        percorso = bozze.genera_file_recupero()
        self.assertIsNotNone(percorso, "un dato sporco non deve impedire il recupero")
        with open(percorso, encoding="utf-8") as f:
            self.assertIn("Buono", f.read())


class TestScenarioSpegnimentoImprovviso(BaseCartellaFinta):
    """Lo scenario concreto: tre schede preventivo aperte e il PC si spegne per
    un aggiornamento di Windows. Al riavvio si deve poter dire all'utente cosa
    è successo e cosa è recuperabile."""

    def test_ciclo_completo(self):
        # --- Giorno 1: si lavora ---
        diagnostica.segna_avvio("//SERVER/RCS/materiali.db")

        # tre finestre aperte che salvano la propria bozza
        aperti = [
            ("finestra_a", _dati_preventivo("Bianchi SpA", 800.0)),
            ("finestra_b", _dati_preventivo("Verdi Srl", 1500.0)),
            ("finestra_c", _dati_preventivo("Neri & Co", 320.0)),
        ]
        for chiave, dati in aperti:
            bozze.salva_bozza(chiave, dati)

        # una viene salvata regolarmente nel database: la sua bozza sparisce
        bozze.elimina_bozza("finestra_b")
        diagnostica.registra_scrittura("add_preventivo", "id 109", "ok", 30.0)

        # --- Windows Update spegne il PC: nessuna chiusura regolare ---

        # --- Giorno 2: si riapre il programma ---
        stato = diagnostica.segna_avvio("//SERVER/RCS/materiali.db")

        self.assertFalse(stato["chiusura_precedente_regolare"],
                         "deve accorgersi che la chiusura è stata anomala")

        recuperabili = bozze.elenca_bozze()
        self.assertEqual(len(recuperabili), 2,
                         "restano le due bozze non salvate, non la terza")
        clienti = {b["dati"]["nome_cliente"] for b in recuperabili}
        self.assertEqual(clienti, {"Bianchi SpA", "Neri & Co"})

        # il testo mostrato all'utente deve essere comprensibile
        testo = diagnostica.riepilogo_avvio(stato)
        self.assertIn("NON è stata chiusa", testo)
        for bozza in recuperabili:
            descrizione = bozze.descrivi_bozza(bozza)
            self.assertTrue(any(c in descrizione for c in clienti))

        # e il registro dice qual è stata l'ultima operazione andata a buon fine
        ultime = diagnostica.ultime_scritture()
        self.assertIn("id 109", ultime[-1])
        self.assertIn("ok", ultime[-1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
