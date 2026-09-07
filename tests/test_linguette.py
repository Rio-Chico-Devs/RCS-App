#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del calcolo della larghezza delle linguette.

Il difetto corretto: i fogli di stile impostano sulle linguette un carattere
piu' grande e in grassetto, ma Qt calcola la larghezza con il carattere del
widget. Il testo disegnato risultava piu' largo dello spazio calcolato e
veniva tagliato ai due lati ("Scorte" -> "cort"), in misura diversa a seconda
della risoluzione dello schermo.

Qt non e' disponibile nell'ambiente di sviluppo, quindi qui si verifica la
regola di calcolo con finte metriche del carattere, simulando schermi diversi.

Esegui con:  python -m unittest tests.test_linguette -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.misure import larghezza_linguetta, larghezza_testo


class FinteMetriche:
    """Imita QFontMetrics: la larghezza del testo dipende dal carattere."""

    def __init__(self, pixel_per_carattere):
        self.pixel_per_carattere = pixel_per_carattere

    def horizontalAdvance(self, testo):
        return len(testo) * self.pixel_per_carattere


class FinteMetricheVecchie(FinteMetriche):
    """Versioni di Qt precedenti: c'e' solo width(), non horizontalAdvance()."""

    def __getattr__(self, nome):
        if nome == "horizontalAdvance":
            raise AttributeError(nome)
        raise AttributeError(nome)

    def width(self, testo):
        return len(testo) * self.pixel_per_carattere


def larghezza_calcolata(testo, metriche, larghezza_proposta_da_qt, margine=56):
    """E' esattamente la regola usata da BarraLinguette.tabSizeHint()."""
    return larghezza_linguetta(testo, metriche, larghezza_proposta_da_qt, margine)


class TestLarghezzaTesto(unittest.TestCase):

    def test_usa_horizontal_advance_quando_disponibile(self):
        self.assertEqual(larghezza_testo(FinteMetriche(10), "Scorte"), 60)

    def test_ripiega_su_width_sulle_versioni_vecchie(self):
        """Su Qt piu' vecchi horizontalAdvance() non esiste: non deve fallire."""
        self.assertEqual(larghezza_testo(FinteMetricheVecchie(10), "Scorte"), 60)


class TestRegolaDiCalcolo(unittest.TestCase):
    """Le linguette non devono MAI risultare piu' strette del testo."""

    def test_il_testo_ci_sta_sempre(self):
        metriche = FinteMetriche(9)      # 9 px per carattere
        for testo in ["Stato", "Copie di sicurezza", "Database in uso",
                      "Scorte", "Consumi", "Fornitori", "Singoli Materiali"]:
            # Qt propone una larghezza troppo piccola (il difetto originale)
            proposta_sbagliata = len(testo) * 6
            larghezza = larghezza_calcolata(testo, metriche, proposta_sbagliata)
            servono = len(testo) * 9
            self.assertGreaterEqual(
                larghezza, servono,
                f"'{testo}' verrebbe tagliato: {larghezza}px per {servono}px di testo")

    def test_resta_spazio_per_il_riempimento_laterale(self):
        """Oltre al testo serve il margine del foglio di stile (padding)."""
        metriche = FinteMetriche(9)
        larghezza = larghezza_calcolata("Scorte", metriche, 0, margine=56)
        self.assertEqual(larghezza, 6 * 9 + 56)

    def test_non_stringe_mai_una_linguetta_gia_corretta(self):
        """Se Qt propone gia' una larghezza generosa, va tenuta quella:
        la correzione puo' solo allargare, mai stringere."""
        metriche = FinteMetriche(9)
        larghezza = larghezza_calcolata("Stato", metriche, larghezza_proposta_da_qt=500)
        self.assertEqual(larghezza, 500)

    def test_schermi_diversi_stesso_risultato(self):
        """Su schermi con caratteri piu' grandi (alta risoluzione) la linguetta
        deve crescere di conseguenza: e' il motivo per cui il difetto si vedeva
        su alcuni computer e non su altri."""
        testo = "Copie di sicurezza"
        stretto = larghezza_calcolata(testo, FinteMetriche(7), 0)
        largo = larghezza_calcolata(testo, FinteMetriche(14), 0)
        self.assertGreater(largo, stretto)
        self.assertGreaterEqual(largo, len(testo) * 14)

    def test_linguetta_vuota_non_rompe_il_calcolo(self):
        self.assertEqual(larghezza_calcolata("", FinteMetriche(9), 0), 56)


if __name__ == "__main__":
    unittest.main(verbosity=2)
