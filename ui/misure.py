#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Calcoli di dimensionamento dell'interfaccia.
Uso riservato esclusivamente a RCS

Qui non si importa Qt: sono solo calcoli, così possono essere verificati dai
test automatici indipendentemente dall'interfaccia grafica.
"""


def larghezza_testo(metriche, testo):
    """Larghezza in pixel di un testo, secondo le metriche del carattere.

    horizontalAdvance() esiste nelle versioni recenti di Qt, width() in quelle
    precedenti: si prova la prima e si ripiega sulla seconda."""
    try:
        return metriche.horizontalAdvance(testo)
    except AttributeError:
        return metriche.width(testo)


def larghezza_linguetta(testo, metriche, larghezza_proposta, margine=56):
    """Larghezza da dare a una linguetta perché il testo non venga tagliato.

    Non è mai inferiore a quella proposta da Qt: la correzione può solo
    allargare, mai stringere, così non rovina le linguette già corrette."""
    return max(larghezza_proposta, larghezza_testo(metriche, testo) + margine)
