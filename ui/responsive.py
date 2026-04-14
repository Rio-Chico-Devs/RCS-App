#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Responsive UI Metrics - Costanti adattive basate sulla risoluzione schermo
Uso riservato esclusivamente a RCS
"""

from PyQt5.QtWidgets import QApplication


def get_metrics():
    """
    Ritorna un dizionario di valori UI adattivi in base alla risoluzione
    del monitor primario.  Soglia: altezza <= 800 px  O  larghezza <= 1400 px.
    """
    screen = QApplication.primaryScreen().availableGeometry()
    small = screen.height() <= 800 or screen.width() <= 1400

    if small:
        return {
            'small':  True,
            'mo':     16,   # margin outer (margine esterno layout principale)
            'mi':     12,   # margin inner (margine interno GroupBox / card)
            'mi_top': 18,   # margin top GroupBox (tiene il titolo visibile)
            'sm':     12,   # spacing main (spacing tra sezioni principali)
            'sc':     10,   # spacing content (spacing tra elementi)
            'sf':      8,   # spacing form (spacing righe form)
            'bh':     36,   # button height principale
            'bhs':    28,   # button height secondario / piccolo
            'fh':     30,   # input field height
            'ft':     18,   # font size titolo
            'fst':    14,   # font size sottotitolo
            'fb':     13,   # font size body
            'fxs':    11,   # font size extra-small
            'iw':    370,   # larghezza sezione input (rimossa fixed, usata come minimum)
            'dw':    860,   # larghezza dialog
            'dh':    580,   # altezza dialog
        }
    else:
        return {
            'small':  False,
            'mo':     30,
            'mi':     25,
            'mi_top': 28,
            'sm':     20,
            'sc':     16,
            'sf':     16,
            'bh':     46,
            'bhs':    36,
            'fh':     36,
            'ft':     24,
            'fst':    16,
            'fb':     14,
            'fxs':    12,
            'iw':    450,
            'dw':   1000,
            'dh':    700,
        }
