#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Verifica dell'installazione: controlla che tutto sia a posto su QUESTO computer.
Uso riservato esclusivamente a RCS

A cosa serve
------------
Alcune cose si possono controllare solo sul computer dove il programma gira
davvero: se PyQt5 e' installato, se la cartella di rete risponde e quanto ci
mette, se i testi delle linguette ci stanno con i caratteri di QUESTO schermo,
se le cartelle sono scrivibili.

Si lancia con un doppio clic su VERIFICA.bat (oppure:
python verifica_installazione.py). Alla fine scrive un file di testo con
l'esito, da inviare all'assistenza se qualcosa non va.

IMPORTANTE: questo programma NON MODIFICA NULLA.
Non scrive sul database, non crea backup, non cambia impostazioni. Legge e
basta. Le uniche cose che scrive sono il file con l'esito e, per le prove sulle
cartelle, un file di prova che cancella subito.
"""

import os
import platform
import sys
import tempfile
import time
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OK, ATTENZIONE, ERRORE = "OK", "ATTENZIONE", "ERRORE"

_righe = []
_esiti = []


def scrivi(testo=""):
    print(testo)
    _righe.append(testo)


def esito(stato, titolo, dettaglio=""):
    _esiti.append((stato, titolo))
    simbolo = {OK: "[ OK ]", ATTENZIONE: "[ !  ]", ERRORE: "[ NO ]"}[stato]
    scrivi("{} {}".format(simbolo, titolo))
    for riga in str(dettaglio).splitlines():
        if riga.strip():
            scrivi("       " + riga)


def titolo_sezione(testo):
    scrivi()
    scrivi("-" * 62)
    scrivi(testo)
    scrivi("-" * 62)


# ---------------------------------------------------------------------------
# 1. Ambiente
# ---------------------------------------------------------------------------

def verifica_ambiente():
    titolo_sezione("1. IL COMPUTER E PYTHON")

    scrivi("       Computer  : {}".format(platform.node()))
    scrivi("       Sistema   : {}".format(platform.platform()))
    scrivi("       Python    : {}".format(sys.version.split()[0]))
    scrivi("       Programma : {}".format(
        "eseguibile compilato" if getattr(sys, "frozen", False) else "avviato dai sorgenti"))
    scrivi()

    if sys.version_info < (3, 8):
        esito(ERRORE, "Versione di Python troppo vecchia",
              "Serve Python 3.8 o superiore. Installato: {}".format(
                  sys.version.split()[0]))
    else:
        esito(OK, "Versione di Python adeguata")

    try:
        from PyQt5.QtCore import QT_VERSION_STR
        import PyQt5
        esito(OK, "PyQt5 installato", "versione Qt: {}".format(QT_VERSION_STR))
    except Exception as e:
        _pyqt5_mancante(e)


def _altri_python_installati():
    """Gli altri Python presenti sul computer, secondo il lanciatore 'py'.

    Su Windows e' normalissimo averne piu' di uno, e i pacchetti installati in
    uno NON si vedono dall'altro."""
    if os.name != "nt":
        return []
    try:
        import subprocess
        esito_comando = subprocess.run(["py", "-0p"], capture_output=True, text=True, timeout=15)
        righe = [r.strip() for r in esito_comando.stdout.splitlines() if r.strip()]
        return [r for r in righe if ":" in r or "\\" in r]
    except Exception:
        return []


def _pyqt5_mancante(errore):
    """PyQt5 non c'e' IN QUESTO Python: non e' detto che manchi sul computer.

    E' successo davvero: questo controllo e' partito con Python 3.11 mentre il
    programma gira con il 3.13, e ha dichiarato PyQt5 non installato e otto
    file del programma mancanti. Erano tutti falsi allarmi, ed era saltato
    proprio il controllo delle linguette - l'unico che si puo' fare soltanto
    qui. Uno strumento di verifica che manda a cercare un problema inesistente
    fa danno quanto uno che tace su un problema vero."""
    dettaglio = [
        "PyQt5 non risulta installato in QUESTO Python:",
        "   {}".format(sys.executable),
        "",
        "Attenzione: non significa che manchi sul computer. Su Windows e'",
        "normale avere piu' versioni di Python, e i pacchetti installati in una",
        "NON si vedono dalle altre.",
    ]
    altri = _altri_python_installati()
    if altri:
        dettaglio += ["", "Altri Python trovati su questo computer:"]
        dettaglio += ["   " + r for r in altri]
        dettaglio += [
            "",
            "Se il programma si avvia normalmente, PyQt5 e' su uno di questi:",
            "rilancia il controllo con quello, per esempio:",
            "   py -3.13 verifica_installazione.py",
        ]
    else:
        dettaglio += [
            "",
            "Se il programma NON parte per niente, allora manca davvero:",
            "apri il Prompt dei comandi e scrivi:  pip install PyQt5",
        ]
    dettaglio += ["", "Dettaglio tecnico: {}".format(errore)]
    esito(ATTENZIONE, "PyQt5 non disponibile in questo Python", "\n".join(dettaglio))


# ---------------------------------------------------------------------------
# 2. Moduli del programma
# ---------------------------------------------------------------------------

def verifica_moduli():
    titolo_sezione("2. I FILE DEL PROGRAMMA")

    moduli = [
        "database.db_manager", "database.backup_manager", "database.archivio",
        "database.esportazione", "utils.percorsi", "utils.logger",
        "utils.diagnostica", "utils.bozze", "utils.segnalazione",
        "models.preventivo", "models.materiale",
        "ui.main_window", "ui.preventivo_window", "ui.magazzino_window",
        "ui.gestione_materiali_window", "ui.impostazioni_archiviazione_window",
        "ui.finestre_preventivo", "ui.responsive", "ui.misure",
        "ui.visualizza_preventivi_window", "ui.anagrafica_clienti_window",
    ]
    mancanti = []
    fermati_da_pyqt = []
    for modulo in moduli:
        try:
            __import__(modulo)
        except ImportError as e:
            # Distinzione che conta: un file che manca davvero e' un problema
            # dell'installazione; un file che non si carica solo perche' manca
            # PyQt5 e' tutt'altra cosa, ed e' successo davvero: lo strumento
            # aveva dichiarato mancanti otto file che erano al loro posto, e
            # consigliava di ricopiare l'aggiornamento. Un consiglio sbagliato
            # fa perdere tempo dietro a un problema che non esiste.
            if "PyQt5" in str(e):
                fermati_da_pyqt.append(modulo)
            else:
                mancanti.append("{}  ->  {}: {}".format(modulo, type(e).__name__, e))
        except Exception as e:
            mancanti.append("{}  ->  {}: {}".format(modulo, type(e).__name__, e))

    if mancanti:
        esito(ERRORE, "Alcuni file del programma mancano o hanno errori",
              "\n".join(mancanti) +
              "\n\nRimedio: potrebbe essere stato copiato solo una parte "
              "dell'aggiornamento.\nRicopia tutti i file del pacchetto e svuota "
              "le cartelle __pycache__.")
    elif fermati_da_pyqt:
        esito(ATTENZIONE, "I file ci sono tutti, ma {} non si aprono senza PyQt5"
                          .format(len(fermati_da_pyqt)),
              "Non manca nessun file: manca PyQt5 in QUESTO Python.\n"
              "Vedi il punto 1 per sapere quale Python usare.")
    else:
        esito(OK, "Tutti i {} file del programma sono al loro posto".format(len(moduli)))


# ---------------------------------------------------------------------------
# 3. Database
# ---------------------------------------------------------------------------

def verifica_database():
    titolo_sezione("3. IL DATABASE")

    try:
        from database.db_manager import risolvi_percorso_db
        from database import backup_manager
        percorso, configurazione = risolvi_percorso_db()
    except Exception as e:
        esito(ERRORE, "Impossibile capire quale database viene usato", e)
        return None

    scrivi("       Percorso: {}".format(percorso))
    su_rete = backup_manager._e_percorso_di_rete(percorso)
    scrivi("       Posizione: {}".format(
        "CARTELLA DI RETE CONDIVISA" if su_rete else "disco di questo computer"))
    scrivi()

    if not os.path.exists(percorso):
        esito(ERRORE, "Il database NON e' raggiungibile",
              "Il file non si trova. Se e' su una cartella di rete, "
              "controlla che la rete sia collegata.")
        return percorso

    dimensione = os.path.getsize(percorso)
    esito(OK, "Database raggiungibile", "dimensione: {:.1f} KB".format(dimensione / 1024))

    inizio = time.time()
    integro, messaggio, _ms = backup_manager.verifica_integrita(percorso)
    durata = time.time() - inizio

    if integro:
        esito(OK, "Il database e' integro",
              "controllo eseguito in {:.2f} secondi".format(durata))
    else:
        esito(ERRORE, "IL DATABASE RISULTA DANNEGGIATO",
              "{}\n\nNON continuare a lavorare: apri "
              "'Impostazioni di archiviazione' e contatta l'assistenza.".format(messaggio))

    if su_rete:
        if durata > 3.0:
            esito(ATTENZIONE, "La cartella di rete e' molto lenta",
                  "Il controllo ha impiegato {:.1f} secondi. Su una rete che "
                  "risponde bene\nsarebbero meno di 1. Una rete lenta aumenta il "
                  "rischio di danneggiare\nil database durante i salvataggi.".format(durata))
        else:
            esito(OK, "La cartella di rete risponde in tempi normali",
                  "{:.2f} secondi".format(durata))

    _controllo_antivirus(percorso, su_rete)
    return percorso


def _controllo_antivirus(percorso, su_rete):
    """L'antivirus e' una causa documentata di danneggiamento.

    Su Windows SQLite protegge il database con LockFile/LockFileEx e da' per
    scontato che funzionino. Un antivirus che apre il file per analizzarlo
    mentre il programma ci scrive puo' interferire con quei blocchi: il
    risultato va dall'errore "database occupato" fino al danneggiamento vero.
    E' un rischio noto e la contromisura standard e' semplice: escludere dalla
    scansione in tempo reale la cartella del database.

    Qui non si prova a indovinare quale antivirus sia installato (ogni
    prodotto risponde in modo diverso e una risposta sbagliata sarebbe
    peggio di nessuna risposta): si dice all'utente cosa controllare e dove."""
    cartella = os.path.dirname(percorso) or "."
    if not su_rete:
        return
    esito(ATTENZIONE, "Da controllare a mano: esclusione dall'antivirus",
          "Un antivirus che analizza il database mentre il programma ci scrive\n"
          "puo' interferire con i blocchi di Windows e danneggiarlo: e' una\n"
          "causa nota, non un'ipotesi.\n\n"
          "Chiedi a chi gestisce i computer di escludere dalla scansione in\n"
          "tempo reale questa cartella, su OGNI postazione:\n"
          "   {}\n\n"
          "Lo stesso vale per programmi di sincronizzazione automatica\n"
          "(OneDrive, Dropbox, Google Drive): non devono sincronizzare\n"
          "quella cartella mentre il programma e' in uso.".format(cartella))


# ---------------------------------------------------------------------------
# 4. Copie di sicurezza
# ---------------------------------------------------------------------------

def verifica_backup(percorso_db):
    titolo_sezione("4. LE COPIE DI SICUREZZA")
    if not percorso_db:
        esito(ATTENZIONE, "Controllo saltato", "database non raggiungibile")
        return

    try:
        from database import archivio
        voci = archivio.elenco_backup(percorso_db)
    except Exception as e:
        esito(ERRORE, "Impossibile leggere le copie di sicurezza", e)
        return

    utilizzabili = [v for v in voci if v["tipo"] != "danneggiato"]
    if not utilizzabili:
        esito(ATTENZIONE, "Non c'e' ancora nessuna copia di sicurezza",
              "Vengono create automaticamente a ogni apertura del programma.\n"
              "Se hai gia' aperto il programma piu' volte, controlla che la "
              "cartella\n'backup' sia scrivibile.")
        return

    esito(OK, "Copie di sicurezza presenti: {}".format(len(utilizzabili)),
          "piu' recente: {}\npiu' vecchia: {}".format(
              utilizzabili[0]["quando_testo"], utilizzabili[-1]["quando_testo"]))

    scrivi("       Controllo del contenuto della copia piu' recente...")
    try:
        dettagli = archivio.dettagli_backup(utilizzabili[0]["percorso"])
        if dettagli["integro"]:
            esito(OK, "La copia piu' recente e' utilizzabile",
                  "contiene: " + archivio.descrivi_contenuto(dettagli))
        else:
            esito(ERRORE, "La copia piu' recente NON e' utilizzabile",
                  dettagli["messaggio"])
    except Exception as e:
        esito(ERRORE, "Impossibile leggere la copia piu' recente", e)

    danneggiate = [v for v in voci if v["tipo"] == "danneggiato"]
    if danneggiate:
        esito(ATTENZIONE,
              "Ci sono {} copie messe da parte perche' danneggiate".format(len(danneggiate)),
              "Significa che in passato il database si e' rovinato almeno una "
              "volta.\nNon e' un problema adesso, ma vale la pena segnalarlo.")


# ---------------------------------------------------------------------------
# 5. Cartelle scrivibili
# ---------------------------------------------------------------------------

def _prova_scrittura(cartella):
    """Scrive un file di prova e lo cancella subito. Ritorna None se riesce."""
    try:
        os.makedirs(cartella, exist_ok=True)
        prova = os.path.join(cartella, ".prova_scrittura_rcs")
        with open(prova, "w") as f:
            f.write("prova")
        os.remove(prova)
        return None
    except Exception as e:
        return "{}: {}".format(type(e).__name__, e)


def verifica_cartelle(percorso_db):
    titolo_sezione("5. LE CARTELLE")

    try:
        from utils import percorsi
    except Exception as e:
        esito(ERRORE, "Impossibile determinare le cartelle", e)
        return

    da_controllare = [
        ("registri (logs)", percorsi.cartella_registri()),
        ("bozze dei preventivi", percorsi.cartella_bozze()),
        ("copie locali", percorsi.cartella_copie_locali()),
    ]
    if percorso_db and os.path.exists(percorso_db):
        da_controllare.append(
            ("copie di sicurezza", os.path.join(os.path.dirname(percorso_db), "backup")))

    for nome, cartella in da_controllare:
        problema = _prova_scrittura(cartella)
        if problema:
            esito(ERRORE, "Cartella NON scrivibile: {}".format(nome),
                  "{}\n{}\n\nSenza permesso di scrittura questa protezione non "
                  "funziona.".format(cartella, problema))
        else:
            esito(OK, "Cartella scrivibile: {}".format(nome))

    try:
        import shutil
        riferimento = percorso_db if percorso_db and os.path.exists(percorso_db) \
            else percorsi.cartella_applicazione()
        liberi = shutil.disk_usage(os.path.dirname(riferimento)).free / (1024 ** 3)
        if liberi < 1:
            esito(ATTENZIONE, "Poco spazio libero sul disco",
                  "{:.1f} GB. Le copie di sicurezza potrebbero non essere "
                  "create.".format(liberi))
        else:
            esito(OK, "Spazio libero sufficiente", "{:.1f} GB".format(liberi))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 6. Interfaccia: le linguette ci stanno?
# ---------------------------------------------------------------------------

def verifica_interfaccia():
    titolo_sezione("6. L'INTERFACCIA (linguette e schermo)")

    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
    except Exception:
        esito(ATTENZIONE, "Controllo saltato", "PyQt5 non disponibile")
        return

    applicazione = QApplication.instance() or QApplication(sys.argv)

    try:
        schermo = applicazione.primaryScreen().availableGeometry()
        scrivi("       Schermo: {} x {} punti".format(schermo.width(), schermo.height()))
        scrivi()
    except Exception:
        pass

    # Le finestre vengono create su un database temporaneo VUOTO: cosi' la
    # prova non tocca in alcun modo i dati veri.
    cartella_prova = tempfile.mkdtemp(prefix="rcs_verifica_")
    db_prova = os.path.join(cartella_prova, "prova.db")

    try:
        from database.db_manager import DatabaseManager
        from database import backup_manager
        # Il backup automatico va disattivato: qui si prova solo l'interfaccia.
        backup_manager._esito_avvio_cache[db_prova] = {
            "integro": True, "avviso": None, "backup": None,
            "copia_sicura": None, "primo_avvio": True, "diagnostica": {}}
        gestore = DatabaseManager(db_path=db_prova)
    except Exception as e:
        esito(ERRORE, "Impossibile preparare la prova dell'interfaccia", e)
        return

    finestre = []
    try:
        from ui.magazzino_window import MagazzinoWindow
        finestre.append(("Gestione Magazzino", lambda: MagazzinoWindow(gestore)))
    except Exception:
        pass
    try:
        from ui.gestione_materiali_window import GestioneMaterialiWindow
        finestre.append(("Gestione Materiali", lambda: GestioneMaterialiWindow(gestore)))
    except Exception:
        pass
    try:
        from ui.impostazioni_archiviazione_window import ImpostazioniArchiviazioneWindow
        finestre.append(("Impostazioni di archiviazione",
                         lambda: ImpostazioniArchiviazioneWindow(gestore, None)))
    except Exception:
        pass

    problemi_linguette = []
    linguette_misurate = 0
    barre_con_riga = []          # barre che disegnano ancora la propria "base"
    barre_controllate = 0
    for nome, costruttore in finestre:
        try:
            finestra = costruttore()
            # Mostrata SENZA comparire davvero sullo schermo: serve solo perche'
            # Qt calcoli le dimensioni reali delle linguette.
            finestra.setAttribute(Qt.WA_DontShowOnScreen, True)
            finestra.show()
            applicazione.processEvents()

            barre = finestra.findChildren(__import__("PyQt5.QtWidgets",
                                                     fromlist=["QTabBar"]).QTabBar)
            for barra in barre:
                # La riga che prosegue verso destra sotto le linguette: la
                # disegna QTabBar da se', non il foglio di stile. E' proprio il
                # difetto che dall'ambiente di sviluppo non si poteva vedere,
                # perche' li' PyQt5 non gira ed e' Qt a disegnarla.
                barre_controllate += 1
                try:
                    if barra.drawBase():
                        barre_con_riga.append(nome)
                except Exception:
                    pass
                metriche = barra.fontMetrics()
                for indice in range(barra.count()):
                    testo = barra.tabText(indice)
                    if not testo:
                        continue
                    try:
                        serve = metriche.horizontalAdvance(testo)
                    except AttributeError:
                        serve = metriche.width(testo)
                    disponibile = barra.tabRect(indice).width()
                    linguette_misurate += 1
                    if disponibile < serve:
                        problemi_linguette.append(
                            "{} -> linguetta '{}': servono {} punti, ce ne sono {}"
                            .format(nome, testo, serve, disponibile))
            finestra.close()
        except Exception as e:
            esito(ATTENZIONE, "Non e' stato possibile provare la finestra '{}'".format(nome),
                  "{}: {}".format(type(e).__name__, e))

    if barre_con_riga:
        esito(ATTENZIONE, "Sotto le linguette viene ancora disegnata una riga",
              "Finestre interessate: {}\n\n"
              "E' la \"base\" della barra delle linguette: prosegue verso destra "
              "oltre l'ultima\ne le fa sembrare legate. Si spegne dal codice, "
              "non dal foglio di stile.\nSegnalalo all'assistenza."
              .format(", ".join(sorted(set(barre_con_riga)))))
    elif barre_controllate:
        esito(OK, "Nessuna riga sotto le linguette",
              "{} barre controllate".format(barre_controllate))

    if problemi_linguette:
        esito(ERRORE, "Il testo di alcune linguette NON ci sta",
              "\n".join(problemi_linguette) +
              "\n\nSegnala questo elenco all'assistenza: serve ad allargarle "
              "della misura giusta\nper i caratteri di QUESTO schermo.")
    elif linguette_misurate:
        esito(OK, "Il testo delle linguette ci sta",
              "{} linguette misurate in {} finestre".format(
                  linguette_misurate, len(finestre)))
    else:
        # Fondamentale: se non si e' misurato nulla NON si puo' dire che va
        # tutto bene. Un controllo che dice sempre OK e' peggio di nessun
        # controllo, perche' da' una sicurezza che non c'e'.
        esito(ATTENZIONE, "Non e' stato possibile misurare le linguette",
              "Il controllo non ha trovato nessuna linguetta da misurare, "
              "quindi\nNON puo' dire se il testo ci sta. Guardale a occhio: in "
              "Gestione\nMagazzino devono leggersi per intero 'Scorte', "
              "'Consumi', 'Fornitori'.")

    try:
        import shutil
        shutil.rmtree(cartella_prova, ignore_errors=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 7. Altri computer collegati
# ---------------------------------------------------------------------------

def verifica_altri_computer(percorso_db):
    titolo_sezione("7. ALTRI COMPUTER")
    if not percorso_db or not os.path.exists(percorso_db):
        esito(ATTENZIONE, "Controllo saltato", "database non raggiungibile")
        return
    try:
        from database import archivio
        altri = archivio.altri_computer_collegati(percorso_db)
    except Exception as e:
        esito(ATTENZIONE, "Impossibile controllare gli altri computer", e)
        return

    if altri:
        esito(ATTENZIONE, "Altri computer risultano avere il programma aperto",
              "\n".join("  - " + pc for pc in altri) +
              "\n\nNon e' un problema di per se'. Diventa importante saperlo "
              "prima di\nripristinare una copia di sicurezza.")
    else:
        esito(OK, "Nessun altro computer risulta collegato adesso")


# ---------------------------------------------------------------------------
# 8. Registro eventi di Windows
# ---------------------------------------------------------------------------

def verifica_eventi_windows():
    titolo_sezione("8. REGISTRO EVENTI DI WINDOWS")
    if os.name != "nt":
        esito(ATTENZIONE, "Controllo saltato", "non siamo su Windows")
        return
    try:
        from utils import diagnostica
        eventi = diagnostica.eventi_windows(ore=168)
    except Exception as e:
        esito(ATTENZIONE, "Impossibile leggere il registro eventi", e)
        return

    if eventi:
        esito(ATTENZIONE,
              "Nell'ultima settimana Windows ha registrato {} eventi rilevanti".format(
                  len(eventi)),
              "\n".join("  - " + e for e in eventi[:10]) +
              "\n\nSpegnimenti improvvisi o errori di rete possono danneggiare "
              "il database.")
    else:
        esito(OK, "Nessun riavvio anomalo o errore di rete nell'ultima settimana")


# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------

def riepilogo():
    errori = [t for s, t in _esiti if s == ERRORE]
    avvisi = [t for s, t in _esiti if s == ATTENZIONE]

    titolo_sezione("RIEPILOGO")
    scrivi("       Controlli eseguiti : {}".format(len(_esiti)))
    scrivi("       Problemi           : {}".format(len(errori)))
    scrivi("       Da tenere d'occhio : {}".format(len(avvisi)))
    scrivi()

    if errori:
        scrivi("   >>> CI SONO PROBLEMI DA RISOLVERE:")
        for t in errori:
            scrivi("       - " + t)
        scrivi()
        scrivi("   Invia all'assistenza il file di questa verifica.")
    elif avvisi:
        scrivi("   >>> Nessun problema grave. Cose da tenere d'occhio:")
        for t in avvisi:
            scrivi("       - " + t)
    else:
        scrivi("   >>> TUTTO A POSTO: l'installazione e' in ordine.")
    scrivi()
    return 1 if errori else 0


def salva_esito():
    nome = "VERIFICA_{}_{}.txt".format(
        "".join(c for c in platform.node() if c.isalnum())[:12] or "pc",
        datetime.now().strftime("%Y%m%d_%H%M"))
    try:
        percorso = os.path.join(os.path.dirname(os.path.abspath(__file__)), nome)
        with open(percorso, "w", encoding="utf-8") as f:
            f.write("\n".join(_righe))
        scrivi("   Esito salvato in: {}".format(percorso))
        return percorso
    except Exception as e:
        scrivi("   (esito non salvato su file: {})".format(e))
        return None


def main():
    scrivi("=" * 62)
    scrivi("  VERIFICA DELL'INSTALLAZIONE - RCS Gestione Preventivi")
    scrivi("  {}".format(datetime.now().strftime("%d/%m/%Y alle %H:%M")))
    scrivi("=" * 62)
    scrivi()
    scrivi("  Questo controllo NON MODIFICA NULLA: legge soltanto.")
    scrivi("  Non tocca il database, non crea copie, non cambia impostazioni.")

    percorso_db = None
    for funzione, argomenti in (
            (verifica_ambiente, ()),
            (verifica_moduli, ()),
    ):
        try:
            funzione(*argomenti)
        except Exception:
            esito(ERRORE, "Il controllo si e' interrotto", traceback.format_exc())

    try:
        percorso_db = verifica_database()
    except Exception:
        esito(ERRORE, "Il controllo del database si e' interrotto",
              traceback.format_exc())

    for funzione, argomenti in (
            (verifica_backup, (percorso_db,)),
            (verifica_cartelle, (percorso_db,)),
            (verifica_interfaccia, ()),
            (verifica_altri_computer, (percorso_db,)),
            (verifica_eventi_windows, ()),
    ):
        try:
            funzione(*argomenti)
        except Exception:
            esito(ERRORE, "Un controllo si e' interrotto", traceback.format_exc())

    codice = riepilogo()
    salva_esito()
    return codice


if __name__ == "__main__":
    try:
        uscita = main()
    except Exception:
        print(traceback.format_exc())
        uscita = 1
    try:
        input("\nPremi INVIO per chiudere...")
    except Exception:
        pass
    sys.exit(uscita)
