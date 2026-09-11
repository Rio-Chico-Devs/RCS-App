#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Sistema di logging centralizzato
Uso riservato esclusivamente a RCS
"""

import logging
import os
import sys
from datetime import datetime


def setup_logger():
    """Configura il logger centralizzato dell'applicazione."""
    logger = logging.getLogger('rcs')
    if logger.handlers:
        return logger  # Già configurato

    logger.setLevel(logging.DEBUG)

    # Dove scrivere i registri: la logica dei percorsi sta in utils/percorsi.py,
    # in un posto solo, così tutte le parti del programma scrivono e cercano
    # negli stessi posti anche quando gira come eseguibile compilato.
    from utils import percorsi
    log_dir = percorsi.cartella_registri()

    log_file = os.path.join(log_dir, f"rcs_{datetime.now().strftime('%Y%m%d')}.log")

    # Handler file — DEBUG e superiori
    try:
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%H:%M:%S')
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        # UNICO punto in cui tacere e' giusto: qui si sta costruendo il
        # registro stesso. Segnalare l'errore vorrebbe dire scrivere nel
        # registro che non funziona. Il programma prosegue senza registro su
        # file, che e' meglio che non partire.
        pass  # Se non riesce a creare il file di log, continua senza

    # Handler console — WARNING e superiori.
    # Solo se una console c'è davvero: quando il programma gira come eseguibile
    # compilato senza finestra di console, sys.stderr è None. Aggiungere lo
    # stesso l'handler farebbe fallire in silenzio OGNI messaggio di avviso,
    # passando ogni volta per la gestione dell'errore.
    if getattr(sys, 'stderr', None) is not None:
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(logging.WARNING)
        ch.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
        logger.addHandler(ch)

    return logger


# Istanza globale
log = setup_logger()
