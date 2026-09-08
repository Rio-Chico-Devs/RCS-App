#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Preparazione di una segnalazione tecnica.
Uso riservato esclusivamente a RCS

A cosa serve
------------
Quando qualcosa va storto, ricostruire cosa e' successo richiede i registri,
lo stato dei backup e qualche informazione sul computer. Chiederli a voce, uno
alla volta, e' lento e si finisce sempre per dimenticarne qualcuno: e' andata
esattamente cosi' con il danneggiamento del 3 settembre.

Qui viene preparato un unico file .zip con tutto il necessario, pronto da
inviare.

NON contiene i dati aziendali: niente database, niente preventivi, niente
nomi di clienti. Solo registri tecnici ed elenchi di file.
"""

import json
import logging
import os
import platform
import sys
import zipfile
from datetime import datetime, timedelta

GIORNI_DI_REGISTRO = 30
MAX_BYTE_PER_FILE = 5 * 1024 * 1024      # un registro enorme non serve a nessuno


def _log():
    return logging.getLogger('rcs')


def cartella_app():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _informazioni_sistema(db_path):
    """Dati tecnici sul computer e sulla configurazione (nessun dato aziendale)."""
    from database import backup_manager

    info = {
        "generato_il": datetime.now().isoformat(timespec="seconds"),
        "computer": platform.node(),
        "sistema": platform.platform(),
        "versione_python": sys.version.split()[0],
        "eseguibile_compilato": bool(getattr(sys, "frozen", False)),
        "percorso_database": db_path,
        "database_su_rete": backup_manager._e_percorso_di_rete(db_path),
    }
    try:
        info["dimensione_database"] = os.path.getsize(db_path)
    except Exception:
        info["dimensione_database"] = None
    try:
        integro, messaggio, ms = backup_manager.verifica_integrita(db_path)
        info["integrita"] = {"integro": integro, "messaggio": messaggio,
                             "millisecondi": round(ms)}
    except Exception as e:
        info["integrita"] = {"errore": str(e)}
    try:
        from utils import diagnostica
        info["ultimo_avvio"] = diagnostica.esito_avvio_precedente()
    except Exception:
        pass
    return info


def _elenco_backup(db_path):
    """Elenco dei backup: nomi, date e dimensioni. Nessun contenuto."""
    try:
        from database import archivio
        return [
            {"nome": v["nome"], "quando": v["quando_testo"],
             "tipo": v["tipo"], "byte": v["dimensione"]}
            for v in archivio.elenco_backup(db_path)
        ]
    except Exception as e:
        return {"errore": str(e)}


def _registri_recenti():
    """I file di registro degli ultimi giorni, quelli utili a capire."""
    cartella = os.path.join(cartella_app(), "logs")
    limite = datetime.now() - timedelta(days=GIORNI_DI_REGISTRO)
    trovati = []
    if not os.path.isdir(cartella):
        return trovati
    for nome in sorted(os.listdir(cartella)):
        if not nome.endswith(".log"):
            continue
        percorso = os.path.join(cartella, nome)
        try:
            if datetime.fromtimestamp(os.path.getmtime(percorso)) < limite:
                continue
            trovati.append(percorso)
        except OSError:
            continue
    return trovati


def prepara(db_path, destinazione=None):
    """Crea il file .zip della segnalazione e ne restituisce il percorso."""
    nome = "segnalazione_RCS_{}_{}.zip".format(
        "".join(c for c in platform.node() if c.isalnum())[:12] or "pc",
        datetime.now().strftime("%Y%m%d_%H%M"))
    percorso_zip = destinazione or os.path.join(cartella_app(), nome)

    with zipfile.ZipFile(percorso_zip, "w", zipfile.ZIP_DEFLATED) as pacchetto:
        pacchetto.writestr(
            "informazioni.json",
            json.dumps(_informazioni_sistema(db_path), ensure_ascii=False,
                       indent=2, default=str))
        pacchetto.writestr(
            "backup_presenti.json",
            json.dumps(_elenco_backup(db_path), ensure_ascii=False,
                       indent=2, default=str))

        for percorso in _registri_recenti():
            try:
                if os.path.getsize(percorso) > MAX_BYTE_PER_FILE:
                    with open(percorso, "rb") as f:
                        f.seek(-MAX_BYTE_PER_FILE, os.SEEK_END)
                        pacchetto.writestr(
                            "logs/" + os.path.basename(percorso), f.read())
                else:
                    pacchetto.write(percorso, "logs/" + os.path.basename(percorso))
            except Exception as e:
                _log().warning("Registro %s non incluso: %s", percorso, e)

        pacchetto.writestr("LEGGIMI.txt", (
            "SEGNALAZIONE TECNICA - RCS Gestione Preventivi\n"
            "Generata il {}\n\n"
            "Contiene i registri tecnici e lo stato delle copie di sicurezza,\n"
            "per capire cosa e' successo.\n\n"
            "NON contiene dati aziendali: nessun database, nessun preventivo,\n"
            "nessun nominativo di clienti.\n".format(
                datetime.now().strftime("%d/%m/%Y alle %H:%M"))))

    _log().info("Segnalazione preparata: %s", percorso_zip)
    return percorso_zip
