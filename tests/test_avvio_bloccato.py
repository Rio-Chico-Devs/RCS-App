#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
La trappola dell'avvio: database danneggiato e nessuna via d'uscita.

Cosa e' successo davvero
------------------------
Aprendo per prova un vecchio database rovinato, il programma ha fatto quello
per cui era stato scritto: ha avvisato che era danneggiato e si e' chiuso.

Ma quale database usare e' scritto in config.json, e config.json si cambia
solo da dentro il programma. Risultato: a ogni riavvio lo stesso messaggio,
la stessa chiusura, e nessun modo di tornare al database buono. Chiuso fuori
dal proprio gestionale.

La regola che ne esce, e che questi test fissano:
    un programma non deve MAI bloccare l'unica strada che porta alla
    soluzione del problema che sta segnalando.

Fermarsi davanti a un database rovinato e' giusto. Fermarsi e basta no.

Esegui con:  python -m unittest tests.test_avvio_bloccato -v
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RADICE)
sys.path.insert(0, os.path.join(RADICE, "tests"))

import finto_qt
finto_qt.installa()

import main as programma
from database import backup_manager as bm


def crea_database_buono(percorso):
    import sqlite3
    conn = sqlite3.connect(percorso)
    conn.execute("CREATE TABLE preventivi (id INTEGER PRIMARY KEY, nota TEXT)")
    conn.execute("CREATE TABLE materiali (id INTEGER PRIMARY KEY, nome TEXT)")
    conn.executemany("INSERT INTO preventivi (nota) VALUES (?)",
                     [("riga " * 40,) for _ in range(200)])
    conn.commit()
    conn.close()
    return percorso


def rovina(percorso):
    with open(percorso, "r+b") as f:
        f.seek(4096)
        f.write(b"\xff" * 4096)


class BaseAvvio(unittest.TestCase):

    def setUp(self):
        finto_qt.RispostaAutomatica.azzera()
        bm._esito_avvio_cache.clear()
        self.tmp = tempfile.mkdtemp()
        self.rotto = crea_database_buono(os.path.join(self.tmp, "vecchio.db"))
        rovina(self.rotto)
        self.buono = crea_database_buono(os.path.join(self.tmp, "buono.db"))
        self._orig_app = bm.cartella_app
        bm.cartella_app = lambda: self.tmp

    def tearDown(self):
        bm.cartella_app = self._orig_app
        bm._esito_avvio_cache.clear()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def configurazione(self):
        percorso = os.path.join(self.tmp, "config.json")
        if not os.path.exists(percorso):
            return {}
        with open(percorso, encoding="utf-8") as f:
            return json.load(f)


class TestViaDUscita(BaseAvvio):

    def test_il_database_di_prova_e_davvero_rovinato(self):
        """Senza questo, i test sotto potrebbero passare perche' non c'e'
        nessun danno da gestire."""
        integro, _messaggio, _ms = bm.verifica_integrita(self.rotto)
        self.assertFalse(integro, "il database di prova doveva essere rovinato")

    def test_si_puo_scegliere_un_altro_database(self):
        finto_qt.RispostaAutomatica.scelta_pulsante = 0     # "Scegli un altro database"
        finto_qt.FileDialog.prossimo_file = self.buono

        prosegue = programma._come_procedere_col_database_danneggiato(
            self.tmp, self.rotto, "danneggiato")

        self.assertTrue(prosegue, "dopo aver scelto, il programma deve proseguire")
        self.assertEqual(self.configurazione().get("db_path"), self.buono,
                         "la scelta deve essere scritta in config.json, "
                         "altrimenti al riavvio si ricasca nella stessa trappola")

    def test_si_puo_aprire_comunque_per_ripristinare(self):
        finto_qt.RispostaAutomatica.scelta_pulsante = 1     # "Apri comunque"
        prosegue = programma._come_procedere_col_database_danneggiato(
            self.tmp, self.rotto, "danneggiato")
        self.assertTrue(prosegue,
                        "deve poter entrare nel programma per ripristinare una copia")

    def test_si_puo_anche_chiudere(self):
        finto_qt.RispostaAutomatica.scelta_pulsante = 2     # "Chiudi il programma"
        prosegue = programma._come_procedere_col_database_danneggiato(
            self.tmp, self.rotto, "danneggiato")
        self.assertFalse(prosegue)

    def test_il_messaggio_dice_quale_database_e(self):
        finto_qt.RispostaAutomatica.scelta_pulsante = 2
        programma._come_procedere_col_database_danneggiato(
            self.tmp, self.rotto, "danneggiato")
        testi = " ".join(finto_qt.RispostaAutomatica.dialoghi_mostrati)
        self.assertIn(self.rotto, testi,
                      "va detto QUALE file e' rovinato: senza, non si sa "
                      "nemmeno cosa si stava aprendo")

    def test_annullando_la_scelta_non_si_resta_chiusi_fuori(self):
        """Chi apre la finestra di scelta e poi annulla non deve ritrovarsi
        col programma chiuso: sarebbe di nuovo la trappola."""
        finto_qt.RispostaAutomatica.scelta_pulsante = 0
        finto_qt.FileDialog.prossimo_file = ""              # annullato

        prosegue = programma._come_procedere_col_database_danneggiato(
            self.tmp, self.rotto, "danneggiato")
        self.assertTrue(prosegue)

    def test_se_anche_il_secondo_database_e_rotto_si_apre_lo_stesso(self):
        altro_rotto = crea_database_buono(os.path.join(self.tmp, "altro.db"))
        rovina(altro_rotto)
        finto_qt.RispostaAutomatica.scelta_pulsante = 0
        finto_qt.FileDialog.prossimo_file = altro_rotto

        prosegue = programma._come_procedere_col_database_danneggiato(
            self.tmp, self.rotto, "danneggiato")

        self.assertTrue(prosegue, "non si chiude mai la porta")
        self.assertNotEqual(self.configurazione().get("db_path"), altro_rotto,
                            "un database rotto non va scritto in configurazione")


class TestLaViaDUscitaEDAVVERO_COLLEGATA(unittest.TestCase):
    """I test qui sopra provano la funzione. Questo prova che sia CHIAMATA.

    Senza, si potrebbe togliere la via d'uscita da main() e i test
    continuerebbero a passare tutti: verificato, e' proprio quello che e'
    successo scrivendoli. Una protezione scollegata e' come non averla."""

    def _ramo_del_database_danneggiato(self):
        """Il controllo dentro main(), non quello dentro le funzioni di
        appoggio: di 'if ... integro' in main.py ce n'e' piu' di uno, e
        cercando il primo si finiva a guardare quello sbagliato."""
        import ast
        percorso = os.path.join(RADICE, "main.py")
        with open(percorso, encoding="utf-8") as f:
            albero = ast.parse(f.read())
        principale = next((n for n in ast.walk(albero)
                           if isinstance(n, ast.FunctionDef) and n.name == "main"), None)
        if principale is None:
            return None
        for nodo in ast.walk(principale):
            if isinstance(nodo, ast.If) and "integro" in ast.dump(nodo.test):
                return nodo
        return None

    def test_esiste_il_controllo_sul_database_danneggiato(self):
        self.assertIsNotNone(self._ramo_del_database_danneggiato(),
                             "in main.py non si controlla piu' se il database "
                             "e' integro all'avvio")

    def test_quel_ramo_offre_una_scelta_e_non_chiude_e_basta(self):
        import ast
        ramo = self._ramo_del_database_danneggiato()
        self.assertIsNotNone(ramo)
        chiamate = {getattr(n.func, "id", None) or getattr(n.func, "attr", None)
                    for n in ast.walk(ramo) if isinstance(n, ast.Call)}
        self.assertIn(
            "_come_procedere_col_database_danneggiato", chiamate,
            "il ramo del database danneggiato deve offrire una via d'uscita.\n"
            "Se qui si chiama solo sys.exit, chi apre per sbaglio un database "
            "rovinato\nresta chiuso fuori dal programma per sempre: il "
            "database da usare si\ncambia solo da dentro. E' successo davvero.")


class TestScritturaConfigurazione(BaseAvvio):

    def test_conserva_le_altre_impostazioni(self):
        percorso = os.path.join(self.tmp, "config.json")
        with open(percorso, "w", encoding="utf-8") as f:
            json.dump({"db_path": self.rotto, "verifica_dopo_scrittura": False}, f)

        programma.scrivi_percorso_database(self.tmp, self.buono)

        config = self.configurazione()
        self.assertEqual(config["db_path"], self.buono)
        self.assertIs(config.get("verifica_dopo_scrittura"), False,
                      "le altre impostazioni non vanno perse")

    def test_funziona_anche_se_il_file_era_illeggibile(self):
        percorso = os.path.join(self.tmp, "config.json")
        with open(percorso, "w", encoding="utf-8") as f:
            f.write("{ questo non e' json")

        programma.scrivi_percorso_database(self.tmp, self.buono)
        self.assertEqual(self.configurazione().get("db_path"), self.buono)


if __name__ == "__main__":
    unittest.main(verbosity=2)
