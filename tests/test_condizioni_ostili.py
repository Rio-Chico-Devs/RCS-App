#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Condizioni ostili: cosa succede quando l'ambiente non collabora.

Fin qui e' stato provato il funzionamento normale e le interruzioni. Qui si
provano le situazioni scomode che in un'azienda capitano davvero: disco pieno,
file in sola lettura, cartella senza permessi, database aperto da un altro
computer mentre si ripristina.

Il criterio non e' che tutto riesca - a volte non si puo' - ma che il
programma NON PEGGIORI la situazione e lo dica chiaramente.

Esegui con:  python -m unittest tests.test_condizioni_ostili -v
"""

import os
import shutil
import sqlite3
import stat
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import archivio
from database import backup_manager as bm
from database import esportazione
from database.db_manager import DatabaseManager


def preventivo(indice=1):
    return {
        'nome_cliente': f'Cliente {indice}', 'numero_ordine': f'O{indice}',
        'misura': 'x', 'descrizione': 'd', 'codice': 'c', 'finitura': 'f',
        'costo_totale_materiali': 1.0, 'costi_accessori': 1.0,
        'minuti_taglio': 1.0, 'minuti_avvolgimento': 1.0, 'minuti_pulizia': 1.0,
        'minuti_rettifica': 1.0, 'minuti_imballaggio': 1.0, 'tot_mano_opera': 1.0,
        'subtotale': 1.0, 'maggiorazione_25': 1.0, 'preventivo_finale': 1.0,
        'prezzo_cliente': 1.0, 'materiali_utilizzati': [],
    }


class BaseOstile(unittest.TestCase):
    def setUp(self):
        bm._esito_avvio_cache.clear()
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "materiali.db")
        self.backup_dir = os.path.join(self.tmp, "backup")
        self._orig_app = bm.cartella_app
        bm.cartella_app = lambda: self.tmp
        self.gestore = DatabaseManager(db_path=self.db)
        self.gestore.add_preventivo(preventivo())

    def tearDown(self):
        bm.cartella_app = self._orig_app
        bm._esito_avvio_cache.clear()
        for radice, cartelle, file in os.walk(self.tmp):
            for nome in cartelle + file:
                try:
                    os.chmod(os.path.join(radice, nome), 0o700)
                except OSError:
                    pass
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _copia_valida(self):
        bm._esito_avvio_cache.clear()
        DatabaseManager(db_path=self.db)
        voci = archivio.elenco_backup(self.db)
        self.assertTrue(voci, "serve almeno una copia per la prova")
        return voci[0]["percorso"]

    def _conta(self):
        with sqlite3.connect(self.db) as conn:
            return conn.execute("SELECT COUNT(*) FROM preventivi").fetchone()[0]


# ---------------------------------------------------------------------------
# Ripristino mentre altri lavorano
# ---------------------------------------------------------------------------

class TestRipristinoConAltriCollegati(BaseOstile):
    """Il rischio piu' serio: sovrascrivere il database mentre un'altra
    postazione ci scrive."""

    def _segna_altro_pc_collegato(self):
        from datetime import datetime
        bm._scrivi_sessioni(bm._percorso_sessioni(self.db), {
            "PC-OFFICINA|mario": {
                "avvio": datetime.now().isoformat(timespec="seconds"), "pid": 1},
        })

    def test_si_ferma_se_un_altro_pc_e_collegato(self):
        copia = self._copia_valida()
        self._segna_altro_pc_collegato()
        prima = self._conta()

        riuscito, messaggio, precedente = archivio.ripristina_backup(self.db, copia)

        self.assertFalse(riuscito, "non deve ripristinare con altri collegati")
        self.assertIn("altri computer", messaggio)
        self.assertIn("PC-OFFICINA", messaggio, "deve dire QUALE postazione")
        self.assertIsNone(precedente, "non deve nemmeno iniziare")
        self.assertEqual(self._conta(), prima, "il database non va toccato")

    def test_si_puo_forzare_consapevolmente(self):
        """Serve quando una postazione risulta aperta ma in realta' e' bloccata."""
        copia = self._copia_valida()
        self._segna_altro_pc_collegato()

        riuscito, _messaggio, precedente = archivio.ripristina_backup(
            self.db, copia, forza=True)

        self.assertTrue(riuscito)
        self.assertIsNotNone(precedente, "anche forzando si conserva il precedente")

    def test_da_soli_non_chiede_nulla(self):
        copia = self._copia_valida()
        riuscito, _m, _p = archivio.ripristina_backup(self.db, copia)
        self.assertTrue(riuscito)

    def test_le_sessioni_scadute_non_bloccano(self):
        """Una postazione spenta da un giorno non deve impedire il ripristino."""
        from datetime import datetime, timedelta
        copia = self._copia_valida()
        vecchia = (datetime.now() - timedelta(hours=bm.ORE_SESSIONE_SCADUTA + 2))
        bm._scrivi_sessioni(bm._percorso_sessioni(self.db), {
            "PC-SPENTO|tizio": {"avvio": vecchia.isoformat(timespec="seconds")},
        })

        riuscito, messaggio, _p = archivio.ripristina_backup(self.db, copia)
        self.assertTrue(riuscito, messaggio)


# ---------------------------------------------------------------------------
# Permessi e spazio
# ---------------------------------------------------------------------------

class TestPermessi(BaseOstile):

    def test_cartella_backup_in_sola_lettura(self):
        """Il programma deve partire lo stesso e permettere di lavorare."""
        os.makedirs(self.backup_dir, exist_ok=True)
        os.chmod(self.backup_dir, 0o500)
        try:
            bm._esito_avvio_cache.clear()
            gestore = DatabaseManager(db_path=self.db)
            self.assertFalse(gestore.database_inutilizzabile)
            self.assertIsNotNone(gestore.add_preventivo(preventivo(2)))
        finally:
            os.chmod(self.backup_dir, 0o700)

    # I permessi non si applicano all'amministratore: nell'ambiente di
    # sviluppo si gira come root, quindi queste due prove non direbbero nulla.
    # Vanno eseguite su Windows con un utente normale.
    _COME_AMMINISTRATORE = hasattr(os, "geteuid") and os.geteuid() == 0

    @unittest.skipIf(_COME_AMMINISTRATORE,
                     "i permessi non valgono per l'amministratore: prova da fare su Windows")
    def test_database_in_sola_lettura(self):
        """Capita se il file viene contrassegnato per errore: il programma deve
        dirlo, non far finta di aver salvato."""
        os.chmod(self.db, stat.S_IRUSR)
        try:
            bm._esito_avvio_cache.clear()
            gestore = DatabaseManager(db_path=self.db)
            integro, _m = gestore.verifica_integrita()
            self.assertTrue(integro, "in lettura deve funzionare comunque")

            with self.assertRaises(Exception):
                gestore.add_preventivo(preventivo(3))
        finally:
            os.chmod(self.db, 0o600)

    @unittest.skipIf(_COME_AMMINISTRATORE,
                     "i permessi non valgono per l'amministratore: prova da fare su Windows")
    def test_esportazione_in_cartella_non_scrivibile(self):
        cartella = os.path.join(self.tmp, "sola_lettura")
        os.makedirs(cartella, exist_ok=True)
        os.chmod(cartella, 0o500)
        try:
            with self.assertRaises(Exception):
                esportazione.esporta(self.db, cartella=os.path.join(cartella, "x"))
            # ma il database non deve averne risentito
            integro, _m = self.gestore.verifica_integrita()
            self.assertTrue(integro)
        finally:
            os.chmod(cartella, 0o700)

    def test_esportazione_automatica_non_disturba_mai(self):
        """Se non riesce, deve solo annotarlo: mai fermare l'avvio."""
        cartella = esportazione.cartella_esportazioni(self.db)
        os.makedirs(os.path.dirname(cartella), exist_ok=True)
        # crea un FILE dove dovrebbe esserci la cartella: makedirs fallira'
        with open(cartella, "w") as f:
            f.write("ostacolo")
        try:
            esito = esportazione.esporta_se_serve(self.db)
            self.assertIsNone(esito)
        finally:
            os.remove(cartella)


# ---------------------------------------------------------------------------
# File anomali
# ---------------------------------------------------------------------------

class TestFileAnomali(BaseOstile):

    def test_backup_vuoto(self):
        """Un file da ZERO byte per SQLite e' un database valido e supera il
        controllo di integrita'. Se comparisse fra le copie buone,
        ripristinarlo cancellerebbe tutti i dati sostituendoli con il nulla:
        il danno peggiore possibile, causato dalla funzione che dovrebbe
        rimediare ai danni."""
        os.makedirs(self.backup_dir, exist_ok=True)
        vuoto = os.path.join(self.backup_dir, "materiali_backup_20260101_120000.db")
        open(vuoto, "wb").close()

        # il controllo di sola integrita' lo considera valido: e' il tranello
        integro, _messaggio, _ms = bm.verifica_integrita(vuoto)
        self.assertTrue(integro, "SQLite considera valido un file vuoto")

        # ma il controllo del contenuto no
        dettagli = archivio.dettagli_backup(vuoto)
        self.assertFalse(dettagli["integro"],
                         "una copia senza i dati del gestionale non e' utilizzabile")

        riuscito, messaggio, _p = archivio.ripristina_backup(self.db, vuoto)
        self.assertFalse(riuscito, "non deve MAI ripristinare una copia vuota")
        self.assertEqual(self._conta(), 1, "il database non va toccato")

    def test_backup_che_non_e_un_database(self):
        os.makedirs(self.backup_dir, exist_ok=True)
        finto = os.path.join(self.backup_dir, "materiali_backup_20260101_130000.db")
        with open(finto, "w") as f:
            f.write("questo e' un documento di testo, non un database")

        riuscito, _m, _p = archivio.ripristina_backup(self.db, finto)
        self.assertFalse(riuscito)
        self.assertEqual(self._conta(), 1)

    def test_nome_di_backup_non_riconosciuto(self):
        """File estranei nella cartella non devono confondere l'elenco."""
        os.makedirs(self.backup_dir, exist_ok=True)
        for nome in ("appunti.txt", "materiali_backup_senza_data.db", "copia.db"):
            with open(os.path.join(self.backup_dir, nome), "w") as f:
                f.write("x")

        voci = archivio.elenco_backup(self.db)
        for voce in voci:
            self.assertIsNotNone(voce["quando"],
                                 "nell'elenco devono finire solo copie riconosciute")

    def test_cartella_backup_inesistente(self):
        shutil.rmtree(self.backup_dir, ignore_errors=True)
        self.assertEqual(archivio.elenco_backup(self.db), [])
        stato = archivio.riepilogo_stato(self.db)
        self.assertEqual(stato["numero_backup"], 0)
        self.assertTrue(stato["integro"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
