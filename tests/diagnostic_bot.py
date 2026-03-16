#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════╗
║            RCS-App DIAGNOSTIC BOT — test di sistema in larga scala      ║
║                                                                          ║
║  Esegui con:  python tests/diagnostic_bot.py                            ║
║  Opzioni:     --quick   (solo campione ridotto, ~5s)                    ║
║               --verbose (mostra ogni operazione)                         ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import json
import math
import random
import tempfile
import time
import traceback
import argparse
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from models.materiale import Materiale, MaterialeCalcolato
from models.preventivo import Preventivo

# ── colori ANSI ──────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
DIM    = "\033[2m"

# ─────────────────────────────────────────────────────────────────────────────

class Report:
    """Raccoglie e stampa i risultati del diagnostic bot."""

    def __init__(self):
        self.sections = []          # (nome, risultati)
        self._current = None
        self._results = []

    def section(self, nome):
        if self._current:
            self.sections.append((self._current, self._results))
        self._current = nome
        self._results = []
        print(f"\n{BOLD}{CYAN}▶ {nome}{RESET}")

    def ok(self, msg, verbose=False):
        self._results.append(("ok", msg))
        if verbose:
            print(f"  {GREEN}✓{RESET} {msg}")

    def warn(self, msg):
        self._results.append(("warn", msg))
        print(f"  {YELLOW}⚠{RESET}  {msg}")

    def fail(self, msg, exc=None):
        self._results.append(("fail", msg))
        detail = f": {exc}" if exc else ""
        print(f"  {RED}✗{RESET}  {msg}{DIM}{detail}{RESET}")

    def info(self, msg):
        print(f"  {DIM}  {msg}{RESET}")

    def flush(self):
        if self._current:
            self.sections.append((self._current, self._results))
            self._current = None
            self._results = []

    def summary(self):
        self.flush()
        totale_ok = totale_warn = totale_fail = 0
        print(f"\n{BOLD}{'═'*60}{RESET}")
        print(f"{BOLD}  RIEPILOGO DIAGNOSTICA{RESET}")
        print(f"{BOLD}{'═'*60}{RESET}")
        for nome, risultati in self.sections:
            ok   = sum(1 for s, _ in risultati if s == "ok")
            warn = sum(1 for s, _ in risultati if s == "warn")
            fail = sum(1 for s, _ in risultati if s == "fail")
            totale_ok   += ok
            totale_warn += warn
            totale_fail += fail
            stato = f"{GREEN}OK{RESET}" if fail == 0 and warn == 0 else \
                    (f"{YELLOW}WARN{RESET}" if fail == 0 else f"{RED}FAIL{RESET}")
            bar = f"✓{ok} ⚠{warn} ✗{fail}"
            print(f"  {stato:20s}  {nome:35s}  {DIM}{bar}{RESET}")
            # Stampa i dettagli dei failure
            for s, m in risultati:
                if s == "fail":
                    print(f"           {RED}→ {m}{RESET}")
                elif s == "warn":
                    print(f"           {YELLOW}→ {m}{RESET}")

        print(f"{BOLD}{'─'*60}{RESET}")
        colore = GREEN if totale_fail == 0 else RED
        print(f"  {BOLD}TOTALE:{RESET}  "
              f"{GREEN}✓ {totale_ok} ok{RESET}  "
              f"{YELLOW}⚠ {totale_warn} warn{RESET}  "
              f"{colore}✗ {totale_fail} fail{RESET}")
        print(f"{BOLD}{'═'*60}{RESET}\n")
        return totale_fail


R = Report()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_db():
    tmp = tempfile.mkdtemp()
    return DatabaseManager(db_path=os.path.join(tmp, "diagnostic.db"))


def _prev_dict(pid_orig=None, n_rev=1, **kwargs):
    base = {
        "data_creazione": (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat(),
        "numero_revisione": n_rev,
        "preventivo_originale_id": pid_orig,
        "nome_cliente": f"Cliente_{random.randint(1000, 9999)}",
        "numero_ordine": f"ORD-{random.randint(1, 9999):04d}",
        "misura": f"{random.randint(50, 300)}x{random.randint(100, 600)}",
        "descrizione": "Generato da diagnostic bot",
        "codice": f"DC{random.randint(10, 99)}",
        "costo_totale_materiali": round(random.uniform(10, 500), 2),
        "costi_accessori": round(random.uniform(0, 100), 2),
        "minuti_taglio": round(random.uniform(0, 60), 1),
        "minuti_avvolgimento": round(random.uniform(0, 120), 1),
        "minuti_pulizia": round(random.uniform(0, 30), 1),
        "minuti_rettifica": round(random.uniform(0, 20), 1),
        "minuti_imballaggio": round(random.uniform(0, 15), 1),
        "tot_mano_opera": 0.0,
        "subtotale": 0.0,
        "maggiorazione_25": 0.0,
        "preventivo_finale": round(random.uniform(50, 2000), 2),
        "prezzo_cliente": round(random.uniform(50, 2500), 2),
        "materiali_utilizzati": [],
        "note_revisione": "",
        "storico_modifiche": "[]",
    }
    base.update(kwargs)
    return base


def _mc_random(mid=None, nome=None):
    mc = MaterialeCalcolato()
    mc.diametro = round(random.uniform(30, 300), 1)
    mc.lunghezza = round(random.uniform(50, 500), 1)
    mc.giri = random.randint(1, 8)
    mc.spessore = round(random.choice([0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]), 2)
    mc.costo_materiale = round(random.uniform(5, 100), 2)
    if mid:
        mc.materiale_id = mid
    if nome:
        mc.materiale_nome = nome
    mc.ricalcola_tutto()
    return mc


def safe(fn, *args, default=None, **kwargs):
    """Esegui fn senza far crashare il bot. Restituisce (risultato, None) o (default, exc)."""
    try:
        return fn(*args, **kwargs), None
    except Exception as e:
        return default, e


# ─────────────────────────────────────────────────────────────────────────────
# 1. MATERIALI — bulk CRUD
# ─────────────────────────────────────────────────────────────────────────────

def test_materiali(db, n=50, verbose=False):
    R.section(f"MATERIALI — CRUD bulk ({n} record)")
    ids_inseriti = []
    nomi_inseriti = []
    errori_insert = 0

    # INSERT
    for i in range(n):
        nome = f"DIAG_MAT_{i:04d}"
        spessore = round(random.uniform(0.05, 1.0), 3)
        prezzo = round(random.uniform(1.0, 200.0), 2)
        mid, exc = safe(db.add_materiale, nome, spessore, prezzo)
        if exc or not isinstance(mid, int):
            errori_insert += 1
        else:
            ids_inseriti.append(mid)
            nomi_inseriti.append(nome)

    if errori_insert:
        R.fail(f"Insert materiali: {errori_insert}/{n} falliti")
    else:
        R.ok(f"Insert {n} materiali: tutti OK", verbose)

    # DUPLICATO
    dup, exc = safe(db.add_materiale, nomi_inseriti[0], 0.1, 1.0)
    if dup is False or dup is None:
        R.ok("Duplicate insert bloccato correttamente", verbose)
    else:
        R.fail("Duplicate insert NON bloccato", exc)

    # READ e verifica round-trip nome
    errori_read = 0
    for mid, nome in zip(ids_inseriti[:20], nomi_inseriti[:20]):
        row, exc = safe(db.get_materiale_by_id, mid)
        if exc or row is None or row[1] != nome:
            errori_read += 1
    if errori_read:
        R.fail(f"Read by ID: {errori_read}/20 discordanti o None")
    else:
        R.ok("Read by ID (campione 20): tutti concordi", verbose)

    # UPDATE
    errori_upd = 0
    for mid, nome in zip(ids_inseriti[:20], nomi_inseriti[:20]):
        nuovo_nome = nome + "_UPD"
        nuovo_prezzo = round(random.uniform(50, 300), 2)
        result, exc = safe(db.update_materiale_base, mid, nuovo_nome, 0.3, nuovo_prezzo)
        if exc or not result:
            errori_upd += 1
        else:
            row, _ = safe(db.get_materiale_by_id, mid)
            if row and abs(row[3] - nuovo_prezzo) > 0.001:
                errori_upd += 1
    if errori_upd:
        R.fail(f"Update materiali: {errori_upd}/20 falliti o dati discordanti")
    else:
        R.ok("Update 20 materiali: nome e prezzo aggiornati", verbose)

    # UPDATE PREZZO
    errori_pr = 0
    for mid in ids_inseriti[20:40]:
        p = round(random.uniform(1, 999), 4)
        safe(db.update_prezzo_materiale, mid, p)
        row, _ = safe(db.get_materiale_by_id, mid)
        if row and abs(row[3] - p) > 0.0001:
            errori_pr += 1
    if errori_pr:
        R.fail(f"update_prezzo_materiale: {errori_pr}/20 discordanti")
    else:
        R.ok("update_prezzo_materiale (20 materiali): tutti concordi", verbose)

    # DELETE
    errori_del = 0
    da_eliminare = ids_inseriti[:10]
    for mid in da_eliminare:
        result, exc = safe(db.delete_materiale, mid)
        if exc or not result:
            errori_del += 1
        else:
            row, _ = safe(db.get_materiale_by_id, mid)
            if row is not None:
                errori_del += 1
    if errori_del:
        R.fail(f"Delete materiali: {errori_del}/10 non eliminati o ancora presenti")
    else:
        R.ok("Delete 10 materiali + verifica scomparsa: OK", verbose)

    # DOPPIO DELETE
    result, exc = safe(db.delete_materiale, da_eliminare[0])
    if result:
        R.warn("Doppio delete restituisce True (dovrebbe essere False)")
    else:
        R.ok("Doppio delete restituisce False", verbose)

    # GET_ALL count
    tutti, _ = safe(db.get_all_materiali)
    n_attesi = n - len(da_eliminare)
    n_effettivi = sum(1 for r in tutti if r[1].startswith("DIAG_MAT_"))
    if n_effettivi != n_attesi:
        R.fail(f"Count materiali dopo delete: attesi {n_attesi}, trovati {n_effettivi}")
    else:
        R.ok(f"Count materiali dopo delete: {n_effettivi} (corretto)", verbose)

    R.info(f"ID inseriti: {len(ids_inseriti)} | Eliminati: {len(da_eliminare)} | Rimanenti: {n_effettivi}")
    return ids_inseriti[len(da_eliminare):]  # restituisce gli ID ancora validi


# ─────────────────────────────────────────────────────────────────────────────
# 2. FORNITORI
# ─────────────────────────────────────────────────────────────────────────────

def test_fornitori(db, mat_ids, verbose=False):
    R.section("FORNITORI — CRUD + assegnazioni")

    fornitori = [f"DIAG_FORN_{i:02d}" for i in range(5)]
    fids = []
    for nome in fornitori:
        fid, exc = safe(db.add_fornitore, nome)
        if exc or not isinstance(fid, int):
            R.fail(f"Add fornitore '{nome}'", exc)
        else:
            fids.append(fid)
    R.ok(f"Inseriti {len(fids)} fornitori", verbose) if len(fids) == 5 else \
        R.fail(f"Inseriti solo {len(fids)}/5 fornitori")

    # Duplicato
    dup, _ = safe(db.add_fornitore, fornitori[0])
    if dup is False or dup is None:
        R.ok("Duplicato fornitore bloccato", verbose)
    else:
        R.fail("Duplicato fornitore NON bloccato")

    # Assegna materiali (campione 10)
    if mat_ids:
        campione = mat_ids[:10]
        safe(db.assegna_materiali_a_fornitore, fornitori[0], campione)
        scorte, _ = safe(db.get_scorte_per_fornitore, fornitori[0])
        scorte_ids = [r[0] for r in (scorte or [])]
        mancanti = [m for m in campione if m not in scorte_ids]
        if mancanti:
            R.fail(f"assegna_materiali: {len(mancanti)}/10 materiali non trovati nelle scorte")
        else:
            R.ok("assegna_materiali_a_fornitore + get_scorte: OK", verbose)

    # add_fornitore_a_materiale con prezzi
    if mat_ids:
        for i, mid in enumerate(mat_ids[:5]):
            safe(db.add_fornitore_a_materiale, mid, fornitori[1],
                 round(random.uniform(5, 50), 2),
                 round(random.uniform(1, 10), 2),
                 round(random.uniform(50, 500), 2))
        for mid in mat_ids[:5]:
            rows, _ = safe(db.get_fornitori_per_materiale, mid)
            if not rows:
                R.fail(f"get_fornitori_per_materiale({mid}): lista vuota")
                break
        else:
            R.ok("add_fornitore_a_materiale + get_fornitori_per_materiale: OK", verbose)

    # Rename
    safe(db.rename_fornitore, fornitori[2], fornitori[2] + "_REN")
    tutti, _ = safe(db.get_all_fornitori)
    nomi = [r[1] for r in (tutti or [])]
    if fornitori[2] + "_REN" in nomi and fornitori[2] not in nomi:
        R.ok("rename_fornitore: vecchio assente, nuovo presente", verbose)
    else:
        R.fail(f"rename_fornitore: vecchio='{fornitori[2] in nomi}', nuovo='{(fornitori[2]+'_REN') in nomi}'")

    # Rename su nome occupato
    safe(db.add_fornitore, "FORN_COLLISION_A")
    safe(db.add_fornitore, "FORN_COLLISION_B")
    res, _ = safe(db.rename_fornitore, "FORN_COLLISION_A", "FORN_COLLISION_B")
    if res:
        R.warn("rename su nome occupato non blocca (dovrebbe restituire False)")
    else:
        R.ok("rename su nome occupato bloccato", verbose)


# ─────────────────────────────────────────────────────────────────────────────
# 3. MAGAZZINO
# ─────────────────────────────────────────────────────────────────────────────

def test_magazzino(db, mat_ids, verbose=False):
    R.section(f"MAGAZZINO — movimenti su {min(len(mat_ids), 20)} materiali")

    if not mat_ids:
        R.warn("Nessun materiale disponibile, skip")
        return

    campione = mat_ids[:20]
    # Configura fornitore per ciascuno
    for mid in campione:
        safe(db.add_fornitore_a_materiale, mid, "FORN_MAG_TEST",
             round(random.uniform(5, 40), 2), 5.0, 1000.0)

    # Carico multiplo e verifica bilancio
    errori_bilancio = 0
    for mid in campione:
        carichi = [round(random.uniform(10, 100), 2) for _ in range(5)]
        scarichi = [round(random.uniform(1, 20), 2) for _ in range(3)]
        atteso = sum(carichi)
        for q in carichi:
            safe(db.registra_movimento, mid, "carico", q, fornitore_nome="FORN_MAG_TEST")
        for q in scarichi:
            safe(db.registra_movimento, mid, "scarico", q, fornitore_nome="FORN_MAG_TEST")
            atteso = max(atteso - q, 0.0)
        giacenza, exc = safe(db.get_giacenza_totale_materiale, mid)
        if exc:
            errori_bilancio += 1
        elif giacenza is None or abs(giacenza - atteso) > 0.01:
            errori_bilancio += 1

    if errori_bilancio:
        R.fail(f"Bilancio giacenza: {errori_bilancio}/{len(campione)} materiali discordanti")
    else:
        R.ok(f"Bilancio carico/scarico: tutti {len(campione)} materiali concordi", verbose)

    # Giacenza mai negativa
    negativi = 0
    for mid in campione:
        safe(db.registra_movimento, mid, "scarico", 999999.0, fornitore_nome="FORN_MAG_TEST")
        giacenza, _ = safe(db.get_giacenza_totale_materiale, mid)
        if giacenza is not None and giacenza < 0:
            negativi += 1
    if negativi:
        R.fail(f"Giacenza sotto zero: {negativi} materiali con giacenza negativa")
    else:
        R.ok("Giacenza mai negativa (MAX capped a 0): OK", verbose)

    # get_movimenti count
    errori_mov = 0
    for mid in campione[:5]:
        movimenti, _ = safe(db.get_movimenti_per_materiale, mid)
        if movimenti is None or len(movimenti) < 8:  # 5 carichi + 3 scarichi + 1 scarico totale
            errori_mov += 1
    if errori_mov:
        R.fail(f"get_movimenti: {errori_mov}/5 conteggi errati")
    else:
        R.ok("get_movimenti_per_materiale: conteggio corretto", verbose)

    # get_scorte
    scorte, exc = safe(db.get_scorte)
    if exc or scorte is None:
        R.fail("get_scorte crash", exc)
    else:
        ids_scorte = [r[0] for r in scorte]
        trovati = sum(1 for mid in campione if mid in ids_scorte)
        if trovati < len(campione):
            R.warn(f"get_scorte: trovati solo {trovati}/{len(campione)} materiali di test")
        else:
            R.ok(f"get_scorte: tutti {len(campione)} materiali presenti", verbose)

    # get_consumi_periodo
    inizio = (datetime.now() - timedelta(hours=2)).isoformat()
    fine = (datetime.now() + timedelta(hours=1)).isoformat()
    consumi, exc = safe(db.get_consumi_periodo, inizio, fine)
    if exc:
        R.fail("get_consumi_periodo crash", exc)
    elif not consumi:
        R.warn("get_consumi_periodo: lista vuota (aspettati scarichi)")
    else:
        R.ok(f"get_consumi_periodo: {len(consumi)} materiali con scarichi nel periodo", verbose)


# ─────────────────────────────────────────────────────────────────────────────
# 4. CATEGORIE
# ─────────────────────────────────────────────────────────────────────────────

def test_categorie(db, verbose=False):
    R.section("CATEGORIE — CRUD + assegnazione a materiali")

    cat_ids = []
    for i in range(10):
        cid, exc = safe(db.add_categoria, f"DIAG_CAT_{i:02d}",
                        round(random.uniform(5, 50), 1),
                        round(random.uniform(50, 200), 1),
                        round(random.uniform(200, 1000), 1),
                        f"Note categoria {i}")
        if exc or not isinstance(cid, int):
            R.fail(f"add_categoria_{i}", exc)
        else:
            cat_ids.append(cid)

    R.ok(f"Insert 10 categorie: {len(cat_ids)} OK", verbose) if len(cat_ids) == 10 else \
        R.fail(f"Insert: solo {len(cat_ids)}/10 riusciti")

    # Duplicato
    dup, _ = safe(db.add_categoria, "DIAG_CAT_00")
    if dup is False or dup is None:
        R.ok("Duplicato categoria bloccato", verbose)
    else:
        R.fail("Duplicato categoria NON bloccato")

    # Update
    errori = 0
    for cid in cat_ids[:5]:
        nuovo_nome = f"CAT_UPD_{cid}"
        res, exc = safe(db.update_categoria, cid, nuovo_nome, 10.0, 80.0, 400.0, "aggiornata")
        if exc or not res:
            errori += 1
        else:
            row, _ = safe(db.get_categoria_by_id, cid)
            if row is None or row[1] != nuovo_nome:
                errori += 1
    if errori:
        R.fail(f"Update categorie: {errori}/5 falliti o discordanti")
    else:
        R.ok("Update 5 categorie + verifica nome: OK", verbose)

    # Materiali in categoria e verifica
    errori_cat = 0
    if cat_ids:
        for i, cid in enumerate(cat_ids[:5]):
            for j in range(4):
                safe(db.add_materiale, f"MC_{cid}_{j}", round(0.1 * (j + 1), 1), float(j + 1),
                     categoria_id=cid)
            mats, _ = safe(db.get_materiali_per_categoria, cid)
            if mats is None or len(mats) != 4:
                errori_cat += 1
    if errori_cat:
        R.fail(f"get_materiali_per_categoria: {errori_cat}/5 conteggi errati")
    else:
        R.ok("get_materiali_per_categoria: tutti 4 per categoria", verbose)

    # Delete categoria → materiali sopravvivono
    if cat_ids:
        cid = cat_ids[-1]
        mid_test, _ = safe(db.add_materiale, "MAT_CAT_DEL_TEST", 0.1, 1.0, categoria_id=cid)
        safe(db.delete_categoria, cid)
        row, _ = safe(db.get_materiale_by_id, mid_test)
        if row is None:
            R.fail("Delete categoria ha eliminato anche il materiale (non deve)")
        else:
            R.ok("Delete categoria: il materiale sopravvive", verbose)

    return cat_ids[:-1] if cat_ids else []


# ─────────────────────────────────────────────────────────────────────────────
# 5. PREVENTIVI — bulk create, update, revisioni, storico
# ─────────────────────────────────────────────────────────────────────────────

def test_preventivi(db, mat_ids, n=100, verbose=False):
    R.section(f"PREVENTIVI — {n} creazioni, aggiornamenti, revisioni, ripristini")

    pids = []
    errori_insert = 0

    # ── CREATE ──
    for i in range(n):
        # Aggiungi 1-3 materiali calcolati
        n_mat = random.randint(1, 3)
        mats = []
        for _ in range(n_mat):
            mc = _mc_random()
            mats.append(mc.to_dict())
        pid, exc = safe(db.add_preventivo, _prev_dict(materiali_utilizzati=mats))
        if exc or not isinstance(pid, int):
            errori_insert += 1
        else:
            pids.append(pid)

    if errori_insert:
        R.fail(f"Insert preventivi: {errori_insert}/{n} falliti")
    else:
        R.ok(f"Insert {n} preventivi: tutti OK", verbose)

    if not pids:
        R.fail("Nessun preventivo inserito, impossibile continuare")
        return []

    # ── READ e verifica materiali round-trip ──
    errori_read = 0
    campione_read = random.sample(pids, min(20, len(pids)))
    for pid in campione_read:
        prev, exc = safe(db.get_preventivo_by_id, pid)
        if exc or prev is None:
            errori_read += 1
        elif not isinstance(prev.get("materiali_utilizzati"), list):
            errori_read += 1
    if errori_read:
        R.fail(f"Read preventivo: {errori_read}/20 NULL o materiali non lista")
    else:
        R.ok("Read 20 preventivi: struttura dati corretta", verbose)

    # ── UPDATE ──
    errori_upd = 0
    campione_upd = random.sample(pids, min(30, len(pids)))
    valori_aggiornati = {}
    for pid in campione_upd:
        nuovo_valore = round(random.uniform(100, 5000), 2)
        nuovo_cliente = f"AGGIORNATO_{pid}"
        safe(db.update_preventivo, pid, _prev_dict(
            preventivo_finale=nuovo_valore, nome_cliente=nuovo_cliente
        ))
        valori_aggiornati[pid] = (nuovo_valore, nuovo_cliente)
    # Verifica
    for pid, (valore, cliente) in valori_aggiornati.items():
        prev, _ = safe(db.get_preventivo_by_id, pid)
        if prev is None:
            errori_upd += 1
        elif abs(prev.get("preventivo_finale", 0) - valore) > 0.01:
            errori_upd += 1
        elif prev.get("nome_cliente") != cliente:
            errori_upd += 1
    if errori_upd:
        R.fail(f"Update preventivi: {errori_upd}/{len(campione_upd)} dati discordanti")
    else:
        R.ok(f"Update {len(campione_upd)} preventivi + verifica: OK", verbose)

    # ── STORICO MODIFICHE ──
    errori_storico = 0
    for pid in campione_upd[:10]:
        # Aggiorna 3 volte
        valori_storico = []
        for j in range(3):
            v = round(random.uniform(50, 3000), 2)
            valori_storico.append(v)
            safe(db.update_preventivo, pid, _prev_dict(preventivo_finale=v))
        storico, _ = safe(db.get_storico_modifiche, pid)
        if storico is None or len(storico) < 3:
            errori_storico += 1
        else:
            for entry in storico:
                if "timestamp" not in entry:
                    errori_storico += 1
                    break
    if errori_storico:
        R.fail(f"Storico modifiche: {errori_storico}/10 incompleto o malformato")
    else:
        R.ok("Storico modifiche (3 update × 10 preventivi): tutti OK", verbose)

    # ── RIPRISTINO ──
    errori_ripristino = 0
    ripristini_ok = 0
    for pid in campione_upd[:10]:
        storico, _ = safe(db.get_storico_modifiche, pid)
        if not storico:
            continue
        # Prendi il primo snapshot (il più vecchio) e ripristina
        ts = storico[0]["timestamp"]
        valore_atteso = storico[0].get("preventivo_finale")
        res, exc = safe(db.ripristina_versione_preventivo, pid, ts)
        if exc or not res:
            errori_ripristino += 1
        elif valore_atteso is not None:
            prev, _ = safe(db.get_preventivo_by_id, pid)
            if prev and abs(prev.get("preventivo_finale", -1) - valore_atteso) > 0.01:
                errori_ripristino += 1
            else:
                ripristini_ok += 1
    if errori_ripristino:
        R.fail(f"Ripristino versioni: {errori_ripristino} falliti o dati errati")
    else:
        R.ok(f"Ripristino versioni: {ripristini_ok} ripristini corretti", verbose)

    # ── REVISIONI ──
    errori_rev = 0
    pids_con_rev = random.sample(pids, min(20, len(pids)))
    rev_map = {}  # pid_orig → [rev_id, ...]
    for pid_orig in pids_con_rev:
        rev_ids = []
        for n_rev in range(2, 5):  # crea 3 revisioni
            rev_id, exc = safe(db.add_revisione_preventivo, pid_orig,
                               _prev_dict(n_rev=n_rev), f"Revisione {n_rev}")
            if exc or not isinstance(rev_id, int):
                errori_rev += 1
            else:
                rev_ids.append(rev_id)
        rev_map[pid_orig] = rev_ids
    if errori_rev:
        R.fail(f"add_revisione_preventivo: {errori_rev} falliti")
    else:
        R.ok(f"Creazione revisioni ({len(pids_con_rev)} × 3): tutti OK", verbose)

    # Verifica get_revisioni_preventivo
    errori_get_rev = 0
    for pid_orig, rev_ids in list(rev_map.items())[:10]:
        revisioni, _ = safe(db.get_revisioni_preventivo, pid_orig)
        attesi = 1 + len(rev_ids)  # 1 originale + N revisioni
        if revisioni is None or len(revisioni) != attesi:
            errori_get_rev += 1
    if errori_get_rev:
        R.fail(f"get_revisioni_preventivo: {errori_get_rev}/10 conteggi errati")
    else:
        R.ok("get_revisioni_preventivo: conteggi corretti", verbose)

    # ── GET_ALL_PREVENTIVI_LATEST ──
    latest, exc = safe(db.get_all_preventivi_latest)
    if exc:
        R.fail("get_all_preventivi_latest crash", exc)
    else:
        # Verifica che l'originale non compaia se ha revisioni
        ids_latest = {row[0] for row in (latest or [])}
        originali_esposti = [pid for pid in pids_con_rev if pid in ids_latest]
        if originali_esposti:
            R.warn(f"get_all_preventivi_latest: {len(originali_esposti)} originali esposti "
                   f"(si aspettano solo le ultime revisioni)")
        else:
            R.ok(f"get_all_preventivi_latest: nessun originale esposto "
                 f"se ha revisioni ({len(pids_con_rev)} gruppi)", verbose)
        R.info(f"Record in 'latest': {len(latest or [])}")

    # ── DELETE ──
    errori_del = 0
    da_eliminare = pids[:10]
    for pid in da_eliminare:
        res, exc = safe(db.delete_preventivo_e_revisioni, pid)
        if exc or not res:
            errori_del += 1
        else:
            ghost, _ = safe(db.get_preventivo_by_id, pid)
            if ghost is not None:
                errori_del += 1
    if errori_del:
        R.fail(f"delete_preventivo: {errori_del}/10 non eliminati o ancora presenti")
    else:
        R.ok("delete_preventivo_e_revisioni × 10 + verifica: OK", verbose)

    rimanenti = [p for p in pids if p not in da_eliminare]
    R.info(f"Preventivi totali: {len(pids)} | Eliminati: {len(da_eliminare)} | Rimanenti: {len(rimanenti)}")
    return rimanenti


# ─────────────────────────────────────────────────────────────────────────────
# 6. MATERIALECALCOLATO — calcoli e serializzazione in larga scala
# ─────────────────────────────────────────────────────────────────────────────

def test_calcoli(verbose=False):
    R.section("MATERIALECALCOLATO — calcoli, formule, serializzazione (200 campioni)")

    errori_formula = 0
    errori_serial = 0
    errori_nan = 0
    errori_idempotenza = 0

    for _ in range(200):
        mc = _mc_random()

        # Verifica formula diametro_finale
        atteso_df = mc.diametro + (mc.spessore * mc.giri * 2)
        if abs(mc.diametro_finale - atteso_df) > 0.001:
            errori_formula += 1

        # Verifica maggiorazione = costo_totale * 1.1
        if mc.costo_totale > 0:
            ratio = mc.maggiorazione / mc.costo_totale
            if abs(ratio - 1.1) > 0.001:
                errori_formula += 1

        # Verifica NaN / Inf
        for val in [mc.sviluppo, mc.costo_totale, mc.maggiorazione,
                    mc.diametro_finale, mc.lunghezza_utilizzata]:
            if math.isnan(val) or math.isinf(val):
                errori_nan += 1
                break

        # Idempotenza
        s1, c1, m1 = mc.sviluppo, mc.costo_totale, mc.maggiorazione
        mc.ricalcola_tutto()
        if abs(mc.sviluppo - s1) > 1e-9 or abs(mc.costo_totale - c1) > 1e-9:
            errori_idempotenza += 1

        # Serializzazione round-trip
        d = mc.to_dict()
        try:
            j = json.dumps(d)
            d2 = json.loads(j)
            if abs(d2.get("diametro", 0) - mc.diametro) > 0.001:
                errori_serial += 1
            if abs(d2.get("maggiorazione", 0) - mc.maggiorazione) > 0.0001:
                errori_serial += 1
        except (TypeError, ValueError):
            errori_serial += 1

    if errori_formula:
        R.fail(f"Formule: {errori_formula}/200 discordanti")
    else:
        R.ok("Formule diametro_finale e maggiorazione: 200/200 corrette", verbose)

    if errori_nan:
        R.fail(f"NaN/Inf: {errori_nan}/200 valori non finiti")
    else:
        R.ok("Nessun NaN/Inf su 200 campioni casuali", verbose)

    if errori_idempotenza:
        R.fail(f"Idempotenza ricalcola_tutto: {errori_idempotenza}/200 non idempotenti")
    else:
        R.ok("ricalcola_tutto() idempotente: 200/200 OK", verbose)

    if errori_serial:
        R.fail(f"Serializzazione JSON: {errori_serial}/200 errori")
    else:
        R.ok("Round-trip to_dict() → JSON → load: 200/200 OK", verbose)

    # Edge case: giri=0
    mc0 = MaterialeCalcolato()
    mc0.diametro, mc0.giri, mc0.spessore, mc0.lunghezza, mc0.costo_materiale = 100.0, 0, 0.25, 200.0, 30.0
    mc0.ricalcola_tutto()
    if abs(mc0.sviluppo - 5.0) > 0.001:
        R.fail(f"Sviluppo con giri=0: atteso 5.0, ottenuto {mc0.sviluppo}")
    else:
        R.ok("Sviluppo con giri=0 = 5.0 (solo quota fissa): OK", verbose)

    # Edge case: lunghezza=0
    mc_l0 = _mc_random()
    mc_l0.lunghezza = 0.0
    mc_l0.ricalcola_tutto()
    if mc_l0.costo_totale != 0.0 or mc_l0.maggiorazione != 0.0:
        R.fail(f"Lunghezza=0: costo_totale={mc_l0.costo_totale}, maggiorazione={mc_l0.maggiorazione} (devono essere 0)")
    else:
        R.ok("Lunghezza=0 → costo=0, maggiorazione=0: OK", verbose)


# ─────────────────────────────────────────────────────────────────────────────
# 7. PREVENTIVO MODEL — aggregazioni e coerenza
# ─────────────────────────────────────────────────────────────────────────────

def test_preventivo_model(verbose=False):
    R.section("PREVENTIVO MODEL — aggregazioni e coerenza su 100 preventivi")

    errori_subtotale = 0
    errori_mag25 = 0
    errori_finale = 0
    errori_scarto = 0

    for _ in range(100):
        p = Preventivo()
        n_mat = random.randint(1, 10)
        for _ in range(n_mat):
            mc = _mc_random()
            p.aggiungi_materiale(mc)

        p.costi_accessori = round(random.uniform(0, 200), 2)
        p.minuti_taglio = round(random.uniform(0, 60), 1)
        p.minuti_avvolgimento = round(random.uniform(0, 120), 1)
        p.minuti_pulizia = round(random.uniform(0, 30), 1)
        p.minuti_rettifica = round(random.uniform(0, 20), 1)
        p.minuti_imballaggio = round(random.uniform(0, 15), 1)
        p.ricalcola_tutto()

        # Subtotale = costo_materiali + mano_opera + accessori
        atteso_sub = (p.costo_totale_materiali + p.tot_mano_opera + p.costi_accessori)
        if abs(p.subtotale - atteso_sub) > 0.01:
            errori_subtotale += 1

        # Maggiorazione = subtotale * 0.25
        atteso_mag = p.subtotale * 0.25
        if abs(p.maggiorazione_25 - atteso_mag) > 0.01:
            errori_mag25 += 1

        # Finale = subtotale + maggiorazione_25
        atteso_finale = p.subtotale + p.maggiorazione_25
        if abs(p.preventivo_finale - atteso_finale) > 0.01:
            errori_finale += 1

        # Scarto totale
        atteso_scarto = sum(mc.scarto_mm2 for mc in p.materiali_calcolati)
        p.ricalcola_scarto_totale()
        if abs(p.scarto_totale_mm2 - atteso_scarto) > 0.01:
            errori_scarto += 1

    label = "100 preventivi × n materiali"
    if errori_subtotale:
        R.fail(f"Subtotale: {errori_subtotale}/{label} discordanti")
    else:
        R.ok(f"Subtotale: {label} corretti", verbose)
    if errori_mag25:
        R.fail(f"Maggiorazione 25%: {errori_mag25}/{label} discordanti")
    else:
        R.ok(f"Maggiorazione 25%: {label} corretti", verbose)
    if errori_finale:
        R.fail(f"Preventivo_finale: {errori_finale}/{label} discordanti")
    else:
        R.ok(f"Preventivo_finale: {label} corretti", verbose)
    if errori_scarto:
        R.fail(f"Scarto totale: {errori_scarto}/{label} discordanti")
    else:
        R.ok(f"Scarto_totale_mm2: {label} corretti", verbose)

    # Limite 30 materiali
    p_limit = Preventivo()
    for _ in range(30):
        p_limit.aggiungi_materiale(_mc_random())
    res = p_limit.aggiungi_materiale(_mc_random())
    if res:
        R.fail("Limite 30 materiali non rispettato")
    else:
        R.ok("Limite 30 materiali: 31° rifiutato", verbose)

    # Rimuovi e riaggiungi
    p_limit.rimuovi_materiale(0)
    res2 = p_limit.aggiungi_materiale(_mc_random())
    if not res2:
        R.fail("Dopo rimozione, non si riesce ad aggiungere (limite errato)")
    else:
        R.ok("Rimozione + riaggiunte oltre il limite: OK", verbose)


# ─────────────────────────────────────────────────────────────────────────────
# 8. INTEGRITÀ DATI cross-tabella
# ─────────────────────────────────────────────────────────────────────────────

def test_integrita(db, mat_ids, prev_ids, verbose=False):
    R.section("INTEGRITÀ DATI — cross-tabella e scenari distruttivi")

    if not mat_ids or not prev_ids:
        R.warn("Dati insufficienti, skip")
        return

    # Elimina un materiale usato in un preventivo → il preventivo deve sopravvivere
    mid = mat_ids[0]
    mc = _mc_random(mid=mid, nome="TEST_INTEG")
    pid = db.add_preventivo(_prev_dict(materiali_utilizzati=[mc.to_dict()]))
    db.delete_materiale(mid)
    prev, _ = safe(db.get_preventivo_by_id, pid)
    if prev is None:
        R.fail("Delete materiale ha eliminato anche il preventivo")
    else:
        R.ok("Delete materiale: preventivo che lo referenzia sopravvive", verbose)

    # JSON corrotto in materiali_utilizzati → get_preventivo_by_id non crasha
    import sqlite3 as _sql
    pid2 = db.add_preventivo(_prev_dict())
    with _sql.connect(db.db_path) as conn:
        conn.execute("UPDATE preventivi SET materiali_utilizzati=? WHERE id=?",
                     ("NON_JSON_{{{CORROTTO", pid2))
        conn.commit()
    prev2, exc2 = safe(db.get_preventivo_by_id, pid2)
    if exc2:
        R.fail("JSON corrotto in materiali_utilizzati → crash in get_preventivo_by_id", exc2)
    elif prev2 is None:
        R.fail("JSON corrotto → get_preventivo_by_id restituisce None")
    elif not isinstance(prev2.get("materiali_utilizzati", []), list):
        R.fail("JSON corrotto → materiali_utilizzati non è lista dopo fallback")
    else:
        R.ok("JSON corrotto: get_preventivo_by_id non crasha, restituisce lista vuota", verbose)

    # get_all_preventivi e get_all_preventivi_latest coerenza
    tutti, _ = safe(db.get_all_preventivi)
    latest, _ = safe(db.get_all_preventivi_latest)
    if tutti is None or latest is None:
        R.fail("get_all_preventivi o get_all_preventivi_latest crash")
    elif len(latest) > len(tutti):
        R.fail(f"latest ({len(latest)}) > tutti ({len(tutti)}): impossibile")
    else:
        R.ok(f"Cardinalità coerente: tutti={len(tutti)}, latest={len(latest)}", verbose)

    # SQL injection nei campi stringa
    for campo, valore in [
        ("nome_cliente", "'; DROP TABLE preventivi; --"),
        ("numero_ordine", "\" OR 1=1--"),
        ("descrizione", "<script>alert(1)</script>"),
    ]:
        pid_inj, exc = safe(db.add_preventivo, _prev_dict(**{campo: valore}))
        if exc:
            R.fail(f"SQL injection nel campo '{campo}' causa crash", exc)
        else:
            prev_inj, _ = safe(db.get_preventivo_by_id, pid_inj)
            if prev_inj and prev_inj.get(campo) == valore:
                R.ok(f"SQL injection '{campo}': salvato come testo letterale", verbose)
            else:
                R.warn(f"SQL injection '{campo}': valore letto diverso da quello scritto")

    # Verifica cascade: delete preventivo elimina anche le revisioni
    pid_base = db.add_preventivo(_prev_dict())
    rev1 = db.add_revisione_preventivo(pid_base, _prev_dict(), "r1")
    rev2 = db.add_revisione_preventivo(pid_base, _prev_dict(), "r2")
    db.delete_preventivo_e_revisioni(pid_base)
    for check_id in [pid_base, rev1, rev2]:
        row, _ = safe(db.get_preventivo_by_id, check_id)
        if row is not None:
            R.fail(f"delete_preventivo_e_revisioni: id {check_id} ancora presente dopo delete")
            break
    else:
        R.ok("delete_preventivo_e_revisioni: originale + 2 revisioni eliminati", verbose)

    # Fornitore inesistente in get_scorte → lista vuota, no crash
    scorte, exc = safe(db.get_scorte_per_fornitore, "FORNITORE_FANTASMA_XYZ_999")
    if exc:
        R.fail("get_scorte_per_fornitore con nome inesistente → crash", exc)
    elif scorte:
        R.warn(f"get_scorte_per_fornitore('FANTASMA'): lista non vuota ({len(scorte)} record)")
    else:
        R.ok("get_scorte_per_fornitore con fornitore inesistente → lista vuota", verbose)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="RCS-App Diagnostic Bot")
    parser.add_argument("--quick", action="store_true",
                        help="Campione ridotto (n_mat=10, n_prev=20)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Stampa anche i test passati")
    args = parser.parse_args()

    n_mat  = 10 if args.quick else 50
    n_prev = 20 if args.quick else 100

    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  RCS-App DIAGNOSTIC BOT{RESET}  "
          f"{'(modalità quick)' if args.quick else f'({n_mat} mat, {n_prev} prev)'}")
    print(f"{BOLD}{'═'*60}{RESET}")
    print(f"{DIM}  DB: in-memory temporaneo (isolato da produzione){RESET}")
    print(f"{DIM}  Avvio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")

    t0 = time.time()
    db = make_db()

    # ── Esegui sezioni ──────────────────────────────────────────────────────
    mat_ids = test_materiali(db, n=n_mat, verbose=args.verbose)
    test_fornitori(db, mat_ids, verbose=args.verbose)
    test_magazzino(db, mat_ids, verbose=args.verbose)
    cat_ids = test_categorie(db, verbose=args.verbose)
    prev_ids = test_preventivi(db, mat_ids, n=n_prev, verbose=args.verbose)
    test_calcoli(verbose=args.verbose)
    test_preventivo_model(verbose=args.verbose)
    test_integrita(db, mat_ids, prev_ids, verbose=args.verbose)
    # ────────────────────────────────────────────────────────────────────────

    elapsed = time.time() - t0
    print(f"\n{DIM}  Durata totale: {elapsed:.1f}s{RESET}")

    n_fail = R.summary()
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == "__main__":
    main()
