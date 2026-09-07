#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Diagnostica: capire cosa è successo quando qualcosa va storto.
Uso riservato esclusivamente a RCS

Tre strumenti, tutti scritti sul disco LOCALE del singolo PC (mai sulla
cartella di rete, che è la parte fragile):

  1. Marcatore di sessione  -> dice se l'ultima chiusura è stata regolare
                               oppure se il PC/l'app sono stati terminati di
                               colpo (aggiornamento Windows, mancanza di
                               corrente, blocco).
  2. Registro delle scritture -> una riga leggibile per ogni salvataggio, così
                               si sa sempre qual è stata l'ultima operazione
                               prima di un problema.
  3. Eventi di Windows      -> quando si rileva un guasto, va a leggere nel
                               registro eventi di Windows se in quelle ore ci
                               sono stati riavvii anomali, disconnessioni di
                               rete o errori del disco.
"""

import getpass
import json
import logging
import os
import platform
import subprocess
import sys
from datetime import datetime, timedelta

NOME_MARCATORE = "sessione_in_corso.json"

# Eventi di Windows che spiegano un danneggiamento del database.
# (codice, descrizione in italiano semplice)
EVENTI_INTERESSANTI = {
    41: "Il PC si è riavviato senza essere spento correttamente "
        "(mancanza di corrente, blocco o spegnimento forzato)",
    6008: "Spegnimento inatteso del PC",
    1074: "Riavvio o spegnimento richiesto da un programma "
          "(tipicamente un aggiornamento di Windows)",
    7: "Errore sul disco: settore danneggiato",
    51: "Errore durante una scrittura sul disco",
    50: "Errore di scrittura ritardata (spesso su unità di rete)",
    30800: "Connessione alla cartella di rete persa",
    30801: "Connessione alla cartella di rete interrotta",
}


def _log():
    return logging.getLogger('rcs')


def cartella_locale():
    """Cartella dei log sul disco locale di questo PC."""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cartella = os.path.join(base, "logs")
    os.makedirs(cartella, exist_ok=True)
    return cartella


def _utente():
    try:
        return getpass.getuser()
    except Exception:
        return "?"


# ---------------------------------------------------------------------------
# 1. Marcatore di sessione: la chiusura precedente è stata regolare?
# ---------------------------------------------------------------------------

def _percorso_marcatore():
    return os.path.join(cartella_locale(), NOME_MARCATORE)


def segna_avvio(db_path=""):
    """Scrive il marcatore di sessione in corso e riferisce com'è andata la
    volta precedente.

    Ritorna un dizionario:
      chiusura_precedente_regolare : True/False/None (None = prima volta)
      sessione_precedente          : i dati della sessione interrotta, se c'è
    """
    esito = {"chiusura_precedente_regolare": None, "sessione_precedente": None}
    percorso = _percorso_marcatore()

    try:
        if os.path.exists(percorso):
            # Il marcatore è ancora lì: la volta scorsa non si è chiuso bene.
            try:
                with open(percorso, "r", encoding="utf-8") as f:
                    esito["sessione_precedente"] = json.load(f)
            except Exception:
                esito["sessione_precedente"] = {}
            esito["chiusura_precedente_regolare"] = False
            _log().warning(
                "CHIUSURA ANOMALA rilevata: la sessione precedente non è stata "
                "chiusa regolarmente (dati: %s)", esito["sessione_precedente"])
        elif os.path.exists(os.path.join(cartella_locale(), ".gia_avviato")):
            esito["chiusura_precedente_regolare"] = True

        # Segna che ora c'è una sessione aperta
        with open(percorso, "w", encoding="utf-8") as f:
            json.dump({
                "avvio": datetime.now().isoformat(timespec="seconds"),
                "pc": platform.node(),
                "utente": _utente(),
                "pid": os.getpid(),
                "database": db_path,
            }, f, ensure_ascii=False, indent=2)

        # Traccia che almeno un avvio c'è stato (per distinguere la prima volta)
        with open(os.path.join(cartella_locale(), ".gia_avviato"), "w") as f:
            f.write("1")
    except Exception as e:
        _log().error("Marcatore di sessione non scrivibile: %s", e)

    return esito


def segna_chiusura_regolare():
    """Toglie il marcatore: la chiusura è avvenuta correttamente."""
    try:
        percorso = _percorso_marcatore()
        if os.path.exists(percorso):
            os.remove(percorso)
    except Exception as e:
        _log().error("Impossibile rimuovere il marcatore di sessione: %s", e)


# ---------------------------------------------------------------------------
# 2. Registro delle scritture
# ---------------------------------------------------------------------------

def _percorso_registro():
    return os.path.join(cartella_locale(),
                        "scritture_{}.log".format(datetime.now().strftime("%Y%m")))


def registra_scrittura(operazione, dettaglio="", esito="ok", durata_ms=None):
    """Aggiunge una riga leggibile al registro delle scritture.

    Formato pensato per essere capito a colpo d'occhio, es.:
    03/09/2026 16:57:58 | PC-UFFICIO | mario | add_preventivo | id 108 | ok | 42 ms
    """
    try:
        riga = "{} | {} | {} | {} | {} | {}{}\n".format(
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            platform.node(), _utente(), operazione,
            dettaglio or "-", esito,
            " | {} ms".format(round(durata_ms)) if durata_ms is not None else "")
        with open(_percorso_registro(), "a", encoding="utf-8") as f:
            f.write(riga)
    except Exception:
        pass  # il registro non deve mai bloccare un salvataggio


def ultime_scritture(quante=10):
    """Ritorna le ultime righe del registro (per mostrarle all'utente)."""
    try:
        with open(_percorso_registro(), "r", encoding="utf-8") as f:
            righe = f.readlines()
        return [r.strip() for r in righe[-quante:]]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# 3. Eventi di Windows
# ---------------------------------------------------------------------------

def eventi_windows(ore=48, massimo=40):
    """Legge dal registro eventi di Windows i fatti che possono spiegare un
    danneggiamento: riavvii anomali, aggiornamenti che hanno spento il PC,
    errori del disco, cadute della cartella di rete.

    Ritorna una lista di descrizioni in italiano semplice. Lista vuota se non
    siamo su Windows o se la lettura non è possibile."""
    if os.name != "nt":
        return []

    codici = ",".join(str(c) for c in EVENTI_INTERESSANTI)
    query = ("*[System[(EventID={}) and "
             "TimeCreated[timediff(@SystemTime) <= {}]]]").format(
        " or EventID=".join(str(c) for c in EVENTI_INTERESSANTI),
        int(ore * 3600 * 1000))

    try:
        completato = subprocess.run(
            ["wevtutil", "qe", "System", "/q:" + query,
             "/f:text", "/rd:true", "/c:" + str(massimo)],
            capture_output=True, text=True, timeout=25,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        uscita = completato.stdout or ""
    except Exception as e:
        _log().warning("Lettura del registro eventi di Windows non riuscita: %s", e)
        return []

    trovati = []
    blocco = {}
    for riga in uscita.splitlines():
        riga = riga.strip()
        if riga.startswith("Event ID:"):
            blocco = {"id": riga.split(":", 1)[1].strip()}
        elif riga.startswith("Date:") and blocco:
            blocco["quando"] = riga.split(":", 1)[1].strip()
        elif riga.startswith("Description:") and blocco:
            try:
                codice = int(blocco.get("id", "0"))
            except ValueError:
                codice = 0
            descrizione = EVENTI_INTERESSANTI.get(codice)
            if descrizione:
                trovati.append("{} — {}".format(
                    blocco.get("quando", "data sconosciuta"), descrizione))
            blocco = {}

    _log().info("Eventi di Windows rilevanti nelle ultime %d ore: %d", ore, len(trovati))
    for t in trovati:
        _log().info("  EVENTO WINDOWS: %s", t)
    return trovati


# ---------------------------------------------------------------------------
# Riepilogo comprensibile
# ---------------------------------------------------------------------------

def riepilogo_avvio(stato_sessione, eventi=None):
    """Costruisce un testo semplice da mostrare o da mettere nel log, che
    spiega in italiano cosa è successo tra la sessione precedente e questa."""
    parti = []

    if stato_sessione.get("chiusura_precedente_regolare") is False:
        precedente = stato_sessione.get("sessione_precedente") or {}
        quando = precedente.get("avvio", "data sconosciuta")
        pc = precedente.get("pc", "?")
        parti.append(
            "L'ultima sessione (avviata il {} su {}) NON è stata chiusa "
            "regolarmente: il programma è stato interrotto senza passare dalla "
            "chiusura normale.".format(quando, pc))

    if eventi:
        parti.append("Nel frattempo Windows ha registrato:")
        for e in eventi:
            parti.append("  • " + e)

    return "\n".join(parti)
