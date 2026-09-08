#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prove di interruzione: spegnimenti improvvisi, aggiornamenti di sistema,
conflitti fra piu' computer, cartella di rete che sparisce.

A differenza degli altri test, qui si usano PROCESSI VERI che vengono uccisi
mentre stanno scrivendo (kill -9, come fa Windows quando si spegne per un
aggiornamento) e piu' processi che scrivono davvero nello stesso momento sullo
stesso file: e' l'unico modo di riprodurre cio' che e' successo il 3 settembre.

Esegui con:  python -m unittest tests.test_interruzioni -v
"""

import multiprocessing
import os
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RADICE)

from database import backup_manager as bm
from database.db_manager import DatabaseManager, DatabaseOccupato


def preventivo(indice):
    return {
        'nome_cliente': f'Cliente {indice}', 'numero_ordine': f'ORD-{indice}',
        'misura': 'x', 'descrizione': 'd', 'codice': 'c', 'finitura': 'f',
        'costo_totale_materiali': 1.0, 'costi_accessori': 1.0,
        'minuti_taglio': 1.0, 'minuti_avvolgimento': 1.0, 'minuti_pulizia': 1.0,
        'minuti_rettifica': 1.0, 'minuti_imballaggio': 1.0, 'tot_mano_opera': 1.0,
        'subtotale': 1.0, 'maggiorazione_25': 1.0, 'preventivo_finale': 1.0,
        'prezzo_cliente': 1.0, 'materiali_utilizzati': [],
    }


class BaseInterruzioni(unittest.TestCase):
    def setUp(self):
        bm._esito_avvio_cache.clear()
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "materiali.db")
        self._orig_app = bm.cartella_app
        bm.cartella_app = lambda: self.tmp
        DatabaseManager(db_path=self.db)      # crea lo schema

    def tearDown(self):
        bm.cartella_app = self._orig_app
        bm._esito_avvio_cache.clear()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _conta(self):
        with sqlite3.connect(self.db) as conn:
            return conn.execute("SELECT COUNT(*) FROM preventivi").fetchone()[0]


# ---------------------------------------------------------------------------
# Spegnimento improvviso durante una scrittura
# ---------------------------------------------------------------------------

SCRITTORE_INFINITO = """
import sys, time
sys.path.insert(0, {radice!r})
from database.db_manager import DatabaseManager
gestore = DatabaseManager(db_path={db!r})
gestore.verifica_dopo_scrittura = False
i = 0
while True:
    gestore.add_preventivo({{
        'nome_cliente': 'C%d' % i, 'numero_ordine': 'O%d' % i, 'misura': 'x',
        'descrizione': 'd' * 500, 'codice': 'c', 'finitura': 'f',
        'costo_totale_materiali': 1.0, 'costi_accessori': 1.0,
        'minuti_taglio': 1.0, 'minuti_avvolgimento': 1.0, 'minuti_pulizia': 1.0,
        'minuti_rettifica': 1.0, 'minuti_imballaggio': 1.0, 'tot_mano_opera': 1.0,
        'subtotale': 1.0, 'maggiorazione_25': 1.0, 'preventivo_finale': 1.0,
        'prezzo_cliente': 1.0, 'materiali_utilizzati': [{{'n': 'm'}}] * 50,
    }})
    i += 1
"""


class TestSpegnimentoImprovviso(BaseInterruzioni):
    """Il caso del 3 settembre: il programma viene terminato di colpo mentre
    sta salvando."""

    def _uccidi_mentre_scrive(self, dopo_secondi=0.8):
        script = os.path.join(self.tmp, "scrittore.py")
        with open(script, "w", encoding="utf-8") as f:
            f.write(SCRITTORE_INFINITO.format(radice=RADICE, db=self.db))

        processo = subprocess.Popen([sys.executable, script],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        time.sleep(dopo_secondi)
        processo.send_signal(signal.SIGKILL)    # come uno spegnimento forzato
        processo.wait(timeout=10)
        return processo

    def test_il_database_resta_utilizzabile(self):
        """SQLite deve poter recuperare da solo alla riapertura."""
        self._uccidi_mentre_scrive()

        integro, messaggio, _ms = bm.verifica_integrita(self.db)
        righe = self._conta()
        print(f"\n    [kill durante scrittura] {righe} preventivi salvati, "
              f"integrita': {messaggio}")
        self.assertTrue(integro,
                        f"il database non deve restare danneggiato: {messaggio}")
        self.assertGreater(righe, 0, "le scritture completate devono esserci")

    def test_riapertura_dopo_lo_spegnimento(self):
        """Riaprendo, il programma deve funzionare e fare il suo backup."""
        self._uccidi_mentre_scrive()

        bm._esito_avvio_cache.clear()
        gestore = DatabaseManager(db_path=self.db)
        self.assertFalse(gestore.database_inutilizzabile)
        self.assertIsNone(gestore.avviso_integrita)

        nuovo = gestore.add_preventivo(preventivo(9999))
        self.assertIsNotNone(nuovo, "si deve poter continuare a lavorare")

    def test_dieci_spegnimenti_di_fila(self):
        """Ripetuto piu' volte: e' cosi' che si scoprono i danni rari."""
        quante = 10
        for tentativo in range(quante):
            self._uccidi_mentre_scrive(dopo_secondi=0.3 + tentativo * 0.05)
            integro, messaggio, _ms = bm.verifica_integrita(self.db)
            self.assertTrue(
                integro,
                f"database danneggiato al tentativo {tentativo + 1}: {messaggio}")
        print(f"\n    [kill ripetuti] {quante} spegnimenti improvvisi, "
              f"{self._conta()} preventivi, database sempre integro")

    def test_eventuale_file_di_appoggio_rimasto_e_innocuo(self):
        """Dopo uno spegnimento improvviso puo' restare un file '-journal'
        accanto al database. Verificato sul campo:

        - se lo spegnimento avviene a scrittura avviata, il file contiene una
          transazione da annullare e viene risolto alla riapertura;
        - se avviene PRIMA che l'intestazione del file sia stata scritta per
          intero, SQLite lo considera non valido, lo IGNORA e lo lascia li'.
          E' un residuo inerte, non una scrittura in sospeso.

        Quello che conta non e' l'assenza del file, ma che il database sia
        coerente e utilizzabile in entrambi i casi.

        ATTENZIONE per il futuro: NON cancellare i file '-journal' dal codice.
        Se uno di essi fosse valido, cancellarlo causerebbe esattamente il tipo
        di danneggiamento che tutto questo lavoro serve a prevenire."""
        self._uccidi_mentre_scrive()
        bm._esito_avvio_cache.clear()
        DatabaseManager(db_path=self.db)     # la riapertura recupera

        residui = [f for f in os.listdir(self.tmp) if f.startswith("materiali.db-")]

        integro, messaggio, _ms = bm.verifica_integrita(self.db)
        self.assertTrue(integro, f"il database deve essere coerente: {messaggio}")

        # e si deve poter continuare a lavorare normalmente
        gestore = DatabaseManager(db_path=self.db)
        self.assertIsNotNone(gestore.add_preventivo(preventivo(12345)))
        integro_dopo, messaggio_dopo, _ms = bm.verifica_integrita(self.db)
        self.assertTrue(integro_dopo,
                        f"il database deve restare coerente scrivendo: {messaggio_dopo}")

        print(f"\n    [file di appoggio] residui: {residui or 'nessuno'} | "
              f"database coerente e scrivibile: sì")

    def _crea_journal_valido(self):
        """Produce di proposito un file di appoggio VALIDO e non risolto.

        Non ci si puo' affidare a un kill a caso: a seconda dell'istante il
        file puo' risultare incompleto e quindi inerte. Qui si apre una
        transazione, si scrive davvero (cosi' l'intestazione viene completata)
        e si uccide il processo prima della conferma."""
        script = os.path.join(self.tmp, "sospeso.py")
        with open(script, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(f"""
                import sqlite3, time
                conn = sqlite3.connect({self.db!r}, isolation_level=None)
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("INSERT INTO clienti (nome) VALUES ('mai confermato')")
                print("pronto", flush=True)
                time.sleep(60)
            """))
        processo = subprocess.Popen([sys.executable, script],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, text=True)
        processo.stdout.readline()          # attende che la transazione sia aperta
        processo.send_signal(signal.SIGKILL)
        processo.wait(timeout=10)

    def test_il_database_resta_coerente_con_una_scrittura_in_sospeso(self):
        """Con un file di appoggio presente e una transazione mai confermata,
        il database deve risultare coerente e utilizzabile.

        NOTA: non si pretende che il file '-journal' sparisca. Verificato sul
        campo, SQLite lo elimina solo quando c'e' davvero qualcosa da annullare
        sul file principale; se la transazione interrotta non aveva ancora
        riversato pagine, non c'e' nulla da fare e il file resta li', inerte.
        Cio' che conta e' la coerenza dei dati, verificata qui sotto."""
        self._crea_journal_valido()
        self.assertTrue(os.path.exists(self.db + "-journal"),
                        "la prova deve partire da un file di appoggio presente")

        bm.recupera_dopo_arresto(self.db)

        integro, messaggio, _ms = bm.verifica_integrita(self.db)
        self.assertTrue(integro, f"il database deve essere coerente: {messaggio}")

        bm._esito_avvio_cache.clear()
        gestore = DatabaseManager(db_path=self.db)
        self.assertFalse(gestore.database_inutilizzabile)
        self.assertIsNotNone(gestore.add_preventivo(preventivo(777)),
                             "si deve poter continuare a lavorare")
        print("\n    [scrittura in sospeso] database coerente e utilizzabile")

    def test_la_transazione_non_confermata_viene_annullata(self):
        """Il dato scritto ma mai confermato NON deve comparire nel database:
        e' esattamente cio' che il recupero deve garantire."""
        self._crea_journal_valido()
        bm.recupera_dopo_arresto(self.db)

        with sqlite3.connect(self.db) as conn:
            quanti = conn.execute(
                "SELECT COUNT(*) FROM clienti WHERE nome = 'mai confermato'").fetchone()[0]
        self.assertEqual(quanti, 0,
                         "una transazione interrotta non deve lasciare traccia")
        print("    [recupero] la scrittura interrotta e' stata annullata correttamente")


# ---------------------------------------------------------------------------
# Piu' computer che scrivono insieme
# ---------------------------------------------------------------------------

def _scrittore_concorrente(db_path, primo_indice, quanti, coda):
    """Simula una postazione che salva preventivi."""
    sys.path.insert(0, RADICE)
    from database.db_manager import DatabaseManager, DatabaseOccupato
    gestore = DatabaseManager(db_path=db_path)
    gestore.verifica_dopo_scrittura = False
    riusciti, rifiutati, errori = 0, 0, []
    for i in range(quanti):
        try:
            gestore.add_preventivo(preventivo(primo_indice + i))
            riusciti += 1
        except DatabaseOccupato:
            rifiutati += 1          # accettabile: l'utente riprova
        except Exception as e:
            errori.append(f"{type(e).__name__}: {e}")
    coda.put((riusciti, rifiutati, errori))


class TestScrittureContemporanee(BaseInterruzioni):
    """Quattro postazioni che salvano nello stesso momento sullo stesso file:
    e' la situazione della cartella di rete condivisa."""

    def test_nessuna_scrittura_persa_ne_database_rovinato(self):
        postazioni, per_postazione = 4, 15
        coda = multiprocessing.Queue()
        processi = [
            multiprocessing.Process(
                target=_scrittore_concorrente,
                args=(self.db, 1000 * (n + 1), per_postazione, coda))
            for n in range(postazioni)
        ]
        for p in processi:
            p.start()
        for p in processi:
            p.join(timeout=120)

        risultati = [coda.get() for _ in range(postazioni)]
        riusciti = sum(r[0] for r in risultati)
        rifiutati = sum(r[1] for r in risultati)
        errori = [e for r in risultati for e in r[2]]

        righe = self._conta()
        integro, messaggio, _ms = bm.verifica_integrita(self.db)

        print(f"\n    [4 postazioni insieme] {postazioni * per_postazione} tentativi -> "
              f"{riusciti} riusciti, {rifiutati} rimandati, {len(errori)} errori")
        print(f"      righe nel database: {righe} | integrita': {messaggio}")

        self.assertTrue(integro, f"il database si e' rovinato: {messaggio}")
        self.assertEqual(errori, [], "nessun errore imprevisto ammesso")
        self.assertEqual(righe, riusciti,
                         "ogni salvataggio dato per riuscito deve essere nel database")
        self.assertGreater(riusciti, 0)

    def test_letture_durante_le_scritture(self):
        """Mentre un'altra postazione scrive, la lettura non deve fallire."""
        coda = multiprocessing.Queue()
        scrittore = multiprocessing.Process(
            target=_scrittore_concorrente, args=(self.db, 5000, 25, coda))
        scrittore.start()

        gestore = DatabaseManager(db_path=self.db)
        letture, fallite = 0, 0
        inizio = time.time()
        while scrittore.is_alive() and time.time() - inizio < 60:
            try:
                gestore.get_all_preventivi()
                letture += 1
            except Exception:
                fallite += 1
        scrittore.join(timeout=60)
        coda.get()

        print(f"\n    [lettura mentre si scrive] {letture} letture riuscite, "
              f"{fallite} fallite")
        self.assertEqual(fallite, 0, "leggere non deve mai fallire")

    def test_copie_di_backup_non_si_sovrascrivono(self):
        """Due postazioni che aprono il programma nello stesso secondo devono
        produrre due copie distinte, non scrivere sullo stesso file."""
        cartella = os.path.join(self.tmp, "backup")
        os.makedirs(cartella, exist_ok=True)
        nomi = set()
        for _ in range(8):
            percorso = bm._nome_univoco(cartella, bm.PREFISSO_BACKUP)
            open(percorso, "wb").write(b"x")    # occupa il nome, come farebbe la copia
            nomi.add(percorso)
        print(f"\n    [nomi copie] 8 copie nello stesso istante -> "
              f"{len(nomi)} nomi distinti")
        self.assertEqual(len(nomi), 8)


# ---------------------------------------------------------------------------
# La cartella di rete che sparisce
# ---------------------------------------------------------------------------

class TestCartellaIrraggiungibile(BaseInterruzioni):

    def test_backup_impossibile_non_blocca_il_programma(self):
        """Se la cartella dei backup non e' scrivibile (rete caduta, permessi),
        il programma deve comunque partire."""
        cartella = os.path.join(self.tmp, "backup")
        os.makedirs(cartella, exist_ok=True)
        os.chmod(cartella, 0o500)      # sola lettura
        try:
            bm._esito_avvio_cache.clear()
            gestore = DatabaseManager(db_path=self.db)
            self.assertFalse(gestore.database_inutilizzabile,
                             "il programma deve partire anche senza poter fare il backup")
            nuovo = gestore.add_preventivo(preventivo(1))
            self.assertIsNotNone(nuovo, "si deve poter lavorare comunque")
            print("\n    [cartella backup non scrivibile] il programma parte e funziona")
        finally:
            os.chmod(cartella, 0o700)

    def test_database_sparito(self):
        """Se il file del database non c'e' piu' (unita' di rete scollegata),
        il messaggio deve essere comprensibile, non un errore tecnico."""
        os.remove(self.db)
        bm._esito_avvio_cache.clear()
        esito = bm.esegui_backup_avvio(self.db)
        self.assertTrue(esito["primo_avvio"])
        self.assertIsNone(esito["avviso"])
        print("\n    [database assente] trattato come prima installazione, nessun allarme")

    def test_verifica_su_percorso_irraggiungibile(self):
        integro, messaggio, _ms = bm.verifica_integrita("//SERVER-SPENTO/rcs/materiali.db")
        self.assertFalse(integro)
        self.assertIn("inesistente", messaggio)


# ---------------------------------------------------------------------------
# Dati sporchi
# ---------------------------------------------------------------------------

class TestDatiStrani(BaseInterruzioni):
    """Testi inattesi non devono rompere il salvataggio ne' il database."""

    def test_caratteri_speciali_e_testi_lunghi(self):
        gestore = DatabaseManager(db_path=self.db)
        casi = [
            "O'Brien & Figli",                       # apostrofo
            "Ditta \"Virgolette\" SpA",
            "Società àèìòù ÀÈÌÒÙ",                    # accenti
            "'; DROP TABLE preventivi; --",           # tentativo di iniezione
            "Riga1\nRiga2\tTab",                      # a capo e tabulazioni
            "🔧 Emoji Srl 😀",
            "X" * 5000,                               # testo lunghissimo
            "",                                       # vuoto
        ]
        for indice, nome in enumerate(casi):
            dati = preventivo(indice)
            dati['nome_cliente'] = nome
            nuovo = gestore.add_preventivo(dati)
            self.assertIsNotNone(nuovo, f"salvataggio fallito con: {nome[:30]!r}")

        integro, messaggio = gestore.verifica_integrita()
        self.assertTrue(integro, f"database rovinato da testi strani: {messaggio}")

        with sqlite3.connect(self.db) as conn:
            tabelle = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertIn("preventivi", tabelle,
                      "la tabella deve esistere ancora (nessuna iniezione riuscita)")
        print(f"\n    [dati strani] {len(casi)} casi limite salvati, database integro")

    def test_numeri_estremi(self):
        gestore = DatabaseManager(db_path=self.db)
        for valore in (0.0, -1.0, 1e12, 0.000001, 999999999.99):
            dati = preventivo(0)
            dati['prezzo_cliente'] = valore
            dati['preventivo_finale'] = valore
            self.assertIsNotNone(gestore.add_preventivo(dati),
                                 f"fallito con prezzo {valore}")
        integro, _m = gestore.verifica_integrita()
        self.assertTrue(integro)


if __name__ == "__main__":
    unittest.main(verbosity=2)
