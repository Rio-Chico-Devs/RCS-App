#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Registro delle schermate di preventivo aperte.
Uso riservato esclusivamente a RCS

A cosa serve
------------
Le finestre di preventivo vengono create senza "genitore" (per evitare
problemi di ridimensionamento). In PyQt questo significa che restano vive solo
finché il programma conserva un riferimento: prima le finestre venivano tutte
assegnate alla stessa variabile, quindi aprendone una seconda la prima veniva
distrutta insieme al lavoro non ancora salvato.

Qui i riferimenti vengono tenuti tutti insieme, così se ne possono aprire
quante se ne vuole. Le finestre chiuse vengono tolte dall'elenco, per non
tenere occupata memoria inutilmente.
"""

import logging

_aperte = []


def _viva(finestra):
    """True se la finestra esiste ancora ed è visibile."""
    try:
        return bool(finestra.isVisible())
    except RuntimeError:
        return False   # oggetto Qt già distrutto
    except Exception:
        return False


def pulisci():
    """Toglie dall'elenco le schermate chiuse, liberando le risorse."""
    vive = [f for f in _aperte if _viva(f)]
    if len(vive) != len(_aperte):
        logging.getLogger('rcs').debug(
            "Schermate preventivo: %d chiuse, %d ancora aperte",
            len(_aperte) - len(vive), len(vive))
    _aperte[:] = vive
    return _aperte


def registra(finestra):
    """Prende in carico una nuova schermata di preventivo.

    Senza questo, la finestra verrebbe distrutta appena il programma smette di
    riferirsi a lei."""
    pulisci()
    if not any(f is finestra for f in _aperte):
        _aperte.append(finestra)
    return finestra


def dimentica(finestra):
    """Toglie una schermata dall'elenco (dopo la chiusura)."""
    _aperte[:] = [f for f in _aperte if f is not finestra]


def aperte():
    """Elenco delle schermate attualmente aperte, dalla più vecchia."""
    return list(pulisci())


def quante():
    return len(aperte())


def piu_recente():
    """L'ultima schermata aperta, o None."""
    voci = aperte()
    return voci[-1] if voci else None


def descrivi(finestra):
    """Come chiamare un preventivo aperto parlandone all'utente."""
    try:
        nome = (finestra.get_dati_cliente().get('nome_cliente') or '').strip()
    except Exception:
        nome = ''
    return nome if nome else "cliente non ancora indicato"


def aggiorna_prezzi_ovunque():
    """Aggiorna i prezzi dei materiali in tutte le schermate aperte."""
    for finestra in aperte():
        try:
            finestra.aggiorna_prezzi_materiali()
        except Exception:
            continue
