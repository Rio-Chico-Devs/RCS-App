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


class TestPyQt5NelPythonSbagliato(unittest.TestCase):
    """Successo davvero sul PC dell'azienda.

    VERIFICA.bat era partito con Python 3.11 mentre il programma gira con il
    3.13. PyQt5 e' installato solo nel 3.13, quindi lo strumento ha dichiarato
    PyQt5 non installato e OTTO file del programma mancanti, consigliando di
    ricopiare l'aggiornamento. Erano tutti falsi allarmi, ed era saltato
    proprio il controllo delle linguette - l'unico che si puo' fare solo li'.

    Mandare a caccia di un problema che non esiste fa danno quanto tacere su
    uno vero: si perde tempo e si perde fiducia nello strumento."""

    def _modulo(self):
        import importlib
        if "verifica_installazione" in sys.modules:
            del sys.modules["verifica_installazione"]
        modulo = importlib.import_module("verifica_installazione")
        modulo._righe.clear()
        modulo._esiti.clear()
        return modulo

    def _con_import_che_fallisce(self, modulo, errore):
        import builtins
        originale = builtins.__import__

        def finto_import(nome, *a, **k):
            if nome.startswith("ui."):
                raise errore
            return originale(nome, *a, **k)

        builtins.__import__ = finto_import
        try:
            modulo.verifica_moduli()
        finally:
            builtins.__import__ = originale
        return "\n".join(modulo._righe), list(modulo._esiti)

    def test_manca_solo_pyqt5_non_dice_che_mancano_i_file(self):
        modulo = self._modulo()
        testo, esiti = self._con_import_che_fallisce(
            modulo, ImportError("No module named 'PyQt5'"))

        self.assertNotIn("Ricopia tutti i file", testo,
                         "e' il consiglio sbagliato: i file ci sono tutti")
        self.assertNotIn(modulo.ERRORE, [stato for stato, _t in esiti],
                         "non e' un errore dell'installazione")
        self.assertIn("I file ci sono tutti", testo)

    def test_un_file_davvero_mancante_resta_un_errore(self):
        """L'altra direzione: non deve diventare indulgente con i guasti veri."""
        modulo = self._modulo()
        testo, esiti = self._con_import_che_fallisce(
            modulo, ImportError("No module named 'ui.main_window'"))

        self.assertIn(modulo.ERRORE, [stato for stato, _t in esiti])
        self.assertIn("Ricopia tutti i file", testo)

    def test_dice_quale_python_sta_usando(self):
        modulo = self._modulo()
        modulo._pyqt5_mancante(ImportError("No module named 'PyQt5'"))
        testo = "\n".join(modulo._righe)

        self.assertIn(sys.executable, testo,
                      "senza sapere QUALE Python e', il messaggio non serve a niente")
        self.assertIn("piu' versioni di Python", testo,
                      "deve spiegare che il pacchetto puo' essere su un altro Python")

    def tearDown(self):
        for nome in os.listdir(RADICE):
            if nome.startswith("VERIFICA_") and nome.endswith(".txt"):
                os.remove(os.path.join(RADICE, nome))


class TestIngrandimentoDelloSchermo(unittest.TestCase):
    """Su Windows si puo' chiedere di ingrandire testo e finestre al 125% o al
    150%, e sui portatili e' quasi sempre cosi'. Il programma non dice a Qt
    come comportarsi, quindi Qt riferisce una risoluzione ridotta e
    ui/responsive.py decide le misure su quella.

    E' la spiegazione piu' probabile dei difetti grafici che comparivano su un
    computer e non su un altro. Qui non si corregge: si MISURA, perche' la
    correzione va decisa sapendo cosa riferiscono davvero le postazioni."""

    def tearDown(self):
        finto_qt._Application.ingrandimento = 1.0
        for nome in os.listdir(RADICE):
            if nome.startswith("VERIFICA_") and nome.endswith(".txt"):
                os.remove(os.path.join(RADICE, nome))

    def test_schermo_normale_nessuna_segnalazione(self):
        finto_qt._Application.ingrandimento = 1.0
        testo, _e = esegui_verifica()
        self.assertIn("Schermo senza ingrandimento", testo)

    def test_schermo_ingrandito_viene_segnalato_con_la_percentuale(self):
        finto_qt._Application.ingrandimento = 1.5
        testo, _e = esegui_verifica()
        self.assertIn("Lo schermo e' ingrandito da Windows", testo)
        self.assertIn("150%", testo,
                      "deve riportare la percentuale esatta, non solo che c'e'")

    def test_non_spaventa_l_utente(self):
        """E' un dato da raccogliere, non un guasto: il programma funziona."""
        finto_qt._Application.ingrandimento = 1.25
        testo, esiti = esegui_verifica()
        stati = {titolo: stato for stato, titolo in esiti}
        self.assertEqual(stati.get("Lo schermo e' ingrandito da Windows"), "ATTENZIONE",
                         "non e' un errore bloccante")
        self.assertIn("non impedisce di lavorare", testo)


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
