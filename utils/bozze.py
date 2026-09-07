#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Bozze automatiche dei preventivi aperti.
Uso riservato esclusivamente a RCS

Scopo: se il PC si spegne (aggiornamento di Windows, mancanza di corrente,
blocco) mentre ci sono preventivi aperti e non salvati, il lavoro non deve
sparire nel nulla.

Ogni finestra di preventivo aperta salva periodicamente il proprio contenuto in
un file sul disco LOCALE (mai sulla cartella di rete). Al riavvio, se la
chiusura precedente non è stata regolare, le bozze rimaste vengono presentate
all'utente.

Le bozze NON sono preventivi: non finiscono nel database e non hanno un numero.
Servono solo a non perdere il lavoro fatto.
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta

GIORNI_CONSERVAZIONE = 30


def _log():
    return logging.getLogger('rcs')


def cartella_bozze():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cartella = os.path.join(base, "logs", "bozze")
    os.makedirs(cartella, exist_ok=True)
    return cartella


def _percorso(chiave):
    sicura = "".join(c for c in str(chiave) if c.isalnum() or c in "-_")
    return os.path.join(cartella_bozze(), "bozza_{}.json".format(sicura or "senza_nome"))


def salva_bozza(chiave, dati, modalita="nuovo", preventivo_id=None):
    """Salva (o aggiorna) la bozza di una finestra aperta.

    'chiave' identifica la finestra; 'dati' è il contenuto del preventivo così
    come verrebbe salvato nel database."""
    try:
        contenuto = {
            "salvata_il": datetime.now().isoformat(timespec="seconds"),
            "modalita": modalita,
            "preventivo_id": preventivo_id,
            "dati": dati,
        }
        percorso = _percorso(chiave)
        temporaneo = percorso + ".tmp"
        with open(temporaneo, "w", encoding="utf-8") as f:
            json.dump(contenuto, f, ensure_ascii=False, indent=2, default=str)
        os.replace(temporaneo, percorso)
        return True
    except Exception as e:
        _log().warning("Bozza non salvata (%s): %s", chiave, e)
        return False


def elimina_bozza(chiave):
    """Toglie la bozza: il preventivo è stato salvato o chiuso di proposito."""
    try:
        percorso = _percorso(chiave)
        if os.path.exists(percorso):
            os.remove(percorso)
    except Exception:
        pass


def elenca_bozze():
    """Ritorna le bozze presenti, dalla più recente."""
    trovate = []
    try:
        for nome in os.listdir(cartella_bozze()):
            if not (nome.startswith("bozza_") and nome.endswith(".json")):
                continue
            percorso = os.path.join(cartella_bozze(), nome)
            try:
                with open(percorso, "r", encoding="utf-8") as f:
                    contenuto = json.load(f)
                contenuto["_file"] = percorso
                trovate.append(contenuto)
            except Exception:
                continue
    except Exception:
        return []
    trovate.sort(key=lambda c: c.get("salvata_il", ""), reverse=True)
    return trovate


def descrivi_bozza(bozza):
    """Una riga comprensibile che descrive la bozza, per mostrarla all'utente."""
    dati = bozza.get("dati") or {}
    quando = bozza.get("salvata_il", "")
    try:
        quando = datetime.fromisoformat(quando).strftime("%d/%m/%Y alle %H:%M")
    except Exception:
        pass

    cliente = (dati.get("nome_cliente") or "").strip() or "cliente non indicato"
    ordine = (dati.get("numero_ordine") or "").strip()
    descrizione = (dati.get("descrizione") or "").strip()
    materiali = dati.get("materiali_utilizzati") or []
    try:
        prezzo = float(dati.get("prezzo_cliente") or 0)
    except (TypeError, ValueError):
        prezzo = 0.0

    pezzi = [cliente]
    if ordine:
        pezzi.append("ordine {}".format(ordine))
    if descrizione:
        pezzi.append(descrizione[:40])
    pezzi.append("{} material{}".format(len(materiali), "e" if len(materiali) == 1 else "i"))
    if prezzo:
        pezzi.append("€ {:.2f}".format(prezzo))

    return "{} — {}".format(quando, " · ".join(pezzi))


def pulisci_vecchie(giorni=GIORNI_CONSERVAZIONE):
    """Elimina le bozze più vecchie di 'giorni'."""
    limite = datetime.now() - timedelta(days=giorni)
    for bozza in elenca_bozze():
        try:
            if datetime.fromisoformat(bozza.get("salvata_il", "")) < limite:
                os.remove(bozza["_file"])
        except Exception:
            continue
