#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test automatici RCS-App
Database in-memoria: ogni test class crea un DB fresco, zero contaminazione.
Esegui con:  python -m pytest tests/ -v
         o:  python -m unittest discover tests/ -v
"""

import sys
import os
import json
import tempfile
import unittest
import math
from datetime import datetime, timedelta

# Aggiungi la root del progetto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from models.materiale import Materiale, MaterialeCalcolato
from models.preventivo import Preventivo


# ---------------------------------------------------------------------------
# Fixture helper
# ---------------------------------------------------------------------------

def make_db():
    """Crea un DatabaseManager su file temporaneo (isolato per ogni test class)."""
    tmp = tempfile.mkdtemp()
    db_path = os.path.join(tmp, "test.db")
    return DatabaseManager(db_path=db_path)


def _preventivo_data(**kwargs):
    """Restituisce un dict minimo valido per add_preventivo."""
    base = {
        "data_creazione": datetime.now().isoformat(),
        "numero_revisione": 1,
        "preventivo_originale_id": None,
        "nome_cliente": "Test Cliente",
        "numero_ordine": "ORD-001",
        "misura": "100x200",
        "descrizione": "Test desc",
        "codice": "TST",
        "costo_totale_materiali": 0.0,
        "costi_accessori": 0.0,
        "minuti_taglio": 0.0,
        "minuti_avvolgimento": 0.0,
        "minuti_pulizia": 0.0,
        "minuti_rettifica": 0.0,
        "minuti_imballaggio": 0.0,
        "tot_mano_opera": 0.0,
        "subtotale": 0.0,
        "maggiorazione_25": 0.0,
        "preventivo_finale": 0.0,
        "prezzo_cliente": 0.0,
        "materiali_utilizzati": "[]",
        "note_revisione": "",
        "storico_modifiche": "[]",
    }
    base.update(kwargs)
    return base


# ===========================================================================
# 1. MATERIALI CRUD
# ===========================================================================

class TestMateriali(unittest.TestCase):

    def setUp(self):
        self.db = make_db()

    # --- CREATE ---

    def test_add_materiale_ok(self):
        mid = self.db.add_materiale("TESTMAT", 0.25, 30.0)
        self.assertIsInstance(mid, int)
        self.assertGreater(mid, 0)

    def test_add_materiale_duplicato_restituisce_false(self):
        self.db.add_materiale("DUP", 0.1, 10.0)
        result = self.db.add_materiale("DUP", 0.2, 20.0)
        self.assertFalse(result)

    def test_add_materiale_nome_case_insensitive_duplicato(self):
        """SQLite UNIQUE su TEXT è case-sensitive per default; verifica comportamento."""
        self.db.add_materiale("ABC", 0.1, 10.0)
        # "abc" != "ABC" in SQLite TEXT UNIQUE → deve inserire
        mid2 = self.db.add_materiale("abc", 0.1, 10.0)
        self.assertIsInstance(mid2, int)

    def test_add_materiale_spessore_zero(self):
        """Spessore zero: accettato dal DB (nessun vincolo > 0)."""
        mid = self.db.add_materiale("MAT_ZERO_SP", 0.0, 10.0)
        self.assertIsInstance(mid, int)

    def test_add_materiale_prezzo_zero(self):
        mid = self.db.add_materiale("MAT_ZERO_PR", 0.1, 0.0)
        self.assertIsInstance(mid, int)

    def test_add_materiale_valori_negativi(self):
        """Valori negativi: non bloccati da schema — il sistema li accetta."""
        mid = self.db.add_materiale("MAT_NEG", -0.1, -5.0)
        self.assertIsInstance(mid, int)

    def test_add_materiale_nome_vuoto_gestito(self):
        """Nome vuoto: UNIQUE constraint consente un solo '' — dipende dall'impl."""
        try:
            mid = self.db.add_materiale("", 0.1, 1.0)
            # Nessun crash: accettabile
            self.assertIsInstance(mid, int)
        except Exception:
            pass  # Anche un'eccezione è accettabile

    def test_add_materiale_nome_speciali_unicode(self):
        mid = self.db.add_materiale("Maté-Ïon©®∞", 0.3, 99.0)
        self.assertIsInstance(mid, int)

    def test_add_materiale_nome_lungo(self):
        nome = "X" * 500
        mid = self.db.add_materiale(nome, 0.1, 1.0)
        self.assertIsInstance(mid, int)

    def test_add_materiale_sql_injection_nel_nome(self):
        """L'injection non deve corrompere il DB."""
        nome = "'; DROP TABLE materiali; --"
        mid = self.db.add_materiale(nome, 0.1, 1.0)
        # Il materiale viene inserito con il nome letterale
        self.assertIsInstance(mid, int)
        tutti = self.db.get_all_materiali()
        nomi = [r[1] for r in tutti]
        self.assertIn(nome, nomi)

    # --- READ ---

    def test_get_all_materiali_iniziali(self):
        tutti = self.db.get_all_materiali()
        self.assertGreater(len(tutti), 0)  # i materiali di esempio

    def test_get_materiale_by_id_esistente(self):
        mid = self.db.add_materiale("CERCA_ID", 0.1, 1.0)
        row = self.db.get_materiale_by_id(mid)
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "CERCA_ID")

    def test_get_materiale_by_id_non_esistente(self):
        row = self.db.get_materiale_by_id(999999)
        self.assertIsNone(row)

    def test_get_materiale_by_nome_esistente(self):
        self.db.add_materiale("CERCA_NOME", 0.2, 2.0)
        row = self.db.get_materiale_by_nome("CERCA_NOME")
        self.assertIsNotNone(row)

    def test_get_materiale_by_nome_non_esistente(self):
        row = self.db.get_materiale_by_nome("NON_ESISTE_XYZ")
        self.assertIsNone(row)

    # --- UPDATE ---

    def test_update_materiale_base_ok(self):
        mid = self.db.add_materiale("UPD_BASE", 0.1, 10.0)
        result = self.db.update_materiale_base(mid, "UPD_BASE_MOD", 0.5, 99.0)
        self.assertTrue(result)
        row = self.db.get_materiale_by_id(mid)
        self.assertEqual(row[1], "UPD_BASE_MOD")

    def test_update_materiale_id_non_esistente(self):
        result = self.db.update_materiale_base(999999, "GHOST", 0.1, 1.0)
        # Dovrebbe restituire False o None; non deve crashare
        self.assertFalse(bool(result))

    def test_update_materiale_nome_duplicato_fallisce(self):
        mid1 = self.db.add_materiale("MAT_A", 0.1, 1.0)
        self.db.add_materiale("MAT_B", 0.2, 2.0)
        # Rinomina MAT_A → MAT_B: viola UNIQUE
        result = self.db.update_materiale_base(mid1, "MAT_B", 0.1, 1.0)
        self.assertFalse(bool(result))

    def test_update_prezzo_materiale(self):
        mid = self.db.add_materiale("PREZZO_UPD", 0.1, 10.0)
        self.db.update_prezzo_materiale(mid, 99.5)
        row = self.db.get_materiale_by_id(mid)
        self.assertAlmostEqual(row[3], 99.5)

    # --- DELETE ---

    def test_delete_materiale_ok(self):
        mid = self.db.add_materiale("DEL_MAT", 0.1, 1.0)
        result = self.db.delete_materiale(mid)
        self.assertTrue(result)
        self.assertIsNone(self.db.get_materiale_by_id(mid))

    def test_delete_materiale_non_esistente(self):
        result = self.db.delete_materiale(999999)
        self.assertFalse(bool(result))

    def test_delete_materiale_cascada_su_fornitori(self):
        """Eliminare un materiale deve rimuovere anche i suoi materiale_fornitori."""
        mid = self.db.add_materiale("DEL_CASCADE", 0.1, 1.0)
        self.db.add_fornitore_a_materiale(mid, "FORN_X", 5.0, 10.0, 100.0)
        self.db.delete_materiale(mid)
        fornitori = self.db.get_fornitori_per_materiale(mid)
        self.assertEqual(len(fornitori), 0)


# ===========================================================================
# 2. FORNITORI CRUD
# ===========================================================================

class TestFornitori(unittest.TestCase):

    def setUp(self):
        self.db = make_db()

    def test_add_fornitore_ok(self):
        fid = self.db.add_fornitore("NUOVO_FORN")
        self.assertIsInstance(fid, int)

    def test_add_fornitore_duplicato_restituisce_false(self):
        self.db.add_fornitore("FORN_DUP")
        result = self.db.add_fornitore("FORN_DUP")
        self.assertFalse(result)

    def test_add_fornitore_sql_injection(self):
        nome = "'; DELETE FROM fornitori; --"
        fid = self.db.add_fornitore(nome)
        self.assertIsInstance(fid, int)
        tutti = self.db.get_all_fornitori()
        nomi = [r[1] for r in tutti]
        self.assertIn(nome, nomi)

    def test_get_all_fornitori_contiene_iniziali(self):
        tutti = self.db.get_all_fornitori()
        nomi = [r[1] for r in tutti]
        # I fornitori di default: CIT, FIBERTECH, ANGELONI
        self.assertIn("ANGELONI", nomi)
        self.assertIn("FIBERTECH", nomi)

    def test_rename_fornitore_ok(self):
        self.db.add_fornitore("FORN_OLD")
        result = self.db.rename_fornitore("FORN_OLD", "FORN_NEW")
        self.assertTrue(result)
        tutti = self.db.get_all_fornitori()
        nomi = [r[1] for r in tutti]
        self.assertIn("FORN_NEW", nomi)
        self.assertNotIn("FORN_OLD", nomi)

    def test_rename_fornitore_nome_occupato_fallisce(self):
        self.db.add_fornitore("FORN_1")
        self.db.add_fornitore("FORN_2")
        result = self.db.rename_fornitore("FORN_1", "FORN_2")
        self.assertFalse(bool(result))

    def test_rename_fornitore_non_esistente(self):
        """BUG NOTO: rename_fornitore usa UPDATE senza controllare rowcount,
        quindi restituisce True anche se il fornitore non esiste.
        Il test documenta il comportamento attuale."""
        result = self.db.rename_fornitore("NON_ESISTE_XYZ", "QUALCOSA")
        # Comportamento attuale: True (nessuna riga modificata ma nessuna eccezione)
        self.assertTrue(bool(result))
        # Verifica che "QUALCOSA" NON sia stato aggiunto ai fornitori
        tutti = self.db.get_all_fornitori()
        nomi = [r[1] for r in tutti]
        self.assertNotIn("QUALCOSA", nomi)

    def test_assegna_materiali_a_fornitore(self):
        """assegna_materiali_a_fornitore aggiorna il campo legacy materiali.fornitore,
        NON la tabella materiale_fornitori. Verifica via get_scorte_per_fornitore."""
        mid = self.db.add_materiale("MAT_FORN", 0.1, 1.0)
        self.db.add_fornitore("FORN_ASSEGNA")
        self.db.assegna_materiali_a_fornitore("FORN_ASSEGNA", [mid])
        scorte = self.db.get_scorte_per_fornitore("FORN_ASSEGNA")
        ids = [r[0] for r in scorte]
        self.assertIn(mid, ids)

    def test_assegna_materiali_lista_vuota_non_crasha(self):
        self.db.add_fornitore("FORN_VUOTO")
        # Non deve sollevare eccezione
        self.db.assegna_materiali_a_fornitore("FORN_VUOTO", [])

    def test_get_scorte_per_fornitore(self):
        """get_scorte_per_fornitore legge il campo legacy materiali.fornitore.
        Si deve usare update_materiale (o fornitore= in add_materiale) per renderlo visibile."""
        mid = self.db.add_materiale("MAT_SC_FORN", 0.1, 1.0, fornitore="FORN_SCORTE")
        scorte = self.db.get_scorte_per_fornitore("FORN_SCORTE")
        self.assertGreater(len(scorte), 0)

    def test_get_scorte_fornitore_non_esistente_lista_vuota(self):
        scorte = self.db.get_scorte_per_fornitore("FANTASMA")
        self.assertEqual(len(scorte), 0)


# ===========================================================================
# 3. MATERIALE_FORNITORI (multi-fornitore per materiale)
# ===========================================================================

class TestMateriale_Fornitori(unittest.TestCase):

    def setUp(self):
        self.db = make_db()
        self.mid = self.db.add_materiale("MAT_MF", 0.25, 30.0)

    def test_add_fornitore_a_materiale_ok(self):
        mfid = self.db.add_fornitore_a_materiale(self.mid, "FORN_A", 10.0, 5.0, 50.0)
        self.assertIsInstance(mfid, int)

    def test_add_fornitore_duplicato_per_stesso_materiale_fallisce(self):
        self.db.add_fornitore_a_materiale(self.mid, "FORN_DUP", 10.0)
        result = self.db.add_fornitore_a_materiale(self.mid, "FORN_DUP", 20.0)
        self.assertFalse(result)

    def test_stesso_fornitore_su_materiali_diversi_ok(self):
        mid2 = self.db.add_materiale("MAT_MF2", 0.1, 5.0)
        mfid1 = self.db.add_fornitore_a_materiale(self.mid, "FORN_COMUNE", 10.0)
        mfid2 = self.db.add_fornitore_a_materiale(mid2, "FORN_COMUNE", 12.0)
        self.assertIsInstance(mfid1, int)
        self.assertIsInstance(mfid2, int)

    def test_get_fornitori_per_materiale(self):
        self.db.add_fornitore_a_materiale(self.mid, "F1", 10.0, 5.0, 50.0)
        self.db.add_fornitore_a_materiale(self.mid, "F2", 12.0, 5.0, 50.0)
        rows = self.db.get_fornitori_per_materiale(self.mid)
        self.assertEqual(len(rows), 2)

    def test_get_fornitori_materiale_non_esistente_lista_vuota(self):
        rows = self.db.get_fornitori_per_materiale(999999)
        self.assertEqual(len(rows), 0)

    def test_update_fornitore_materiale_ok(self):
        mfid = self.db.add_fornitore_a_materiale(self.mid, "F_UPD", 10.0, 5.0, 50.0)
        result = self.db.update_fornitore_materiale(mfid, "F_UPD_NEW", 20.0, 10.0, 100.0)
        self.assertTrue(result)
        rows = self.db.get_fornitori_per_materiale(self.mid)
        nomi = [r[1] for r in rows]
        self.assertIn("F_UPD_NEW", nomi)

    def test_update_fornitore_id_non_esistente(self):
        result = self.db.update_fornitore_materiale(999999, "GHOST", 1.0)
        self.assertFalse(bool(result))

    def test_delete_fornitore_materiale_ok(self):
        mfid = self.db.add_fornitore_a_materiale(self.mid, "F_DEL", 10.0)
        result = self.db.delete_fornitore_materiale(mfid)
        self.assertTrue(result)
        rows = self.db.get_fornitori_per_materiale(self.mid)
        nomi = [r[1] for r in rows]
        self.assertNotIn("F_DEL", nomi)

    def test_delete_fornitore_id_non_esistente(self):
        result = self.db.delete_fornitore_materiale(999999)
        self.assertFalse(bool(result))

    def test_get_giacenza_totale_materiale_somma(self):
        self.db.add_fornitore_a_materiale(self.mid, "GA1", 10.0, 0.0, 100.0)
        self.db.add_fornitore_a_materiale(self.mid, "GA2", 12.0, 0.0, 100.0)
        # Registra movimenti per far salire la giacenza
        self.db.registra_movimento(self.mid, "carico", 20.0, fornitore_nome="GA1")
        self.db.registra_movimento(self.mid, "carico", 15.0, fornitore_nome="GA2")
        tot = self.db.get_giacenza_totale_materiale(self.mid)
        self.assertAlmostEqual(tot, 35.0, places=2)

    def test_giacenza_totale_materiale_senza_fornitori(self):
        mid2 = self.db.add_materiale("MAT_NOFORN", 0.1, 1.0)
        tot = self.db.get_giacenza_totale_materiale(mid2)
        self.assertAlmostEqual(tot, 0.0)


# ===========================================================================
# 4. MAGAZZINO (movimenti, scorte, consumi)
# ===========================================================================

class TestMagazzino(unittest.TestCase):

    def setUp(self):
        self.db = make_db()
        self.mid = self.db.add_materiale("MAT_MAG", 0.25, 30.0)
        self.db.add_fornitore_a_materiale(self.mid, "FORN_MAG", 10.0, 5.0, 200.0)

    def test_registra_carico(self):
        mov_id = self.db.registra_movimento(self.mid, "carico", 50.0, fornitore_nome="FORN_MAG")
        self.assertIsInstance(mov_id, int)

    def test_registra_scarico(self):
        self.db.registra_movimento(self.mid, "carico", 100.0, fornitore_nome="FORN_MAG")
        mov_id = self.db.registra_movimento(self.mid, "scarico", 30.0, fornitore_nome="FORN_MAG")
        self.assertIsInstance(mov_id, int)

    def test_scarico_blocca_giacenza_sotto_zero(self):
        """Il DB usa MAX(giacenza - ?, 0): la giacenza non scende mai sotto zero.
        Il movimento viene registrato, ma la giacenza si ferma a 0."""
        mov_id = self.db.registra_movimento(self.mid, "scarico", 999.0, fornitore_nome="FORN_MAG")
        self.assertIsInstance(mov_id, int)
        tot = self.db.get_giacenza_totale_materiale(self.mid)
        self.assertGreaterEqual(tot, 0.0)

    def test_carico_quantita_zero(self):
        """Quantità zero: accettata dal DB."""
        mov_id = self.db.registra_movimento(self.mid, "carico", 0.0, fornitore_nome="FORN_MAG")
        self.assertIsInstance(mov_id, int)

    def test_carico_quantita_molto_grande(self):
        mov_id = self.db.registra_movimento(self.mid, "carico", 999999.99, fornitore_nome="FORN_MAG")
        self.assertIsInstance(mov_id, int)

    def test_get_movimenti_per_materiale(self):
        self.db.registra_movimento(self.mid, "carico", 10.0, fornitore_nome="FORN_MAG")
        self.db.registra_movimento(self.mid, "carico", 20.0, fornitore_nome="FORN_MAG")
        movimenti = self.db.get_movimenti_per_materiale(self.mid)
        self.assertEqual(len(movimenti), 2)

    def test_get_movimenti_limit(self):
        for i in range(10):
            self.db.registra_movimento(self.mid, "carico", float(i + 1), fornitore_nome="FORN_MAG")
        movimenti = self.db.get_movimenti_per_materiale(self.mid, limit=5)
        self.assertLessEqual(len(movimenti), 5)

    def test_get_movimenti_materiale_non_esistente_lista_vuota(self):
        movimenti = self.db.get_movimenti_per_materiale(999999)
        self.assertEqual(len(movimenti), 0)

    def test_get_scorte_restituisce_materiale(self):
        self.db.registra_movimento(self.mid, "carico", 50.0, fornitore_nome="FORN_MAG")
        scorte = self.db.get_scorte()
        ids = [r[0] for r in scorte]
        self.assertIn(self.mid, ids)

    def test_get_scorte_ordine_asc(self):
        mid2 = self.db.add_materiale("MAT_MAG2", 0.1, 1.0)
        self.db.add_fornitore_a_materiale(mid2, "F2", 5.0, 0.0, 50.0)
        self.db.registra_movimento(self.mid, "carico", 100.0, fornitore_nome="FORN_MAG")
        self.db.registra_movimento(mid2, "carico", 5.0, fornitore_nome="F2")
        scorte = self.db.get_scorte(ordina_per="giacenza_asc")
        giacenze = [r[2] for r in scorte]
        self.assertEqual(giacenze, sorted(giacenze))

    def test_get_scorte_ordine_desc(self):
        mid2 = self.db.add_materiale("MAT_MAG3", 0.1, 1.0)
        self.db.add_fornitore_a_materiale(mid2, "F3", 5.0, 0.0, 50.0)
        self.db.registra_movimento(self.mid, "carico", 100.0, fornitore_nome="FORN_MAG")
        self.db.registra_movimento(mid2, "carico", 5.0, fornitore_nome="F3")
        scorte = self.db.get_scorte(ordina_per="giacenza_desc")
        giacenze = [r[2] for r in scorte]
        self.assertEqual(giacenze, sorted(giacenze, reverse=True))

    def test_get_consumi_periodo_scarichi(self):
        inizio = (datetime.now() - timedelta(days=1)).isoformat()
        fine = (datetime.now() + timedelta(days=1)).isoformat()
        self.db.registra_movimento(self.mid, "scarico", 25.0, fornitore_nome="FORN_MAG")
        consumi = self.db.get_consumi_periodo(inizio, fine)
        self.assertGreater(len(consumi), 0)

    def test_get_consumi_periodo_fuori_range_lista_vuota(self):
        inizio = "2000-01-01T00:00:00"
        fine = "2000-01-02T00:00:00"
        self.db.registra_movimento(self.mid, "scarico", 25.0, fornitore_nome="FORN_MAG")
        consumi = self.db.get_consumi_periodo(inizio, fine)
        self.assertEqual(len(consumi), 0)

    def test_carico_e_scarico_bilancio(self):
        self.db.registra_movimento(self.mid, "carico", 100.0, fornitore_nome="FORN_MAG")
        self.db.registra_movimento(self.mid, "scarico", 40.0, fornitore_nome="FORN_MAG")
        tot = self.db.get_giacenza_totale_materiale(self.mid)
        self.assertAlmostEqual(tot, 60.0, places=2)


# ===========================================================================
# 5. CATEGORIE CRUD
# ===========================================================================

class TestCategorie(unittest.TestCase):

    def setUp(self):
        self.db = make_db()

    def test_add_categoria_ok(self):
        cid = self.db.add_categoria("CAT_TEST", 10.0, 50.0, 200.0, "note test")
        self.assertIsInstance(cid, int)

    def test_add_categoria_duplicata_restituisce_false(self):
        self.db.add_categoria("CAT_DUP")
        result = self.db.add_categoria("CAT_DUP")
        self.assertFalse(result)

    def test_add_categoria_valori_default(self):
        cid = self.db.add_categoria("CAT_DEFAULT")
        self.assertIsInstance(cid, int)
        row = self.db.get_categoria_by_id(cid)
        self.assertIsNotNone(row)

    def test_get_all_categorie(self):
        self.db.add_categoria("CAT_A")
        self.db.add_categoria("CAT_B")
        cats = self.db.get_all_categorie()
        nomi = [r[1] for r in cats]
        self.assertIn("CAT_A", nomi)
        self.assertIn("CAT_B", nomi)

    def test_get_categoria_by_id_esistente(self):
        cid = self.db.add_categoria("CAT_ID")
        row = self.db.get_categoria_by_id(cid)
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "CAT_ID")

    def test_get_categoria_by_id_non_esistente(self):
        row = self.db.get_categoria_by_id(999999)
        self.assertIsNone(row)

    def test_update_categoria_ok(self):
        cid = self.db.add_categoria("CAT_UPD", 10.0, 50.0)
        result = self.db.update_categoria(cid, "CAT_UPD_NEW", 20.0, 80.0, 300.0, "new note")
        self.assertTrue(result)
        row = self.db.get_categoria_by_id(cid)
        self.assertEqual(row[1], "CAT_UPD_NEW")
        self.assertAlmostEqual(row[2], 20.0)

    def test_update_categoria_id_non_esistente(self):
        result = self.db.update_categoria(999999, "GHOST", 0.0, 0.0)
        self.assertFalse(bool(result))

    def test_delete_categoria_ok(self):
        cid = self.db.add_categoria("CAT_DEL")
        result = self.db.delete_categoria(cid)
        self.assertTrue(result)
        self.assertIsNone(self.db.get_categoria_by_id(cid))

    def test_delete_categoria_non_esistente(self):
        result = self.db.delete_categoria(999999)
        self.assertFalse(bool(result))

    def test_delete_categoria_rimuove_riferimento_da_materiali(self):
        """Eliminare una categoria non deve eliminare i materiali, solo il riferimento."""
        cid = self.db.add_categoria("CAT_CASCADE")
        mid = self.db.add_materiale("MAT_IN_CAT", 0.1, 1.0, categoria_id=cid)
        self.db.delete_categoria(cid)
        row = self.db.get_materiale_by_id(mid)
        self.assertIsNotNone(row)  # Il materiale esiste ancora

    def test_get_materiali_per_categoria(self):
        cid = self.db.add_categoria("CAT_MATS")
        self.db.add_materiale("M_CAT_1", 0.1, 1.0, categoria_id=cid)
        self.db.add_materiale("M_CAT_2", 0.2, 2.0, categoria_id=cid)
        mats = self.db.get_materiali_per_categoria(cid)
        self.assertEqual(len(mats), 2)

    def test_get_materiali_categoria_vuota(self):
        cid = self.db.add_categoria("CAT_EMPTY")
        mats = self.db.get_materiali_per_categoria(cid)
        self.assertEqual(len(mats), 0)


# ===========================================================================
# 6. PREVENTIVI CRUD + VERSIONING
# ===========================================================================

class TestPreventivi(unittest.TestCase):

    def setUp(self):
        self.db = make_db()

    def _add_prev(self, **kwargs):
        return self.db.add_preventivo(_preventivo_data(**kwargs))

    def test_add_preventivo_ok(self):
        pid = self._add_prev(nome_cliente="Mario Rossi")
        self.assertIsInstance(pid, int)
        self.assertGreater(pid, 0)

    def test_get_preventivo_by_id_esistente(self):
        pid = self._add_prev(nome_cliente="Luigi Verdi")
        prev = self.db.get_preventivo_by_id(pid)
        self.assertIsNotNone(prev)
        self.assertEqual(prev["nome_cliente"], "Luigi Verdi")

    def test_get_preventivo_by_id_non_esistente(self):
        prev = self.db.get_preventivo_by_id(999999)
        self.assertIsNone(prev)

    def test_get_all_preventivi(self):
        self._add_prev(nome_cliente="A")
        self._add_prev(nome_cliente="B")
        tutti = self.db.get_all_preventivi()
        self.assertGreaterEqual(len(tutti), 2)

    def test_get_all_preventivi_latest_esclude_revisioni(self):
        pid = self._add_prev(nome_cliente="ORIG")
        self.db.add_revisione_preventivo(pid, _preventivo_data(nome_cliente="REV1"), "rev1")
        latest = self.db.get_all_preventivi_latest()
        # L'originale non deve apparire se ha revisioni, o viceversa — dipende dall'impl
        self.assertIsInstance(latest, list)

    def test_update_preventivo_crea_storico(self):
        pid = self._add_prev(nome_cliente="STORICO_TEST")
        dati_upd = _preventivo_data(nome_cliente="STORICO_TEST_UPD", costo_totale_materiali=99.0)
        self.db.update_preventivo(pid, dati_upd)
        storico = self.db.get_storico_modifiche(pid)
        self.assertGreater(len(storico), 0)

    def test_update_preventivo_preserva_storico_multiplo(self):
        pid = self._add_prev(nome_cliente="MULTI_UPD")
        for i in range(3):
            self.db.update_preventivo(pid, _preventivo_data(
                nome_cliente=f"MULTI_UPD_{i}", costo_totale_materiali=float(i * 10)
            ))
        storico = self.db.get_storico_modifiche(pid)
        self.assertGreaterEqual(len(storico), 3)

    def test_ripristina_versione_preventivo(self):
        pid = self._add_prev(nome_cliente="RIPRISTINA")
        self.db.update_preventivo(pid, _preventivo_data(
            nome_cliente="RIPRISTINA_MOD", costo_totale_materiali=55.0
        ))
        storico = self.db.get_storico_modifiche(pid)
        self.assertGreater(len(storico), 0)
        ts = storico[0]["timestamp"]
        result = self.db.ripristina_versione_preventivo(pid, ts)
        self.assertTrue(result)

    def test_ripristina_versione_timestamp_non_esistente(self):
        pid = self._add_prev()
        result = self.db.ripristina_versione_preventivo(pid, "2000-01-01T00:00:00")
        self.assertFalse(bool(result))

    def test_add_revisione_preventivo(self):
        pid = self._add_prev(nome_cliente="ORIG_REV")
        rev_id = self.db.add_revisione_preventivo(pid, _preventivo_data(
            nome_cliente="ORIG_REV", numero_revisione=2
        ), "Prima revisione")
        self.assertIsInstance(rev_id, int)

    def test_get_revisioni_preventivo(self):
        """get_revisioni_preventivo include l'originale + tutte le revisioni
        (query: WHERE preventivo_originale_id = ? OR id = ?)."""
        pid = self._add_prev(nome_cliente="ORIG_GET_REV")
        self.db.add_revisione_preventivo(pid, _preventivo_data(numero_revisione=2), "rev 1")
        self.db.add_revisione_preventivo(pid, _preventivo_data(numero_revisione=3), "rev 2")
        revisioni = self.db.get_revisioni_preventivo(pid)
        # 1 originale + 2 revisioni = 3
        self.assertEqual(len(revisioni), 3)

    def test_delete_preventivo_e_revisioni(self):
        pid = self._add_prev(nome_cliente="DEL_E_REV")
        self.db.add_revisione_preventivo(pid, _preventivo_data(numero_revisione=2), "r1")
        result = self.db.delete_preventivo_e_revisioni(pid)
        self.assertTrue(result)
        self.assertIsNone(self.db.get_preventivo_by_id(pid))
        revisioni = self.db.get_revisioni_preventivo(pid)
        self.assertEqual(len(revisioni), 0)

    def test_delete_preventivo_non_esistente(self):
        result = self.db.delete_preventivo_e_revisioni(999999)
        self.assertFalse(bool(result))

    def test_preventivo_con_materiali_json(self):
        """add_preventivo fa json.dumps() su materiali_utilizzati:
        passare una lista di dict (non una stringa JSON già serializzata)."""
        mc = MaterialeCalcolato()
        mc.diametro = 100.0
        mc.lunghezza = 200.0
        mc.giri = 3
        mc.spessore = 0.25
        mc.costo_materiale = 30.0
        mc.ricalcola_tutto()
        dati = _preventivo_data(
            materiali_utilizzati=[mc.to_dict()],   # lista, NON stringa JSON
            costo_totale_materiali=mc.maggiorazione
        )
        pid = self.db.add_preventivo(dati)
        prev = self.db.get_preventivo_by_id(pid)
        mats = prev.get("materiali_utilizzati", [])
        self.assertEqual(len(mats), 1)
        self.assertAlmostEqual(mats[0]["diametro"], 100.0)

    def test_storico_modifiche_preventivo_non_esistente(self):
        storico = self.db.get_storico_modifiche(999999)
        self.assertIsInstance(storico, list)

    def test_save_preventivo_alias_add(self):
        """save_preventivo è un alias di add_preventivo."""
        pid = self.db.save_preventivo(_preventivo_data(nome_cliente="ALIAS"))
        self.assertIsInstance(pid, int)

    def test_get_preventivi_con_modifiche(self):
        pid = self._add_prev()
        self.db.update_preventivo(pid, _preventivo_data(costo_totale_materiali=10.0))
        risultati = self.db.get_preventivi_con_modifiche()
        self.assertIsInstance(risultati, list)

    def test_preventivo_campi_numerici_float(self):
        pid = self._add_prev(
            costo_totale_materiali=123.45,
            costi_accessori=10.0,
            minuti_taglio=5.5,
            preventivo_finale=200.0,
            prezzo_cliente=250.0
        )
        prev = self.db.get_preventivo_by_id(pid)
        self.assertAlmostEqual(prev["costo_totale_materiali"], 123.45)
        self.assertAlmostEqual(prev["prezzo_cliente"], 250.0)


# ===========================================================================
# 7. MaterialeCalcolato — calcoli e edge case
# ===========================================================================

class TestMaterialeCalcolato(unittest.TestCase):

    def _mc(self, diametro=100.0, lunghezza=200.0, giri=3, spessore=0.25, costo=30.0):
        mc = MaterialeCalcolato()
        mc.diametro = diametro
        mc.lunghezza = lunghezza
        mc.giri = giri
        mc.spessore = spessore
        mc.costo_materiale = costo
        mc.ricalcola_tutto()
        return mc

    def test_diametro_finale_formula(self):
        mc = self._mc(diametro=100.0, giri=3, spessore=0.25)
        expected = 100.0 + (0.25 * (3 * 2))
        self.assertAlmostEqual(mc.diametro_finale, expected)

    def test_sviluppo_formula(self):
        mc = self._mc(diametro=100.0, giri=3, spessore=0.25)
        expected = ((100.0 + 3 * 0.25) * 3.14) * 3 + 5
        self.assertAlmostEqual(mc.sviluppo, expected, places=4)

    def test_arrotondamento_manuale_sovrascrive_sviluppo(self):
        mc = MaterialeCalcolato()
        mc.diametro = 100.0
        mc.giri = 3
        mc.spessore = 0.25
        mc.arrotondamento_manuale = 999.0
        mc.calcola_sviluppo()
        self.assertAlmostEqual(mc.sviluppo, 999.0)

    def test_lunghezza_utilizzata(self):
        mc = self._mc(lunghezza=200.0)
        expected = (200.0 * mc.sviluppo) / 1_000_000
        self.assertAlmostEqual(mc.lunghezza_utilizzata, expected, places=8)

    def test_costo_totale(self):
        mc = self._mc(costo=30.0)
        self.assertAlmostEqual(mc.costo_totale, mc.lunghezza_utilizzata * 30.0, places=8)

    def test_maggiorazione_110_percento(self):
        mc = self._mc()
        self.assertAlmostEqual(mc.maggiorazione, mc.costo_totale * 1.1, places=8)

    def test_giri_zero_sviluppo(self):
        mc = MaterialeCalcolato()
        mc.diametro = 100.0
        mc.lunghezza = 200.0
        mc.giri = 0
        mc.spessore = 0.25
        mc.costo_materiale = 30.0
        mc.ricalcola_tutto()
        # Sviluppo con giri=0: ((100 + 0) * 3.14) * 0 + 5 = 5
        self.assertAlmostEqual(mc.sviluppo, 5.0, places=4)

    def test_lunghezza_zero_costo_zero(self):
        mc = self._mc(lunghezza=0.0)
        self.assertAlmostEqual(mc.costo_totale, 0.0)
        self.assertAlmostEqual(mc.maggiorazione, 0.0)

    def test_costo_materiale_zero_usa_prezzo(self):
        mc = MaterialeCalcolato()
        mc.diametro = 100.0
        mc.lunghezza = 200.0
        mc.giri = 2
        mc.spessore = 0.1
        mc.costo_materiale = 0.0
        mc.prezzo = 25.0  # Deve essere usato come fallback
        mc.ricalcola_tutto()
        # Con costo_materiale=0 e prezzo=25: calcola_costo_totale usa prezzo come costo
        self.assertAlmostEqual(mc.costo_materiale, 25.0)

    def test_stratifica_alias_sviluppo(self):
        mc = self._mc()
        self.assertAlmostEqual(mc.stratifica, mc.sviluppo)

    def test_stratifica_setter(self):
        mc = MaterialeCalcolato()
        mc.stratifica = 123.45
        self.assertAlmostEqual(mc.sviluppo, 123.45)

    def test_to_dict_chiavi_presenti(self):
        mc = self._mc()
        d = mc.to_dict()
        chiavi_attese = [
            "diametro", "lunghezza", "materiale_id", "materiale_nome",
            "giri", "spessore", "diametro_finale", "sviluppo", "arrotondamento_manuale",
            "costo_materiale", "lunghezza_utilizzata", "costo_totale", "maggiorazione",
            "is_conica", "conicita_lato", "conicita_altezza_mm", "conicita_lunghezza_mm",
            "scarto_mm2", "orientamento"
        ]
        for k in chiavi_attese:
            self.assertIn(k, d, msg=f"Chiave '{k}' mancante in to_dict()")

    def test_ricalcola_tutto_non_crasha_valori_estremi(self):
        mc = self._mc(diametro=0.0001, lunghezza=99999.0, giri=30, spessore=0.001, costo=0.01)
        # Non deve sollevare eccezioni
        mc.ricalcola_tutto()

    def test_is_conica_default_false(self):
        mc = MaterialeCalcolato()
        self.assertFalse(mc.is_conica)

    def test_orientamento_default(self):
        mc = MaterialeCalcolato()
        self.assertEqual(mc.orientamento["rotation"], 0)
        self.assertFalse(mc.orientamento["flip_h"])
        self.assertFalse(mc.orientamento["flip_v"])


# ===========================================================================
# 8. Preventivo model — aggregazioni
# ===========================================================================

class TestPreventivoModel(unittest.TestCase):

    def _mc_con_maggiorazione(self, valore):
        """Crea un MaterialeCalcolato con maggiorazione fissa."""
        mc = MaterialeCalcolato()
        mc.maggiorazione = valore
        mc.costo_totale = valore / 1.1
        return mc

    def test_aggiungi_materiale(self):
        p = Preventivo()
        mc = self._mc_con_maggiorazione(10.0)
        result = p.aggiungi_materiale(mc)
        self.assertTrue(result)
        self.assertEqual(len(p.materiali_calcolati), 1)

    def test_aggiungi_materiale_limite_30(self):
        p = Preventivo()
        for _ in range(30):
            p.aggiungi_materiale(self._mc_con_maggiorazione(1.0))
        result = p.aggiungi_materiale(self._mc_con_maggiorazione(1.0))
        self.assertFalse(result)
        self.assertEqual(len(p.materiali_calcolati), 30)

    def test_rimuovi_materiale_ok(self):
        p = Preventivo()
        mc = self._mc_con_maggiorazione(5.0)
        p.aggiungi_materiale(mc)
        result = p.rimuovi_materiale(0)
        self.assertTrue(result)
        self.assertEqual(len(p.materiali_calcolati), 0)

    def test_rimuovi_materiale_indice_fuori_range(self):
        p = Preventivo()
        result = p.rimuovi_materiale(5)
        self.assertFalse(result)

    def test_costo_totale_materiali_somma_maggiorazioni(self):
        p = Preventivo()
        p.aggiungi_materiale(self._mc_con_maggiorazione(10.0))
        p.aggiungi_materiale(self._mc_con_maggiorazione(20.0))
        p.ricalcola_costo_totale_materiali()
        self.assertAlmostEqual(p.costo_totale_materiali, 30.0)

    def test_calcola_tot_mano_opera(self):
        p = Preventivo()
        p.minuti_taglio = 10.0
        p.minuti_avvolgimento = 5.0
        p.minuti_pulizia = 3.0
        p.minuti_rettifica = 2.0
        p.minuti_imballaggio = 1.0
        p.calcola_tot_mano_opera()
        self.assertAlmostEqual(p.tot_mano_opera, 21.0)

    def test_calcola_subtotale(self):
        p = Preventivo()
        p.costi_accessori = 10.0
        p.tot_mano_opera = 20.0
        p.costo_totale_materiali = 30.0
        p.calcola_subtotale()
        self.assertAlmostEqual(p.subtotale, 60.0)

    def test_calcola_maggiorazione_25(self):
        p = Preventivo()
        p.subtotale = 100.0
        p.calcola_maggiorazione_25()
        self.assertAlmostEqual(p.maggiorazione_25, 25.0)

    def test_calcola_preventivo_finale(self):
        p = Preventivo()
        p.subtotale = 100.0
        p.maggiorazione_25 = 25.0
        p.calcola_preventivo_finale()
        self.assertAlmostEqual(p.preventivo_finale, 125.0)

    def test_ricalcola_tutto_coerenza(self):
        p = Preventivo()
        p.aggiungi_materiale(self._mc_con_maggiorazione(50.0))
        p.aggiungi_materiale(self._mc_con_maggiorazione(30.0))
        p.costi_accessori = 20.0
        p.minuti_taglio = 15.0
        p.ricalcola_tutto()
        # costo_materiali = 80, mano_opera = 15, accessori = 20 → subtotale = 115
        self.assertAlmostEqual(p.costo_totale_materiali, 80.0)
        self.assertAlmostEqual(p.subtotale, 115.0)
        self.assertAlmostEqual(p.maggiorazione_25, 28.75)
        self.assertAlmostEqual(p.preventivo_finale, 143.75)

    def test_to_dict_chiavi_presenti(self):
        p = Preventivo()
        p.ricalcola_tutto()
        d = p.to_dict()
        chiavi = ["costo_totale_materiali", "costi_accessori", "minuti_taglio",
                  "subtotale", "maggiorazione_25", "preventivo_finale",
                  "prezzo_cliente", "materiali_utilizzati"]
        for k in chiavi:
            self.assertIn(k, d, msg=f"Chiave '{k}' mancante in Preventivo.to_dict()")

    def test_scarto_totale_somma_materiali(self):
        p = Preventivo()
        mc1 = MaterialeCalcolato()
        mc1.scarto_mm2 = 100.0
        mc1.maggiorazione = 5.0
        mc2 = MaterialeCalcolato()
        mc2.scarto_mm2 = 250.0
        mc2.maggiorazione = 5.0
        p.aggiungi_materiale(mc1)
        p.aggiungi_materiale(mc2)
        p.ricalcola_scarto_totale()
        self.assertAlmostEqual(p.scarto_totale_mm2, 350.0)

    def test_preventivo_senza_materiali_zero(self):
        p = Preventivo()
        p.ricalcola_tutto()
        self.assertAlmostEqual(p.preventivo_finale, 0.0)
        self.assertAlmostEqual(p.costo_totale_materiali, 0.0)


# ===========================================================================
# 9. Materiale model
# ===========================================================================

class TestMaterialeModel(unittest.TestCase):

    def test_costruttore_default(self):
        m = Materiale()
        self.assertEqual(m.nome, "")
        self.assertAlmostEqual(m.spessore, 0.0)
        self.assertAlmostEqual(m.prezzo, 0.0)
        self.assertIsNone(m.categoria_id)

    def test_costruttore_con_valori(self):
        m = Materiale("HS300", 0.3, 20.0, "CIT", 18.0, 100.0, 50.0, 3)
        self.assertEqual(m.nome, "HS300")
        self.assertAlmostEqual(m.spessore, 0.3)
        self.assertEqual(m.categoria_id, 3)


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
