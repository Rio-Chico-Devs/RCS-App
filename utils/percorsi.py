#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Le cartelle usate dall'applicazione, decise in un posto solo.
Uso riservato esclusivamente a RCS

Perche' un modulo apposta
-------------------------
Sapere dov'e' la cartella dell'applicazione non e' banale: quando il programma
gira come eseguibile compilato (.exe) il punto di riferimento e' l'eseguibile
stesso, mentre durante lo sviluppo e' la posizione dei file .py. Questa
distinzione era ripetuta in quattro moduli diversi.

Ripetere una logica significa doverla correggere in quattro punti, e prima o
poi correggerla solo in tre. Qui sta scritta una volta sola.
"""

import os
import sys


def cartella_applicazione():
    """La cartella dell'applicazione.

    Se il programma e' stato compilato in un eseguibile, e' la cartella che
    contiene l'eseguibile; altrimenti la cartella del progetto."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # utils/percorsi.py -> utils -> cartella del progetto
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _sottocartella(*parti):
    """Costruisce (e crea) una cartella dentro quella dell'applicazione."""
    percorso = os.path.join(cartella_applicazione(), *parti)
    os.makedirs(percorso, exist_ok=True)
    return percorso


def cartella_registri():
    """Dove finiscono i registri tecnici, sul disco locale di questo PC."""
    return _sottocartella("logs")


def cartella_bozze():
    """Dove finiscono le bozze dei preventivi aperti."""
    return _sottocartella("logs", "bozze")


def cartella_copie_locali():
    """Copie di sicurezza tenute sul disco locale, per non dipendere solo
    dalla cartella di rete."""
    return _sottocartella("backup_locale")
