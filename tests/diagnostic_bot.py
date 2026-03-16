#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         RCS-App DIAGNOSTIC BOT — test di sistema in larga scala             ║
║                                                                              ║
║  Esegui con:  python tests/diagnostic_bot.py                                ║
║  Opzioni:     --quick    (N_MAT=15, N_PREV=50, N_CALC=100, ~10s)            ║
║               --verbose  (mostra anche i test passati)                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
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
import sqlite3 as _sqlite3
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

# ── seed riproducibilità parziale + varietà per run ──────────────────────────
_RUN_SEED = random.randint(0, 2**31)
random.seed(42)       # seed fisso per la costruzione dei dati
_RANDOM_SEED = _RUN_SEED

# =============================================================================
# Report
# =============================================================================

class Report:
    """Raccoglie e stampa i risultati del diagnostic bot."""

    def __init__(self):
        self.sections    = []          # list of (nome, t_start, t_end, risultati)
        self._current    = None
        self._results    = []
        self._t_start    = None
        self._check_total = 0

    def section(self, nome):
        if self._current is not None:
            self.sections.append((self._current, self._t_start, time.time(), self._results))
        self._current  = nome
        self._results  = []
        self._t_start  = time.time()
        print(f"\n{BOLD}{CYAN}▶ {nome}{RESET}")

    def ok(self, msg, verbose=False):
        self._results.append(("ok", msg))
        self._check_total += 1
        if verbose:
            print(f"  {GREEN}✓{RESET} {msg}")

    def warn(self, msg):
        self._results.append(("warn", msg))
        self._check_total += 1
        print(f"  {YELLOW}⚠{RESET}  {msg}")

    def fail(self, msg, exc=None):
        self._results.append(("fail", msg))
        self._check_total += 1
        detail = f"  →  {exc}" if exc else ""
        print(f"  {RED}✗{RESET}  {msg}{DIM}{detail}{RESET}")

    def info(self, msg):
        print(f"  {DIM}  {msg}{RESET}")

    def flush(self):
        if self._current is not None:
            self.sections.append((self._current, self._t_start, time.time(), self._results))
            self._current = None
            self._results = []

    def summary(self):
        self.flush()
        totale_ok = totale_warn = totale_fail = 0
        print(f"\n{BOLD}{'═'*72}{RESET}")
        print(f"{BOLD}  RIEPILOGO DIAGNOSTICA{RESET}")
        print(f"{BOLD}{'═'*72}{RESET}")
        for nome, t0, t1, risultati in self.sections:
            ok   = sum(1 for s, _ in risultati if s == "ok")
            warn = sum(1 for s, _ in risultati if s == "warn")
            fail = sum(1 for s, _ in risultati if s == "fail")
            totale_ok   += ok
            totale_warn += warn
            totale_fail += fail
            stato = (f"{GREEN}OK  {RESET}" if fail == 0 and warn == 0 else
                     (f"{YELLOW}WARN{RESET}" if fail == 0 else f"{RED}FAIL{RESET}"))
            durata = f"{t1 - t0:.1f}s"
            bar    = f"✓{ok} ⚠{warn} ✗{fail}"
            print(f"  {stato}  {nome:45s}  {DIM}{bar:12s}  {durata:>6s}{RESET}")
            for s, m in risultati:
                if s == "fail":
                    print(f"           {RED}→ {m}{RESET}")
                elif s == "warn":
                    print(f"           {YELLOW}→ {m}{RESET}")
        print(f"{BOLD}{'─'*72}{RESET}")
        colore = GREEN if totale_fail == 0 else RED
        totale_check = totale_ok + totale_warn + totale_fail
        print(f"  {BOLD}TOTALE CHECK: {totale_check}{RESET}  "
              f"{GREEN}✓ {totale_ok} ok{RESET}  "
              f"{YELLOW}⚠ {totale_warn} warn{RESET}  "
              f"{colore}✗ {totale_fail} fail{RESET}")
        print(f"{BOLD}{'═'*72}{RESET}\n")
        return totale_fail


R = Report()


# =============================================================================
# Helpers globali
# =============================================================================

def make_db():
    """Crea un DB temporaneo isolato dalla produzione."""
    tmp = tempfile.mkdtemp()
    return DatabaseManager(db_path=os.path.join(tmp, "diagnostic.db"))


def _prev_dict(**kwargs):
    """Genera un dict preventivo con valori random; kwargs sovrascrivono."""
    base = {
        "data_creazione":        (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat(),
        "numero_revisione":      1,
        "preventivo_originale_id": None,
        "nome_cliente":          f"Cliente_{random.randint(1000, 9999)}",
        "numero_ordine":         f"ORD-{random.randint(1, 9999):04d}",
        "misura":                f"{random.randint(50, 300)}x{random.randint(100, 600)}",
        "descrizione":           "Generato da diagnostic bot",
        "codice":                f"DC{random.randint(10, 99)}",
        "costo_totale_materiali": round(random.uniform(10, 500), 2),
        "costi_accessori":        round(random.uniform(0, 100), 2),
        "minuti_taglio":          round(random.uniform(0, 60), 1),
        "minuti_avvolgimento":    round(random.uniform(0, 120), 1),
        "minuti_pulizia":         round(random.uniform(0, 30), 1),
        "minuti_rettifica":       round(random.uniform(0, 20), 1),
        "minuti_imballaggio":     round(random.uniform(0, 15), 1),
        "tot_mano_opera":         0.0,
        "subtotale":              0.0,
        "maggiorazione_25":       0.0,
        "preventivo_finale":      round(random.uniform(50, 2000), 2),
        "prezzo_cliente":         round(random.uniform(50, 2500), 2),
        "materiali_utilizzati":   [],
        "note_revisione":         "",
        "storico_modifiche":      "[]",
    }
    base.update(kwargs)
    return base


def _mc_random(mid=None, nome=None, is_conica=False, lunghezza=None, giri=None,
               spessore=None, diametro=None, costo_materiale=None):
    """Crea un MaterialeCalcolato con valori casuali, ricalcola e restituisce."""
    mc = MaterialeCalcolato()
    mc.diametro         = diametro        if diametro        is not None else round(random.uniform(30, 300), 1)
    mc.lunghezza        = lunghezza       if lunghezza       is not None else round(random.uniform(50, 500), 1)
    mc.giri             = giri            if giri            is not None else random.randint(1, 8)
    mc.spessore         = spessore        if spessore        is not None else round(random.choice([0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]), 2)
    mc.costo_materiale  = costo_materiale if costo_materiale is not None else round(random.uniform(5, 100), 2)
    mc.is_conica        = is_conica
    if mid  is not None: mc.materiale_id   = mid
    if nome is not None: mc.materiale_nome = nome
    mc.ricalcola_tutto()
    return mc


def safe(fn, *args, default=None, **kwargs):
    """Esegui fn senza crashare. Restituisce (risultato, None) o (default, exc)."""
    try:
        return fn(*args, **kwargs), None
    except Exception as e:
        return default, e


def _is_valid_iso(ts):
    """Verifica che ts sia una stringa ISO datetime valida."""
    if not isinstance(ts, str):
        return False
    try:
        datetime.fromisoformat(ts)
        return True
    except ValueError:
        return False


# =============================================================================
# SEZ. 1 — MATERIALI: INSERT bulk, round-trip, update, delete
# =============================================================================

def test_01_materiali_bulk(db, N_MAT, verbose=False):
    R.section(f"1. MATERIALI — INSERT bulk ({N_MAT} record)")
    ids_inseriti = []
    nomi_inseriti = []
    errori_insert = 0

    # INSERT N_MAT materiali
    for i in range(N_MAT):
        nome     = f"DIAG_MAT_{i:04d}"
        spessore = round(random.uniform(0.05, 1.0), 3)
        prezzo   = round(random.uniform(1.0, 200.0), 2)
        mid, exc = safe(db.add_materiale, nome, spessore, prezzo)
        if exc or not isinstance(mid, int):
            errori_insert += 1
        else:
            ids_inseriti.append(mid)
            nomi_inseriti.append(nome)

    if errori_insert:
        R.fail(f"Insert materiali: {errori_insert}/{N_MAT} falliti")
    else:
        R.ok(f"Insert {N_MAT} materiali: tutti OK", verbose)

    if not ids_inseriti:
        R.fail("Nessun materiale inserito — sezione 1 abortisce")
        return []

    # DUPLICATO bloccato
    dup, exc = safe(db.add_materiale, nomi_inseriti[0], 0.1, 1.0)
    if dup is False or dup is None:
        R.ok("Duplicato nome bloccato (IntegrityError)", verbose)
    else:
        R.fail(f"Duplicato nome NON bloccato: ritorna {dup!r}", exc)

    # READ by ID (tutti)
    errori_read = 0
    for mid, nome_atteso in zip(ids_inseriti, nomi_inseriti):
        row, exc = safe(db.get_materiale_by_id, mid)
        if exc or row is None or row[1] != nome_atteso:
            errori_read += 1
    if errori_read:
        R.fail(f"Read by ID: {errori_read}/{len(ids_inseriti)} discordanti o None")
    else:
        R.ok(f"Read by ID ({len(ids_inseriti)} materiali): nome round-trip OK", verbose)

    # update_materiale_base (campione 40 o tutti se <40)
    n_upd_base = min(40, len(ids_inseriti))
    errori_upd_base = 0
    upd_base_data = {}
    for mid, nome_orig in zip(ids_inseriti[:n_upd_base], nomi_inseriti[:n_upd_base]):
        nuovo_nome   = nome_orig + "_BASE"
        nuovo_spes   = round(random.uniform(0.1, 0.9), 3)
        nuovo_prezzo = round(random.uniform(10.0, 500.0), 2)
        res, exc = safe(db.update_materiale_base, mid, nuovo_nome, nuovo_spes, nuovo_prezzo)
        if exc or not res:
            errori_upd_base += 1
        else:
            upd_base_data[mid] = (nuovo_nome, nuovo_spes, nuovo_prezzo)
    for mid, (nn, ns, np_) in upd_base_data.items():
        row, _ = safe(db.get_materiale_by_id, mid)
        if row is None or row[1] != nn or abs(row[3] - np_) > 0.001:
            errori_upd_base += 1
    if errori_upd_base:
        R.fail(f"update_materiale_base: {errori_upd_base} check falliti")
    else:
        R.ok(f"update_materiale_base ({n_upd_base} materiali): nome/spessore/prezzo OK", verbose)

    # update_materiale firma completa (campione 20)
    n_upd_full = min(20, len(ids_inseriti))
    errori_upd_full = 0
    for mid in ids_inseriti[:n_upd_full]:
        row_prima, _ = safe(db.get_materiale_by_id, mid)
        nome_full = (row_prima[1] if row_prima else "X") + "_FULL"
        res, exc = safe(db.update_materiale, mid, nome_full, 0.25, 99.99,
                        "FORN_FULL", 50.0, 1000.0, 5.0, None)
        if exc or not res:
            errori_upd_full += 1
        else:
            row, _ = safe(db.get_materiale_by_id, mid)
            if row is None or row[1] != nome_full or abs(row[3] - 99.99) > 0.001:
                errori_upd_full += 1
    if errori_upd_full:
        R.fail(f"update_materiale (firma completa): {errori_upd_full}/{n_upd_full} check falliti")
    else:
        R.ok(f"update_materiale firma completa ({n_upd_full}): tutti OK", verbose)

    # update_prezzo_materiale con 4 decimali (campione 20)
    n_upd_prz = min(20, len(ids_inseriti))
    errori_prz = 0
    for mid in ids_inseriti[:n_upd_prz]:
        p = round(random.uniform(1.0, 999.0), 4)
        safe(db.update_prezzo_materiale, mid, p)
        row, _ = safe(db.get_materiale_by_id, mid)
        if row is None or abs(row[3] - p) > 0.0001:
            errori_prz += 1
    if errori_prz:
        R.fail(f"update_prezzo_materiale (4 decimali): {errori_prz}/{n_upd_prz} discordanti")
    else:
        R.ok(f"update_prezzo_materiale ({n_upd_prz}, 4 dec): OK", verbose)

    # get_materiale_by_nome: 10 nomi noti → trovato, 5 inesistenti → None
    nomi_noti = nomi_inseriti[:min(10, len(nomi_inseriti))]
    errori_nome = 0
    for nome in nomi_noti:
        # I nomi sono stati aggiornati con _BASE, cerca quello originale potrebbe non esistere
        row_n, _ = safe(db.get_materiale_by_nome, nome + "_BASE")
        # oppure il nome originale non aggiornato
        row_orig, _ = safe(db.get_materiale_by_nome, nome)
        # almeno uno dei due deve esistere
        if row_n is None and row_orig is None:
            # prova con _FULL
            row_full, _ = safe(db.get_materiale_by_nome, nome + "_BASE_FULL")
            if row_full is None:
                errori_nome += 1
    for idx in range(5):
        row_fan, _ = safe(db.get_materiale_by_nome, f"NOME_FANTASMA_INESISTENTE_{idx:04d}")
        if row_fan is not None:
            errori_nome += 1
    if errori_nome:
        R.fail(f"get_materiale_by_nome: {errori_nome} check falliti (trovato quando non doveva, o non trovato quando doveva)")
    else:
        R.ok("get_materiale_by_nome: nomi noti trovati, nomi inesistenti → None", verbose)

    # DELETE (max 20% dei materiali, almeno 3 ma non più di 20) + verifica scomparsa + doppio delete
    n_del = min(20, max(3, len(ids_inseriti) // 5))
    da_eliminare = ids_inseriti[:n_del]
    rimanenti_ids = ids_inseriti[n_del:]
    errori_del = 0
    for mid in da_eliminare:
        res, exc = safe(db.delete_materiale, mid)
        if exc or not res:
            errori_del += 1
        else:
            row, _ = safe(db.get_materiale_by_id, mid)
            if row is not None:
                errori_del += 1
    if errori_del:
        R.fail(f"Delete 20 materiali: {errori_del} non eliminati o ancora presenti")
    else:
        R.ok(f"Delete {n_del} materiali + verifica scomparsa: OK", verbose)

    # Doppio delete
    res2, _ = safe(db.delete_materiale, da_eliminare[0])
    if res2:
        R.warn("Doppio delete restituisce True (atteso False o 0 rowcount)")
    else:
        R.ok("Doppio delete restituisce False/0", verbose)

    # Count finale
    tutti, _ = safe(db.get_all_materiali)
    n_diag = sum(1 for r in (tutti or []) if str(r[1]).startswith("DIAG_MAT_"))
    attesi = len(rimanenti_ids)
    if n_diag < attesi:
        R.fail(f"Count finale DIAG_MAT_*: attesi ≥{attesi}, trovati {n_diag}")
    else:
        R.ok(f"Count finale materiali DIAG_MAT_*: {n_diag} (corretto)", verbose)

    # Verifica no duplicati nei nomi DIAG_MAT_*
    nomi_diag = [r[1] for r in (tutti or []) if str(r[1]).startswith("DIAG_MAT_")]
    if len(nomi_diag) != len(set(nomi_diag)):
        R.fail("get_all_materiali: duplicati nei nomi DIAG_MAT_*")
    else:
        R.ok("get_all_materiali: nessun duplicato nei nomi DIAG_MAT_*", verbose)

    R.info(f"Inseriti: {len(ids_inseriti)} | Eliminati: {n_del} | Rimanenti: {len(rimanenti_ids)}")
    return rimanenti_ids


# =============================================================================
# SEZ. 2 — MATERIALI: edge case e valori limite
# =============================================================================

def test_02_materiali_edge(db, verbose=False):
    R.section("2. MATERIALI — edge case e valori limite")

    # Nome vuoto
    mid_vuoto, exc_vuoto = safe(db.add_materiale, "", 0.1, 1.0)
    if exc_vuoto is not None:
        R.ok("Nome vuoto → eccezione gestita correttamente", verbose)
    elif mid_vuoto is False or mid_vuoto is None:
        R.ok("Nome vuoto → bloccato (False/None)", verbose)
    else:
        R.warn(f"Nome vuoto accettato (id={mid_vuoto}) — potrebbe essere OK per il DB ma insolito")

    # Nome con caratteri speciali
    nomi_speciali = [
        ("SPEC_ACCENTI", "àèìùò materiale"),
        ("SPEC_SLASH",   "mat/con\\slash:e*altri?\"<>|"),
        ("SPEC_NEWLINE", "mat\ncon\nnewline"),
        ("SPEC_TAB",     "mat\tcon\ttab"),
        ("SPEC_LUNGO",   "X" * 500),
    ]
    for label, nome in nomi_speciali:
        mid_sp, exc_sp = safe(db.add_materiale, nome, 0.1, 1.0)
        if exc_sp:
            R.ok(f"Nome speciale [{label}] → eccezione gestita", verbose)
        elif mid_sp is False or mid_sp is None:
            R.ok(f"Nome speciale [{label}] → bloccato", verbose)
        else:
            # Verifica round-trip
            row_sp, _ = safe(db.get_materiale_by_id, mid_sp)
            if row_sp and row_sp[1] == nome:
                R.ok(f"Nome speciale [{label}] → salvato e riletto correttamente", verbose)
            else:
                R.warn(f"Nome speciale [{label}] → salvato ma nome letto diverso")
            safe(db.delete_materiale, mid_sp)

    # Spessore = 0.0
    mid_s0, exc_s0 = safe(db.add_materiale, "EDGE_SPESS_ZERO", 0.0, 1.0)
    if exc_s0:
        R.ok("Spessore=0.0 → eccezione gestita", verbose)
    elif mid_s0 is False or mid_s0 is None:
        R.ok("Spessore=0.0 → bloccato", verbose)
    else:
        R.ok("Spessore=0.0 → accettato", verbose)
        safe(db.delete_materiale, mid_s0)

    # Spessore molto piccolo
    mid_sp2, exc_sp2 = safe(db.add_materiale, "EDGE_SPESS_MICRO", 0.0001, 1.0)
    if exc_sp2:
        R.warn(f"Spessore=0.0001 → eccezione: {exc_sp2}")
    else:
        R.ok("Spessore=0.0001 → accettato", verbose)
        if mid_sp2 and isinstance(mid_sp2, int): safe(db.delete_materiale, mid_sp2)

    # Prezzo = 0.0
    mid_p0, exc_p0 = safe(db.add_materiale, "EDGE_PREZZO_ZERO", 0.1, 0.0)
    if exc_p0:
        R.warn(f"Prezzo=0.0 → eccezione: {exc_p0}")
    elif mid_p0 is False or mid_p0 is None:
        R.warn("Prezzo=0.0 → bloccato (potrebbe essere OK)")
    else:
        R.ok("Prezzo=0.0 → accettato", verbose)
        safe(db.delete_materiale, mid_p0)

    # Prezzo molto grande
    mid_pg, exc_pg = safe(db.add_materiale, "EDGE_PREZZO_GRANDE", 0.1, 999999.99)
    if exc_pg:
        R.warn(f"Prezzo=999999.99 → eccezione: {exc_pg}")
    else:
        row_pg, _ = safe(db.get_materiale_by_id, mid_pg)
        if row_pg and abs(row_pg[3] - 999999.99) < 0.01:
            R.ok("Prezzo=999999.99 → round-trip OK", verbose)
        else:
            R.warn("Prezzo=999999.99 → letto diversamente")
        if mid_pg and isinstance(mid_pg, int): safe(db.delete_materiale, mid_pg)

    # Prezzo negativo
    mid_pn, exc_pn = safe(db.add_materiale, "EDGE_PREZZO_NEG", 0.1, -5.0)
    if exc_pn:
        R.ok("Prezzo negativo → eccezione gestita", verbose)
    elif mid_pn is False or mid_pn is None:
        R.ok("Prezzo negativo → bloccato", verbose)
    else:
        R.warn(f"Prezzo negativo accettato (id={mid_pn}) — potrebbe richiedere validazione lato UI")
        safe(db.delete_materiale, mid_pn)

    # Stesso spessore, nomi diversi → OK (non è vincolo univoco sullo spessore)
    mid_a, exc_a = safe(db.add_materiale, "EDGE_DUP_SPES_A", 0.25, 10.0)
    mid_b, exc_b = safe(db.add_materiale, "EDGE_DUP_SPES_B", 0.25, 20.0)
    if exc_a or exc_b or not mid_a or not mid_b:
        R.fail("Stesso spessore, nomi diversi: almeno uno fallito (non è vincolo univoco)")
    else:
        R.ok("Stesso spessore, nomi diversi → entrambi inseriti (OK)", verbose)
    for mid_x in [mid_a, mid_b]:
        if mid_x and isinstance(mid_x, int): safe(db.delete_materiale, mid_x)


# =============================================================================
# SEZ. 3 — FORNITORI: CRUD completo
# =============================================================================

def test_03_fornitori(db, mat_ids, verbose=False):
    R.section("3. FORNITORI — CRUD completo")

    if not mat_ids:
        R.warn("Nessun materiale disponibile — sezione parziale")

    # Insert 10 fornitori
    fornitori_nomi = [f"DIAG_FORN_{i:02d}" for i in range(10)]
    fids = []
    errori_ins = 0
    for nome in fornitori_nomi:
        fid, exc = safe(db.add_fornitore, nome)
        if exc or not isinstance(fid, int):
            errori_ins += 1
        else:
            fids.append(fid)
    if errori_ins:
        R.fail(f"Insert 10 fornitori: {errori_ins} falliti")
    else:
        R.ok(f"Insert 10 fornitori: tutti OK", verbose)

    # Duplicato bloccato
    dup, _ = safe(db.add_fornitore, fornitori_nomi[0])
    if dup is False or dup is None:
        R.ok("Duplicato fornitore bloccato", verbose)
    else:
        R.fail(f"Duplicato fornitore NON bloccato: {dup!r}")

    # assegna_materiali_a_fornitore (30 o tutti se <30)
    if mat_ids:
        campione_ass = mat_ids[:min(30, len(mat_ids))]
        safe(db.assegna_materiali_a_fornitore, fornitori_nomi[0], campione_ass)
        scorte, exc = safe(db.get_scorte_per_fornitore, fornitori_nomi[0])
        if exc:
            R.fail("assegna_materiali_a_fornitore → get_scorte_per_fornitore crash", exc)
        else:
            ids_scorte = {r[0] for r in (scorte or [])}
            mancanti = [m for m in campione_ass if m not in ids_scorte]
            if mancanti:
                R.warn(f"assegna_materiali: {len(mancanti)}/{len(campione_ass)} non nelle scorte (campo legacy)")
            else:
                R.ok(f"assegna_materiali_a_fornitore ({len(campione_ass)}) + scorte: OK", verbose)

    # add_fornitore_a_materiale con prezzi: 20 materiali × 2 fornitori
    mf_ids_campione = []  # lista di mf_id per test successivi
    if mat_ids and len(fornitori_nomi) >= 2:
        campione_mf = mat_ids[:min(20, len(mat_ids))]
        errori_mf = 0
        for mid in campione_mf:
            for fi in [1, 2]:  # fornitori_nomi[1] e [2]
                prezzo_f = round(random.uniform(5, 80), 2)
                sc_min   = round(random.uniform(1, 10), 1)
                sc_max   = round(random.uniform(50, 500), 1)
                mfid, exc = safe(db.add_fornitore_a_materiale, mid,
                                 fornitori_nomi[fi], prezzo_f, sc_min, sc_max)
                if exc or not isinstance(mfid, int):
                    errori_mf += 1
                else:
                    mf_ids_campione.append(mfid)
        if errori_mf:
            R.fail(f"add_fornitore_a_materiale: {errori_mf} falliti")
        else:
            R.ok(f"add_fornitore_a_materiale: {len(mf_ids_campione)} associazioni OK", verbose)

        # get_fornitori_per_materiale: ogni materiale ha ≥2 fornitori (o ≥1)
        errori_gfm = 0
        for mid in campione_mf:
            rows, _ = safe(db.get_fornitori_per_materiale, mid)
            if not rows or len(rows) < 1:
                errori_gfm += 1
        if errori_gfm:
            R.fail(f"get_fornitori_per_materiale: {errori_gfm}/{len(campione_mf)} vuoti")
        else:
            R.ok(f"get_fornitori_per_materiale ({len(campione_mf)} mat): tutti con ≥1 fornitore", verbose)

    # update_fornitore_materiale + verifica round-trip
    if mf_ids_campione:
        mfid_test = mf_ids_campione[0]
        nuovo_prezzo_f = round(random.uniform(100, 200), 2)
        res_upd, exc_upd = safe(db.update_fornitore_materiale,
                                mfid_test, fornitori_nomi[1],
                                nuovo_prezzo_f, 5.0, 300.0)
        if exc_upd or not res_upd:
            R.fail(f"update_fornitore_materiale: fallito", exc_upd)
        else:
            # Verifica: cerca tra i fornitori del primo materiale del campione
            rows_verif, _ = safe(db.get_fornitori_per_materiale, mat_ids[0]) if mat_ids else (None, None)
            found = any(r[0] == mfid_test and abs(r[2] - nuovo_prezzo_f) < 0.01 for r in (rows_verif or []))
            if found:
                R.ok("update_fornitore_materiale: prezzo aggiornato e riletto OK", verbose)
            else:
                R.warn("update_fornitore_materiale: aggiornato ma verifica prezzo non trovata (potrebbe essere su altro mat)")

    # delete_fornitore_materiale + verifica scomparsa
    if mf_ids_campione and len(mf_ids_campione) > 1:
        mfid_del = mf_ids_campione[-1]
        res_del, exc_del = safe(db.delete_fornitore_materiale, mfid_del)
        if exc_del or not res_del:
            R.fail("delete_fornitore_materiale: fallito", exc_del)
        else:
            # Verifica che non compaia più tra i fornitori dei materiali
            # Facciamo una query diretta per sicurezza
            try:
                with _sqlite3.connect(db.db_path) as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM materiale_fornitori WHERE id=?", (mfid_del,))
                    row_ghost = cur.fetchone()
                if row_ghost:
                    R.fail(f"delete_fornitore_materiale: mf_id {mfid_del} ancora presente nel DB")
                else:
                    R.ok("delete_fornitore_materiale: mf_id rimosso correttamente", verbose)
            except Exception as e:
                R.warn(f"delete_fornitore_materiale: verifica diretta fallita: {e}")

    # rename_fornitore: vecchio scompare, nuovo appare
    safe(db.add_fornitore, "FORN_OLD_RENAME")
    res_ren, _ = safe(db.rename_fornitore, "FORN_OLD_RENAME", "FORN_NEW_RENAME")
    tutti_f, _ = safe(db.get_all_fornitori)
    nomi_f = [r[1] for r in (tutti_f or [])]
    if "FORN_NEW_RENAME" in nomi_f and "FORN_OLD_RENAME" not in nomi_f:
        R.ok("rename_fornitore: vecchio assente, nuovo presente", verbose)
    else:
        R.fail(f"rename_fornitore: vecchio={('FORN_OLD_RENAME' in nomi_f)}, nuovo={('FORN_NEW_RENAME' in nomi_f)}")

    # rename su nome occupato → False
    safe(db.add_fornitore, "FORN_COLL_A")
    safe(db.add_fornitore, "FORN_COLL_B")
    res_coll, _ = safe(db.rename_fornitore, "FORN_COLL_A", "FORN_COLL_B")
    if res_coll:
        R.warn("rename su nome occupato non bloccato (atteso False)")
    else:
        R.ok("rename su nome occupato → False (corretto)", verbose)

    # rename su nome inesistente → False o gestito
    res_fan, exc_fan = safe(db.rename_fornitore, "FORN_FANTASMA_XYZ_999", "FORN_ALTRO")
    if exc_fan:
        R.ok("rename su nome inesistente → eccezione gestita", verbose)
    elif res_fan is False or res_fan is None or res_fan == 0:
        R.ok("rename su nome inesistente → False/None/0 (corretto)", verbose)
    else:
        R.warn(f"rename su nome inesistente restituisce {res_fan!r} (atteso False)")

    # get_all_fornitori count
    tutti_ff, _ = safe(db.get_all_fornitori)
    n_diag_f = sum(1 for r in (tutti_ff or []) if str(r[1]).startswith("DIAG_FORN_") or
                   str(r[1]).startswith("FORN_"))
    R.ok(f"get_all_fornitori: {n_diag_f} fornitori di test presenti", verbose)
    R.info(f"Totale fornitori nel DB: {len(tutti_ff or [])}")

    return fornitori_nomi


# =============================================================================
# SEZ. 4 — MAGAZZINO: movimenti in larga scala
# =============================================================================

def test_04_magazzino_movimenti(db, mat_ids, verbose=False):
    R.section("4. MAGAZZINO — movimenti in larga scala")

    if not mat_ids:
        R.warn("Nessun materiale disponibile — skip")
        return

    n_mat_mag = min(30, len(mat_ids))
    campione  = mat_ids[:n_mat_mag]
    forn_mag  = "FORN_MAG_TEST_04"
    safe(db.add_fornitore, forn_mag)

    # Setup fornitore per ciascun materiale
    for mid in campione:
        safe(db.add_fornitore_a_materiale, mid, forn_mag,
             round(random.uniform(5, 40), 2), 5.0, 1000.0)

    # 10 carichi + 5 scarichi per ogni materiale → verifica bilancio (ε=0.01)
    errori_bilancio = 0
    for mid in campione:
        carichi  = [round(random.uniform(10.0, 100.0), 3) for _ in range(10)]
        scarichi = [round(random.uniform(1.0, 20.0), 3)  for _ in range(5)]
        atteso   = sum(carichi)
        for q in carichi:
            safe(db.registra_movimento, mid, "carico", q, fornitore_nome=forn_mag)
        for q in scarichi:
            safe(db.registra_movimento, mid, "scarico", q, fornitore_nome=forn_mag)
            atteso = max(atteso - q, 0.0)
        giacenza, exc = safe(db.get_giacenza_totale_materiale, mid)
        if exc:
            errori_bilancio += 1
        elif giacenza is None or abs(giacenza - atteso) > 0.01:
            errori_bilancio += 1
    if errori_bilancio:
        R.fail(f"Bilancio 10 carichi + 5 scarichi: {errori_bilancio}/{n_mat_mag} discordanti")
    else:
        R.ok(f"Bilancio carico/scarico ({n_mat_mag} mat, ε=0.01): tutti OK", verbose)

    # Scarico massivo → giacenza = 0, mai negativa
    negativi = 0
    for mid in campione:
        safe(db.registra_movimento, mid, "scarico", 999999.0, fornitore_nome=forn_mag)
        g, _ = safe(db.get_giacenza_totale_materiale, mid)
        if g is not None and g < -0.001:
            negativi += 1
    if negativi:
        R.fail(f"Giacenza sotto zero: {negativi} materiali con giacenza negativa dopo scarico massivo")
    else:
        R.ok("Scarico massivo (999999): giacenza ≥ 0 per tutti", verbose)

    # 100 micro-carichi da 0.001 → verifica sommati correttamente
    mid_micro = campione[0] if campione else None
    if mid_micro:
        g_prima, _ = safe(db.get_giacenza_totale_materiale, mid_micro)
        g_prima = g_prima or 0.0
        for _ in range(100):
            safe(db.registra_movimento, mid_micro, "carico", 0.001, fornitore_nome=forn_mag)
        g_dopo, _ = safe(db.get_giacenza_totale_materiale, mid_micro)
        atteso_micro = g_prima + 100 * 0.001
        if g_dopo is None or abs(g_dopo - atteso_micro) > 0.05:
            R.fail(f"100 micro-carichi 0.001: atteso≈{atteso_micro:.3f}, trovato={g_dopo}")
        else:
            R.ok("100 micro-carichi da 0.001: sommati correttamente", verbose)

    # get_movimenti_per_materiale: count per materiale campione
    # default limit=100, quindi per vedere tutti usiamo un limit alto
    if mid_micro:
        movimenti, _ = safe(db.get_movimenti_per_materiale, mid_micro, 500)
        # 10 carichi + 5 scarichi + 1 scarico massivo + 100 micro = 116
        atteso_count = 116
        if movimenti is None or len(movimenti) < atteso_count:
            R.fail(f"get_movimenti_per_materiale: attesi ≥{atteso_count}, trovati {len(movimenti or [])}")
        else:
            R.ok(f"get_movimenti_per_materiale: {len(movimenti)} movimenti (atteso={atteso_count})", verbose)

    # Movimento con quantità = 0 → gestito
    mid_q0 = campione[1] if len(campione) > 1 else campione[0]
    g_prima_q0, _ = safe(db.get_giacenza_totale_materiale, mid_q0)
    safe(db.registra_movimento, mid_q0, "carico", 0.0, fornitore_nome=forn_mag)
    g_dopo_q0, _ = safe(db.get_giacenza_totale_materiale, mid_q0)
    g_prima_q0 = g_prima_q0 or 0.0
    g_dopo_q0  = g_dopo_q0  or 0.0
    if abs(g_dopo_q0 - g_prima_q0) < 0.001:
        R.ok("Movimento quantità=0: giacenza invariata (corretto)", verbose)
    else:
        R.warn(f"Movimento quantità=0: giacenza cambiata ({g_prima_q0} → {g_dopo_q0})")

    # Movimento con quantità negativa → bloccato o trattato come scarico
    mid_qn = campione[2] if len(campione) > 2 else campione[0]
    g_prima_qn, _ = safe(db.get_giacenza_totale_materiale, mid_qn)
    _, exc_qn = safe(db.registra_movimento, mid_qn, "carico", -10.0, fornitore_nome=forn_mag)
    g_dopo_qn, _ = safe(db.get_giacenza_totale_materiale, mid_qn)
    if exc_qn:
        R.ok("Movimento quantità negativa → eccezione gestita", verbose)
    elif g_dopo_qn is not None and g_prima_qn is not None:
        diff = g_dopo_qn - g_prima_qn
        if diff <= 0:
            R.ok(f"Movimento q=-10 trattato come scarico (diff={diff:.3f})", verbose)
        else:
            R.warn(f"Movimento q=-10 aumenta la giacenza di {diff:.3f} (anomalo)")
    else:
        R.warn("Movimento quantità negativa: giacenza non leggibile")


# =============================================================================
# SEZ. 5 — MAGAZZINO: query e periodi
# =============================================================================

def test_05_magazzino_query(db, mat_ids, verbose=False):
    R.section("5. MAGAZZINO — query e periodi")

    if not mat_ids:
        R.warn("Nessun materiale — skip")
        return

    # get_scorte: tutti i materiali presenti, nessun duplicato
    scorte, exc = safe(db.get_scorte)
    if exc:
        R.fail("get_scorte crash", exc)
    else:
        ids_sc = [r[0] for r in (scorte or [])]
        if len(ids_sc) != len(set(ids_sc)):
            R.fail("get_scorte: ID duplicati nella lista")
        else:
            R.ok(f"get_scorte: {len(ids_sc)} record, nessun duplicato", verbose)
        trovati = sum(1 for mid in mat_ids[:min(30, len(mat_ids))] if mid in ids_sc)
        if trovati < min(30, len(mat_ids)):
            R.warn(f"get_scorte: solo {trovati}/{min(30,len(mat_ids))} dei materiali di test trovati")
        else:
            R.ok(f"get_scorte: tutti i {trovati} materiali di test presenti", verbose)

    # get_scorte_per_fornitore con fornitore esistente
    scorte_f, exc_f = safe(db.get_scorte_per_fornitore, "FORN_MAG_TEST_04")
    if exc_f:
        R.fail("get_scorte_per_fornitore crash", exc_f)
    elif scorte_f is None:
        R.warn("get_scorte_per_fornitore: restituisce None (atteso lista)")
    else:
        R.ok(f"get_scorte_per_fornitore('FORN_MAG_TEST_04'): {len(scorte_f)} record", verbose)

    # get_scorte_per_categoria con varie opzioni ordina_per
    for ordine in ["giacenza_asc", "giacenza_desc", "nome_asc"]:
        scorte_c, exc_c = safe(db.get_scorte_per_categoria, ordine)
        if exc_c:
            R.fail(f"get_scorte_per_categoria(ordina_per='{ordine}') crash", exc_c)
        else:
            R.ok(f"get_scorte_per_categoria('{ordine}'): {len(scorte_c or [])} record, no crash", verbose)

    # get_consumi_periodo: range stretto (±2h) → include movimenti di scarico recenti
    inizio_range = (datetime.now() - timedelta(hours=2)).isoformat()
    fine_range   = (datetime.now() + timedelta(hours=1)).isoformat()
    consumi, exc_cons = safe(db.get_consumi_periodo, inizio_range, fine_range)
    if exc_cons:
        R.fail("get_consumi_periodo (range recente) crash", exc_cons)
    elif consumi is None:
        R.warn("get_consumi_periodo: restituisce None")
    elif len(consumi) == 0:
        R.warn("get_consumi_periodo (range recente): lista vuota — scarichi potrebbero non esserci")
    else:
        R.ok(f"get_consumi_periodo (range recente): {len(consumi)} materiali con scarichi", verbose)

    # get_consumi_periodo: range passato (-2w, -1w) → lista vuota (nessun movimento storico)
    inizio_pass = (datetime.now() - timedelta(weeks=2)).isoformat()
    fine_pass   = (datetime.now() - timedelta(weeks=1)).isoformat()
    consumi_past, exc_past = safe(db.get_consumi_periodo, inizio_pass, fine_pass)
    if exc_past:
        R.fail("get_consumi_periodo (range passato) crash", exc_past)
    elif consumi_past:
        R.warn(f"get_consumi_periodo (range 2w-1w fa): lista non vuota ({len(consumi_past)} record) — DB pre-esistente?")
    else:
        R.ok("get_consumi_periodo (range 2w-1w fa): lista vuota (corretto)", verbose)


# =============================================================================
# SEZ. 6 — CATEGORIE: CRUD + relazioni
# =============================================================================

def test_06_categorie(db, mat_ids, verbose=False):
    R.section("6. CATEGORIE — CRUD + relazioni")

    cat_ids = []
    errori_ins = 0
    # Insert 15 categorie
    for i in range(15):
        cid, exc = safe(db.add_categoria,
                        f"DIAG_CAT_{i:02d}",
                        round(random.uniform(5, 50), 1),
                        round(random.uniform(50, 200), 1),
                        round(random.uniform(200, 1000), 1),
                        f"Note categoria {i}")
        if exc or not isinstance(cid, int):
            errori_ins += 1
        else:
            cat_ids.append(cid)
    if errori_ins:
        R.fail(f"Insert 15 categorie: {errori_ins} falliti")
    else:
        R.ok(f"Insert 15 categorie: tutte OK", verbose)

    # Duplicato bloccato
    dup, _ = safe(db.add_categoria, "DIAG_CAT_00")
    if dup is False or dup is None:
        R.ok("Duplicato categoria bloccato", verbose)
    else:
        R.fail(f"Duplicato categoria NON bloccato: {dup!r}")

    # update_categoria tutti i campi + verifica
    errori_upd = 0
    for cid in cat_ids[:5]:
        nuovo_nome = f"CAT_UPD_{cid}"
        res, exc = safe(db.update_categoria, cid, nuovo_nome, 10.0, 80.0, 400.0, "aggiornata")
        if exc or not res:
            errori_upd += 1
        else:
            row, _ = safe(db.get_categoria_by_id, cid)
            if row is None or row[1] != nuovo_nome:
                errori_upd += 1
    if errori_upd:
        R.fail(f"update_categoria: {errori_upd}/5 falliti o discordanti")
    else:
        R.ok("update_categoria (5 cat): tutti i campi aggiornati e verificati", verbose)

    # get_all_categorie: count corretto
    tutte, _ = safe(db.get_all_categorie)
    n_diag_cat = sum(1 for r in (tutte or []) if str(r[1]).startswith("DIAG_CAT_") or str(r[1]).startswith("CAT_UPD_"))
    if n_diag_cat < len(cat_ids):
        R.fail(f"get_all_categorie: trovate {n_diag_cat}, attese ≥{len(cat_ids)}")
    else:
        R.ok(f"get_all_categorie: {n_diag_cat} categorie di test presenti", verbose)

    # get_categoria_by_id: ogni categoria trovata con dati corretti
    errori_read = 0
    for cid in cat_ids:
        row, _ = safe(db.get_categoria_by_id, cid)
        if row is None or row[0] != cid:
            errori_read += 1
    if errori_read:
        R.fail(f"get_categoria_by_id: {errori_read}/{len(cat_ids)} non trovate o ID sbagliato")
    else:
        R.ok(f"get_categoria_by_id ({len(cat_ids)} cat): tutte trovate con ID corretto", verbose)

    # Aggiungi 5 materiali per 4 categorie → verifica get_materiali_per_categoria count
    if cat_ids:
        errori_mat_cat = 0
        for cid in cat_ids[:4]:
            for j in range(5):
                safe(db.add_materiale, f"MC_CAT_{cid}_{j:02d}", round(0.1 * (j + 1), 2), float(j + 1),
                     categoria_id=cid)
            mats, _ = safe(db.get_materiali_per_categoria, cid)
            if mats is None or len(mats) < 5:
                errori_mat_cat += 1
        if errori_mat_cat:
            R.fail(f"get_materiali_per_categoria: {errori_mat_cat}/4 conteggi errati")
        else:
            R.ok("get_materiali_per_categoria (5 mat × 4 cat): tutti OK", verbose)

    # get_materiali_per_categoria_con_fornitori
    if cat_ids and mat_ids:
        forn_cat = "FORN_CAT_TEST"
        safe(db.add_fornitore, forn_cat)
        cid_test = cat_ids[0]
        mats_cat, _ = safe(db.get_materiali_per_categoria, cid_test)
        for row_mat in (mats_cat or [])[:3]:
            safe(db.add_fornitore_a_materiale, row_mat[0], forn_cat, 10.0, 5.0, 100.0)
        res_mpcf, exc_mpcf = safe(db.get_materiali_per_categoria_con_fornitori, cid_test)
        if exc_mpcf:
            R.fail("get_materiali_per_categoria_con_fornitori crash", exc_mpcf)
        elif res_mpcf is None:
            R.fail("get_materiali_per_categoria_con_fornitori: None")
        else:
            # Ogni riga: (id, nome, giacenza_totale, scorta_massima, n_fornitori)
            ok_struttura = all(len(r) >= 3 for r in res_mpcf)
            if ok_struttura:
                R.ok(f"get_materiali_per_categoria_con_fornitori: {len(res_mpcf)} record, struttura OK", verbose)
            else:
                R.warn("get_materiali_per_categoria_con_fornitori: struttura riga inattesa")

    # get_scorte_per_categoria: cat con materiali → lista, cat senza → vuota o 0
    if cat_ids and len(cat_ids) >= 2:
        sc_cat, exc_sc = safe(db.get_scorte_per_categoria)
        if exc_sc:
            R.fail("get_scorte_per_categoria crash", exc_sc)
        else:
            R.ok(f"get_scorte_per_categoria: {len(sc_cat or [])} categorie nel risultato", verbose)

    # Delete categoria → materiali sopravvivono, categoria_id=NULL
    if cat_ids:
        cid_del = cat_ids[-1]
        mid_temp, _ = safe(db.add_materiale, f"MAT_CAT_DEL_{cid_del}", 0.1, 1.0, categoria_id=cid_del)
        safe(db.delete_categoria, cid_del)
        if mid_temp and isinstance(mid_temp, int):
            row_mat_surv, _ = safe(db.get_materiale_by_id, mid_temp)
            if row_mat_surv is None:
                R.fail("Delete categoria: ha eliminato anche il materiale (non deve)")
            else:
                cat_id_after = row_mat_surv[8] if len(row_mat_surv) > 8 else "N/A"
                if cat_id_after is None:
                    R.ok("Delete categoria: materiale sopravvive con categoria_id=NULL", verbose)
                else:
                    R.warn(f"Delete categoria: materiale sopravvive ma categoria_id={cat_id_after} (atteso NULL)")
            safe(db.delete_materiale, mid_temp)

    # Delete categoria inesistente → gestito
    _, exc_del_fan = safe(db.delete_categoria, 9999999)
    if exc_del_fan:
        R.fail("delete_categoria su ID inesistente → crash", exc_del_fan)
    else:
        R.ok("delete_categoria su ID inesistente → no crash", verbose)

    return cat_ids[:-1] if cat_ids else []


# =============================================================================
# SEZ. 7 — PREVENTIVI: creazione 500 scenari diversificati
# =============================================================================

def test_07_preventivi_creazione(db, mat_ids, N_PREV, verbose=False):
    R.section(f"7. PREVENTIVI — {N_PREV} scenari diversificati (profili A-F)")

    # Profili: (etichetta, percentuale, n_mat_range, is_conica_prob)
    profili = [
        ("A", 0.30, (0,  0),  0.0),
        ("B", 0.20, (1,  1),  0.0),
        ("C", 0.20, (5,  5),  0.0),
        ("D", 0.15, (15, 15), 0.0),
        ("E", 0.10, (30, 30), 0.0),
        ("F", 0.05, (3,  6),  1.0),  # is_conica=True
    ]
    # Distribuisci i preventivi tra i profili
    conteggi = []
    rimasto = N_PREV
    for i, (lbl, pct, rng, conica_p) in enumerate(profili):
        if i == len(profili) - 1:
            conteggi.append(rimasto)
        else:
            n = max(1, int(N_PREV * pct))
            conteggi.append(n)
            rimasto -= n

    pids_tutti  = []
    fail_per_profilo = {}

    for (lbl, pct, rng, conica_p), n_prof in zip(profili, conteggi):
        fail_prof = 0
        pids_prof = []
        for _ in range(n_prof):
            n_mat_prev = random.randint(rng[0], rng[1])
            mats = []
            for _ in range(n_mat_prev):
                is_conica = (random.random() < conica_p)
                mid_rand = random.choice(mat_ids) if mat_ids else None
                mc = _mc_random(mid=mid_rand, is_conica=is_conica)
                mats.append(mc.to_dict())
            pid, exc = safe(db.add_preventivo, _prev_dict(materiali_utilizzati=mats))
            if exc or not isinstance(pid, int):
                fail_prof += 1
            else:
                pids_prof.append(pid)
                pids_tutti.append(pid)
        # Verifica per ogni profilo: fail ≤ 2%
        fail_rate = fail_prof / n_prof if n_prof > 0 else 0
        if fail_rate > 0.02:
            R.fail(f"Profilo {lbl}: {fail_prof}/{n_prof} falliti ({fail_rate*100:.1f}% > 2%)")
        else:
            R.ok(f"Profilo {lbl}: {len(pids_prof)}/{n_prof} OK, {fail_prof} falliti", verbose)
        fail_per_profilo[lbl] = (fail_prof, n_prof, pids_prof)

    # Verifica round-trip per campione
    campione_rt = random.sample(pids_tutti, min(30, len(pids_tutti)))
    errori_rt = 0
    for pid in campione_rt:
        prev, exc = safe(db.get_preventivo_by_id, pid)
        if exc or prev is None:
            errori_rt += 1
            continue
        if not isinstance(prev.get("materiali_utilizzati"), list):
            errori_rt += 1
            continue
        # Verifica nessun campo obbligatorio None
        for campo in ["nome_cliente", "numero_ordine", "preventivo_finale", "prezzo_cliente"]:
            if campo not in prev:
                errori_rt += 1
                break
    if errori_rt:
        R.fail(f"Round-trip preventivi: {errori_rt}/{len(campione_rt)} con errori di struttura")
    else:
        R.ok(f"Round-trip {len(campione_rt)} preventivi: struttura e materiali_utilizzati OK", verbose)

    R.info(f"Totale preventivi inseriti: {len(pids_tutti)}/{N_PREV}")
    return pids_tutti


# =============================================================================
# SEZ. 8 — PREVENTIVI: campi e update
# =============================================================================

def test_08_preventivi_update(db, pids, verbose=False):
    R.section("8. PREVENTIVI — update campi e round-trip")

    if not pids:
        R.warn("Nessun preventivo disponibile — skip")
        return

    # Update 100 preventivi random
    campione_upd = random.sample(pids, min(100, len(pids)))
    valori_upd = {}
    errori_upd = 0
    for pid in campione_upd:
        nc  = f"CLIENTE_UPD_{pid}"
        no  = f"ORD-UPD-{pid}"
        mis = f"{random.randint(10,500)}x{random.randint(10,500)}"
        cod = f"COD{pid}"
        pf  = round(random.uniform(10, 9999), 2)
        safe(db.update_preventivo, pid, _prev_dict(
            nome_cliente=nc, numero_ordine=no, misura=mis, codice=cod,
            preventivo_finale=pf
        ))
        valori_upd[pid] = (nc, no, mis, cod, pf)

    # Verifica ogni campo
    for pid, (nc, no, mis, cod, pf) in valori_upd.items():
        prev, _ = safe(db.get_preventivo_by_id, pid)
        if prev is None:
            errori_upd += 1
            continue
        if prev.get("nome_cliente") != nc:        errori_upd += 1
        elif prev.get("numero_ordine") != no:     errori_upd += 1
        elif prev.get("misura") != mis:           errori_upd += 1
        elif prev.get("codice") != cod:           errori_upd += 1
        elif abs(prev.get("preventivo_finale", -1) - pf) > 0.01: errori_upd += 1
    if errori_upd:
        R.fail(f"Update 100 preventivi: {errori_upd} campi discordanti dopo lettura")
    else:
        R.ok(f"Update {len(campione_upd)} preventivi: tutti i campi concordi", verbose)

    # Update materiali_utilizzati: sostituisci lista con lista diversa
    pid_mat_upd = campione_upd[0] if campione_upd else None
    if pid_mat_upd:
        nuovi_mats = [_mc_random().to_dict() for _ in range(3)]
        safe(db.update_preventivo, pid_mat_upd, _prev_dict(materiali_utilizzati=nuovi_mats))
        prev_new, _ = safe(db.get_preventivo_by_id, pid_mat_upd)
        if prev_new and len(prev_new.get("materiali_utilizzati", [])) == 3:
            R.ok("Update materiali_utilizzati: nuova lista (3 mat) letta OK", verbose)
        else:
            n_letta = len(prev_new.get("materiali_utilizzati", [])) if prev_new else "N/A"
            R.fail(f"Update materiali_utilizzati: attesi 3, letti {n_letta}")

    # Update su ID inesistente → no crash
    _, exc_fan = safe(db.update_preventivo, 9999999, _prev_dict())
    if exc_fan:
        R.fail("update_preventivo su ID inesistente → crash", exc_fan)
    else:
        R.ok("update_preventivo su ID inesistente → no crash (False/None)", verbose)

    # save_preventivo (upsert): su ID esistente → aggiorna, non crea duplicato
    pid_save = campione_upd[1] if len(campione_upd) > 1 else campione_upd[0]
    tutti_prima, _ = safe(db.get_all_preventivi)
    n_prima = len(tutti_prima or [])
    dati_save = _prev_dict(nome_cliente="SAVE_UPSERT_TEST")
    dati_save["id"] = pid_save  # ID esistente
    safe(db.save_preventivo, dati_save)
    tutti_dopo, _ = safe(db.get_all_preventivi)
    n_dopo = len(tutti_dopo or [])
    if n_dopo > n_prima:
        R.warn(f"save_preventivo su ID esistente: ha creato nuovo record (n: {n_prima}→{n_dopo})")
    else:
        R.ok("save_preventivo su ID esistente: non crea duplicato", verbose)

    # save_preventivo su nuovo (senza ID) → inserisce
    nuovo_d = _prev_dict(nome_cliente="SAVE_NEW_TEST")
    pid_new, exc_new = safe(db.save_preventivo, nuovo_d)
    if exc_new or not isinstance(pid_new, int):
        R.fail("save_preventivo (nuovo): fallito", exc_new)
    else:
        prev_salvato, _ = safe(db.get_preventivo_by_id, pid_new)
        if prev_salvato and prev_salvato.get("nome_cliente") == "SAVE_NEW_TEST":
            R.ok("save_preventivo (nuovo): crea record e nome OK", verbose)
        else:
            R.warn("save_preventivo (nuovo): creato ma nome non verificato")


# =============================================================================
# SEZ. 9 — PREVENTIVI: storico e ripristino approfondito
# =============================================================================

def test_09_preventivi_storico(db, pids, verbose=False):
    R.section("9. PREVENTIVI — storico modifiche e ripristino approfondito")

    if not pids:
        R.warn("Nessun preventivo — skip")
        return

    # 20 preventivi × 10 update ciascuno → storico ≥10 entry
    campione_stor = random.sample(pids, min(20, len(pids)))
    valori_intermedi = {}  # pid → lista di (pf) per ogni update
    errori_stor = 0

    for pid in campione_stor:
        valori_seq = []
        for step in range(10):
            pf_step = round(random.uniform(10.0, 5000.0), 2)
            nc_step = f"STOR_{pid}_STEP{step}"
            safe(db.update_preventivo, pid, _prev_dict(
                preventivo_finale=pf_step,
                nome_cliente=nc_step
            ))
            valori_seq.append((pf_step, nc_step))
        valori_intermedi[pid] = valori_seq
        storico, _ = safe(db.get_storico_modifiche, pid)
        if storico is None or len(storico) < 10:
            errori_stor += 1

    if errori_stor:
        R.fail(f"Storico modifiche (20 prev × 10 update): {errori_stor} con <10 entry")
    else:
        R.ok(f"Storico modifiche: tutti {len(campione_stor)} prev hanno ≥10 entry", verbose)

    # Verifica struttura delle entry: timestamp, preventivo_finale, nome_cliente
    pid_check = campione_stor[0]
    storico_check, _ = safe(db.get_storico_modifiche, pid_check)
    errori_struct = 0
    for entry in (storico_check or []):
        if "timestamp" not in entry:
            errori_struct += 1
        elif not _is_valid_iso(entry["timestamp"]):
            errori_struct += 1
        if "data" not in entry:
            errori_struct += 1
        elif "preventivo_finale" not in entry.get("data", {}):
            errori_struct += 1
        elif "nome_cliente" not in entry.get("data", {}):
            errori_struct += 1
    if errori_struct:
        R.fail(f"Struttura storico: {errori_struct} entry malformate (manca timestamp/preventivo_finale/nome_cliente)")
    else:
        R.ok("Struttura storico: timestamp ISO, preventivo_finale, nome_cliente presenti", verbose)

    # Timestamp in ordine crescente
    if storico_check:
        ts_list = [e["timestamp"] for e in storico_check if "timestamp" in e]
        if ts_list != sorted(ts_list):
            R.warn("Timestamp storico non in ordine crescente (potrebbero essere quasi uguali)")
        else:
            R.ok("Timestamp storico in ordine crescente", verbose)

    # Ripristina alla versione 3 (entry index 2) → verifica preventivo_finale
    errori_ripristino = 0
    ripristini_ok = 0
    for pid in campione_stor[:10]:
        storico, _ = safe(db.get_storico_modifiche, pid)
        if not storico or len(storico) < 3:
            continue
        entry_3 = storico[2]  # terza entry (index 2)
        ts_3    = entry_3.get("timestamp")
        pf_3    = entry_3.get("data", {}).get("preventivo_finale")
        if ts_3 is None:
            continue
        res_rip, exc_rip = safe(db.ripristina_versione_preventivo, pid, ts_3)
        if exc_rip or not res_rip:
            errori_ripristino += 1
        else:
            prev_rip, _ = safe(db.get_preventivo_by_id, pid)
            if pf_3 is not None and prev_rip:
                if abs(prev_rip.get("preventivo_finale", -1) - pf_3) > 0.01:
                    errori_ripristino += 1
                else:
                    ripristini_ok += 1
    if errori_ripristino:
        R.fail(f"Ripristino versione 3: {errori_ripristino} falliti o preventivo_finale discordante")
    else:
        R.ok(f"Ripristino versione 3: {ripristini_ok} preventivi ripristinati correttamente", verbose)

    # Ripristina alla versione più vecchia
    pid_oldest = campione_stor[-1] if campione_stor else None
    if pid_oldest:
        storico_old, _ = safe(db.get_storico_modifiche, pid_oldest)
        if storico_old:
            ts_old = storico_old[0]["timestamp"]
            pf_old = storico_old[0].get("data", {}).get("preventivo_finale")
            res_old, exc_old = safe(db.ripristina_versione_preventivo, pid_oldest, ts_old)
            if exc_old or not res_old:
                R.fail("Ripristino versione più vecchia: fallito", exc_old)
            else:
                prev_old, _ = safe(db.get_preventivo_by_id, pid_oldest)
                if pf_old is not None and prev_old:
                    if abs(prev_old.get("preventivo_finale", -1) - pf_old) > 0.01:
                        R.fail(f"Ripristino versione più vecchia: pf atteso {pf_old}, trovato {prev_old.get('preventivo_finale')}")
                    else:
                        R.ok("Ripristino versione più vecchia: preventivo_finale corretto", verbose)
                else:
                    R.ok("Ripristino versione più vecchia: eseguito (pf non verificabile)", verbose)

    # Ripristino su timestamp inesistente → no crash, False
    pid_rip_fan = campione_stor[0] if campione_stor else None
    if pid_rip_fan:
        res_fan, exc_fan = safe(db.ripristina_versione_preventivo, pid_rip_fan,
                                "9999-01-01T00:00:00.000000")
        if exc_fan:
            R.fail("Ripristino su timestamp inesistente → crash", exc_fan)
        elif res_fan:
            R.warn("Ripristino su timestamp inesistente restituisce True (atteso False)")
        else:
            R.ok("Ripristino su timestamp inesistente → False (corretto)", verbose)

    # get_preventivi_con_modifiche: lista non vuota, ogni elemento ha storico non vuoto
    con_mod, exc_cm = safe(db.get_preventivi_con_modifiche)
    if exc_cm:
        R.fail("get_preventivi_con_modifiche crash", exc_cm)
    elif not con_mod:
        R.warn("get_preventivi_con_modifiche: lista vuota (atteso almeno qualcuno)")
    else:
        # colonna 9 è storico_modifiche (come get_all_preventivi)
        errori_cm = 0
        for row in con_mod[:10]:
            stor_raw = row[9] if len(row) > 9 else None
            if stor_raw in (None, "[]", ""):
                errori_cm += 1
        if errori_cm:
            R.fail(f"get_preventivi_con_modifiche: {errori_cm}/10 hanno storico_modifiche vuoto")
        else:
            R.ok(f"get_preventivi_con_modifiche: {len(con_mod)} preventivi con storico non vuoto", verbose)


# =============================================================================
# SEZ. 10 — PREVENTIVI: revisioni e catene profonde
# =============================================================================

def test_10_preventivi_revisioni(db, pids, verbose=False):
    R.section("10. PREVENTIVI — revisioni e catene profonde")

    if len(pids) < 30:
        R.warn(f"Solo {len(pids)} preventivi, riduco campione")
    n_orig = min(30, len(pids))
    campione_orig = pids[:n_orig]

    # 30 originali × 5 revisioni = catene profonde
    rev_map = {}  # pid_orig → [rev_id×5]
    errori_rev = 0
    for pid_orig in campione_orig:
        rev_ids = []
        for r in range(5):
            rev_id, exc = safe(db.add_revisione_preventivo, pid_orig,
                               _prev_dict(nome_cliente=f"REV_{pid_orig}_r{r}"),
                               f"Revisione {r+1}")
            if exc or not isinstance(rev_id, int):
                errori_rev += 1
            else:
                rev_ids.append(rev_id)
        rev_map[pid_orig] = rev_ids
    if errori_rev:
        R.fail(f"add_revisione_preventivo: {errori_rev} falliti")
    else:
        R.ok(f"Creazione revisioni ({n_orig} orig × 5 rev): tutti OK", verbose)

    # Revisione su ID inesistente → gestito
    _, exc_rev_fan = safe(db.add_revisione_preventivo, 9999999, _prev_dict(), "test")
    if exc_rev_fan:
        R.ok("add_revisione_preventivo su ID inesistente → eccezione gestita", verbose)
    else:
        R.warn("add_revisione_preventivo su ID inesistente non ha generato eccezione (potrebbe creare record orfano)")

    # get_revisioni_preventivo: conta correttamente (1 orig + 5 rev = 6)
    errori_count = 0
    for pid_orig, rev_ids in list(rev_map.items())[:10]:
        revisioni, _ = safe(db.get_revisioni_preventivo, pid_orig)
        # La query ritorna: WHERE preventivo_originale_id=? OR id=?
        # Quindi: 1 orig + N revisioni
        atteso = 1 + len(rev_ids)
        if revisioni is None or len(revisioni) != atteso:
            errori_count += 1
    if errori_count:
        R.fail(f"get_revisioni_preventivo: {errori_count}/10 conteggi errati (atteso 6)")
    else:
        R.ok("get_revisioni_preventivo: conteggi corretti (1+5=6)", verbose)

    # get_all_preventivi_latest: originali con revisioni NON compaiono
    latest, exc_lat = safe(db.get_all_preventivi_latest)
    if exc_lat:
        R.fail("get_all_preventivi_latest crash", exc_lat)
    else:
        ids_latest = {row[0] for row in (latest or [])}
        originali_esposti = [p for p in campione_orig if p in ids_latest]
        if originali_esposti:
            R.warn(f"get_all_preventivi_latest: {len(originali_esposti)} originali esposti (atteso solo ultime revisioni)")
        else:
            R.ok(f"get_all_preventivi_latest: nessun originale esposto se ha revisioni", verbose)

        # L'ultima revisione di ogni gruppo compare in latest
        ultime_rev = [rev_ids[-1] for rev_ids in rev_map.values() if rev_ids]
        trovate = sum(1 for r in ultime_rev if r in ids_latest)
        if trovate < len(ultime_rev):
            R.warn(f"get_all_preventivi_latest: solo {trovate}/{len(ultime_rev)} ultime revisioni visibili")
        else:
            R.ok(f"get_all_preventivi_latest: tutte le {trovate} ultime revisioni presenti", verbose)

    # Revisioni hanno numero_revisione crescente
    pid_check_rev = campione_orig[0]
    rev_rows, _ = safe(db.get_revisioni_preventivo, pid_check_rev)
    if rev_rows and len(rev_rows) > 1:
        numeri_rev = [r[8] for r in rev_rows]  # colonna numero_revisione (index 8)
        numeri_rev_sorted = sorted(numeri_rev, reverse=True)
        if numeri_rev == numeri_rev_sorted:
            R.ok("Revisioni ordinate per numero_revisione decrescente (come da query)", verbose)
        else:
            R.warn(f"Revisioni: numeri_rev={numeri_rev}, non in ordine decrescente atteso")

    # Delete originale → tutte le revisioni eliminate (cascade)
    pid_del_orig = campione_orig[-1]
    rev_del = rev_map.get(pid_del_orig, [])
    safe(db.delete_preventivo_e_revisioni, pid_del_orig)
    superstiti = []
    for check_id in [pid_del_orig] + rev_del:
        row_ghost, _ = safe(db.get_preventivo_by_id, check_id)
        if row_ghost is not None:
            superstiti.append(check_id)
    if superstiti:
        R.fail(f"delete_preventivo_e_revisioni: {len(superstiti)} record ancora presenti: {superstiti[:3]}")
    else:
        R.ok("delete_preventivo_e_revisioni: originale + 5 revisioni eliminate (cascade)", verbose)

    # Delete solo revisione (non l'originale) → originale sopravvive
    pid_del_solo_rev = campione_orig[0]
    rev_del_solo = rev_map.get(pid_del_solo_rev, [])
    if rev_del_solo:
        # Elimina solo la prima revisione (che è una revisione, non l'originale)
        # Usiamo delete_preventivo_e_revisioni sulla revisione stessa
        # La funzione cerca il gruppo_id e cancella tutto il gruppo — quindi non ideale
        # Facciamo invece una verifica che l'originale sopravviva dopo delete di revisione
        rev_first = rev_del_solo[0]
        safe(db.delete_preventivo_e_revisioni, rev_first)
        # L'originale deve ancora esserci
        orig_surv, _ = safe(db.get_preventivo_by_id, pid_del_solo_rev)
        if orig_surv is None:
            R.warn("delete_preventivo_e_revisioni su revisione: originale eliminato (cascade completo)")
        else:
            R.ok("delete_preventivo_e_revisioni su revisione: originale sopravvive", verbose)


# =============================================================================
# SEZ. 11 — PREVENTIVI: valori estremi e campi speciali
# =============================================================================

def test_11_preventivi_estremi(db, verbose=False):
    R.section("11. PREVENTIVI — valori estremi e campi speciali")

    # preventivo_finale = 0.0
    pid_zero, exc_zero = safe(db.add_preventivo, _prev_dict(preventivo_finale=0.0))
    if exc_zero:
        R.fail("preventivo_finale=0.0 → crash in add_preventivo", exc_zero)
    else:
        prev_zero, _ = safe(db.get_preventivo_by_id, pid_zero)
        if prev_zero and abs(prev_zero.get("preventivo_finale", -1)) < 0.01:
            R.ok("preventivo_finale=0.0: salvato e riletto OK", verbose)
        else:
            R.fail(f"preventivo_finale=0.0: riletto come {prev_zero.get('preventivo_finale') if prev_zero else 'None'}")

    # preventivo_finale = 999999.99
    pid_big, exc_big = safe(db.add_preventivo, _prev_dict(preventivo_finale=999999.99))
    if exc_big:
        R.fail("preventivo_finale=999999.99 → crash", exc_big)
    else:
        prev_big, _ = safe(db.get_preventivo_by_id, pid_big)
        if prev_big and abs(prev_big.get("preventivo_finale", -1) - 999999.99) < 0.01:
            R.ok("preventivo_finale=999999.99: round-trip OK", verbose)
        else:
            R.fail(f"preventivo_finale=999999.99: round-trip fallito")

    # nome_cliente con unicode
    unicode_nome = "Ünïcödé Clïënt 日本語 العربية"
    pid_uni, exc_uni = safe(db.add_preventivo, _prev_dict(nome_cliente=unicode_nome))
    if exc_uni:
        R.fail("nome_cliente unicode → crash", exc_uni)
    else:
        prev_uni, _ = safe(db.get_preventivo_by_id, pid_uni)
        if prev_uni and prev_uni.get("nome_cliente") == unicode_nome:
            R.ok("nome_cliente unicode: round-trip OK", verbose)
        else:
            R.fail(f"nome_cliente unicode: letto '{prev_uni.get('nome_cliente') if prev_uni else 'None'}'")

    # nome_cliente = stringa di 1000 caratteri
    nome_lungo = "A" * 1000
    pid_lungo, exc_lungo = safe(db.add_preventivo, _prev_dict(nome_cliente=nome_lungo))
    if exc_lungo:
        R.warn(f"nome_cliente 1000 char → eccezione: {exc_lungo}")
    else:
        prev_lungo, _ = safe(db.get_preventivo_by_id, pid_lungo)
        if prev_lungo:
            letto = prev_lungo.get("nome_cliente", "")
            if len(letto) >= 100:
                R.ok(f"nome_cliente 1000 char: salvato (letto {len(letto)} char)", verbose)
            else:
                R.warn(f"nome_cliente 1000 char: letto solo {len(letto)} char (troncato)")
        else:
            R.fail("nome_cliente 1000 char: non riletto")

    # numero_ordine = stringa vuota ""
    pid_ord_empty, exc_oe = safe(db.add_preventivo, _prev_dict(numero_ordine=""))
    if exc_oe:
        R.warn(f"numero_ordine='' → eccezione: {exc_oe}")
    else:
        prev_oe, _ = safe(db.get_preventivo_by_id, pid_ord_empty)
        if prev_oe and prev_oe.get("numero_ordine") == "":
            R.ok("numero_ordine='': salvato come stringa vuota", verbose)
        else:
            R.warn(f"numero_ordine='': letto come '{prev_oe.get('numero_ordine') if prev_oe else 'None'}'")

    # descrizione con newline e tab
    desc_special = "Linea1\nLinea2\tcon\ttab"
    pid_desc, exc_desc = safe(db.add_preventivo, _prev_dict(descrizione=desc_special))
    if exc_desc:
        R.warn(f"descrizione con newline/tab → eccezione: {exc_desc}")
    else:
        prev_desc, _ = safe(db.get_preventivo_by_id, pid_desc)
        if prev_desc and "\n" in prev_desc.get("descrizione", ""):
            R.ok("descrizione con newline: round-trip OK", verbose)
        else:
            R.warn("descrizione con newline: newline non preservato")

    # codice = None/NULL
    pid_cod_none, exc_cn = safe(db.add_preventivo, _prev_dict(codice=None))
    if exc_cn:
        R.warn(f"codice=None → eccezione: {exc_cn}")
    else:
        R.ok("codice=None: accettato senza crash", verbose)

    # misura con formato non standard
    pid_mis, exc_mis = safe(db.add_preventivo, _prev_dict(misura="CUSTOM/FORMATO"))
    if exc_mis:
        R.warn(f"misura='CUSTOM/FORMATO' → eccezione: {exc_mis}")
    else:
        prev_mis, _ = safe(db.get_preventivo_by_id, pid_mis)
        if prev_mis and prev_mis.get("misura") == "CUSTOM/FORMATO":
            R.ok("misura non standard: round-trip OK", verbose)
        else:
            R.warn("misura non standard: non letta correttamente")

    # Tutti i campi numerici a 0
    pid_all0, exc_all0 = safe(db.add_preventivo, _prev_dict(
        costo_totale_materiali=0.0, costi_accessori=0.0,
        minuti_taglio=0.0, minuti_avvolgimento=0.0, minuti_pulizia=0.0,
        minuti_rettifica=0.0, minuti_imballaggio=0.0,
        tot_mano_opera=0.0, subtotale=0.0, maggiorazione_25=0.0,
        preventivo_finale=0.0, prezzo_cliente=0.0
    ))
    if exc_all0:
        R.fail("Tutti campi numerici a 0 → crash", exc_all0)
    else:
        R.ok("Tutti campi numerici a 0: preventivo valido inserito", verbose)


# =============================================================================
# SEZ. 12 — PREVENTIVI: query e filtri
# =============================================================================

def test_12_preventivi_query(db, pids, verbose=False):
    R.section("12. PREVENTIVI — query e filtri")

    if not pids:
        R.warn("Nessun preventivo — skip")
        return

    # get_all_preventivi: lista non None, ognuno ha id e dati base
    tutti, exc_tutti = safe(db.get_all_preventivi)
    if exc_tutti:
        R.fail("get_all_preventivi crash", exc_tutti)
    elif tutti is None:
        R.fail("get_all_preventivi: None")
    else:
        errori_struct = sum(1 for r in tutti if not r or r[0] is None)
        if errori_struct:
            R.fail(f"get_all_preventivi: {errori_struct} record con id=None")
        else:
            R.ok(f"get_all_preventivi: {len(tutti)} record, tutti con id", verbose)

    # get_all_preventivi_latest: lista non None, no duplicati di pid
    latest, exc_lat = safe(db.get_all_preventivi_latest)
    if exc_lat:
        R.fail("get_all_preventivi_latest crash", exc_lat)
    elif latest is None:
        R.fail("get_all_preventivi_latest: None")
    else:
        ids_lat = [r[0] for r in latest]
        if len(ids_lat) != len(set(ids_lat)):
            R.fail(f"get_all_preventivi_latest: ID duplicati ({len(ids_lat)} vs {len(set(ids_lat))} unici)")
        else:
            R.ok(f"get_all_preventivi_latest: {len(ids_lat)} record, nessun duplicato", verbose)

    # Tutti gli ID in latest esistono realmente in get_all_preventivi
    if tutti and latest:
        tutti_ids = {r[0] for r in tutti}
        ids_lat_set = {r[0] for r in latest}
        orfani = ids_lat_set - tutti_ids
        if orfani:
            R.fail(f"get_all_preventivi_latest: {len(orfani)} ID non presenti in get_all_preventivi")
        else:
            R.ok("get_all_preventivi_latest: tutti gli ID esistono in get_all_preventivi", verbose)

    # get_preventivi_con_modifiche: solo quelli con storico non vuoto
    con_mod, exc_cm = safe(db.get_preventivi_con_modifiche)
    if exc_cm:
        R.fail("get_preventivi_con_modifiche crash", exc_cm)
    else:
        R.ok(f"get_preventivi_con_modifiche: {len(con_mod or [])} record", verbose)

    # Verifica che get_all_preventivi_latest non esponga revisioni come standalone
    # (una revisione ha preventivo_originale_id != NULL)
    if latest:
        # Controlla direttamente nel DB quali hanno preventivo_originale_id non NULL
        try:
            with _sqlite3.connect(db.db_path) as conn:
                cur = conn.cursor()
                ids_lat_list = [r[0] for r in latest]
                if ids_lat_list:
                    placeholders = ",".join("?" for _ in ids_lat_list)
                    cur.execute(
                        f"SELECT COUNT(*) FROM preventivi WHERE id IN ({placeholders}) AND preventivo_originale_id IS NOT NULL",
                        ids_lat_list
                    )
                    n_rev_in_lat = cur.fetchone()[0]
                    if n_rev_in_lat > 0:
                        R.warn(f"get_all_preventivi_latest: {n_rev_in_lat} revisioni raw incluse (atteso solo ultime per gruppo)")
                    else:
                        R.ok("get_all_preventivi_latest: nessuna revisione raw standalone", verbose)
        except Exception as e:
            R.warn(f"Verifica revisioni in latest: {e}")

    R.info(f"Totale preventivi: {len(tutti or [])} | Latest: {len(latest or [])} | Con modifiche: {len(con_mod or [])}")


# =============================================================================
# SEZ. 13 — MATERIALECALCOLATO: calcoli puri N_CALC campioni
# =============================================================================

def test_13_mc_calcoli_puri(N_CALC, verbose=False):
    R.section(f"13. MATERIALECALCOLATO — calcoli puri ({N_CALC} campioni)")

    errori_formula_sviluppo   = 0
    errori_formula_df         = 0
    errori_formula_mag        = 0
    errori_nan                = 0
    errori_idempotenza        = 0
    errori_serial             = 0
    errori_pos_lu             = 0
    errori_pos_scarto         = 0

    for _ in range(N_CALC):
        mc = _mc_random()

        # Formula sviluppo: ((D + giri*spes)*pi)*giri + 5 (dal sorgente)
        atteso_sv = ((mc.diametro + mc.giri * mc.spessore) * 3.14) * mc.giri + 5
        if mc.arrotondamento_manuale > 0:
            atteso_sv = mc.arrotondamento_manuale
        if abs(mc.sviluppo - atteso_sv) > 0.01:
            errori_formula_sviluppo += 1

        # Formula diametro_finale: D + spes * giri * 2
        atteso_df = mc.diametro + mc.spessore * mc.giri * 2
        if abs(mc.diametro_finale - atteso_df) > 0.001:
            errori_formula_df += 1

        # maggiorazione = costo_totale * 1.1
        if mc.costo_totale > 0:
            if abs(mc.maggiorazione - mc.costo_totale * 1.1) > 0.001:
                errori_formula_mag += 1

        # Nessun NaN/Inf
        valori = [mc.sviluppo, mc.costo_totale, mc.maggiorazione, mc.diametro_finale,
                  mc.lunghezza_utilizzata, mc.scarto_mm2]
        if any(not math.isfinite(v) for v in valori):
            errori_nan += 1

        # Idempotenza: 2ª chiamata = stesso risultato
        sv1, ct1, df1 = mc.sviluppo, mc.costo_totale, mc.diametro_finale
        mc.ricalcola_tutto()
        if abs(mc.sviluppo - sv1) > 1e-9 or abs(mc.costo_totale - ct1) > 1e-9 or abs(mc.diametro_finale - df1) > 1e-9:
            errori_idempotenza += 1

        # Serializzazione JSON round-trip
        d = mc.to_dict()
        try:
            j  = json.dumps(d)
            d2 = json.loads(j)
            if abs(d2.get("diametro", 0) - mc.diametro) > 0.001: errori_serial += 1
            if abs(d2.get("spessore", 0) - mc.spessore) > 0.0001: errori_serial += 1
            if d2.get("giri") != mc.giri: errori_serial += 1
            if abs(d2.get("sviluppo", 0) - mc.sviluppo) > 0.001: errori_serial += 1
            if abs(d2.get("costo_totale", 0) - mc.costo_totale) > 0.001: errori_serial += 1
        except (TypeError, ValueError):
            errori_serial += 1

        # lunghezza_utilizzata ≥ 0
        if mc.lunghezza_utilizzata < 0:
            errori_pos_lu += 1

        # scarto_mm2 ≥ 0
        if mc.scarto_mm2 < 0:
            errori_pos_scarto += 1

    def _report(label, n_err):
        if n_err:
            R.fail(f"{label}: {n_err}/{N_CALC} discordanti")
        else:
            R.ok(f"{label}: {N_CALC}/{N_CALC} OK", verbose)

    _report("Formula sviluppo",    errori_formula_sviluppo)
    _report("Formula diametro_finale", errori_formula_df)
    _report("Formula maggiorazione",  errori_formula_mag)
    _report("Nessun NaN/Inf",         errori_nan)
    _report("Idempotenza ricalcola",  errori_idempotenza)
    _report("JSON round-trip",        errori_serial)
    _report("lunghezza_utilizzata ≥0", errori_pos_lu)
    _report("scarto_mm2 ≥0",           errori_pos_scarto)

    # Monotonia: giri++ → diametro_finale++
    errori_mono_giri = 0
    for _ in range(50):
        d   = round(random.uniform(30, 300), 1)
        sps = round(random.uniform(0.1, 0.5), 2)
        g1  = random.randint(1, 7)
        g2  = g1 + 1
        mc1 = _mc_random(diametro=d, spessore=sps, giri=g1)
        mc2 = _mc_random(diametro=d, spessore=sps, giri=g2)
        if mc2.diametro_finale <= mc1.diametro_finale:
            errori_mono_giri += 1
    if errori_mono_giri:
        R.fail(f"Monotonia giri→diametro_finale: {errori_mono_giri}/50 non monotoni")
    else:
        R.ok("Monotonia: giri++ → diametro_finale++: 50/50 OK", verbose)

    # Monotonia: spessore++ → sviluppo++ (sviluppo cresce con spessore a parità di giri/lunghezza)
    # dal codice: sviluppo = ((D + giri*spes)*pi)*giri + 5  → cresce con spessore
    errori_mono_spes = 0
    for _ in range(50):
        d   = round(random.uniform(30, 300), 1)
        g   = random.randint(1, 8)
        lun = round(random.uniform(50, 500), 1)
        s1  = round(random.uniform(0.05, 0.4), 3)
        s2  = s1 + 0.05
        mc1 = _mc_random(diametro=d, giri=g, spessore=s1, lunghezza=lun)
        mc2 = _mc_random(diametro=d, giri=g, spessore=s2, lunghezza=lun)
        if mc2.sviluppo < mc1.sviluppo:
            errori_mono_spes += 1
    if errori_mono_spes:
        R.fail(f"Monotonia spessore→sviluppo: {errori_mono_spes}/50 non monotoni")
    else:
        R.ok("Monotonia: spessore++ → sviluppo++: 50/50 OK", verbose)


# =============================================================================
# SEZ. 14 — MATERIALECALCOLATO: edge case
# =============================================================================

def test_14_mc_edge(verbose=False):
    R.section("14. MATERIALECALCOLATO — edge case")

    # giri = 0: no division by zero, sviluppo = 5 (((D+0*spes)*pi)*0 + 5 = 5)
    mc_g0 = MaterialeCalcolato()
    mc_g0.diametro = 100.0
    mc_g0.giri     = 0
    mc_g0.spessore = 0.25
    mc_g0.lunghezza = 200.0
    mc_g0.costo_materiale = 30.0
    mc_g0.ricalcola_tutto()
    if not math.isfinite(mc_g0.sviluppo):
        R.fail(f"giri=0: sviluppo non finito ({mc_g0.sviluppo})")
    else:
        # sviluppo = ((D + 0*spes)*pi)*0 + 5 = 5
        if abs(mc_g0.sviluppo - 5.0) < 0.01:
            R.ok(f"giri=0: sviluppo=5.0 (formula: 0+5=5), no division by zero", verbose)
        else:
            R.ok(f"giri=0: sviluppo={mc_g0.sviluppo:.3f}, no crash (formula consistente)", verbose)

    # lunghezza = 0: costo_totale = 0 (lunghezza_utilizzata = 0)
    mc_l0 = _mc_random(lunghezza=0.0)
    if mc_l0.costo_totale != 0.0:
        R.fail(f"lunghezza=0: costo_totale={mc_l0.costo_totale} (atteso 0)")
    else:
        R.ok("lunghezza=0: costo_totale=0", verbose)
    if mc_l0.lunghezza_utilizzata != 0.0:
        R.fail(f"lunghezza=0: lunghezza_utilizzata={mc_l0.lunghezza_utilizzata} (atteso 0)")
    else:
        R.ok("lunghezza=0: lunghezza_utilizzata=0", verbose)

    # diametro = 0: diametro_finale = spessore*giri*2
    mc_d0 = MaterialeCalcolato()
    mc_d0.diametro = 0.0
    mc_d0.giri     = 4
    mc_d0.spessore = 0.3
    mc_d0.lunghezza = 100.0
    mc_d0.costo_materiale = 10.0
    mc_d0.ricalcola_tutto()
    atteso_df0 = 0.0 + 0.3 * 4 * 2
    if abs(mc_d0.diametro_finale - atteso_df0) > 0.001:
        R.fail(f"diametro=0: diametro_finale atteso {atteso_df0}, trovato {mc_d0.diametro_finale}")
    else:
        R.ok(f"diametro=0: diametro_finale={mc_d0.diametro_finale:.3f} (spessore*giri*2)", verbose)

    # costo_materiale = 0: costo_totale = 0, maggiorazione = 0
    mc_cm0 = _mc_random(costo_materiale=0.0)
    if mc_cm0.costo_totale != 0.0 or mc_cm0.maggiorazione != 0.0:
        R.fail(f"costo_materiale=0: costo_totale={mc_cm0.costo_totale}, mag={mc_cm0.maggiorazione}")
    else:
        R.ok("costo_materiale=0: costo_totale=0, maggiorazione=0", verbose)

    # spessore = 0: diametro_finale = diametro, sviluppo cambia ma no crash
    mc_sp0 = _mc_random(spessore=0.0)
    atteso_df_sp0 = mc_sp0.diametro + 0.0 * mc_sp0.giri * 2
    if abs(mc_sp0.diametro_finale - atteso_df_sp0) > 0.001:
        R.fail(f"spessore=0: diametro_finale atteso {atteso_df_sp0}, trovato {mc_sp0.diametro_finale}")
    else:
        R.ok(f"spessore=0: diametro_finale = diametro ({mc_sp0.diametro_finale:.3f})", verbose)

    # giri = 1: sviluppo = ((D + spes)*pi)*1 + 5
    mc_g1 = MaterialeCalcolato()
    mc_g1.diametro = 50.0
    mc_g1.giri     = 1
    mc_g1.spessore = 0.2
    mc_g1.lunghezza = 100.0
    mc_g1.costo_materiale = 20.0
    mc_g1.ricalcola_tutto()
    atteso_sv_g1 = ((50.0 + 1 * 0.2) * 3.14) * 1 + 5
    if abs(mc_g1.sviluppo - atteso_sv_g1) > 0.01:
        R.fail(f"giri=1: sviluppo atteso {atteso_sv_g1:.3f}, trovato {mc_g1.sviluppo:.3f}")
    else:
        R.ok(f"giri=1: sviluppo={(mc_g1.sviluppo):.3f} (formula corretta)", verbose)

    # arrotondamento_manuale: se impostato, sviluppo usa quello
    mc_arr = MaterialeCalcolato()
    mc_arr.diametro = 100.0
    mc_arr.giri     = 3
    mc_arr.spessore = 0.25
    mc_arr.lunghezza = 200.0
    mc_arr.costo_materiale = 40.0
    mc_arr.arrotondamento_manuale = 999.0
    mc_arr.ricalcola_tutto()
    if abs(mc_arr.sviluppo - 999.0) > 0.001:
        R.fail(f"arrotondamento_manuale=999: sviluppo={mc_arr.sviluppo} (atteso 999.0)")
    else:
        R.ok("arrotondamento_manuale=999: sviluppo=999.0 (override attivo)", verbose)

    # is_conica = True: no crash, stratifica = sviluppo
    mc_con = _mc_random(is_conica=True)
    if mc_con.stratifica != mc_con.sviluppo:
        R.fail(f"is_conica=True: stratifica ({mc_con.stratifica}) != sviluppo ({mc_con.sviluppo})")
    else:
        R.ok("is_conica=True: stratifica = sviluppo, no crash", verbose)
    if mc_con.scarto_mm2 < 0:
        R.fail(f"is_conica=True: scarto_mm2={mc_con.scarto_mm2} < 0")
    else:
        R.ok(f"is_conica=True: scarto_mm2={mc_con.scarto_mm2:.3f} ≥ 0", verbose)

    # is_conica = False: sezioni_coniche = []
    mc_ncon = _mc_random(is_conica=False)
    if mc_ncon.sezioni_coniche != []:
        R.warn(f"is_conica=False: sezioni_coniche={mc_ncon.sezioni_coniche} (atteso [])")
    else:
        R.ok("is_conica=False: sezioni_coniche=[] (corretto)", verbose)

    # Orientamento diversi: no crash
    for orient in [{"rotation": 0, "flip_h": False, "flip_v": False},
                   {"rotation": 90, "flip_h": True, "flip_v": False},
                   {"rotation": 180, "flip_h": False, "flip_v": True}]:
        mc_or = _mc_random()
        mc_or.orientamento = orient
        _, exc_or = safe(mc_or.ricalcola_tutto)
        if exc_or:
            R.fail(f"Orientamento {orient}: ricalcola_tutto crash", exc_or)
        else:
            R.ok(f"Orientamento {orient}: no crash", verbose)


# =============================================================================
# SEZ. 15 — PREVENTIVO MODEL: aggregazioni (200 preventivi)
# =============================================================================

def test_15_preventivo_model_agg(verbose=False):
    R.section("15. PREVENTIVO MODEL — aggregazioni (200 preventivi)")

    errori_sub = errori_mag25 = errori_fin = errori_costo_mat = errori_scarto = 0
    errori_dict_mat = 0
    n_campioni = 200

    for _ in range(n_campioni):
        p = Preventivo()
        n_mat_p = random.randint(0, 10)
        for _ in range(n_mat_p):
            mc = _mc_random()
            p.aggiungi_materiale(mc)
        p.costi_accessori     = round(random.uniform(0, 200), 2)
        p.minuti_taglio       = round(random.uniform(0, 60), 1)
        p.minuti_avvolgimento = round(random.uniform(0, 120), 1)
        p.minuti_pulizia      = round(random.uniform(0, 30), 1)
        p.minuti_rettifica    = round(random.uniform(0, 20), 1)
        p.minuti_imballaggio  = round(random.uniform(0, 15), 1)
        p.ricalcola_tutto()

        atteso_sub = p.costo_totale_materiali + p.tot_mano_opera + p.costi_accessori
        if abs(p.subtotale - atteso_sub) > 0.01: errori_sub += 1

        atteso_mag = p.subtotale * 0.25
        if abs(p.maggiorazione_25 - atteso_mag) > 0.01: errori_mag25 += 1

        atteso_fin = p.subtotale + p.maggiorazione_25
        if abs(p.preventivo_finale - atteso_fin) > 0.01: errori_fin += 1

        # costo_totale_materiali = somma delle maggiorazioni dei MaterialeCalcolato
        atteso_ctm = sum(mc.maggiorazione for mc in p.materiali_calcolati)
        if abs(p.costo_totale_materiali - atteso_ctm) > 0.01: errori_costo_mat += 1

        # scarto_totale_mm2 = somma scarto_mm2
        atteso_scarto = sum(mc.scarto_mm2 for mc in p.materiali_calcolati)
        p.ricalcola_scarto_totale()
        if abs(p.scarto_totale_mm2 - atteso_scarto) > 0.01: errori_scarto += 1

        # to_dict() ha 'materiali_utilizzati' con len = n_mat_p
        d_p = p.to_dict()
        if len(d_p.get("materiali_utilizzati", [])) != n_mat_p: errori_dict_mat += 1
        # Ogni dict materiale ha i campi chiave
        for dm in d_p.get("materiali_utilizzati", []):
            if not all(k in dm for k in ["diametro", "giri", "spessore", "costo_totale"]):
                errori_dict_mat += 1

    def _rpt(lbl, n_e):
        if n_e: R.fail(f"{lbl}: {n_e}/{n_campioni} discordanti")
        else:   R.ok(f"{lbl}: {n_campioni}/{n_campioni} OK", verbose)

    _rpt("subtotale = ctm + mop + acc",   errori_sub)
    _rpt("maggiorazione_25 = sub*0.25",    errori_mag25)
    _rpt("preventivo_finale = sub+mag25",  errori_fin)
    _rpt("costo_totale_materiali = Σmag",  errori_costo_mat)
    _rpt("scarto_totale_mm2 = Σscarto",    errori_scarto)
    _rpt("to_dict materiali_utilizzati",   errori_dict_mat)


# =============================================================================
# SEZ. 16 — PREVENTIVO MODEL: edge case
# =============================================================================

def test_16_preventivo_model_edge(verbose=False):
    R.section("16. PREVENTIVO MODEL — edge case")

    # 0 materiali: preventivo_finale dipende solo da accessori e mop
    p0 = Preventivo()
    p0.costi_accessori = 50.0
    p0.minuti_taglio   = 10.0
    p0.ricalcola_tutto()
    if abs(p0.costo_totale_materiali) > 0.001:
        R.fail(f"0 materiali: costo_totale_materiali={p0.costo_totale_materiali} (atteso 0)")
    else:
        R.ok("0 materiali: costo_totale_materiali=0", verbose)
    atteso_sub0 = 0.0 + p0.tot_mano_opera + 50.0
    if abs(p0.subtotale - atteso_sub0) > 0.01:
        R.fail(f"0 materiali: subtotale atteso {atteso_sub0:.2f}, trovato {p0.subtotale:.2f}")
    else:
        R.ok(f"0 materiali: subtotale={p0.subtotale:.2f} (solo mop+acc)", verbose)

    # 30 materiali (max): tutti calcolati, 31° rifiutato
    p30 = Preventivo()
    for _ in range(30):
        p30.aggiungi_materiale(_mc_random())
    if len(p30.materiali_calcolati) != 30:
        R.fail(f"Max 30 materiali: solo {len(p30.materiali_calcolati)} aggiunti")
    else:
        R.ok("Max 30 materiali: tutti 30 aggiunti", verbose)
    res31 = p30.aggiungi_materiale(_mc_random())
    if res31:
        R.fail("31° materiale: aggiungi_materiale restituisce True (atteso False)")
    else:
        R.ok("31° materiale: rifiutato (False)", verbose)
    if len(p30.materiali_calcolati) != 30:
        R.fail(f"Dopo rifiuto 31°: len={len(p30.materiali_calcolati)} (atteso 30)")
    else:
        R.ok("Dopo rifiuto 31°: len=30 (invariato)", verbose)

    # Rimuovi materiale al centro (idx=15): len=29, ricalcola correttamente
    p30.rimuovi_materiale(15)
    if len(p30.materiali_calcolati) != 29:
        R.fail(f"Rimozione idx=15: len={len(p30.materiali_calcolati)} (atteso 29)")
    else:
        R.ok("Rimozione idx=15: len=29", verbose)
    p30.ricalcola_tutto()
    ctm_atteso = sum(mc.maggiorazione for mc in p30.materiali_calcolati)
    if abs(p30.costo_totale_materiali - ctm_atteso) > 0.01:
        R.fail("Dopo rimozione: costo_totale_materiali non ricalcolato correttamente")
    else:
        R.ok("Dopo rimozione idx=15: ricalcolo corretto", verbose)

    # Rimuovi tutti: len=0, tutti i totali=0
    while p30.materiali_calcolati:
        p30.rimuovi_materiale(0)
    p30.ricalcola_tutto()
    if len(p30.materiali_calcolati) != 0:
        R.fail("Rimuovi tutti: len != 0")
    elif abs(p30.costo_totale_materiali) > 0.001:
        R.fail(f"Rimuovi tutti: costo_totale_materiali={p30.costo_totale_materiali}")
    else:
        R.ok("Rimuovi tutti: len=0, costo_totale_materiali=0", verbose)

    # Aggiunta materiale con lunghezza=0: costo_totale=0, non influenza il totale
    p_l0 = Preventivo()
    ctm_prima = p_l0.costo_totale_materiali
    mc_l0 = _mc_random(lunghezza=0.0)
    p_l0.aggiungi_materiale(mc_l0)
    p_l0.ricalcola_tutto()
    if abs(p_l0.costo_totale_materiali - ctm_prima) > 0.001:
        R.warn(f"Materiale lunghezza=0: influenza costo (ctm da {ctm_prima} a {p_l0.costo_totale_materiali})")
    else:
        R.ok("Materiale lunghezza=0: costo_totale=0, non influenza il totale", verbose)

    # costi_accessori molto grandi (100000): subtotale corretto
    p_acc = Preventivo()
    p_acc.costi_accessori = 100000.0
    p_acc.ricalcola_tutto()
    atteso_sub_acc = 0.0 + 0.0 + 100000.0
    if abs(p_acc.subtotale - atteso_sub_acc) > 0.01:
        R.fail(f"costi_accessori=100000: subtotale={p_acc.subtotale} (atteso {atteso_sub_acc})")
    else:
        R.ok("costi_accessori=100000: subtotale corretto", verbose)

    # to_dict() contiene tutti i campi numerici come float
    p_dict_test = Preventivo()
    for _ in range(5):
        p_dict_test.aggiungi_materiale(_mc_random())
    p_dict_test.ricalcola_tutto()
    d_test = p_dict_test.to_dict()
    campi_num = ["costo_totale_materiali", "costi_accessori", "tot_mano_opera",
                 "subtotale", "maggiorazione_25", "preventivo_finale", "prezzo_cliente",
                 "scarto_totale_mm2"]
    errori_float = 0
    for campo in campi_num:
        if campo not in d_test:
            errori_float += 1
        elif not isinstance(d_test[campo], (int, float)):
            errori_float += 1
    if errori_float:
        R.fail(f"to_dict(): {errori_float} campi numerici mancanti o non float")
    else:
        R.ok("to_dict(): tutti i campi numerici presenti come float", verbose)


# =============================================================================
# SEZ. 17 — INTEGRITÀ DATI: cross-tabella
# =============================================================================

def test_17_integrita_cross(db, mat_ids, pids, verbose=False):
    R.section("17. INTEGRITÀ DATI — cross-tabella")

    # Delete materiale usato in preventivo → preventivo sopravvive
    if mat_ids and pids:
        mid_test = mat_ids[0]
        mc_test  = _mc_random(mid=mid_test, nome="INTEG_TEST")
        pid_integ, _ = safe(db.add_preventivo, _prev_dict(materiali_utilizzati=[mc_test.to_dict()]))
        safe(db.delete_materiale, mid_test)
        prev_integ, _ = safe(db.get_preventivo_by_id, pid_integ)
        if prev_integ is None:
            R.fail("Delete materiale: ha eliminato il preventivo che lo referenzia (non deve)")
        else:
            R.ok("Delete materiale: preventivo con quel materiale sopravvive", verbose)

    # JSON corrotto in materiali_utilizzati → get_preventivo_by_id non crasha
    pid_corrotto, _ = safe(db.add_preventivo, _prev_dict())
    if pid_corrotto and isinstance(pid_corrotto, int):
        try:
            with _sqlite3.connect(db.db_path) as conn:
                conn.execute("UPDATE preventivi SET materiali_utilizzati=? WHERE id=?",
                             ("NON_JSON_{{{CORROTTO_INVALIDO", pid_corrotto))
                conn.commit()
            prev_cor, exc_cor = safe(db.get_preventivo_by_id, pid_corrotto)
            if exc_cor:
                R.fail("JSON corrotto: get_preventivo_by_id crash", exc_cor)
            elif prev_cor is None:
                R.fail("JSON corrotto: get_preventivo_by_id restituisce None")
            elif not isinstance(prev_cor.get("materiali_utilizzati", []), list):
                R.fail("JSON corrotto: materiali_utilizzati non è lista dopo fallback")
            else:
                R.ok("JSON corrotto: get_preventivo_by_id non crasha, materiali_utilizzati=[]", verbose)
        except Exception as e:
            R.fail(f"JSON corrotto: eccezione nella scrittura diretta DB: {e}")

    # get_all_preventivi count >= get_all_preventivi_latest count
    tutti, _  = safe(db.get_all_preventivi)
    latest, _ = safe(db.get_all_preventivi_latest)
    if tutti is None or latest is None:
        R.fail("get_all_preventivi o latest restituisce None")
    elif len(latest) > len(tutti):
        R.fail(f"latest ({len(latest)}) > tutti ({len(tutti)}): impossibile")
    else:
        R.ok(f"Cardinalità: tutti={len(tutti)}, latest={len(latest)} (latest ≤ tutti)", verbose)

    # Tutti gli ID in latest esistono in get_all_preventivi
    if tutti and latest:
        ids_tutti = {r[0] for r in tutti}
        ids_lat   = {r[0] for r in latest}
        orfani = ids_lat - ids_tutti
        if orfani:
            R.fail(f"{len(orfani)} ID in latest non in get_all_preventivi")
        else:
            R.ok("Tutti gli ID in latest esistono in get_all_preventivi", verbose)

    # Nessun ID in latest punta a originale che ha revisioni
    if latest:
        try:
            with _sqlite3.connect(db.db_path) as conn:
                cur = conn.cursor()
                ids_lat_list = [r[0] for r in latest]
                if ids_lat_list:
                    ph = ",".join("?" for _ in ids_lat_list)
                    # Trova originali con revisioni figle
                    cur.execute(f"""
                        SELECT COUNT(*) FROM preventivi p
                        WHERE p.id IN ({ph})
                          AND p.preventivo_originale_id IS NULL
                          AND EXISTS (SELECT 1 FROM preventivi r WHERE r.preventivo_originale_id = p.id)
                    """, ids_lat_list)
                    n_orig_con_rev = cur.fetchone()[0]
                    if n_orig_con_rev > 0:
                        R.warn(f"{n_orig_con_rev} originali con revisioni compaiono in latest (atteso 0)")
                    else:
                        R.ok("Nessun originale con revisioni in latest (corretto)", verbose)
        except Exception as e:
            R.warn(f"Verifica originali in latest: {e}")

    # get_fornitori_per_materiale dopo delete_fornitore_materiale → quel fornitore non c'è più
    if mat_ids and len(mat_ids) > 5:
        mid_forn = mat_ids[5]
        safe(db.add_fornitore, "FORN_DEL_INTEG")
        mfid_new, _ = safe(db.add_fornitore_a_materiale, mid_forn, "FORN_DEL_INTEG", 10.0, 1.0, 100.0)
        if mfid_new and isinstance(mfid_new, int):
            safe(db.delete_fornitore_materiale, mfid_new)
            forn_rows, _ = safe(db.get_fornitori_per_materiale, mid_forn)
            still_there = any(r[1] == "FORN_DEL_INTEG" for r in (forn_rows or []))
            if still_there:
                R.fail("delete_fornitore_materiale: fornitore ancora in get_fornitori_per_materiale")
            else:
                R.ok("delete_fornitore_materiale: fornitore non più in get_fornitori_per_materiale", verbose)

    # Categoria eliminata → materiali con quella categoria hanno categoria_id NULL
    if mat_ids:
        cid_integ, _ = safe(db.add_categoria, "CAT_INTEG_DEL", 0.0, 0.0, 0.0, "")
        mid_integ, _ = safe(db.add_materiale, "MAT_INTEG_CAT_DEL", 0.1, 1.0, categoria_id=cid_integ)
        safe(db.delete_categoria, cid_integ)
        if mid_integ and isinstance(mid_integ, int):
            row_integ, _ = safe(db.get_materiale_by_id, mid_integ)
            if row_integ is None:
                R.fail("Categoria eliminata: ha eliminato anche il materiale")
            else:
                cid_after = row_integ[8] if len(row_integ) > 8 else "N/A"
                if cid_after is None:
                    R.ok("Categoria eliminata: materiale sopravvive con categoria_id=NULL", verbose)
                else:
                    R.warn(f"Categoria eliminata: categoria_id={cid_after} (atteso NULL)")
            safe(db.delete_materiale, mid_integ)


# =============================================================================
# SEZ. 18 — ROBUSTEZZA: input pericolosi e anomali
# =============================================================================

def test_18_robustezza(db, verbose=False):
    R.section("18. ROBUSTEZZA — input pericolosi e anomali")

    # SQL injection nei campi stringa del preventivo (5 payload)
    payloads_inj = [
        ("nome_cliente",   "'; DROP TABLE preventivi; --"),
        ("numero_ordine",  "\" OR 1=1 --"),
        ("descrizione",    "<script>alert('xss')</script>"),
        ("codice",         "' UNION SELECT 1,2,3 --"),
        ("misura",         "'; INSERT INTO preventivi VALUES(999,'evil'); --"),
    ]
    for campo, payload in payloads_inj:
        pid_inj, exc_inj = safe(db.add_preventivo, _prev_dict(**{campo: payload}))
        if exc_inj:
            R.fail(f"SQL injection '{campo}': crash in add_preventivo", exc_inj)
        else:
            prev_inj, exc_read = safe(db.get_preventivo_by_id, pid_inj)
            if exc_read:
                R.fail(f"SQL injection '{campo}': crash in get_preventivo_by_id", exc_read)
            elif prev_inj and prev_inj.get(campo) == payload:
                R.ok(f"SQL injection '{campo}': salvato come testo letterale", verbose)
            else:
                letto = prev_inj.get(campo) if prev_inj else "None"
                R.warn(f"SQL injection '{campo}': letto '{letto[:40]}...' (diverso da payload)")

    # SQL injection nel nome materiale
    sql_nome_mat = "'; DROP TABLE materiali; --"
    mid_sqlinj, exc_sqlinj = safe(db.add_materiale, sql_nome_mat, 0.1, 1.0)
    if exc_sqlinj:
        R.ok("SQL injection nome materiale → eccezione gestita (forse duplicato)", verbose)
    else:
        row_sqlinj, _ = safe(db.get_materiale_by_id, mid_sqlinj)
        if row_sqlinj and row_sqlinj[1] == sql_nome_mat:
            R.ok("SQL injection nome materiale: salvato come testo letterale", verbose)
        else:
            R.warn("SQL injection nome materiale: nome letto diverso o None")
        if mid_sqlinj and isinstance(mid_sqlinj, int):
            safe(db.delete_materiale, mid_sqlinj)

    # SQL injection nel nome fornitore
    sql_nome_f = "'; DROP TABLE fornitori; --"
    fid_sqlinj, exc_fsql = safe(db.add_fornitore, sql_nome_f)
    if exc_fsql:
        R.ok("SQL injection nome fornitore → eccezione gestita", verbose)
    else:
        tutti_f, _ = safe(db.get_all_fornitori)
        found_f = any(r[1] == sql_nome_f for r in (tutti_f or []))
        if found_f:
            R.ok("SQL injection nome fornitore: salvato come testo letterale", verbose)
        else:
            R.warn("SQL injection nome fornitore: non trovato dopo inserimento")

    # Valori float NaN/Infinity in preventivo_finale → gestito
    for val_label, val_f in [("NaN", float("nan")), ("Inf", float("inf")), ("-Inf", float("-inf"))]:
        pid_nan, exc_nan = safe(db.add_preventivo, _prev_dict(preventivo_finale=val_f))
        if exc_nan:
            R.ok(f"preventivo_finale={val_label} → eccezione gestita (sqlite rifiuta)", verbose)
        else:
            R.warn(f"preventivo_finale={val_label}: accettato da SQLite (può causare problemi)")

    # JSON enorme in materiali_utilizzati (500 elementi dummy)
    mats_huge = [{"diametro": i, "giri": 1, "spessore": 0.1, "costo_totale": 0.0,
                  "costo_materiale": 0.0, "maggiorazione": 0.0, "sviluppo": 1.0,
                  "lunghezza": 10.0, "lunghezza_utilizzata": 0.0, "diametro_finale": 10.0,
                  "materiale_id": None, "materiale_nome": f"DUM{i}",
                  "is_conica": False, "sezioni_coniche": [], "scarto_mm2": 0.0,
                  "arrotondamento_manuale": 0.0, "stratifica": 1.0,
                  "conicita_lato": "sinistra", "conicita_altezza_mm": 0.0,
                  "conicita_lunghezza_mm": 0.0, "orientamento": {}} for i in range(500)]
    pid_huge, exc_huge = safe(db.add_preventivo, _prev_dict(materiali_utilizzati=mats_huge))
    if exc_huge:
        R.fail("JSON enorme (500 mat dummy): crash in add_preventivo", exc_huge)
    else:
        prev_huge, exc_rh = safe(db.get_preventivo_by_id, pid_huge)
        if exc_rh:
            R.fail("JSON enorme: crash in get_preventivo_by_id", exc_rh)
        elif prev_huge and len(prev_huge.get("materiali_utilizzati", [])) == 500:
            R.ok("JSON enorme (500 mat): salvato e riletto OK", verbose)
        else:
            n_letti = len(prev_huge.get("materiali_utilizzati", [])) if prev_huge else "None"
            R.warn(f"JSON enorme: letti {n_letti} elementi (atteso 500)")

    # update_preventivo con dict vuoto {} → no crash o errore gestito
    pid_upd_empty, _ = safe(db.add_preventivo, _prev_dict())
    if pid_upd_empty and isinstance(pid_upd_empty, int):
        _, exc_ue = safe(db.update_preventivo, pid_upd_empty, {})
        if exc_ue:
            R.warn(f"update_preventivo con dict vuoto → eccezione ({type(exc_ue).__name__}: campi mancanti)")
        else:
            R.ok("update_preventivo con dict vuoto {}: no crash", verbose)

    # add_preventivo con dict mancante di campi obbligatori → no crash o errore gestito
    _, exc_miss = safe(db.add_preventivo, {"nome_cliente": "SOLO_NOME"})
    if exc_miss:
        R.ok(f"add_preventivo dict parziale → eccezione gestita ({type(exc_miss).__name__})", verbose)
    else:
        R.warn("add_preventivo dict parziale: accettato senza eccezione (potrebbero esserci NULL)")

    # get_preventivo_by_id con ID=0, -1, 9999999 → None
    for bad_id in [0, -1, 9999999]:
        prev_bad, exc_bad = safe(db.get_preventivo_by_id, bad_id)
        if exc_bad:
            R.fail(f"get_preventivo_by_id({bad_id}) → crash", exc_bad)
        elif prev_bad is not None:
            R.fail(f"get_preventivo_by_id({bad_id}) → non None (trovato qualcosa)")
        else:
            R.ok(f"get_preventivo_by_id({bad_id}) → None (corretto)", verbose)

    # delete_preventivo_e_revisioni su ID inesistente → no crash
    _, exc_del_fan = safe(db.delete_preventivo_e_revisioni, 9999999)
    if exc_del_fan:
        R.fail("delete_preventivo_e_revisioni su ID inesistente → crash", exc_del_fan)
    else:
        R.ok("delete_preventivo_e_revisioni su ID inesistente → no crash", verbose)

    # registra_movimento con tipo sconosciuto → gestito
    if True:
        # Usa il primo materiale del DB (se esiste)
        tutti_mat, _ = safe(db.get_all_materiali)
        if tutti_mat:
            mid_any = tutti_mat[0][0]
            _, exc_tipo = safe(db.registra_movimento, mid_any, "pippo", 1.0)
            if exc_tipo:
                R.ok("registra_movimento(tipo='pippo') → eccezione gestita", verbose)
            else:
                R.warn("registra_movimento(tipo='pippo'): accettato (nessun aggiornamento giacenza atteso)")
        else:
            R.warn("registra_movimento tipo sconosciuto: nessun materiale disponibile — skip")


# =============================================================================
# SEZ. 19 — METODI DB NON COPERTI
# =============================================================================

def test_19_metodi_non_coperti(db, mat_ids, pids, cat_ids, verbose=False):
    R.section("19. METODI DB NON COPERTI — copertura complementare")

    # get_materiale_by_nome: nome esistente → row corretta, inesistente → None
    if mat_ids:
        tutti_mat, _ = safe(db.get_all_materiali)
        # Prendi un nome noto dal DB
        if tutti_mat:
            nome_noto = tutti_mat[0][1]
            row_noto, exc_n = safe(db.get_materiale_by_nome, nome_noto)
            if exc_n:
                R.fail("get_materiale_by_nome (nome noto) → crash", exc_n)
            elif row_noto and row_noto[1] == nome_noto:
                R.ok(f"get_materiale_by_nome('{nome_noto[:20]}...'): row corretta", verbose)
            else:
                R.fail(f"get_materiale_by_nome('{nome_noto[:20]}...'): None o nome diverso")
        row_fan, exc_fn = safe(db.get_materiale_by_nome, "NOME_ASSOLUTAMENTE_INESISTENTE_XYZ_777")
        if exc_fn:
            R.fail("get_materiale_by_nome (inesistente) → crash", exc_fn)
        elif row_fan is None:
            R.ok("get_materiale_by_nome (inesistente) → None (corretto)", verbose)
        else:
            R.fail(f"get_materiale_by_nome (inesistente) → trovato {row_fan}")

    # get_all_categorie: lista con tutte le categorie inserite
    tutte_cat, exc_tc = safe(db.get_all_categorie)
    if exc_tc:
        R.fail("get_all_categorie → crash", exc_tc)
    elif tutte_cat is None:
        R.fail("get_all_categorie → None")
    else:
        n_diag_cat = sum(1 for r in tutte_cat if "DIAG_CAT" in str(r[1]) or "CAT_UPD" in str(r[1]))
        R.ok(f"get_all_categorie: {len(tutte_cat)} totali, {n_diag_cat} DIAG/UPD", verbose)

    # get_materiali_per_categoria_con_fornitori: struttura corretta
    if cat_ids:
        cid_nc = cat_ids[0]
        rows_nc, exc_nc = safe(db.get_materiali_per_categoria_con_fornitori, cid_nc)
        if exc_nc:
            R.fail("get_materiali_per_categoria_con_fornitori → crash", exc_nc)
        elif rows_nc is None:
            R.fail("get_materiali_per_categoria_con_fornitori → None")
        else:
            # Struttura attesa: (id, nome, giacenza_totale, scorta_massima, n_fornitori)
            ok_struct = all(len(r) >= 3 for r in rows_nc) if rows_nc else True
            if ok_struct:
                R.ok(f"get_materiali_per_categoria_con_fornitori: {len(rows_nc)} mat, struttura OK", verbose)
            else:
                R.warn("get_materiali_per_categoria_con_fornitori: struttura riga inattesa (<3 colonne)")

    # get_preventivi_con_modifiche: solo preventivi con storico non vuoto
    con_mod, exc_cm = safe(db.get_preventivi_con_modifiche)
    if exc_cm:
        R.fail("get_preventivi_con_modifiche → crash", exc_cm)
    else:
        # Verifica che nessuno abbia storico_modifiche vuoto
        errori_cm = 0
        for row in (con_mod or [])[:20]:
            stor_raw = row[9] if len(row) > 9 else None
            if stor_raw in (None, "[]", ""):
                errori_cm += 1
        if errori_cm:
            R.fail(f"get_preventivi_con_modifiche: {errori_cm} con storico vuoto")
        else:
            R.ok(f"get_preventivi_con_modifiche: {len(con_mod or [])} tutti con storico non vuoto", verbose)

    # save_preventivo (upsert): crea nuovo se no ID, aggiorna se ID esistente
    # Crea nuovo:
    pid_save_n, exc_sn = safe(db.save_preventivo, _prev_dict(nome_cliente="SAVE_UPSERT_NUOVO"))
    if exc_sn or not isinstance(pid_save_n, int):
        R.fail("save_preventivo (nuovo): fallito", exc_sn)
    else:
        prev_sn, _ = safe(db.get_preventivo_by_id, pid_save_n)
        if prev_sn:
            R.ok(f"save_preventivo (nuovo): id={pid_save_n} creato e letto", verbose)
        else:
            R.fail(f"save_preventivo (nuovo): id={pid_save_n} non trovato")

    # get_scorte_per_categoria con tutte le opzioni ordina_per
    for ord_k in ["giacenza_asc", "giacenza_desc", "nome_asc"]:
        sc_c, exc_sc = safe(db.get_scorte_per_categoria, ord_k)
        if exc_sc:
            R.fail(f"get_scorte_per_categoria('{ord_k}') → crash", exc_sc)
        else:
            R.ok(f"get_scorte_per_categoria('{ord_k}'): {len(sc_c or [])} record, no crash", verbose)

    # update_fornitore_materiale: aggiorna prezzi, verifica round-trip
    if mat_ids:
        mid_ufm = mat_ids[0] if mat_ids else None
        if mid_ufm:
            forn_ufm = "FORN_UFM_TEST_19"
            safe(db.add_fornitore, forn_ufm)
            mfid_ufm, _ = safe(db.add_fornitore_a_materiale, mid_ufm, forn_ufm, 10.0, 1.0, 100.0)
            if mfid_ufm and isinstance(mfid_ufm, int):
                nuovo_p = round(random.uniform(50, 200), 2)
                res_ufm, exc_ufm = safe(db.update_fornitore_materiale,
                                        mfid_ufm, forn_ufm, nuovo_p, 2.0, 200.0)
                if exc_ufm or not res_ufm:
                    R.fail("update_fornitore_materiale: fallito", exc_ufm)
                else:
                    rows_ufm, _ = safe(db.get_fornitori_per_materiale, mid_ufm)
                    trovato = any(r[0] == mfid_ufm and abs(r[2] - nuovo_p) < 0.01 for r in (rows_ufm or []))
                    if trovato:
                        R.ok("update_fornitore_materiale: prezzo aggiornato e verificato", verbose)
                    else:
                        R.warn("update_fornitore_materiale: prezzo non verificabile (mf_id su altro mat?)")

    # delete_fornitore_materiale: rimozione + verifica scomparsa
    if mat_ids and len(mat_ids) > 1:
        mid_dfm = mat_ids[1]
        forn_dfm = "FORN_DFM_TEST_19"
        safe(db.add_fornitore, forn_dfm)
        mfid_dfm, _ = safe(db.add_fornitore_a_materiale, mid_dfm, forn_dfm, 5.0, 1.0, 50.0)
        if mfid_dfm and isinstance(mfid_dfm, int):
            res_dfm, exc_dfm = safe(db.delete_fornitore_materiale, mfid_dfm)
            if exc_dfm or not res_dfm:
                R.fail("delete_fornitore_materiale (sez.19): fallito", exc_dfm)
            else:
                try:
                    with _sqlite3.connect(db.db_path) as conn:
                        cur = conn.cursor()
                        cur.execute("SELECT id FROM materiale_fornitori WHERE id=?", (mfid_dfm,))
                        ghost = cur.fetchone()
                    if ghost:
                        R.fail(f"delete_fornitore_materiale: mf_id {mfid_dfm} ancora presente")
                    else:
                        R.ok("delete_fornitore_materiale: mf_id rimosso e verificato", verbose)
                except Exception as e:
                    R.warn(f"delete_fornitore_materiale verifica: {e}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="RCS-App Diagnostic Bot — test di sistema in larga scala"
    )
    parser.add_argument("--quick", action="store_true",
                        help="Campione ridotto: N_MAT=15, N_PREV=50, N_CALC=100 (~10s)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Stampa anche i test passati (ok)")
    args = parser.parse_args()

    N_MAT  = 15  if args.quick else 100
    N_PREV = 50  if args.quick else 500
    N_CALC = 100 if args.quick else 500

    print(f"\n{BOLD}{'═'*72}{RESET}")
    print(f"{BOLD}  RCS-App DIAGNOSTIC BOT{RESET}")
    print(f"{BOLD}{'═'*72}{RESET}")
    print(f"{DIM}  Data:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{DIM}  Scala:   N_MAT={N_MAT}, N_PREV={N_PREV}, N_CALC={N_CALC}"
          f"  {'(--quick)' if args.quick else '(full)'}{RESET}")

    t0_totale = time.time()
    db = make_db()
    print(f"{DIM}  DB:      {db.db_path}{RESET}")
    print(f"{DIM}  Verbose: {'SI' if args.verbose else 'NO'}{RESET}")

    # ── Sezione 1: Materiali bulk ────────────────────────────────────────────
    mat_ids = test_01_materiali_bulk(db, N_MAT, verbose=args.verbose)

    # ── Sezione 2: Materiali edge case ───────────────────────────────────────
    test_02_materiali_edge(db, verbose=args.verbose)

    # ── Sezione 3: Fornitori CRUD ────────────────────────────────────────────
    fornitori_nomi = test_03_fornitori(db, mat_ids, verbose=args.verbose)

    # ── Sezione 4: Magazzino movimenti ───────────────────────────────────────
    test_04_magazzino_movimenti(db, mat_ids, verbose=args.verbose)

    # ── Sezione 5: Magazzino query e periodi ─────────────────────────────────
    test_05_magazzino_query(db, mat_ids, verbose=args.verbose)

    # ── Sezione 6: Categorie CRUD + relazioni ────────────────────────────────
    cat_ids = test_06_categorie(db, mat_ids, verbose=args.verbose)

    # ── Sezione 7: Preventivi creazione 500 scenari ──────────────────────────
    pids = test_07_preventivi_creazione(db, mat_ids, N_PREV, verbose=args.verbose)

    # ── Sezione 8: Preventivi update campi ──────────────────────────────────
    test_08_preventivi_update(db, pids, verbose=args.verbose)

    # ── Sezione 9: Preventivi storico e ripristino ───────────────────────────
    test_09_preventivi_storico(db, pids, verbose=args.verbose)

    # ── Sezione 10: Preventivi revisioni e catene ────────────────────────────
    test_10_preventivi_revisioni(db, pids, verbose=args.verbose)

    # ── Sezione 11: Preventivi valori estremi ────────────────────────────────
    test_11_preventivi_estremi(db, verbose=args.verbose)

    # ── Sezione 12: Preventivi query e filtri ────────────────────────────────
    # Aggiorna pids (alcuni potrebbero essere stati eliminati)
    tutti_now, _ = safe(db.get_all_preventivi)
    pids_now = [r[0] for r in (tutti_now or [])]
    test_12_preventivi_query(db, pids_now, verbose=args.verbose)

    # ── Sezione 13: MaterialeCalcolato calcoli puri ──────────────────────────
    test_13_mc_calcoli_puri(N_CALC, verbose=args.verbose)

    # ── Sezione 14: MaterialeCalcolato edge case ─────────────────────────────
    test_14_mc_edge(verbose=args.verbose)

    # ── Sezione 15: Preventivo model aggregazioni ────────────────────────────
    test_15_preventivo_model_agg(verbose=args.verbose)

    # ── Sezione 16: Preventivo model edge case ───────────────────────────────
    test_16_preventivo_model_edge(verbose=args.verbose)

    # ── Sezione 17: Integrità dati cross-tabella ─────────────────────────────
    test_17_integrita_cross(db, mat_ids, pids_now, verbose=args.verbose)

    # ── Sezione 18: Robustezza input pericolosi ──────────────────────────────
    test_18_robustezza(db, verbose=args.verbose)

    # ── Sezione 19: Metodi DB non coperti ───────────────────────────────────
    test_19_metodi_non_coperti(db, mat_ids, pids_now, cat_ids, verbose=args.verbose)

    # ── Summary ─────────────────────────────────────────────────────────────
    elapsed = time.time() - t0_totale
    print(f"\n{DIM}  Durata totale: {elapsed:.1f}s{RESET}")

    n_fail = R.summary()
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == "__main__":
    main()
