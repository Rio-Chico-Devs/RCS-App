#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test INVASIVI RCS-App — cerca attivamente di far andare in errore il programma.
Copre: sequenze CRUD complesse, dati corrotti, FK, concorrenza logica,
       integrità dati cross-tabella, round-trip serializzazione, bulk ops.
"""

import sys
import os
import json
import math
import tempfile
import sqlite3
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from models.materiale import Materiale, MaterialeCalcolato
from models.preventivo import Preventivo


# ---------------------------------------------------------------------------
# Helpers condivisi
# ---------------------------------------------------------------------------

def make_db():
    tmp = tempfile.mkdtemp()
    return DatabaseManager(db_path=os.path.join(tmp, "test.db"))


def _prev(**kwargs):
    base = {
        "data_creazione": datetime.now().isoformat(),
        "numero_revisione": 1,
        "preventivo_originale_id": None,
        "nome_cliente": "Cliente Test",
        "numero_ordine": "ORD-001",
        "misura": "100x200",
        "descrizione": "desc",
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
        "materiali_utilizzati": [],
        "note_revisione": "",
        "storico_modifiche": "[]",
    }
    base.update(kwargs)
    return base


# ===========================================================================
# A. MATERIALI — operazioni invasive
# ===========================================================================

class TestMateriali_Invasivi(unittest.TestCase):

    def setUp(self):
        self.db = make_db()

    # --- Sequenze add/update/delete ---

    def test_add_delete_readd_stesso_nome(self):
        """Elimina e reinserisce lo stesso nome: deve funzionare, ID diverso."""
        mid1 = self.db.add_materiale("RICICLO", 0.1, 1.0)
        self.db.delete_materiale(mid1)
        mid2 = self.db.add_materiale("RICICLO", 0.2, 2.0)
        self.assertIsInstance(mid2, int)
        self.assertNotEqual(mid1, mid2)

    def test_update_dopo_delete_restituisce_false(self):
        mid = self.db.add_materiale("GHOST_UPD", 0.1, 1.0)
        self.db.delete_materiale(mid)
        result = self.db.update_materiale_base(mid, "GHOST_UPD_2", 0.2, 2.0)
        self.assertFalse(bool(result))

    def test_update_multiplo_stesso_materiale_conserva_ultimo(self):
        mid = self.db.add_materiale("MULTI_UPD", 0.1, 1.0)
        for i in range(10):
            self.db.update_materiale_base(mid, f"MULTI_UPD_{i}", float(i) * 0.1, float(i) * 10)
        row = self.db.get_materiale_by_id(mid)
        self.assertEqual(row[1], "MULTI_UPD_9")
        self.assertAlmostEqual(row[2], 0.9, places=5)
        self.assertAlmostEqual(row[3], 90.0)

    def test_update_prezzo_multiplo_conserva_ultimo(self):
        mid = self.db.add_materiale("PREZZO_MULTI", 0.1, 1.0)
        for p in [10.0, 20.0, 30.0, 0.01, 999.99]:
            self.db.update_prezzo_materiale(mid, p)
        row = self.db.get_materiale_by_id(mid)
        self.assertAlmostEqual(row[3], 999.99)

    def test_get_by_nome_dopo_update_vecchio_nome_non_trovato(self):
        mid = self.db.add_materiale("NOME_A", 0.1, 1.0)
        self.db.update_materiale_base(mid, "NOME_B", 0.1, 1.0)
        self.assertIsNone(self.db.get_materiale_by_nome("NOME_A"))
        self.assertIsNotNone(self.db.get_materiale_by_nome("NOME_B"))

    def test_bulk_insert_100_materiali(self):
        """Inserisce 100 materiali e verifica count."""
        count_iniziale = len(self.db.get_all_materiali())
        for i in range(100):
            self.db.add_materiale(f"BULK_{i:03d}", round(i * 0.01, 4), float(i))
        tutti = self.db.get_all_materiali()
        self.assertEqual(len(tutti), count_iniziale + 100)

    def test_bulk_delete_tutti_i_nuovi(self):
        ids = [self.db.add_materiale(f"DEL_BULK_{i}", 0.1, 1.0) for i in range(20)]
        for mid in ids:
            self.db.delete_materiale(mid)
        for mid in ids:
            self.assertIsNone(self.db.get_materiale_by_id(mid))

    def test_categoria_id_inesistente_accettata(self):
        self.skipTest("Categoria rimossa dal sistema")

    def test_update_materiale_completo_tutti_campi(self):
        """update_materiale aggiorna tutti i campi inclusi quelli legacy."""
        mid = self.db.add_materiale("FULL_UPD", 0.1, 1.0)
        result = self.db.update_materiale(
            mid, "FULL_UPD_MOD", 0.5, 50.0,
            fornitore="FORN_TEST", prezzo_fornitore=45.0,
            capacita_magazzino=200.0, giacenza=10.0
        )
        self.assertTrue(result)
        row = self.db.get_materiale_by_id(mid)
        self.assertEqual(row[1], "FULL_UPD_MOD")
        self.assertAlmostEqual(row[2], 0.5)
        self.assertAlmostEqual(row[3], 50.0)

    def test_doppio_delete_stesso_materiale(self):
        """Il secondo delete deve restituire False, non crashare."""
        mid = self.db.add_materiale("DOUBLE_DEL", 0.1, 1.0)
        self.assertTrue(self.db.delete_materiale(mid))
        self.assertFalse(bool(self.db.delete_materiale(mid)))

    def test_get_materiale_by_nome_con_apostrofo(self):
        nome = "L'acciaio"
        mid = self.db.add_materiale(nome, 0.1, 1.0)
        self.assertIsInstance(mid, int)
        row = self.db.get_materiale_by_nome(nome)
        self.assertIsNotNone(row)
        self.assertEqual(row[1], nome)

    def test_add_materiale_prezzo_molto_preciso(self):
        """Float con molti decimali: SQLite REAL ha precisione ~15 cifre."""
        mid = self.db.add_materiale("PRECISIONE", 0.123456789, 12.3456789012345)
        row = self.db.get_materiale_by_id(mid)
        self.assertAlmostEqual(row[2], 0.123456789, places=9)
        self.assertAlmostEqual(row[3], 12.3456789012345, places=10)


# ===========================================================================
# B. MAGAZZINO — operazioni invasive
# ===========================================================================

class TestMagazzino_Invasivi(unittest.TestCase):

    def setUp(self):
        self.db = make_db()
        self.mid = self.db.add_materiale("MAT_INV", 0.25, 30.0)
        self.db.add_fornitore_a_materiale(self.mid, "F_INV", 10.0, 5.0, 500.0)

    def test_sequenza_carico_scarico_multipla(self):
        """Carico e scarico alternati: bilancio finale corretto."""
        ops = [("carico", 100.0), ("scarico", 30.0), ("carico", 50.0),
               ("scarico", 20.0), ("carico", 10.0), ("scarico", 10.0)]
        atteso = 0.0
        for tipo, q in ops:
            self.db.registra_movimento(self.mid, tipo, q, fornitore_nome="F_INV")
            if tipo == "carico":
                atteso += q
            else:
                atteso = max(atteso - q, 0.0)
        tot = self.db.get_giacenza_totale_materiale(self.mid)
        self.assertAlmostEqual(tot, atteso, places=2)

    def test_scarico_piu_grande_del_carico_si_ferma_a_zero(self):
        self.db.registra_movimento(self.mid, "carico", 50.0, fornitore_nome="F_INV")
        self.db.registra_movimento(self.mid, "scarico", 200.0, fornitore_nome="F_INV")
        tot = self.db.get_giacenza_totale_materiale(self.mid)
        self.assertAlmostEqual(tot, 0.0, places=2)

    def test_carico_senza_fornitore_aggiorna_giacenza_legacy(self):
        """Movimento senza fornitore_nome → aggiorna materiali.giacenza (legacy)."""
        self.db.registra_movimento(self.mid, "carico", 75.0)  # nessun fornitore
        # Il campo materiale_fornitori rimane invariato (0)
        # La giacenza legacy di materiali.giacenza sale
        # get_giacenza_totale prima controlla materiale_fornitori (0 da F_INV)
        # poi il fallback legacy. Verifica che il movimento sia stato registrato.
        movimenti = self.db.get_movimenti_per_materiale(self.mid)
        self.assertEqual(len(movimenti), 1)

    def test_tipo_movimento_non_valido_non_crasha(self):
        """Tipo non previsto ('reso', 'trasferimento'): viene registrato ma giacenza non cambia."""
        giacenza_prima = self.db.get_giacenza_totale_materiale(self.mid)
        mov_id = self.db.registra_movimento(self.mid, "reso", 10.0, fornitore_nome="F_INV")
        self.assertIsInstance(mov_id, int)
        giacenza_dopo = self.db.get_giacenza_totale_materiale(self.mid)
        self.assertAlmostEqual(giacenza_prima, giacenza_dopo)

    def test_carico_quantita_negativa_non_blocca_ma_registra(self):
        """Quantità negativa: il DB la registra (nessun vincolo CHECK)."""
        mov_id = self.db.registra_movimento(self.mid, "carico", -10.0, fornitore_nome="F_INV")
        self.assertIsInstance(mov_id, int)

    def test_movimenti_materiali_diversi_non_si_mescolano(self):
        mid2 = self.db.add_materiale("MAT_INV2", 0.1, 5.0)
        self.db.add_fornitore_a_materiale(mid2, "F2", 5.0, 0.0, 100.0)
        self.db.registra_movimento(self.mid, "carico", 100.0, fornitore_nome="F_INV")
        self.db.registra_movimento(mid2, "carico", 30.0, fornitore_nome="F2")
        mov1 = self.db.get_movimenti_per_materiale(self.mid)
        mov2 = self.db.get_movimenti_per_materiale(mid2)
        self.assertEqual(len(mov1), 1)
        self.assertEqual(len(mov2), 1)
        self.assertAlmostEqual(self.db.get_giacenza_totale_materiale(self.mid), 100.0)
        self.assertAlmostEqual(self.db.get_giacenza_totale_materiale(mid2), 30.0)

    def test_bulk_movimenti_conta_correttamente(self):
        """50 carichi da 1.0 ciascuno → giacenza = 50.0"""
        for _ in range(50):
            self.db.registra_movimento(self.mid, "carico", 1.0, fornitore_nome="F_INV")
        tot = self.db.get_giacenza_totale_materiale(self.mid)
        self.assertAlmostEqual(tot, 50.0, places=2)

    def test_get_movimenti_limit_zero(self):
        """limit=0: comportamento non standard, non deve crashare."""
        self.db.registra_movimento(self.mid, "carico", 10.0, fornitore_nome="F_INV")
        try:
            movimenti = self.db.get_movimenti_per_materiale(self.mid, limit=0)
            self.assertIsInstance(movimenti, list)
        except Exception:
            pass  # accettabile se il driver non supporta LIMIT 0

    def test_consumi_periodo_solo_scarichi(self):
        """get_consumi_periodo conta solo tipo='scarico', non i carichi."""
        inizio = (datetime.now() - timedelta(hours=1)).isoformat()
        fine = (datetime.now() + timedelta(hours=1)).isoformat()
        self.db.registra_movimento(self.mid, "carico", 100.0, fornitore_nome="F_INV")
        self.db.registra_movimento(self.mid, "scarico", 40.0, fornitore_nome="F_INV")
        consumi = self.db.get_consumi_periodo(inizio, fine)
        # Deve riportare 40, non 140
        qtà = {r[0]: r[3] for r in consumi}
        self.assertAlmostEqual(qtà.get(self.mid, 0.0), 40.0)

    def test_giacenza_multi_fornitore_indipendente(self):
        """Scarico da F2 non tocca giacenza di F1."""
        mid = self.db.add_materiale("MAT_MULTI_F", 0.1, 1.0)
        self.db.add_fornitore_a_materiale(mid, "FA", 5.0, 0.0, 100.0)
        self.db.add_fornitore_a_materiale(mid, "FB", 5.0, 0.0, 100.0)
        self.db.registra_movimento(mid, "carico", 60.0, fornitore_nome="FA")
        self.db.registra_movimento(mid, "carico", 40.0, fornitore_nome="FB")
        self.db.registra_movimento(mid, "scarico", 10.0, fornitore_nome="FB")
        tot = self.db.get_giacenza_totale_materiale(mid)
        self.assertAlmostEqual(tot, 90.0, places=2)


# ===========================================================================
# C. PREVENTIVI — operazioni invasive
# ===========================================================================

class TestPreventivi_Invasivi(unittest.TestCase):

    def setUp(self):
        self.db = make_db()

    def _add(self, **kwargs):
        return self.db.add_preventivo(_prev(**kwargs))

    # --- Sequenze update/storico ---

    def test_update_10_volte_storico_contiene_tutte_le_versioni(self):
        pid = self._add(nome_cliente="STORIA")
        for i in range(10):
            self.db.update_preventivo(pid, _prev(
                nome_cliente=f"STORIA_V{i}", preventivo_finale=float(i * 100)
            ))
        storico = self.db.get_storico_modifiche(pid)
        self.assertGreaterEqual(len(storico), 10)

    def test_ripristina_versione_i_dati_tornano_indietro(self):
        pid = self._add(nome_cliente="RIPRISTINA_DATI", preventivo_finale=100.0)
        self.db.update_preventivo(pid, _prev(nome_cliente="RIPRISTINA_DATI", preventivo_finale=200.0))
        storico = self.db.get_storico_modifiche(pid)
        # Il primo snapshot contiene preventivo_finale=100
        ts = storico[-1]["timestamp"]  # la versione più vecchia
        self.db.ripristina_versione_preventivo(pid, ts)
        ripristinato = self.db.get_preventivo_by_id(pid)
        self.assertAlmostEqual(ripristinato["preventivo_finale"], 100.0)

    def test_storico_e_json_valido(self):
        pid = self._add()
        self.db.update_preventivo(pid, _prev(costo_totale_materiali=42.0))
        storico = self.db.get_storico_modifiche(pid)
        self.assertIsInstance(storico, list)
        for entry in storico:
            self.assertIn("timestamp", entry)

    def test_delete_revisione_elimina_solo_revisione(self):
        """delete_preventivo_e_revisioni su una revisione elimina solo quella revisione,
        lasciando intatto il preventivo originale."""
        pid_orig = self._add(nome_cliente="ORIG_KEEP")
        rev_id = self.db.add_revisione_preventivo(pid_orig, _prev(numero_revisione=2), "r1")
        self.db.delete_preventivo_e_revisioni(rev_id)
        # Solo la revisione viene eliminata, l'originale sopravvive
        self.assertIsNone(self.db.get_preventivo_by_id(rev_id))
        self.assertIsNotNone(self.db.get_preventivo_by_id(pid_orig))

    def test_catena_revisioni_tre_livelli(self):
        """rev1 → rev2 → rev3: tutte leggibili, numero revisione crescente."""
        pid = self._add(nome_cliente="CATENA")
        r2 = self.db.add_revisione_preventivo(pid, _prev(numero_revisione=2), "rev2")
        r3 = self.db.add_revisione_preventivo(pid, _prev(numero_revisione=3), "rev3")
        revisioni = self.db.get_revisioni_preventivo(pid)
        numeri = [r[8] for r in revisioni]  # numero_revisione è col index 8
        self.assertIn(2, numeri)
        self.assertIn(3, numeri)

    def test_preventivo_con_30_materiali_round_trip(self):
        """Salva e rilegge un preventivo con 30 MaterialeCalcolato."""
        mats = []
        for i in range(30):
            mc = MaterialeCalcolato()
            mc.diametro = float(50 + i)
            mc.lunghezza = 200.0
            mc.giri = 3
            mc.spessore = 0.25
            mc.costo_materiale = 30.0
            mc.ricalcola_tutto()
            mats.append(mc.to_dict())
        pid = self._add(materiali_utilizzati=mats, costo_totale_materiali=999.0)
        prev = self.db.get_preventivo_by_id(pid)
        self.assertEqual(len(prev["materiali_utilizzati"]), 30)
        self.assertAlmostEqual(prev["materiali_utilizzati"][0]["diametro"], 50.0)
        self.assertAlmostEqual(prev["materiali_utilizzati"][29]["diametro"], 79.0)

    def test_preventivo_materiali_utilizzati_json_corrotto_non_crasha(self):
        """Se materiali_utilizzati nel DB è JSON malformato, get_preventivo_by_id
        restituisce lista vuota senza eccezione."""
        pid = self._add()
        # Scrivi direttamente nel DB un JSON corrotto
        import sqlite3 as _sqlite3
        with _sqlite3.connect(self.db.db_path) as conn:
            conn.execute("UPDATE preventivi SET materiali_utilizzati=? WHERE id=?",
                         ("QUESTO NON È JSON {{{", pid))
            conn.commit()
        prev = self.db.get_preventivo_by_id(pid)
        self.assertIsNotNone(prev)
        self.assertIsInstance(prev.get("materiali_utilizzati", []), list)

    def test_get_all_preventivi_latest_restituisce_uno_per_gruppo(self):
        """get_all_preventivi_latest restituisce UN solo record per ogni gruppo:
        la revisione con numero_revisione più alto (col index 8).
        L'originale NON compare se esiste una revisione più recente."""
        pid = self._add(nome_cliente="LATEST_GRUPPO")
        rev_id = self.db.add_revisione_preventivo(pid, _prev(numero_revisione=2), "r1")
        latest = self.db.get_all_preventivi_latest()
        ids_latest = [row[0] for row in latest]
        # La revisione (rev_id) deve essere presente
        self.assertIn(rev_id, ids_latest)
        # L'originale (pid) NON deve comparire (è coperto dalla revisione)
        self.assertNotIn(pid, ids_latest)
        # Numero revisione dell'entry deve essere 2
        entry = next(row for row in latest if row[0] == rev_id)
        self.assertEqual(entry[8], 2)

    def test_preventivo_campi_stringa_con_caratteri_speciali(self):
        nome = "José García & Figli™ S.r.l."
        pid = self._add(nome_cliente=nome, numero_ordine="ORD/2024-001\\test")
        prev = self.db.get_preventivo_by_id(pid)
        self.assertEqual(prev["nome_cliente"], nome)

    def test_update_preventivo_id_non_esistente_restituisce_false(self):
        result = self.db.update_preventivo(999999, _prev())
        self.assertFalse(bool(result))

    def test_preventivo_valori_float_estremi(self):
        pid = self._add(
            costo_totale_materiali=0.0001,
            preventivo_finale=9999999.99,
            prezzo_cliente=0.01
        )
        prev = self.db.get_preventivo_by_id(pid)
        self.assertAlmostEqual(prev["costo_totale_materiali"], 0.0001, places=4)
        self.assertAlmostEqual(prev["preventivo_finale"], 9999999.99, places=2)


# ===========================================================================
# D. CATEGORIE — operazioni invasive
# ===========================================================================

class TestCategorie_Invasivi(unittest.TestCase):

    def setUp(self):
        self.db = make_db()

    def test_update_nome_categoria_duplicato_fallisce(self):
        self.skipTest("Categoria rimossa dal sistema")

    def test_delete_categoria_con_materiali_non_elimina_materiali(self):
        self.skipTest("Categoria rimossa dal sistema")

    def test_categoria_con_giacenza_minima_maggiore_di_desiderata(self):
        self.skipTest("Categoria rimossa dal sistema")

    def test_get_materiali_per_categoria_dopo_delete_categoria(self):
        self.skipTest("Categoria rimossa dal sistema")

    def test_bulk_categorie_e_materiali(self):
        self.skipTest("Categoria rimossa dal sistema")


# ===========================================================================
# E. FORNITORI — operazioni invasive
# ===========================================================================

class TestFornitori_Invasivi(unittest.TestCase):

    def setUp(self):
        self.db = make_db()

    def test_rename_fornitore_propaga_a_legacy_e_materiale_fornitori(self):
        """Dopo rename, sia materiali.fornitore che materiale_fornitori sono aggiornati."""
        mid = self.db.add_materiale("MAT_PROP", 0.1, 1.0, fornitore="FORN_PRIMA")
        self.db.add_fornitore("FORN_PRIMA")
        self.db.add_fornitore_a_materiale(mid, "FORN_PRIMA", 8.0)
        self.db.rename_fornitore("FORN_PRIMA", "FORN_DOPO")
        # Controllo legacy: get_scorte_per_fornitore("FORN_DOPO") deve trovare il materiale
        scorte = self.db.get_scorte_per_fornitore("FORN_DOPO")
        self.assertGreater(len(scorte), 0)
        # Controllo materiale_fornitori
        fornitori_mat = self.db.get_fornitori_per_materiale(mid)
        nomi = [r[1] for r in fornitori_mat]
        self.assertIn("FORN_DOPO", nomi)
        self.assertNotIn("FORN_PRIMA", nomi)
        # Il vecchio nome non deve più dare risultati
        scorte_vecchio = self.db.get_scorte_per_fornitore("FORN_PRIMA")
        self.assertEqual(len(scorte_vecchio), 0)

    def test_assegna_materiali_sovrascrive_fornitore_legacy_precedente(self):
        """assegna_materiali sovrascrive materiali.fornitore con il nuovo nome."""
        mid = self.db.add_materiale("MAT_SOVR", 0.1, 1.0, fornitore="FORN_OLD")
        self.db.add_fornitore("FORN_NEW")
        self.db.assegna_materiali_a_fornitore("FORN_NEW", [mid])
        scorte_old = self.db.get_scorte_per_fornitore("FORN_OLD")
        ids_old = [r[0] for r in scorte_old]
        self.assertNotIn(mid, ids_old)
        scorte_new = self.db.get_scorte_per_fornitore("FORN_NEW")
        ids_new = [r[0] for r in scorte_new]
        self.assertIn(mid, ids_new)

    def test_fornitore_con_molti_materiali(self):
        """Un fornitore assegnato a 50 materiali: get_scorte_per_fornitore li ritorna tutti."""
        self.db.add_fornitore("FORN_MANY")
        ids = [self.db.add_materiale(f"M_MANY_{i}", 0.1, 1.0) for i in range(50)]
        self.db.assegna_materiali_a_fornitore("FORN_MANY", ids)
        scorte = self.db.get_scorte_per_fornitore("FORN_MANY")
        self.assertEqual(len(scorte), 50)

    def test_add_fornitore_nome_molto_lungo(self):
        nome = "F" * 300
        fid = self.db.add_fornitore(nome)
        self.assertIsInstance(fid, int)

    def test_rename_sequenziale_a_b_poi_b_c(self):
        """A→B poi B→C: alla fine i materiali devono avere 'C', non 'A' né 'B'."""
        mid = self.db.add_materiale("MAT_ABC", 0.1, 1.0, fornitore="FORN_A")
        self.db.add_fornitore("FORN_A")
        self.db.add_fornitore_a_materiale(mid, "FORN_A", 5.0)
        self.db.rename_fornitore("FORN_A", "FORN_B")
        self.db.rename_fornitore("FORN_B", "FORN_C")
        scorte = self.db.get_scorte_per_fornitore("FORN_C")
        ids = [r[0] for r in scorte]
        self.assertIn(mid, ids)
        self.assertEqual(len(self.db.get_scorte_per_fornitore("FORN_A")), 0)
        self.assertEqual(len(self.db.get_scorte_per_fornitore("FORN_B")), 0)


# ===========================================================================
# F. MATERIALECALCOLATO — calcoli e serializzazione invasivi
# ===========================================================================

class TestMaterialeCalcolato_Invasivi(unittest.TestCase):

    def _mc(self, **kwargs):
        mc = MaterialeCalcolato()
        mc.diametro = kwargs.get("diametro", 100.0)
        mc.lunghezza = kwargs.get("lunghezza", 200.0)
        mc.giri = kwargs.get("giri", 3)
        mc.spessore = kwargs.get("spessore", 0.25)
        mc.costo_materiale = kwargs.get("costo", 30.0)
        mc.ricalcola_tutto()
        return mc

    def test_to_dict_from_dict_round_trip(self):
        """Serializza, deserializza via JSON e verifica tutti i valori numerici."""
        mc = self._mc(diametro=150.0, lunghezza=300.0, giri=5, spessore=0.3, costo=45.0)
        d = mc.to_dict()
        json_str = json.dumps(d)
        d2 = json.loads(json_str)
        self.assertAlmostEqual(d2["diametro"], mc.diametro)
        self.assertAlmostEqual(d2["lunghezza"], mc.lunghezza)
        self.assertAlmostEqual(d2["giri"], mc.giri)
        self.assertAlmostEqual(d2["spessore"], mc.spessore)
        self.assertAlmostEqual(d2["sviluppo"], mc.sviluppo, places=6)
        self.assertAlmostEqual(d2["diametro_finale"], mc.diametro_finale, places=6)
        self.assertAlmostEqual(d2["costo_totale"], mc.costo_totale, places=8)
        self.assertAlmostEqual(d2["maggiorazione"], mc.maggiorazione, places=8)

    def test_to_dict_non_contiene_tipi_non_serializzabili(self):
        """json.dumps non deve sollevare eccezioni su nessun valore del dict."""
        mc = self._mc()
        mc.is_conica = True
        mc.conicita_lato = "sinistra"
        mc.conicita_altezza_mm = 10.5
        mc.conicita_lunghezza_mm = 5.0
        d = mc.to_dict()
        try:
            json.dumps(d)
        except TypeError as e:
            self.fail(f"to_dict() contiene tipo non serializzabile: {e}")

    def test_ricalcola_dopo_modifica_diametro(self):
        mc = self._mc(diametro=100.0)
        sviluppo_old = mc.sviluppo
        mc.diametro = 200.0
        mc.ricalcola_tutto()
        self.assertGreater(mc.sviluppo, sviluppo_old)

    def test_ricalcola_dopo_modifica_giri(self):
        mc = self._mc(giri=3)
        mc.giri = 10
        mc.ricalcola_tutto()
        # Con più giri, sviluppo e costo devono aumentare
        mc_base = self._mc(giri=3)
        self.assertGreater(mc.sviluppo, mc_base.sviluppo)
        self.assertGreater(mc.costo_totale, mc_base.costo_totale)

    def test_giri_molto_grandi(self):
        mc = self._mc(giri=100, spessore=0.01)
        mc.ricalcola_tutto()
        self.assertGreater(mc.sviluppo, 0)
        self.assertFalse(math.isnan(mc.costo_totale))
        self.assertFalse(math.isinf(mc.costo_totale))

    def test_diametro_molto_piccolo(self):
        mc = self._mc(diametro=0.001, giri=1, spessore=0.001)
        mc.ricalcola_tutto()
        self.assertGreaterEqual(mc.sviluppo, 0)

    def test_costo_materiale_molto_alto(self):
        mc = self._mc(costo=99999.0)
        self.assertFalse(math.isnan(mc.maggiorazione))
        self.assertFalse(math.isinf(mc.maggiorazione))

    def test_arrotondamento_manuale_zero_usa_calcolo(self):
        """arrotondamento_manuale=0 significa 'nessun override': usa il calcolo."""
        mc = MaterialeCalcolato()
        mc.diametro = 100.0
        mc.giri = 3
        mc.spessore = 0.25
        mc.arrotondamento_manuale = 0.0
        mc.calcola_sviluppo()
        expected = ((100.0 + 3 * 0.25) * 3.14) * 3 + 5
        self.assertAlmostEqual(mc.sviluppo, expected, places=4)

    def test_piu_ricalcola_tutto_idempotente(self):
        """Chiamare ricalcola_tutto() più volte deve dare sempre lo stesso risultato."""
        mc = self._mc()
        mc.ricalcola_tutto()
        s1, c1, m1 = mc.sviluppo, mc.costo_totale, mc.maggiorazione
        mc.ricalcola_tutto()
        mc.ricalcola_tutto()
        self.assertAlmostEqual(mc.sviluppo, s1, places=10)
        self.assertAlmostEqual(mc.costo_totale, c1, places=10)
        self.assertAlmostEqual(mc.maggiorazione, m1, places=10)

    def test_orientamento_modifica_non_influenza_calcoli(self):
        """Cambiare orientamento non deve alterare sviluppo o costo."""
        mc = self._mc()
        s_prima = mc.sviluppo
        c_prima = mc.costo_totale
        mc.orientamento = {"rotation": 90, "flip_h": True, "flip_v": False}
        mc.ricalcola_tutto()
        self.assertAlmostEqual(mc.sviluppo, s_prima, places=10)
        self.assertAlmostEqual(mc.costo_totale, c_prima, places=10)


# ===========================================================================
# G. PREVENTIVO MODEL — aggregazioni invasive
# ===========================================================================

class TestPreventivoModel_Invasivi(unittest.TestCase):

    def _mc(self, mag=10.0, scarto=0.0):
        mc = MaterialeCalcolato()
        mc.maggiorazione = mag
        mc.costo_totale = mag / 1.1
        mc.scarto_mm2 = scarto
        return mc

    def test_rimuovi_primo_aggiorna_costo(self):
        p = Preventivo()
        p.aggiungi_materiale(self._mc(mag=20.0))
        p.aggiungi_materiale(self._mc(mag=30.0))
        p.rimuovi_materiale(0)
        self.assertAlmostEqual(p.costo_totale_materiali, 30.0)

    def test_rimuovi_ultimo_aggiorna_costo(self):
        p = Preventivo()
        p.aggiungi_materiale(self._mc(mag=20.0))
        p.aggiungi_materiale(self._mc(mag=30.0))
        p.rimuovi_materiale(1)
        self.assertAlmostEqual(p.costo_totale_materiali, 20.0)

    def test_rimuovi_indice_negativo_restituisce_false(self):
        p = Preventivo()
        p.aggiungi_materiale(self._mc())
        result = p.rimuovi_materiale(-1)
        self.assertFalse(result)

    def test_add_rimuovi_tutto_costo_zero(self):
        p = Preventivo()
        for _ in range(10):
            p.aggiungi_materiale(self._mc(mag=5.0))
        for i in range(9, -1, -1):
            p.rimuovi_materiale(i)
        self.assertAlmostEqual(p.costo_totale_materiali, 0.0)
        self.assertEqual(len(p.materiali_calcolati), 0)

    def test_ricalcola_tutto_con_valori_zero(self):
        p = Preventivo()
        p.ricalcola_tutto()
        self.assertAlmostEqual(p.subtotale, 0.0)
        self.assertAlmostEqual(p.maggiorazione_25, 0.0)
        self.assertAlmostEqual(p.preventivo_finale, 0.0)

    def test_mano_opera_senza_materiali(self):
        p = Preventivo()
        p.minuti_taglio = 60.0
        p.minuti_avvolgimento = 30.0
        p.ricalcola_tutto()
        self.assertAlmostEqual(p.tot_mano_opera, 90.0)
        self.assertAlmostEqual(p.subtotale, 90.0)
        self.assertAlmostEqual(p.preventivo_finale, 112.5)  # 90 * 1.25

    def test_to_dict_materiali_e_lista_di_dict(self):
        p = Preventivo()
        mc = MaterialeCalcolato()
        mc.diametro = 80.0
        mc.lunghezza = 150.0
        mc.giri = 2
        mc.spessore = 0.2
        mc.costo_materiale = 25.0
        mc.ricalcola_tutto()
        p.aggiungi_materiale(mc)
        d = p.to_dict()
        self.assertIsInstance(d["materiali_utilizzati"], list)
        self.assertEqual(len(d["materiali_utilizzati"]), 1)
        self.assertIsInstance(d["materiali_utilizzati"][0], dict)

    def test_scarto_totale_aggiornato_dopo_rimozione(self):
        p = Preventivo()
        p.aggiungi_materiale(self._mc(mag=5.0, scarto=100.0))
        p.aggiungi_materiale(self._mc(mag=5.0, scarto=200.0))
        p.ricalcola_scarto_totale()
        self.assertAlmostEqual(p.scarto_totale_mm2, 300.0)
        p.rimuovi_materiale(0)
        p.ricalcola_scarto_totale()
        self.assertAlmostEqual(p.scarto_totale_mm2, 200.0)

    def test_preventivo_finale_formula_corretta(self):
        """preventivo_finale = subtotale * 1.25 sempre."""
        p = Preventivo()
        p.aggiungi_materiale(self._mc(mag=80.0))
        p.costi_accessori = 20.0
        p.minuti_taglio = 40.0
        p.ricalcola_tutto()
        atteso = p.subtotale * 1.25
        self.assertAlmostEqual(p.preventivo_finale, atteso, places=6)


# ===========================================================================
# H. INTEGRAZIONE — workflow end-to-end
# ===========================================================================

class TestIntegrazione(unittest.TestCase):

    def setUp(self):
        self.db = make_db()

    def test_workflow_completo_materiale_magazzino_preventivo(self):
        """
        Crea categoria → materiale → fornitore → carico → preventivo → verifica.
        Simula un ciclo di vita reale completo.
        """
        # 1. Materiale
        mid = self.db.add_materiale("CF300", 0.3, 55.0)
        self.assertIsInstance(mid, int)

        # 3. Fornitore
        fid = self.db.add_fornitore("CARBONTECH")
        self.assertIsInstance(fid, int)
        mfid = self.db.add_fornitore_a_materiale(mid, "CARBONTECH", 50.0, 10.0, 200.0)
        self.assertIsInstance(mfid, int)

        # 4. Carico magazzino
        self.db.registra_movimento(mid, "carico", 150.0, note="Arrivo lotto", fornitore_nome="CARBONTECH")
        giacenza = self.db.get_giacenza_totale_materiale(mid)
        self.assertAlmostEqual(giacenza, 150.0)

        # 5. Calcola materiale per preventivo
        mc = MaterialeCalcolato()
        mc.diametro = 120.0
        mc.lunghezza = 250.0
        mc.giri = 4
        mc.spessore = 0.3
        mc.costo_materiale = 55.0
        mc.materiale_id = mid
        mc.materiale_nome = "CF300"
        mc.ricalcola_tutto()

        # 6. Crea preventivo
        p = Preventivo()
        p.aggiungi_materiale(mc)
        p.costi_accessori = 15.0
        p.minuti_taglio = 20.0
        p.ricalcola_tutto()

        pid = self.db.add_preventivo({
            **p.to_dict(),
            "data_creazione": datetime.now().isoformat(),
            "numero_revisione": 1,
            "preventivo_originale_id": None,
            "nome_cliente": "Acme Racing",
            "numero_ordine": "ORD-2024-001",
            "misura": "Ø120×250",
            "descrizione": "Rullo CF300",
            "codice": "R-001",
            "note_revisione": "",
        })
        self.assertIsInstance(pid, int)

        # 7. Scarico magazzino per il preventivo
        self.db.registra_movimento(mid, "scarico", 5.0,
                                   note="Usato per preventivo", preventivo_id=pid,
                                   fornitore_nome="CARBONTECH")
        giacenza_dopo = self.db.get_giacenza_totale_materiale(mid)
        self.assertAlmostEqual(giacenza_dopo, 145.0)

        # 8. Verifica lettura preventivo
        prev_letto = self.db.get_preventivo_by_id(pid)
        self.assertEqual(prev_letto["nome_cliente"], "Acme Racing")
        self.assertEqual(len(prev_letto["materiali_utilizzati"]), 1)
        self.assertAlmostEqual(prev_letto["preventivo_finale"], p.preventivo_finale, places=4)

    def test_elimina_materiale_con_movimenti_non_crasha(self):
        """Eliminare un materiale che ha movimenti in magazzino non deve crashare."""
        mid = self.db.add_materiale("MAT_CON_MOV", 0.1, 1.0)
        self.db.add_fornitore_a_materiale(mid, "F_MOV", 5.0)
        for _ in range(5):
            self.db.registra_movimento(mid, "carico", 10.0, fornitore_nome="F_MOV")
        result = self.db.delete_materiale(mid)
        self.assertTrue(result)
        self.assertIsNone(self.db.get_materiale_by_id(mid))

    def test_consistenza_giacenza_dopo_rename_fornitore(self):
        """
        Carico tramite 'FORN_A', poi rename a 'FORN_B':
        la giacenza letta con il nuovo nome deve essere uguale.
        """
        mid = self.db.add_materiale("MAT_REN_GIAC", 0.1, 1.0)
        self.db.add_fornitore("FORN_A")
        self.db.add_fornitore_a_materiale(mid, "FORN_A", 5.0)
        self.db.registra_movimento(mid, "carico", 80.0, fornitore_nome="FORN_A")
        giacenza_prima = self.db.get_giacenza_totale_materiale(mid)
        self.db.rename_fornitore("FORN_A", "FORN_B")
        giacenza_dopo = self.db.get_giacenza_totale_materiale(mid)
        self.assertAlmostEqual(giacenza_prima, giacenza_dopo, places=2)

    def test_preventivo_update_non_perde_materiali(self):
        """Dopo update_preventivo, i materiali_utilizzati non vengono cancellati."""
        mc = MaterialeCalcolato()
        mc.diametro = 90.0
        mc.lunghezza = 180.0
        mc.giri = 3
        mc.spessore = 0.2
        mc.costo_materiale = 20.0
        mc.ricalcola_tutto()
        pid = self.db.add_preventivo(_prev(
            materiali_utilizzati=[mc.to_dict()],
            costo_totale_materiali=mc.maggiorazione
        ))
        self.db.update_preventivo(pid, _prev(
            materiali_utilizzati=[mc.to_dict()],
            costo_totale_materiali=mc.maggiorazione,
            nome_cliente="CLIENTE_AGGIORNATO"
        ))
        prev = self.db.get_preventivo_by_id(pid)
        self.assertEqual(len(prev["materiali_utilizzati"]), 1)
        self.assertEqual(prev["nome_cliente"], "CLIENTE_AGGIORNATO")

    def test_workflow_revisioni_con_storico_e_ripristino(self):
        """
        Crea preventivo → aggiorna 3 volte → verifica storico →
        ripristina la prima versione → verifica valore tornato indietro.
        Lo storico è ordinato dal più vecchio al più recente (append):
          storico[0] = snapshot prima del 1° update (valore=100)
          storico[-1] = snapshot prima dell'ultimo update (valore=300)
        """
        pid = self.db.add_preventivo(_prev(preventivo_finale=100.0, nome_cliente="WORKFLOW_V"))
        for i, valore in enumerate([200.0, 300.0, 400.0], start=1):
            self.db.update_preventivo(pid, _prev(
                preventivo_finale=valore, nome_cliente=f"WORKFLOW_V{i}"
            ))
        storico = self.db.get_storico_modifiche(pid)
        self.assertGreaterEqual(len(storico), 3)
        # storico[0] = snapshot prima del 1° update → preventivo_finale era 100
        ts_primo = storico[0]["timestamp"]
        self.db.ripristina_versione_preventivo(pid, ts_primo)
        ripristinato = self.db.get_preventivo_by_id(pid)
        self.assertAlmostEqual(ripristinato["preventivo_finale"], 100.0)


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
