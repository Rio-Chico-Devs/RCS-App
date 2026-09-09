#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test dello strumento di verifica dell'installazione.

Uno strumento di controllo ha due modi di essere inutile, ed e' il secondo il
piu' pericoloso:
  1. dice che c'e' un problema quando non c'e' (fastidioso);
  2. dice che va tutto bene senza aver controllato niente (dannoso, perche'
     da' una sicurezza che non esiste).

E' successo davvero mentre lo scrivevo: la sezione sulle linguette non
trovava nulla da misurare e concludeva "tutto a posto". Questi test
verificano che non possa piu' capitare, e che lo strumento NON MODIFICHI
NULLA - promessa che fa all'utente nella sua prima riga.

Esegui con:  python -m unittest tests.test_verifica_installazione -v
"""

import hashlib
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


def esegui_verifica():
    """Esegue lo strumento e restituisce il testo prodotto."""
    import importlib
    if "verifica_installazione" in sys.modules:
        del sys.modules["verifica_installazione"]
    modulo = importlib.import_module("verifica_installazione")
    modulo._righe.clear()
    modulo._esiti.clear()
    modulo.main()
    return "\n".join(modulo._righe), list(modulo._esiti)


class TestNonModificaNulla(unittest.TestCase):
    """La promessa piu' importante: e' un controllo, non un intervento."""

    def setUp(self):
        self.database = os.path.join(RADICE, "data", "materiali.db")
        self.cartella_backup = os.path.join(RADICE, "data", "backup")

    def _impronta(self, percorso):
        with open(percorso, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def test_il_database_resta_identico(self):
        if not os.path.exists(self.database):
            self.skipTest("nessun database di prova nel progetto")
        prima = self._impronta(self.database)
        esegui_verifica()
        self.assertEqual(self._impronta(self.database), prima,
                         "lo strumento NON deve toccare il database")

    def test_non_crea_ne_cancella_copie_di_sicurezza(self):
        if not os.path.isdir(self.cartella_backup):
            self.skipTest("nessuna cartella di backup nel progetto")
        prima = sorted(os.listdir(self.cartella_backup))
        esegui_verifica()
        self.assertEqual(sorted(os.listdir(self.cartella_backup)), prima,
                         "lo strumento NON deve creare ne' cancellare copie")

    def tearDown(self):
        for nome in os.listdir(RADICE):
            if nome.startswith("VERIFICA_") and nome.endswith(".txt"):
                os.remove(os.path.join(RADICE, nome))


class TestNonDiceMaiOkAVuoto(unittest.TestCase):
    """Il difetto trovato durante la scrittura: dichiarare che le linguette
    stanno bene senza averne misurata nemmeno una."""

    def tearDown(self):
        for nome in os.listdir(RADICE):
            if nome.startswith("VERIFICA_") and nome.endswith(".txt"):
                os.remove(os.path.join(RADICE, nome))

    def test_senza_linguette_da_misurare_non_dichiara_ok(self):
        originale = finto_qt._Base.findChildren
        finto_qt._Base.findChildren = lambda self, tipo, *a, **k: []
        try:
            testo, esiti = esegui_verifica()
        finally:
            finto_qt._Base.findChildren = originale

        self.assertIn("Non e' stato possibile misurare le linguette", testo)
        stati = {titolo: stato for stato, titolo in esiti}
        self.assertNotIn("Il testo delle linguette ci sta", stati,
                         "non deve dichiarare che va bene se non ha misurato nulla")

    def test_quando_misura_dice_quante(self):
        testo, _esiti = esegui_verifica()
        if "Il testo delle linguette ci sta" in testo:
            self.assertIn("linguette misurate", testo,
                          "deve dire QUANTE ne ha misurate, altrimenti un OK "
                          "a vuoto sarebbe indistinguibile da uno vero")

    def test_rileva_le_linguette_troppo_strette(self):
        originale = finto_qt._TabBar.tabRect
        finto_qt._TabBar.tabRect = lambda self, i: finto_qt._Rettangolo(10, 30)
        try:
            testo, _esiti = esegui_verifica()
        finally:
            finto_qt._TabBar.tabRect = originale

        self.assertIn("NON ci sta", testo)
        self.assertIn("servono", testo)
        self.assertIn("ce ne sono 10", testo,
                      "deve riportare le misure esatte, non solo che c'e' un problema")


class TestRobustezza(unittest.TestCase):
    """Un controllo che si pianta a meta' non serve a nessuno."""

    def tearDown(self):
        for nome in os.listdir(RADICE):
            if nome.startswith("VERIFICA_") and nome.endswith(".txt"):
                os.remove(os.path.join(RADICE, nome))

    def test_arriva_in_fondo_anche_se_una_parte_fallisce(self):
        import importlib
        if "verifica_installazione" in sys.modules:
            del sys.modules["verifica_installazione"]
        modulo = importlib.import_module("verifica_installazione")

        def esplode():
            raise RuntimeError("guasto simulato")

        modulo.verifica_backup = lambda *a, **k: esplode()
        modulo._righe.clear()
        modulo._esiti.clear()
        modulo.main()
        testo = "\n".join(modulo._righe)

        self.assertIn("RIEPILOGO", testo,
                      "deve arrivare al riepilogo anche se un controllo fallisce")
        self.assertIn("REGISTRO EVENTI", testo,
                      "i controlli successivi devono comunque essere eseguiti")

    def test_produce_sempre_un_riepilogo(self):
        testo, esiti = esegui_verifica()
        self.assertIn("RIEPILOGO", testo)
        self.assertIn("Controlli eseguiti", testo)
        self.assertGreater(len(esiti), 5, "deve eseguire piu' controlli")

    def test_dice_dove_ha_salvato_lesito(self):
        testo, _e = esegui_verifica()
        self.assertIn("Esito salvato in", testo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
