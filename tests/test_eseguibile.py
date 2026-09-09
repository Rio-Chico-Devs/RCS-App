#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifica della generazione dell'eseguibile (.exe).

Il problema che questo file previene: PyInstaller analizza il codice per
capire quali moduli includere, ma diversi moduli di questa applicazione
vengono importati DENTRO le funzioni, non in cima al file. Se uno non venisse
incluso, l'eseguibile si creerebbe senza errori e si pianterebbe solo al
momento di usare quella funzione - magari mesi dopo, davanti a un cliente.

Per questo pyexecreator.bat elenca i moduli uno per uno. Elencarli a mano pero'
significa che prima o poi qualcuno aggiungera' un modulo e si dimentichera' di
aggiornare l'elenco: questi test se ne accorgono da soli.

Esegui con:  python -m unittest tests.test_eseguibile -v
"""

import ast
import os
import re
import sys
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RADICE)

PACCHETTI = ("database", "ui", "utils", "models")

# Cartelle non collegate all'applicazione (file di lavoro rimasti li')
CARTELLE_ESCLUSE = {"DashboardPage"}


def moduli_dellapplicazione():
    """Tutti i moduli che compongono l'applicazione."""
    trovati = set()
    for pacchetto in PACCHETTI:
        cartella = os.path.join(RADICE, pacchetto)
        if not os.path.isdir(cartella):
            continue
        trovati.add(pacchetto)
        for nome in sorted(os.listdir(cartella)):
            if nome in CARTELLE_ESCLUSE:
                continue
            if nome.endswith(".py") and nome != "__init__.py":
                trovati.add("{}.{}".format(pacchetto, nome[:-3]))
    return trovati


def _chiudi_handler(logger):
    """Chiude e stacca gli handler del registro, senza lasciare file aperti."""
    for handler in list(logger.handlers):
        try:
            handler.close()
        except Exception:
            pass
        logger.removeHandler(handler)


def moduli_elencati_nel_bat():
    percorso = os.path.join(RADICE, "pyexecreator.bat")
    with open(percorso, encoding="utf-8", errors="replace") as f:
        contenuto = f.read()
    return set(re.findall(r"--hidden-import=([\w.]+)", contenuto))


class TestElencoModuli(unittest.TestCase):

    def test_tutti_i_moduli_sono_elencati(self):
        """Se questo test fallisce, e' stato aggiunto un modulo senza
        aggiornare pyexecreator.bat: l'eseguibile potrebbe non includerlo."""
        mancanti = sorted(moduli_dellapplicazione() - moduli_elencati_nel_bat())
        self.assertEqual(
            mancanti, [],
            "moduli non elencati in pyexecreator.bat: {}\n"
            "Aggiungi per ciascuno una riga --hidden-import=<modulo>".format(mancanti))

    def test_nessun_modulo_inesistente_nellelenco(self):
        """L'elenco non deve contenere moduli che non esistono piu':
        sarebbero un errore in fase di creazione dell'eseguibile."""
        nostri = {m for m in moduli_elencati_nel_bat()
                  if m.split(".")[0] in PACCHETTI}
        inesistenti = sorted(nostri - moduli_dellapplicazione())
        self.assertEqual(inesistenti, [],
                         "in pyexecreator.bat sono elencati moduli inesistenti: "
                         "{}".format(inesistenti))

    def test_le_librerie_esterne_sono_elencate(self):
        elencati = moduli_elencati_nel_bat()
        for necessaria in ("PyQt5", "PyQt5.QtWidgets", "PyQt5.QtCore",
                           "PyQt5.QtGui", "sqlite3"):
            self.assertIn(necessaria, elencati)

    def test_il_bat_installa_le_dipendenze(self):
        with open(os.path.join(RADICE, "pyexecreator.bat"),
                  encoding="utf-8", errors="replace") as f:
            contenuto = f.read()
        for pacchetto in ("pyinstaller", "PyQt5"):
            self.assertIn("pip install " + pacchetto, contenuto)

    def test_il_bat_verifica_che_leseguibile_sia_stato_creato(self):
        """Senza questo controllo, un errore di creazione passerebbe
        inosservato e si distribuirebbe l'eseguibile vecchio."""
        with open(os.path.join(RADICE, "pyexecreator.bat"),
                  encoding="utf-8", errors="replace") as f:
            contenuto = f.read()
        self.assertIn("if not exist", contenuto)


class TestCompatibilitaEseguibile(unittest.TestCase):
    """Cose che si comportano diversamente dentro un eseguibile compilato."""

    def test_i_percorsi_tengono_conto_delleseguibile(self):
        """Nell'eseguibile il riferimento e' il file .exe, non i sorgenti."""
        from utils import percorsi
        import inspect
        sorgente = inspect.getsource(percorsi.cartella_applicazione)
        self.assertIn("frozen", sorgente)
        self.assertIn("sys.executable", sorgente)

    def test_i_percorsi_sono_decisi_in_un_posto_solo(self):
        """Se la logica tornasse a essere duplicata, l'eseguibile potrebbe
        scrivere un file dove poi nessuno lo cerca. E' successo davvero con
        config.json, calcolato in due modi diversi in due file.

        Si cerca il modello esatto del calcolo di un percorso,
        'os.path.dirname(sys.executable)'. Cercare solo 'frozen' o
        'sys.executable' darebbe falsi allarmi: segnalazione.py usa 'frozen'
        per riferire se il programma e' compilato, e cambia_database() usa
        'sys.executable' per riavviare il programma. Sono usi legittimi."""
        import glob
        duplicati = []
        consentiti = {
            os.path.join("utils", "percorsi.py"),   # e' il posto giusto
            "main.py",                              # primo avvio, prima dei moduli
        }
        for percorso in glob.glob(os.path.join(RADICE, "*.py")) + \
                glob.glob(os.path.join(RADICE, "*", "*.py")):
            relativo = os.path.relpath(percorso, RADICE)
            if relativo in consentiti or relativo.startswith(("tests", "CruscottoAziendale")):
                continue
            with open(percorso, encoding="utf-8", errors="replace") as f:
                contenuto = f.read()
            if re.search(r"dirname\(\s*sys\.executable\s*\)", contenuto):
                duplicati.append(relativo)

        self.assertEqual(duplicati, [],
                         "la logica dei percorsi e' tornata a essere duplicata "
                         "in: {}".format(duplicati))

    def test_il_registro_funziona_senza_console(self):
        """In un eseguibile senza finestra di console sys.stderr non esiste:
        aggiungere lo stesso l'handler farebbe fallire in silenzio ogni
        messaggio di avviso."""
        import importlib
        import logging
        import utils.logger

        stderr_vero = sys.stderr
        try:
            sys.stderr = None                      # come in un .exe --windowed
            importlib.reload(utils.logger)
            # setup_logger() si ferma se il registro è già configurato: va
            # azzerato, altrimenti si riguarderebbero gli handler di prima.
            _chiudi_handler(logging.getLogger('rcs'))
            logger = utils.logger.setup_logger()
            tipi = [type(h).__name__ for h in logger.handlers]
            self.assertNotIn("StreamHandler", tipi,
                             "senza console non va aggiunto l'handler di console")
            logger.warning("prova")                # non deve sollevare nulla
            logger.error("prova")
        finally:
            sys.stderr = stderr_vero
            importlib.reload(utils.logger)
            _chiudi_handler(logging.getLogger('rcs'))
            utils.logger.setup_logger()


if __name__ == "__main__":
    unittest.main(verbosity=2)
