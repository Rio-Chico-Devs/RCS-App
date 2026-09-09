#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Logica delle "Impostazioni di archiviazione": stato dei dati, elenco dei
backup e ripristino.
Uso riservato esclusivamente a RCS

Questo modulo NON contiene interfaccia grafica: così può essere provato per
intero con i test automatici. La finestra si limita a mostrare quello che
queste funzioni restituiscono.
"""

import logging
import os
import shutil
import sqlite3
from datetime import datetime

from database import backup_manager

TABELLE_DA_CONTARE = ("preventivi", "clienti", "materiali", "movimenti_magazzino")

PREFISSO_PRIMA_RIPRISTINO = "materiali_PRIMA_DEL_RIPRISTINO_"

# I file di appoggio che SQLite tiene ACCANTO al database.
SUFFISSI_APPOGGIO = ("-journal", "-wal", "-shm")


def _file_di_appoggio(db_path):
    """I file di appoggio presenti in questo momento accanto al database."""
    return [db_path + s for s in SUFFISSI_APPOGGIO if os.path.exists(db_path + s)]


def _rimuovi_appoggi_orfani(db_path):
    """Toglie i file di appoggio rimasti DOPO aver sostituito il database.

    ATTENZIONE, la distinzione qui è tutto:

    - cancellare il '-journal' di un database che si tiene è una delle cause di
      danneggiamento elencate da SQLite, e non va MAI fatto;
    - ma quando il file del database viene SOSTITUITO da un altro, quel
      '-journal' descrive pagine di un database che non esiste più. Se resta
      lì, alla prima apertura SQLite lo riversa sopra il database appena
      ripristinato.

    Non è teoria: provato: ripristinando un backup da 5 preventivi con accanto
    il journal di un arresto improvviso si ottengono 8 preventivi, e
    integrity_check risponde comunque "ok". Dati sbagliati che nessun controllo
    segnala.

    Per questo la funzione si chiama solo subito dopo la sostituzione del file,
    mai in altri momenti."""
    tolti = []
    for percorso in _file_di_appoggio(db_path):
        try:
            os.remove(percorso)
            tolti.append(os.path.basename(percorso))
        except OSError as e:
            _log().error("Non è stato possibile togliere %s (%s)", percorso, e)
    if tolti:
        _log().warning("Ripristino: tolti i file di appoggio del database "
                       "precedente (%s)", ", ".join(tolti))
    return tolti


def _log():
    return logging.getLogger('rcs')


def _dimensione_leggibile(byte):
    try:
        byte = float(byte)
    except (TypeError, ValueError):
        return "?"
    for unita in ("byte", "KB", "MB", "GB"):
        if byte < 1024 or unita == "GB":
            return "{:.0f} {}".format(byte, unita) if unita == "byte" else "{:.1f} {}".format(byte, unita)
        byte /= 1024.0


def cartella_backup(db_path):
    return os.path.join(os.path.dirname(db_path), "backup")


# ---------------------------------------------------------------------------
# Elenco dei backup
# ---------------------------------------------------------------------------

def elenco_backup(db_path):
    """Elenco di TUTTE le copie disponibili, dalla più recente.

    Non apre i file (sarebbe lento su una cartella di rete): restituisce solo
    le informazioni ricavabili dal nome e dal file system. I dettagli si
    chiedono con dettagli_backup() sulla copia selezionata.

    Ogni voce: percorso, nome, quando (datetime o None), quando_testo,
    dimensione, dimensione_testo, tipo."""
    base = cartella_backup(db_path)
    posti = [
        (base, backup_manager.PREFISSO_BACKUP, "automatico"),
        (os.path.join(base, "sicurezza"), backup_manager.PREFISSO_SICUREZZA, "protetto"),
        (os.path.join(base, "corrotti"), backup_manager.PREFISSO_CORROTTO, "danneggiato"),
        (os.path.join(backup_manager.cartella_app(), "backup_locale"),
         backup_manager.PREFISSO_BACKUP, "copia locale"),
    ]

    voci = []
    for cartella, prefisso, tipo in posti:
        if not os.path.isdir(cartella):
            continue
        for quando, nome in backup_manager.elenca_backup(cartella, prefisso):
            percorso = os.path.join(cartella, nome)
            try:
                dimensione = os.path.getsize(percorso)
            except OSError:
                continue
            voci.append({
                "percorso": percorso,
                "nome": nome,
                "quando": quando,
                "quando_testo": quando.strftime("%d/%m/%Y  %H:%M") if quando else "?",
                "dimensione": dimensione,
                "dimensione_testo": _dimensione_leggibile(dimensione),
                "tipo": tipo,
            })

    voci.sort(key=lambda v: v["quando"] or datetime.min, reverse=True)
    return voci


TABELLE_ATTESE = ("preventivi", "materiali")


def _e_un_database_del_gestionale(conn):
    """Verifica che il file sia davvero un database di questo programma.

    Serve perche' un file VUOTO (zero byte) per SQLite e' un database valido:
    supera il controllo di integrita' senza problemi. Senza questo controllo
    comparirebbe fra le copie buone, e ripristinarlo cancellerebbe tutti i
    dati sostituendoli con il nulla."""
    try:
        tabelle = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    except Exception:
        return False
    return all(t in tabelle for t in TABELLE_ATTESE)


def dettagli_backup(percorso):
    """Apre UNA copia e ne riferisce lo stato e il contenuto.

    Ritorna: integro (bool), messaggio, conteggi {tabella: righe},
    ultimo_preventivo (data del preventivo più recente)."""
    esito = {"integro": False, "messaggio": "", "conteggi": {}, "ultimo_preventivo": None}

    integro, messaggio, _ms = backup_manager.verifica_integrita(percorso)
    esito["integro"] = integro
    esito["messaggio"] = messaggio
    if not integro:
        return esito

    conn = None
    try:
        # Se l'indirizzo in sola lettura non e' utilizzabile (capita sui
        # percorsi di rete), si apre normalmente: qui si legge soltanto.
        # Senza questo ripiego OGNI copia risulterebbe "danneggiata" e il
        # ripristino sarebbe impossibile proprio quando serve.
        try:
            conn = sqlite3.connect(backup_manager.uri_sola_lettura(percorso),
                                   uri=True, timeout=backup_manager.TIMEOUT_SQLITE)
            conn.execute("PRAGMA schema_version")
        except Exception:
            conn = sqlite3.connect(percorso, timeout=backup_manager.TIMEOUT_SQLITE)
        if not _e_un_database_del_gestionale(conn):
            esito["integro"] = False
            esito["messaggio"] = ("il file non contiene i dati del gestionale "
                                  "(potrebbe essere vuoto o non essere una copia valida)")
            return esito

        cur = conn.cursor()
        tabelle = {r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        for tabella in TABELLE_DA_CONTARE:
            if tabella in tabelle:
                esito["conteggi"][tabella] = cur.execute(
                    "SELECT COUNT(*) FROM {}".format(tabella)).fetchone()[0]
        if "preventivi" in tabelle:
            riga = cur.execute(
                "SELECT MAX(data_creazione) FROM preventivi").fetchone()
            esito["ultimo_preventivo"] = riga[0] if riga else None
    except Exception as e:
        esito["messaggio"] = "{}: {}".format(type(e).__name__, e)
        esito["integro"] = False
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
    return esito


def descrivi_contenuto(dettagli):
    """Frase leggibile: '61 preventivi, 20 clienti, 19 materiali'."""
    if not dettagli.get("integro"):
        return "copia danneggiata, non utilizzabile"
    etichette = {
        "preventivi": "preventivi", "clienti": "clienti",
        "materiali": "materiali", "movimenti_magazzino": "movimenti",
    }
    pezzi = []
    for tabella in TABELLE_DA_CONTARE:
        if tabella in dettagli.get("conteggi", {}):
            pezzi.append("{} {}".format(dettagli["conteggi"][tabella], etichette[tabella]))
    return ", ".join(pezzi) if pezzi else "nessun dato riconosciuto"


# ---------------------------------------------------------------------------
# Ripristino
# ---------------------------------------------------------------------------

def altri_computer_collegati(db_path):
    """Altri computer che in questo momento hanno l'applicazione aperta sullo
    stesso database. Elenco vuoto se si e' soli (o se non si riesce a saperlo)."""
    try:
        sessioni = backup_manager._pulisci_sessioni_scadute(
            backup_manager._leggi_sessioni(backup_manager._percorso_sessioni(db_path)))
        mia = backup_manager._chiave_sessione()
        return [chiave for chiave in sessioni if chiave != mia]
    except Exception:
        return []


def ripristina_backup(db_path, percorso_backup, forza=False):
    """Rimette in uso una copia di backup, in sicurezza.

    Passaggi, in quest'ordine:
      1. la copia da ripristinare viene verificata: se è danneggiata ci si
         ferma subito, senza toccare nulla;
      2. il database attuale viene messo da parte (anche se rovinato: potrebbe
         contenere dati recuperabili), così il ripristino è reversibile;
      3. la copia prende il posto del database;
      4. il risultato viene verificato: se qualcosa è andato storto si torna
         automaticamente indietro.

    Se altri computer hanno l'applicazione aperta ci si ferma: sovrascrivere il
    file mentre un'altra postazione ci scrive e' il modo classico per
    danneggiare il database, proprio nell'operazione che dovrebbe ripararlo.
    'forza' serve solo per il caso di una postazione che risulta aperta ma non
    lo e' piu' (per esempio dopo un blocco), e va usato con cognizione.

    Ritorna (riuscito, messaggio, percorso_copia_precedente)."""
    if not os.path.exists(percorso_backup):
        return False, "La copia selezionata non esiste più.", None

    altri = altri_computer_collegati(db_path)
    if altri and not forza:
        return (False,
                "Il ripristino è stato annullato: risultano altri computer con "
                "l'applicazione aperta su questo database.\n\n{}\n\n"
                "Sovrascrivere il database mentre un'altra postazione ci sta "
                "lavorando lo danneggerebbe. Chiudi l'applicazione su tutti gli "
                "altri computer e riprova.".format(
                    "\n".join("  • " + pc for pc in altri)),
                None)

    integro, messaggio, _ms = backup_manager.verifica_integrita(percorso_backup)
    if not integro:
        return (False,
                "La copia selezionata è danneggiata e NON è stata ripristinata "
                "({}).\n\nIl database attuale non è stato toccato.".format(messaggio),
                None)

    # Il controllo di integrità non basta: un file VUOTO per SQLite è un
    # database valido. Ripristinarlo cancellerebbe tutto sostituendolo con il
    # nulla, e sarebbe il danno peggiore possibile proprio nell'operazione
    # pensata per rimediare a un danno.
    dettagli = dettagli_backup(percorso_backup)
    if not dettagli["integro"]:
        return (False,
                "La copia selezionata non contiene i dati del gestionale e NON "
                "è stata ripristinata ({}).\n\nIl database attuale non è stato "
                "toccato.".format(dettagli["messaggio"]),
                None)

    # Prima di mettere da parte il database attuale bisogna far completare a
    # SQLite un'eventuale scrittura interrotta: altrimenti la copia che
    # conserviamo sarebbe una fotografia scattata a metà di un'operazione, e
    # sarebbe proprio quella a cui torneremmo se il ripristino fallisse.
    # SQLite, finito il recupero, toglie da sé il file di appoggio.
    if os.path.exists(db_path):
        backup_manager.recupera_dopo_arresto(db_path)
        if _file_di_appoggio(db_path):
            return (False,
                    "Il database ha una scrittura ancora in sospeso e non è "
                    "stato possibile completarla: probabilmente un altro "
                    "computer ci sta lavorando proprio adesso.\n\n"
                    "Non è stato toccato nulla. Chiudi l'applicazione sugli "
                    "altri computer e riprova fra qualche secondo.",
                    None)

    # 2. Da parte il database attuale
    copia_precedente = None
    try:
        if os.path.exists(db_path):
            cartella = os.path.join(cartella_backup(db_path), "prima_del_ripristino")
            os.makedirs(cartella, exist_ok=True)
            copia_precedente = backup_manager._nome_univoco(
                cartella, PREFISSO_PRIMA_RIPRISTINO)
            shutil.copy2(db_path, copia_precedente)
            _log().info("Ripristino: database attuale messo da parte in %s", copia_precedente)
    except Exception as e:
        return (False,
                "Non è stato possibile mettere da parte il database attuale "
                "({}).\n\nPer sicurezza il ripristino è stato annullato.".format(e),
                None)

    # 3. Ripristino vero e proprio
    try:
        shutil.copy2(percorso_backup, db_path)
        # Subito dopo la sostituzione: gli eventuali file di appoggio rimasti
        # appartengono al database di prima e vanno tolti (vedi la spiegazione
        # in _rimuovi_appoggi_orfani).
        _rimuovi_appoggi_orfani(db_path)
    except Exception as e:
        _annulla_ripristino(db_path, copia_precedente)
        return False, "Ripristino non riuscito ({}). Il database precedente è stato rimesso al suo posto.".format(e), copia_precedente

    # 4. Verifica del risultato
    integro_dopo, messaggio_dopo, _ms = backup_manager.verifica_integrita(db_path)
    if not integro_dopo:
        _annulla_ripristino(db_path, copia_precedente)
        return (False,
                "Dopo il ripristino il database non risulta valido ({}). "
                "È stato rimesso al suo posto quello precedente.".format(messaggio_dopo),
                copia_precedente)

    dettagli = dettagli_backup(db_path)
    _log().warning("RIPRISTINO ESEGUITO da %s (%s)", percorso_backup, descrivi_contenuto(dettagli))
    return (True,
            "Ripristino completato.\n\nOra il database contiene: {}.\n\n"
            "Il database precedente è stato conservato in:\n{}".format(
                descrivi_contenuto(dettagli), copia_precedente or "(nessuna copia)"),
            copia_precedente)


def _annulla_ripristino(db_path, copia_precedente):
    """Rimette al suo posto il database che c'era prima del ripristino."""
    if not copia_precedente or not os.path.exists(copia_precedente):
        return False
    try:
        shutil.copy2(copia_precedente, db_path)
        _rimuovi_appoggi_orfani(db_path)    # anche tornando indietro si sostituisce il file
        _log().error("Ripristino annullato: rimesso il database precedente")
        return True
    except Exception as e:
        _log().error("Impossibile annullare il ripristino: %s", e)
        return False


# ---------------------------------------------------------------------------
# Riepilogo dello stato
# ---------------------------------------------------------------------------

def riepilogo_stato(db_path):
    """Fotografia dello stato dell'archiviazione, pronta da mostrare."""
    stato = {
        "db_path": db_path,
        "su_rete": backup_manager._e_percorso_di_rete(db_path),
        "dimensione_testo": "?",
        "integro": None,
        "integrita_messaggio": "",
        "numero_backup": 0,
        "backup_piu_recente": None,
        "backup_piu_vecchio": None,
        "copie_protette": 0,
        "copie_danneggiate": 0,
        "chiusura_precedente_regolare": None,
        "altri_pc": [],
        "ultime_scritture": [],
    }

    try:
        stato["dimensione_testo"] = _dimensione_leggibile(os.path.getsize(db_path))
    except OSError:
        pass

    integro, messaggio, _ms = backup_manager.verifica_integrita(db_path)
    stato["integro"] = integro
    stato["integrita_messaggio"] = messaggio

    voci = elenco_backup(db_path)
    utilizzabili = [v for v in voci if v["tipo"] != "danneggiato"]
    stato["numero_backup"] = len(utilizzabili)
    stato["copie_protette"] = sum(1 for v in voci if v["tipo"] == "protetto")
    stato["copie_danneggiate"] = sum(1 for v in voci if v["tipo"] == "danneggiato")
    if utilizzabili:
        stato["backup_piu_recente"] = utilizzabili[0]["quando_testo"]
        stato["backup_piu_vecchio"] = utilizzabili[-1]["quando_testo"]

    try:
        percorso_sessioni = backup_manager._percorso_sessioni(db_path)
        sessioni = backup_manager._pulisci_sessioni_scadute(
            backup_manager._leggi_sessioni(percorso_sessioni))
        mia = backup_manager._chiave_sessione()
        stato["altri_pc"] = [k for k in sessioni if k != mia]
    except Exception:
        pass

    try:
        from utils import diagnostica
        stato["ultime_scritture"] = diagnostica.ultime_scritture(10)
        stato["chiusura_precedente_regolare"] = not os.path.exists(
            os.path.join(diagnostica.cartella_locale(), diagnostica.NOME_MARCATORE))
    except Exception:
        pass

    return stato


def testo_riepilogo(stato):
    """Traduce il riepilogo in righe di testo comprensibili."""
    righe = []
    righe.append("DATABASE IN USO")
    righe.append("  " + stato["db_path"])
    righe.append("  Posizione: {}".format(
        "cartella di rete condivisa" if stato["su_rete"] else "disco di questo computer"))
    righe.append("  Dimensione: {}".format(stato["dimensione_testo"]))
    if stato["integro"] is True:
        righe.append("  Stato: nessun problema rilevato")
    elif stato["integro"] is False:
        righe.append("  Stato: ATTENZIONE, il database risulta danneggiato")
        righe.append("         ({})".format(stato["integrita_messaggio"]))

    righe.append("")
    righe.append("COPIE DI SICUREZZA")
    righe.append("  Disponibili: {}".format(stato["numero_backup"]))
    if stato["backup_piu_recente"]:
        righe.append("  Più recente: {}".format(stato["backup_piu_recente"]))
        righe.append("  Più vecchia: {}".format(stato["backup_piu_vecchio"]))
    if stato["copie_protette"]:
        righe.append("  Di cui protette (mai cancellate): {}".format(stato["copie_protette"]))
    if stato["copie_danneggiate"]:
        righe.append("  Copie danneggiate messe da parte: {}".format(stato["copie_danneggiate"]))

    righe.append("")
    righe.append("ULTIMO AVVIO")
    if stato["chiusura_precedente_regolare"] is True:
        righe.append("  La volta scorsa il programma è stato chiuso regolarmente")
    elif stato["chiusura_precedente_regolare"] is False:
        righe.append("  ATTENZIONE: la volta scorsa il programma non è stato chiuso")
        righe.append("  regolarmente (spegnimento improvviso o blocco)")

    righe.append("")
    righe.append("ALTRI COMPUTER COLLEGATI ADESSO")
    if stato["altri_pc"]:
        for pc in stato["altri_pc"]:
            righe.append("  • " + pc)
    else:
        righe.append("  Nessuno")

    if stato["ultime_scritture"]:
        righe.append("")
        righe.append("ULTIMI SALVATAGGI")
        for riga in stato["ultime_scritture"]:
            righe.append("  " + riga)

    return "\n".join(righe)
