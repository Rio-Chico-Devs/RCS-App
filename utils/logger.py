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

    # Determina la directory dei log
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"rcs_{datetime.now().strftime('%Y%m%d')}.log")

    # Handler file — DEBUG e superiori
    try:
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%H:%M:%S')
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        pass  # Se non riesce a creare il file di log, continua senza

    # Handler console — WARNING e superiori
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(ch)

    return logger


# Istanza globale
log = setup_logger()
