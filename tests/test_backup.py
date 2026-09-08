#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del sistema di backup, verifica di integrità e diagnostica.
Esegui con:  python -m pytest tests/test_backup.py -v
         o:  python -m unittest tests.test_backup -v
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import backup_manager as bm


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def crea_db_valido(percorso, righe=200):
    """Crea un database SQLite sano con abbastanza righe da occupare più pagine."""
    conn = sqlite3.connect(percorso)
    conn.execute("CREATE TABLE preventivi (id INTEGER PRIMARY KEY, testo TEXT)")
    conn.executemany("INSERT INTO preventivi (testo) VALUES (?)",
                     [("riga di prova numero {} con del testo".format(i),) for i in range(righe)])
    conn.commit()
    conn.close()
    return percorso


def corrompi(percorso):
    """Danneggia il file sovrascrivendo una pagina interna, come farebbe una
    scrittura interrotta."""
    with open(percorso, "r+b") as f:
        f.seek(4096)          # pagina 2: contiene dati, non l'intestazione
        f.write(b"\xff" * 4096)


def nome_backup(quando):
    return bm.PREFISSO_BACKUP + quando.strftime(bm.FORMATO_TIMESTAMP) + ".db"


class BaseTemp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "materiali.db")
        self.backup_dir = os.path.join(self.tmp, "backup")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Verifica di integrità
# ---------------------------------------------------------------------------

class TestVerificaIntegrita(BaseTemp):

    def test_database_sano_passa(self):
        crea_db_valido(self.db)
        ok, messaggio, durata = bm.verifica_integrita(self.db)
        self.assertTrue(ok, "un database sano deve passare la verifica")
        self.assertEqual(messaggio, "ok")
        self.assertGreaterEqual(durata, 0)

    def test_database_corrotto_viene_rilevato(self):
        crea_db_valido(self.db)
        corrompi(self.db)
        ok, messaggio, _ = bm.verifica_integrita(self.db)
        self.assertFalse(ok, "un database corrotto NON deve passare la verifica")
        self.assertNotEqual(messaggio, "ok")

    def test_file_inesistente(self):
        ok, messaggio, _ = bm.verifica_integrita(os.path.join(self.tmp, "boh.db"))
        self.assertFalse(ok)
        self.assertIn("inesistente", messaggio)

    def test_file_non_database(self):
        percorso = os.path.join(self.tmp, "finto.db")
        with open(percorso, "wb") as f:
            f.write(b"questo non e' un database")
        ok, _messaggio, _ = bm.verifica_integrita(percorso)
        self.assertFalse(ok)


# ---------------------------------------------------------------------------
# Backup all'avvio
# ---------------------------------------------------------------------------

class TestBackupAvvio(BaseTemp):

    def test_database_sano_crea_backup_verificato(self):
        crea_db_valido(self.db)
        esito = bm.esegui_backup_avvio(self.db)

        self.assertTrue(esito["integro"])
        self.assertIsNone(esito["avviso"], "nessun avviso se è tutto a posto")
        self.assertIsNotNone(esito["backup"])
        self.assertTrue(os.path.exists(esito["backup"]))

        ok, _m, _ms = bm.verifica_integrita(esito["backup"])
        self.assertTrue(ok, "il backup creato deve essere a sua volta integro")

    def test_database_sano_crea_copia_protetta(self):
        crea_db_valido(self.db)
        esito = bm.esegui_backup_avvio(self.db)
        self.assertIsNotNone(esito["copia_sicura"])
        self.assertTrue(os.path.exists(esito["copia_sicura"]))
        self.assertIn("sicurezza", esito["copia_sicura"])

    def test_la_copia_protetta_non_si_rifa_a_ogni_apertura(self):
        """Rifarla a ogni avvio significherebbe una scrittura in piu' sulla
        cartella di rete ogni volta, e farebbe ruotare le copie protette per
        numero di aperture invece che nel tempo: cinque riaperture di fila
        cancellerebbero tutta la profondita'."""
        crea_db_valido(self.db)
        bm.esegui_backup_avvio(self.db)
        sicurezza = os.path.join(self.backup_dir, "sicurezza")
        dopo_la_prima = len(os.listdir(sicurezza))

        for _ in range(6):                      # altre sei aperture ravvicinate
            bm._esito_avvio_cache.clear()
            bm.esegui_backup_avvio(self.db)

        self.assertEqual(len(os.listdir(sicurezza)), dopo_la_prima,
                         "entro le 24 ore non deve rifare la copia protetta")

    def test_la_copia_protetta_si_rifa_se_e_passato_un_giorno(self):
        crea_db_valido(self.db)
        bm.esegui_backup_avvio(self.db)
        sicurezza = os.path.join(self.backup_dir, "sicurezza")

        # invecchia la copia protetta rinominandola a ieri
        for nome in os.listdir(sicurezza):
            vecchio = (datetime.now() - timedelta(days=2)).strftime(bm.FORMATO_TIMESTAMP)
            os.rename(os.path.join(sicurezza, nome),
                      os.path.join(sicurezza, bm.PREFISSO_SICUREZZA + vecchio + ".db"))

        bm._esito_avvio_cache.clear()
        bm.esegui_backup_avvio(self.db)
        self.assertEqual(len(os.listdir(sicurezza)), 2,
                         "passato un giorno, una nuova copia protetta va fatta")

    def test_su_problema_la_copia_protetta_si_fa_subito(self):
        """Quando si rileva un danno non si aspetta il giorno dopo."""
        crea_db_valido(self.db)
        bm.esegui_backup_avvio(self.db)          # copia protetta di oggi
        sicurezza = os.path.join(self.backup_dir, "sicurezza")
        prima = len(os.listdir(sicurezza))

        corrompi(self.db)
        bm._esito_avvio_cache.clear()
        esito = bm.esegui_backup_avvio(self.db)

        self.assertFalse(esito["integro"])
        self.assertIsNotNone(esito["copia_sicura"])
        self.assertEqual(len(os.listdir(sicurezza)), prima + 1,
                         "in caso di problema la copia va messa al sicuro subito")

    def test_database_corrotto_non_cancella_i_backup_buoni(self):
        # Un backup buono già presente
        crea_db_valido(self.db)
        os.makedirs(self.backup_dir, exist_ok=True)
        buono = os.path.join(self.backup_dir, nome_backup(datetime.now() - timedelta(days=1)))
        shutil.copy2(self.db, buono)

        # Ora il database si corrompe
        corrompi(self.db)
        esito = bm.esegui_backup_avvio(self.db)

        self.assertFalse(esito["integro"])
        self.assertIsNotNone(esito["avviso"], "l'utente deve essere avvisato")
        self.assertTrue(os.path.exists(buono),
                        "il backup buono NON deve essere cancellato dalla rotazione")

    def test_database_corrotto_finisce_in_quarantena(self):
        crea_db_valido(self.db)
        corrompi(self.db)
        bm.esegui_backup_avvio(self.db)

        cartella_corrotti = os.path.join(self.backup_dir, "corrotti")
        self.assertTrue(os.path.isdir(cartella_corrotti))
        file_corrotti = os.listdir(cartella_corrotti)
        self.assertEqual(len(file_corrotti), 1)
        self.assertTrue(file_corrotti[0].startswith(bm.PREFISSO_CORROTTO))

    def test_database_corrotto_mette_al_sicuro_lultimo_backup_valido(self):
        crea_db_valido(self.db)
        os.makedirs(self.backup_dir, exist_ok=True)
        buono = os.path.join(self.backup_dir, nome_backup(datetime.now() - timedelta(hours=3)))
        shutil.copy2(self.db, buono)

        corrompi(self.db)
        esito = bm.esegui_backup_avvio(self.db)

        self.assertIsNotNone(esito["copia_sicura"],
                             "deve mettere al riparo una copia del backup buono")
        self.assertTrue(os.path.exists(esito["copia_sicura"]))

    def test_corrotto_e_nessun_backup_valido_avvisa_comunque(self):
        crea_db_valido(self.db)
        os.makedirs(self.backup_dir, exist_ok=True)
        # Anche il backup presente è corrotto
        rotto = os.path.join(self.backup_dir, nome_backup(datetime.now() - timedelta(days=2)))
        shutil.copy2(self.db, rotto)
        corrompi(rotto)
        corrompi(self.db)

        esito = bm.esegui_backup_avvio(self.db)
        self.assertFalse(esito["integro"])
        self.assertIsNone(esito["copia_sicura"])
        self.assertIn("nessun backup integro", esito["avviso"])

    def test_diagnostica_registrata(self):
        crea_db_valido(self.db)
        esito = bm.esegui_backup_avvio(self.db)
        diag = esito["diagnostica"]
        self.assertIn("pc", diag)
        self.assertIn("su_rete", diag)
        self.assertIn("integrita", diag)
        self.assertIn("verifica_ms", diag)


# ---------------------------------------------------------------------------
# Politica di conservazione
# ---------------------------------------------------------------------------

class TestRetention(BaseTemp):

    def setUp(self):
        super().setUp()
        os.makedirs(self.backup_dir, exist_ok=True)
        crea_db_valido(self.db, righe=10)

    def _crea_backup_datato(self, quando):
        percorso = os.path.join(self.backup_dir, nome_backup(quando))
        shutil.copy2(self.db, percorso)
        return percorso

    def test_tiene_tutti_i_backup_recenti(self):
        adesso = datetime.now()
        creati = [self._crea_backup_datato(adesso - timedelta(hours=h)) for h in range(0, 10, 2)]
        bm.applica_retention(self.backup_dir)
        for percorso in creati:
            self.assertTrue(os.path.exists(percorso),
                            "i backup delle ultime 48 ore vanno tenuti tutti")

    def test_tiene_uno_al_giorno_nel_mese(self):
        adesso = datetime.now()
        # Tre backup nello stesso giorno, 10 giorni fa
        giorno = adesso - timedelta(days=10)
        primi = [self._crea_backup_datato(giorno.replace(hour=h, minute=0, second=0))
                 for h in (8, 12, 17)]

        bm.applica_retention(self.backup_dir)

        rimasti = [p for p in primi if os.path.exists(p)]
        self.assertEqual(len(rimasti), 1,
                         "di un giorno vecchio deve restare un solo backup")
        self.assertEqual(os.path.basename(rimasti[0]), os.path.basename(primi[-1]),
                         "deve restare il più recente della giornata")

    def test_copre_tutto_il_mese(self):
        adesso = datetime.now()
        for giorni in range(1, 29):
            self._crea_backup_datato(adesso - timedelta(days=giorni, hours=1))

        bm.applica_retention(self.backup_dir)

        rimasti = bm.elenca_backup(self.backup_dir)
        self.assertGreaterEqual(len(rimasti), 28,
                                "deve restare almeno un backup per ciascuno dei 28 giorni")

    def test_dirada_oltre_il_mese(self):
        adesso = datetime.now()
        # 5 backup nello stesso mese, ma di 4 mesi fa
        vecchio = adesso - timedelta(days=120)
        for g in range(5):
            self._crea_backup_datato(vecchio + timedelta(days=g))

        bm.applica_retention(self.backup_dir)

        rimasti = [n for _t, n in bm.elenca_backup(self.backup_dir)]
        self.assertEqual(len(rimasti), 1,
                         "oltre il mese deve restare un solo backup per mese")

    def test_non_tocca_file_estranei(self):
        estraneo = os.path.join(self.backup_dir, "appunti.txt")
        with open(estraneo, "w") as f:
            f.write("da non cancellare")
        self._crea_backup_datato(datetime.now() - timedelta(days=200))

        bm.applica_retention(self.backup_dir)
        self.assertTrue(os.path.exists(estraneo))


# ---------------------------------------------------------------------------
# Copia verificata
# ---------------------------------------------------------------------------

class TestCopiaVerificata(BaseTemp):

    def test_copia_buona_accettata(self):
        crea_db_valido(self.db)
        destinazione = os.path.join(self.tmp, "copia.db")
        self.assertTrue(bm._copia_verificata(self.db, destinazione))
        self.assertTrue(os.path.exists(destinazione))

    def test_copia_di_sorgente_corrotta_viene_rifiutata_e_rimossa(self):
        crea_db_valido(self.db)
        corrompi(self.db)
        destinazione = os.path.join(self.tmp, "copia.db")
        self.assertFalse(bm._copia_verificata(self.db, destinazione))
        self.assertFalse(os.path.exists(destinazione),
                         "una copia non valida non deve restare sul disco")


# ---------------------------------------------------------------------------
# Sessioni attive (rilevamento accessi contemporanei)
# ---------------------------------------------------------------------------

class TestSessioni(BaseTemp):

    def test_registra_e_chiude_sessione(self):
        crea_db_valido(self.db)
        altri = bm.registra_sessione(self.db)
        self.assertEqual(altri, [], "nessun altro PC dovrebbe risultare aperto")

        percorso = bm._percorso_sessioni(self.db)
        self.assertTrue(os.path.exists(percorso))
        self.assertIn(bm._chiave_sessione(), bm._leggi_sessioni(percorso))

        bm.chiudi_sessione(self.db)
        self.assertNotIn(bm._chiave_sessione(), bm._leggi_sessioni(percorso))

    def test_rileva_altro_pc_aperto(self):
        crea_db_valido(self.db)
        percorso = bm._percorso_sessioni(self.db)
        bm._scrivi_sessioni(percorso, {
            "ALTROPC|mario": {"avvio": datetime.now().isoformat(timespec="seconds"), "pid": 999}
        })

        altri = bm.registra_sessione(self.db)
        self.assertEqual(altri, ["ALTROPC|mario"])

    def test_sessioni_vecchie_vengono_ignorate(self):
        crea_db_valido(self.db)
        percorso = bm._percorso_sessioni(self.db)
        vecchia = (datetime.now() - timedelta(hours=bm.ORE_SESSIONE_SCADUTA + 1)).isoformat()
        bm._scrivi_sessioni(percorso, {"VECCHIO|pc": {"avvio": vecchia, "pid": 1}})

        altri = bm.registra_sessione(self.db)
        self.assertEqual(altri, [], "una sessione scaduta non va contata come aperta")


# ---------------------------------------------------------------------------
# Verifica dopo scrittura
# ---------------------------------------------------------------------------

class TestVerificaDopoScrittura(BaseTemp):

    def test_ok_su_database_sano(self):
        crea_db_valido(self.db)
        self.assertTrue(bm.verifica_dopo_scrittura(self.db, "test"))

    def test_rileva_corruzione_e_protegge_backup(self):
        crea_db_valido(self.db)
        os.makedirs(self.backup_dir, exist_ok=True)
        buono = os.path.join(self.backup_dir, nome_backup(datetime.now() - timedelta(hours=1)))
        shutil.copy2(self.db, buono)

        corrompi(self.db)
        self.assertFalse(bm.verifica_dopo_scrittura(self.db, "add_preventivo"))

        sicurezza = os.path.join(self.backup_dir, "sicurezza")
        self.assertTrue(os.path.isdir(sicurezza))
        self.assertTrue(os.listdir(sicurezza),
                        "deve aver messo al sicuro una copia buona")


# ---------------------------------------------------------------------------
# Casi limite: prima installazione e riuso dell'esito
# ---------------------------------------------------------------------------

class TestCasiLimite(BaseTemp):

    def setUp(self):
        super().setUp()
        bm._esito_avvio_cache.clear()

    def tearDown(self):
        bm._esito_avvio_cache.clear()
        super().tearDown()

    def test_database_inesistente_non_e_un_allarme(self):
        """Prima installazione: non c'è ancora nessun database, e non è un errore."""
        esito = bm.esegui_backup_avvio(self.db)
        self.assertTrue(esito["integro"])
        self.assertTrue(esito["primo_avvio"])
        self.assertIsNone(esito["avviso"],
                          "al primo avvio non deve comparire nessun allarme")

    def test_esito_riusato_nello_stesso_processo(self):
        """Chiamata due volte (controllo in main.py + DatabaseManager): il
        secondo giro riusa l'esito e non crea un secondo backup."""
        crea_db_valido(self.db)
        primo = bm.esegui_backup_avvio(self.db)
        quanti_dopo_primo = len(bm.elenca_backup(self.backup_dir))

        secondo = bm.esegui_backup_avvio(self.db)
        self.assertIs(primo, secondo, "deve restituire lo stesso esito")
        self.assertEqual(len(bm.elenca_backup(self.backup_dir)), quanti_dopo_primo,
                         "non deve creare un secondo backup nello stesso avvio")


class TestIntegrazioneDatabaseManager(BaseTemp):
    """Verifica il comportamento attraverso DatabaseManager, come in produzione."""

    def setUp(self):
        super().setUp()
        bm._esito_avvio_cache.clear()

    def tearDown(self):
        bm._esito_avvio_cache.clear()
        super().tearDown()

    def _db_manager(self):
        from database.db_manager import DatabaseManager
        return DatabaseManager(db_path=self.db)

    def test_avvio_su_database_nuovo(self):
        gestore = self._db_manager()
        self.assertIsNone(gestore.avviso_integrita)
        self.assertFalse(gestore.database_inutilizzabile)

    def test_database_corrotto_non_fa_esplodere_lapplicazione(self):
        """Prima della correzione, init_database() falliva con un errore tecnico
        PRIMA che le protezioni potessero salvare i backup."""
        self._db_manager()          # crea lo schema
        bm._esito_avvio_cache.clear()
        self._db_manager()          # secondo avvio: produce un backup buono
        buoni_prima = set(os.listdir(self.backup_dir))

        corrompi(self.db)
        bm._esito_avvio_cache.clear()

        gestore = self._db_manager()   # non deve sollevare eccezioni
        self.assertTrue(gestore.database_inutilizzabile)
        self.assertIsNotNone(gestore.avviso_integrita)
        self.assertFalse(buoni_prima - set(os.listdir(self.backup_dir)),
                         "nessun backup buono deve essere stato cancellato")

    def test_verifica_integrita_esposta(self):
        gestore = self._db_manager()
        ok, messaggio = gestore.verifica_integrita()
        self.assertTrue(ok)
        self.assertEqual(messaggio, "ok")


if __name__ == "__main__":
    unittest.main(verbosity=2)
