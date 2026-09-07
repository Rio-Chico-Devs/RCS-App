#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Responsive UI Metrics - Costanti adattive basate sulla risoluzione schermo
Uso riservato esclusivamente a RCS
"""

from PyQt5.QtWidgets import QApplication, QTabBar
from PyQt5.QtCore import QSize, Qt

from ui.misure import larghezza_linguetta


class BarraLinguette(QTabBar):
    """Linguette che si adattano al testo, su qualsiasi schermo.

    Perche' serve: i fogli di stile dell'applicazione impostano sulle linguette
    un carattere piu' grande e in grassetto ("font-size: 13px; font-weight:
    600") e un riempimento laterale. Qt pero' calcola la larghezza della
    linguetta con il carattere del widget, mentre disegna il testo con quello
    del foglio di stile: il testo disegnato risulta piu' largo dello spazio
    calcolato e viene tagliato ai due lati ("Scorte" diventa "cort").
    Quanto si perde dipende dalla risoluzione e dai caratteri di sistema,
    quindi il difetto si vede su alcuni computer e non su altri.

    Qui la larghezza viene ricalcolata sul testo effettivo, con un margine per
    il riempimento laterale, e non e' mai inferiore a quella proposta da Qt."""

    def __init__(self, margine=56, grassetto=True, parent=None):
        super().__init__(parent)
        self._margine = margine
        # Stesso carattere che verra' disegnato: cosi' la misura corrisponde.
        if grassetto:
            carattere = self.font()
            carattere.setBold(True)
            self.setFont(carattere)
        self.setElideMode(Qt.ElideNone)       # mai puntini di sospensione
        self.setUsesScrollButtons(False)      # mai frecce di scorrimento

    def tabSizeHint(self, indice):
        dimensione = super().tabSizeHint(indice)
        larghezza = larghezza_linguetta(
            self.tabText(indice), self.fontMetrics(),
            dimensione.width(), self._margine)
        return QSize(larghezza, dimensione.height())


def adatta_linguette(tab_widget, margine=56, grassetto=True):
    """Applica BarraLinguette a un QTabWidget.

    Va chiamata PRIMA di aggiungere le schede: QTabWidget.setTabBar() sostituisce
    la barra esistente."""
    try:
        tab_widget.setTabBar(BarraLinguette(margine=margine, grassetto=grassetto))
    except Exception:
        # Se qualcosa andasse storto, meglio linguette imperfette che una
        # finestra che non si apre.
        try:
            tab_widget.tabBar().setElideMode(Qt.ElideNone)
            tab_widget.tabBar().setUsesScrollButtons(False)
        except Exception:
            pass
    return tab_widget


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
