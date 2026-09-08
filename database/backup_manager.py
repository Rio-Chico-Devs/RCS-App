#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Backup, verifica di integrità e diagnostica del database.
Uso riservato esclusivamente a RCS

Nato dopo un episodio reale di corruzione del database su cartella di rete
condivisa. Obiettivi, in ordine di importanza:
  1. Non perdere mai i dati: molte copie, distribuite nel tempo, mai
     sovrascritte da una copia corrotta.
  2. Accorgersi subito del problema, non settimane dopo.
  3. Registrare abbastanza informazioni da capire QUANDO e DOVE si corrompe.
"""

import getpass
import json
import logging
import os
import platform
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta

PREFISSO_BACKUP = "materiali_backup_"
PREFISSO_CORROTTO = "materiali_CORROTTO_"
PREFISSO_SICUREZZA = "materiali_SICURO_"
FORMATO_TIMESTAMP = "%Y%m%d_%H%M%S"

# --- Politica di conservazione dei backup -------------------------------
# Pensata per coprire tutto il mese, non "gli ultimi N avvii".
ORE_TIENI_TUTTI = 48        # tutti i backup delle ultime 48 ore
GIORNI_GIORNALIERI = 30     # + il piu' recente di ogni giorno, per 30 giorni
MESI_MENSILI = 12           # + il piu' recente di ogni mese, per 12 mesi
MAX_CORROTTI = 10           # quarantena: quanti file corrotti conservare
MAX_SICUREZZA = 5           # copie protette, mai toccate dalla rotazione
MAX_MIRROR_LOCALE = 10      # copie sul disco locale del singolo PC
ORE_SESSIONE_SCADUTA = 12   # oltre questo, una sessione e' considerata chiusa

TIMEOUT_SQLITE = 30.0       # secondi: su cartella di rete 5s (default) sono pochi

NOME_FILE_SESSIONI = "sessioni_attive.json"

# La routine di avvio può essere invocata due volte nello stesso processo
# (controllo preliminare in main.py + creazione del DatabaseManager): la
# seconda volta si riusa l'esito, per non rifare verifica e backup.
_esito_avvio_cache = {}


def _log():
    return logging.getLogger('rcs')


def cartella_app():
    """Cartella dell'applicazione (accanto all'eseguibile se compilata)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Verifica di integrità
# ---------------------------------------------------------------------------

def uri_sola_lettura(percorso):
    """Costruisce l'indirizzo per aprire un file in sola lettura.

    Attenzione ai percorsi di rete di Windows: '\\\\NOMEPC\\cartella\\dati.db'
    tradotto ingenuamente diventa 'file://NOMEPC/cartella/dati.db', e SQLite
    legge 'NOMEPC' come nome di host e rifiuta l'indirizzo
    ("invalid uri authority"). La forma corretta lascia l'host vuoto e mette
    il percorso completo: 'file:////NOMEPC/cartella/dati.db'."""
    normalizzato = percorso.replace("\\", "/")
    if normalizzato.startswith("//"):
        # percorso di rete: host vuoto + percorso che inizia con //
        return "file://" + "//" + normalizzato.lstrip("/") + "?mode=ro"
    return "file:" + normalizzato + "?mode=ro"


def _connessione_sola_lettura(db_path):
    """Apre il database in sola lettura. Se l'URI non e' supportato (capita su
    certi percorsi di rete UNC) ripiega su una connessione normale, comunque
    usata solo per leggere."""
    try:
        conn = sqlite3.connect(uri_sola_lettura(db_path), uri=True, timeout=TIMEOUT_SQLITE)
        conn.execute("PRAGMA schema_version")  # verifica che l'URI funzioni davvero
        return conn
    except Exception:
        return sqlite3.connect(db_path, timeout=TIMEOUT_SQLITE)


def verifica_integrita(db_path):
    """Controlla che il file sia un database SQLite sano.

    Ritorna (ok, messaggio, millisecondi). Usa quick_check: piu' veloce di
    integrity_check e sufficiente a rilevare le corruzioni di pagina, che sono
    quelle causate dalle scritture interrotte."""
    inizio = datetime.now()
    if not db_path or not os.path.exists(db_path):
        return False, "file inesistente", 0.0

    conn = None
    try:
        conn = _connessione_sola_lettura(db_path)
        esito = conn.execute("PRAGMA quick_check(1)").fetchone()
        durata = (datetime.now() - inizio).total_seconds() * 1000
        if esito and esito[0] == "ok":
            return True, "ok", durata
        return False, "quick_check: {}".format(esito[0] if esito else "nessun esito"), durata
    except Exception as e:
        durata = (datetime.now() - inizio).total_seconds() * 1000
        return False, "{}: {}".format(type(e).__name__, e), durata
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Diagnostica dell'ambiente
# ---------------------------------------------------------------------------

def _e_percorso_di_rete(percorso):
    """True se il database sta su un percorso di rete (UNC o unita' mappata)."""
    if not percorso:
        return False
    if percorso.startswith("\\\\") or percorso.startswith("//"):
        return True
    try:
        if os.name == "nt":
            import ctypes
            unita = os.path.splitdrive(os.path.abspath(percorso))[0]
            if unita:
                # DRIVE_REMOTE == 4
                return ctypes.windll.kernel32.GetDriveTypeW(unita + "\\") == 4
    except Exception:
        pass
    return False


def diagnostica_ambiente(db_path):
    """Raccoglie i dati utili a capire dove/quando avviene una corruzione."""
    info = {
        "quando": datetime.now().isoformat(timespec="seconds"),
        "pc": platform.node(),
        "utente": "",
        "db_path": db_path,
        "su_rete": _e_percorso_di_rete(db_path),
        "dimensione_db": None,
        "spazio_libero_mb": None,
    }
    try:
        info["utente"] = getpass.getuser()
    except Exception:
        pass
    try:
        info["dimensione_db"] = os.path.getsize(db_path)
    except Exception:
        pass
    try:
        info["spazio_libero_mb"] = round(
            shutil.disk_usage(os.path.dirname(db_path)).free / (1024 * 1024))
    except Exception:
        pass
    return info


# ---------------------------------------------------------------------------
# Sessioni attive: serve a capire se due PC erano aperti nello stesso momento
# ---------------------------------------------------------------------------

def _percorso_sessioni(db_path):
    return os.path.join(os.path.dirname(db_path), NOME_FILE_SESSIONI)


def _chiave_sessione():
    try:
        utente = getpass.getuser()
    except Exception:
        utente = "?"
    return "{}|{}".format(platform.node(), utente)


def _leggi_sessioni(percorso):
    try:
        with open(percorso, "r", encoding="utf-8") as f:
            dati = json.load(f)
        return dati if isinstance(dati, dict) else {}
    except Exception:
        return {}


def _scrivi_sessioni(percorso, dati):
    """Scrittura prudente: file temporaneo + sostituzione atomica."""
    try:
        tmp = percorso + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(dati, f, ensure_ascii=False, indent=2)
        os.replace(tmp, percorso)
        return True
    except Exception:
        return False


def _pulisci_sessioni_scadute(sessioni):
    limite = datetime.now() - timedelta(hours=ORE_SESSIONE_SCADUTA)
    vive = {}
    for chiave, voce in sessioni.items():
        try:
            if datetime.fromisoformat(voce.get("avvio", "")) > limite:
                vive[chiave] = voce
        except Exception:
            continue
    return vive


def registra_sessione(db_path):
    """Segna che questo PC ha aperto l'applicazione. Ritorna l'elenco degli
    ALTRI PC che risultano gia' aperti in questo momento."""
    percorso = _percorso_sessioni(db_path)
    try:
        sessioni = _pulisci_sessioni_scadute(_leggi_sessioni(percorso))
        mia = _chiave_sessione()
        altri = [k for k in sessioni.keys() if k != mia]
        sessioni[mia] = {
            "avvio": datetime.now().isoformat(timespec="seconds"),
            "pid": os.getpid(),
        }
        _scrivi_sessioni(percorso, sessioni)
        return altri
    except Exception:
        return []


def chiudi_sessione(db_path):
    """Rimuove questo PC dall'elenco delle sessioni aperte."""
    percorso = _percorso_sessioni(db_path)
    try:
        sessioni = _leggi_sessioni(percorso)
        sessioni.pop(_chiave_sessione(), None)
        _scrivi_sessioni(percorso, _pulisci_sessioni_scadute(sessioni))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Gestione dei file di backup
# ---------------------------------------------------------------------------

def _timestamp_da_nome(nome, prefisso=PREFISSO_BACKUP):
    """Estrae data/ora dal nome del backup. None se non riconoscibile.

    Dopo la data puo' esserci il nome del computer (vedi _nome_univoco), quindi
    si legge solo la parte iniziale. I nomi vecchi, senza quel pezzo, restano
    leggibili."""
    try:
        return datetime.strptime(
            nome[len(prefisso):len(prefisso) + 15], FORMATO_TIMESTAMP)
    except Exception:
        return None


def _nome_univoco(cartella, prefisso, momento=None, estensione=".db"):
    """Costruisce un nome di file che non puo' collidere con altri.

    Con la sola data al secondo, due copie fatte nello stesso secondo
    finirebbero sullo stesso file. Sulla cartella di rete condivisa questo
    significa due computer che scrivono contemporaneamente sullo stesso nome:
    una copia va persa, o peggio ne esce una rovinata. Aggiungendo il nome del
    computer il problema sparisce, e in piu' si vede da quale postazione
    proviene ogni copia."""
    momento = momento or datetime.now()
    base = prefisso + momento.strftime(FORMATO_TIMESTAMP)

    computer = "".join(c for c in platform.node() if c.isalnum())[:12]
    if computer:
        base = "{}_{}".format(base, computer)

    percorso = os.path.join(cartella, base + estensione)
    contatore = 2
    while os.path.exists(percorso):     # stesso PC, stesso secondo
        percorso = os.path.join(cartella, "{}_{}{}".format(base, contatore, estensione))
        contatore += 1
    return percorso


def elenca_backup(cartella_backup, prefisso=PREFISSO_BACKUP):
    """Elenco (timestamp, nome) dei backup riconosciuti, dal piu' recente."""
    risultato = []
    try:
        for nome in os.listdir(cartella_backup):
            if not (nome.startswith(prefisso) and nome.endswith(".db")):
                continue
            ts = _timestamp_da_nome(nome, prefisso)
            if ts is not None:
                risultato.append((ts, nome))
    except Exception:
        return []
    risultato.sort(reverse=True)
    return risultato


def applica_retention(cartella_backup, adesso=None):
    """Conserva: tutto delle ultime 48 ore, uno al giorno per 30 giorni, uno al
    mese per 12 mesi. Cancella il resto. I file non riconosciuti non si toccano.

    'adesso' serve ai test per simulare il passare dei mesi.
    Ritorna (tenuti, eliminati)."""
    adesso = adesso or datetime.now()
    backup = elenca_backup(cartella_backup)
    da_tenere = set()
    giorni_visti = set()
    mesi_visti = set()

    for ts, nome in backup:
        eta = adesso - ts
        giorno = ts.date()
        mese = (ts.year, ts.month)

        if eta <= timedelta(hours=ORE_TIENI_TUTTI):
            da_tenere.add(nome)
            giorni_visti.add(giorno)
            mesi_visti.add(mese)
            continue
        if eta <= timedelta(days=GIORNI_GIORNALIERI) and giorno not in giorni_visti:
            da_tenere.add(nome)
            giorni_visti.add(giorno)
            mesi_visti.add(mese)
            continue
        if eta <= timedelta(days=MESI_MENSILI * 31) and mese not in mesi_visti:
            da_tenere.add(nome)
            mesi_visti.add(mese)

    eliminati = 0
    for _ts, nome in backup:
        if nome in da_tenere:
            continue
        try:
            os.remove(os.path.join(cartella_backup, nome))
            eliminati += 1
        except Exception:
            pass
    return len(da_tenere), eliminati


def _limita_numero_file(cartella, prefisso, massimo):
    """Tiene solo i 'massimo' file piu' recenti con quel prefisso."""
    file_lista = elenca_backup(cartella, prefisso)
    for _ts, nome in file_lista[massimo:]:
        try:
            os.remove(os.path.join(cartella, nome))
        except Exception:
            pass


def trova_ultimo_backup_valido(cartella_backup):
    """Scorre i backup dal piu' recente e ritorna il primo che supera la
    verifica di integrità. None se nessuno e' valido."""
    for _ts, nome in elenca_backup(cartella_backup):
        percorso = os.path.join(cartella_backup, nome)
        ok, _msg, _ms = verifica_integrita(percorso)
        if ok:
            return percorso
    return None


def recupera_dopo_arresto(db_path):
    """Fa completare a SQLite il recupero rimasto in sospeso.

    Quando il programma viene terminato di colpo (spegnimento, aggiornamento
    di Windows, blocco) resta accanto al database un file di appoggio
    '-journal' con la scrittura interrotta. SQLite lo risolve da solo alla
    prima scrittura, ma finche' resta li' il database e' in uno stato
    "da recuperare": il backup fotograferebbe quello stato, e sulla cartella
    di rete condivisa un file di appoggio in sospeso e' proprio una delle
    situazioni da cui nascono i danneggiamenti.

    Serve una transazione di scrittura CHE LEGGA davvero qualcosa: verificato
    sul campo, il solo blocco non basta (SQLite non ha motivo di toccare le
    pagine e lascia il file dov'e'), e nemmeno una lettura semplice o un
    quick_check. La combinazione blocco + lettura risolve il recupero senza
    modificare nulla."""
    try:
        conn = sqlite3.connect(db_path, timeout=TIMEOUT_SQLITE)
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
            conn.rollback()
        finally:
            conn.close()
        return True
    except Exception as e:
        # Puo' fallire se un altro computer sta scrivendo proprio adesso:
        # non e' grave, il recupero avverra' comunque alla prima scrittura.
        _log().warning("Recupero dopo arresto non completato (%s)", e)
        return False


def _copia_database(sorgente, destinazione):
    """Copia il database usando il meccanismo di SQLite invece di copiare il
    file.

    E' il modo documentato di copiare un database mentre e' in uso: SQLite
    prende i blocchi che servono e garantisce una copia coerente anche se in
    quel momento qualcuno sta scrivendo. Copiare il file e' rapido ma non da'
    questa garanzia, soprattutto su una cartella di rete dove la copia non e'
    istantanea e un altro computer puo' scrivere nel frattempo.

    Se il meccanismo di SQLite non e' utilizzabile si ripiega sulla copia del
    file: meglio un backup imperfetto che nessun backup."""
    try:
        origine = sqlite3.connect(sorgente, timeout=TIMEOUT_SQLITE)
        try:
            copia = sqlite3.connect(destinazione)
            try:
                origine.backup(copia)
            finally:
                copia.close()
        finally:
            origine.close()
        return True
    except Exception as e:
        _log().warning(
            "Backup: copia tramite SQLite non riuscita (%s), ripiego sulla copia del file", e)

    try:
        if os.path.exists(destinazione):
            os.remove(destinazione)
        shutil.copy2(sorgente, destinazione)
        return True
    except Exception as e:
        _log().error("Backup: copia fallita verso %s (%s)", destinazione, e)
        return False


def _copia_verificata(sorgente, destinazione):
    """Copia e poi RIVERIFICA la copia: su cartella di rete anche la copia puo'
    arrivare danneggiata. Ritorna True solo se la copia e' sana."""
    if not _copia_database(sorgente, destinazione):
        return False

    ok, msg, _ms = verifica_integrita(destinazione)
    if ok:
        return True

    _log().error("Backup: la copia %s risulta danneggiata (%s), la elimino", destinazione, msg)
    try:
        os.remove(destinazione)
    except Exception:
        pass
    return False


ORE_TRA_COPIE_PROTETTE = 24


def _serve_copia_protetta(cartella_sicurezza):
    """True se vale la pena fare una nuova copia protetta.

    Farla a ogni apertura significherebbe una scrittura in piu' sulla cartella
    di rete ogni volta (e su una condivisione fragile ogni scrittura e' un
    rischio), e farebbe ruotare le copie protette per numero di aperture invece
    che nel tempo: cinque riaperture di fila cancellerebbero tutta la
    profondita'. Una al giorno e' sufficiente."""
    esistenti = elenca_backup(cartella_sicurezza, PREFISSO_SICUREZZA)
    if not esistenti:
        return True
    piu_recente = esistenti[0][0]
    return (datetime.now() - piu_recente) > timedelta(hours=ORE_TRA_COPIE_PROTETTE)


def _proteggi_copia_buona(percorso_buono, cartella_sicurezza, sempre=False):
    """Mette una copia del backup buono al riparo dalla rotazione.

    'sempre=True' quando si e' rilevato un problema: in quel caso la copia va
    fatta subito, senza aspettare."""
    try:
        os.makedirs(cartella_sicurezza, exist_ok=True)
        if not sempre and not _serve_copia_protetta(cartella_sicurezza):
            return None
        destinazione = _nome_univoco(cartella_sicurezza, PREFISSO_SICUREZZA)
        if _copia_verificata(percorso_buono, destinazione):
            _limita_numero_file(cartella_sicurezza, PREFISSO_SICUREZZA, MAX_SICUREZZA)
            return destinazione
    except Exception as e:
        _log().error("Backup: impossibile proteggere la copia buona (%s)", e)
    return None


def _mirror_locale(percorso_backup):
    """Copia il backup anche sul disco LOCALE del PC: se la cartella di rete
    diventa irraggiungibile o si danneggia, i dati restano comunque qui."""
    try:
        cartella = os.path.join(cartella_app(), "backup_locale")
        os.makedirs(cartella, exist_ok=True)
        destinazione = os.path.join(cartella, os.path.basename(percorso_backup))
        if not os.path.exists(destinazione):
            shutil.copy2(percorso_backup, destinazione)
        _limita_numero_file(cartella, PREFISSO_BACKUP, MAX_MIRROR_LOCALE)
        return destinazione
    except Exception as e:
        _log().warning("Backup: mirror locale non riuscito (%s)", e)
        return None


# ---------------------------------------------------------------------------
# Routine principale, chiamata all'avvio
# ---------------------------------------------------------------------------

def esegui_backup_avvio(db_path):
    """Verifica il database e ne crea un backup.

    Se il database e' SANO: crea il backup, lo riverifica, ne tiene una copia
    protetta e una locale, poi applica la politica di conservazione.

    Se il database e' CORROTTO: NON tocca i backup esistenti (cosi' non spinge
    fuori dalla rotazione le copie buone), mette il file corrotto in quarantena
    e mette al sicuro l'ultimo backup valido che trova.

    Ritorna un dizionario con l'esito; 'avviso' e' un testo da mostrare
    all'utente, oppure None se e' tutto a posto."""
    log = _log()
    esito = {"integro": True, "avviso": None, "backup": None,
             "copia_sicura": None, "primo_avvio": False, "diagnostica": {}}

    # Già eseguita in questo processo per lo stesso database: riusa l'esito.
    if db_path in _esito_avvio_cache:
        return _esito_avvio_cache[db_path]

    # Database non ancora esistente (prima installazione): non c'è nulla da
    # verificare né da salvare, e non è un errore.
    if not db_path or not os.path.exists(db_path):
        esito["primo_avvio"] = True
        _esito_avvio_cache[db_path] = esito
        return esito

    # Registrato subito: 'esito' viene modificato sotto, e il dizionario in
    # cache è lo stesso oggetto, quindi resta sempre aggiornato.
    _esito_avvio_cache[db_path] = esito

    try:
        cartella_backup = os.path.join(os.path.dirname(db_path), "backup")
        cartella_corrotti = os.path.join(cartella_backup, "corrotti")
        cartella_sicurezza = os.path.join(cartella_backup, "sicurezza")
        os.makedirs(cartella_backup, exist_ok=True)

        # Prima di ogni altra cosa: se un arresto improvviso ha lasciato una
        # scrittura a meta', la si fa completare a SQLite. Cosi' la verifica e
        # il backup lavorano su uno stato pulito.
        recupera_dopo_arresto(db_path)

        info = diagnostica_ambiente(db_path)
        esito["diagnostica"] = info

        integro, messaggio, durata_ms = verifica_integrita(db_path)
        info["integrita"] = messaggio
        info["verifica_ms"] = round(durata_ms)

        altri_pc = registra_sessione(db_path)
        info["altri_pc_aperti"] = altri_pc

        log.info(
            "AVVIO | pc=%s utente=%s | db=%s (rete=%s, %s byte) | integrita=%s in %d ms | "
            "altri PC aperti: %s",
            info.get("pc"), info.get("utente"), db_path, info.get("su_rete"),
            info.get("dimensione_db"), messaggio, info.get("verifica_ms", 0),
            ", ".join(altri_pc) if altri_pc else "nessuno")

        if altri_pc:
            log.warning("ATTENZIONE: il database risulta aperto anche da: %s",
                        ", ".join(altri_pc))

        if integro:
            destinazione = _nome_univoco(cartella_backup, PREFISSO_BACKUP)
            if _copia_verificata(db_path, destinazione):
                esito["backup"] = destinazione
                esito["copia_sicura"] = _proteggi_copia_buona(destinazione, cartella_sicurezza)
                _mirror_locale(destinazione)
                tenuti, eliminati = applica_retention(cartella_backup)
                log.info("Backup creato: %s | conservati %d, eliminati %d",
                         os.path.basename(destinazione), tenuti, eliminati)
            else:
                # La copia non e' venuta bene: meglio non toccare nulla.
                esito["avviso"] = (
                    "Non e' stato possibile creare un backup valido del database.\n\n"
                    "I backup precedenti sono stati lasciati intatti. "
                    "Se il problema si ripete, segnalalo: potrebbe indicare un problema "
                    "sulla cartella di rete.")
                log.error("Backup NON creato: la copia non ha superato la verifica.")
            return esito

        # --- Database corrotto -------------------------------------------
        esito["integro"] = False
        log.error("DATABASE CORROTTO rilevato all'avvio: %s (%s)", db_path, messaggio)

        try:
            os.makedirs(cartella_corrotti, exist_ok=True)
            quarantena = _nome_univoco(cartella_corrotti, PREFISSO_CORROTTO)
            shutil.copy2(db_path, quarantena)
            _limita_numero_file(cartella_corrotti, PREFISSO_CORROTTO, MAX_CORROTTI)
            log.error("Copia del file corrotto messa in quarantena: %s", quarantena)
        except Exception as e:
            log.error("Quarantena non riuscita (%s)", e)

        buono = trova_ultimo_backup_valido(cartella_backup)
        if buono:
            esito["copia_sicura"] = _proteggi_copia_buona(
                buono, cartella_sicurezza, sempre=True)
            quando = _timestamp_da_nome(os.path.basename(buono))
            quando_txt = quando.strftime("%d/%m/%Y alle %H:%M") if quando else "data sconosciuta"
            esito["avviso"] = (
                "Il database presenta un danneggiamento.\n\n"
                "I dati NON sono stati persi: e' stato trovato un backup integro del "
                "{}, di cui e' stata messa al sicuro una copia nella cartella "
                "'backup\\sicurezza'.\n\n"
                "Nessun backup e' stato cancellato. Contatta l'assistenza prima di "
                "continuare a lavorare, per farti ripristinare il backup.".format(quando_txt))
            log.error("Ultimo backup valido individuato: %s (messo al sicuro)", buono)
        else:
            esito["avviso"] = (
                "Il database presenta un danneggiamento e non e' stato trovato "
                "nessun backup integro nella cartella dei backup.\n\n"
                "NON continuare a lavorare e contatta subito l'assistenza: "
                "esistono ancora copie recuperabili (anche sul disco locale di questo PC, "
                "cartella 'backup_locale').")
            log.error("NESSUN backup valido trovato nella cartella %s", cartella_backup)

        return esito

    except Exception as e:
        # Il backup non deve mai impedire l'avvio dell'applicazione.
        _log().error("Routine di backup fallita in modo imprevisto: %s", e)
        return esito


def verifica_dopo_scrittura(db_path, operazione):
    """Controllo mirato subito dopo un'operazione di scrittura importante.

    Serve a capire QUALE operazione danneggia il database: se il controllo
    fallisce qui, la corruzione e' avvenuta adesso, non 'chissa' quando'.
    Ritorna True se il database e' ancora sano."""
    integro, messaggio, durata_ms = verifica_integrita(db_path)
    if integro:
        _log().debug("Verifica dopo '%s': ok (%d ms)", operazione, round(durata_ms))
        return True

    _log().error(
        "CORRUZIONE RILEVATA SUBITO DOPO L'OPERAZIONE '%s' | pc=%s | db=%s | dettaglio=%s",
        operazione, platform.node(), db_path, messaggio)

    # Mette subito al riparo l'ultimo backup buono, prima che la rotazione
    # possa toccarlo.
    try:
        cartella_backup = os.path.join(os.path.dirname(db_path), "backup")
        buono = trova_ultimo_backup_valido(cartella_backup)
        if buono:
            _proteggi_copia_buona(
                buono, os.path.join(cartella_backup, "sicurezza"), sempre=True)
    except Exception:
        pass
    return False
