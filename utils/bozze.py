#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Bozze automatiche dei preventivi aperti.
Uso riservato esclusivamente a RCS

Scopo: se il PC si spegne (aggiornamento di Windows, mancanza di corrente,
blocco) mentre ci sono preventivi aperti e non salvati, il lavoro non deve
sparire nel nulla.

Ogni finestra di preventivo aperta salva periodicamente il proprio contenuto in
un file sul disco LOCALE (mai sulla cartella di rete). Al riavvio, se la
chiusura precedente non è stata regolare, le bozze rimaste vengono presentate
all'utente.

Le bozze NON sono preventivi: non finiscono nel database e non hanno un numero.
Servono solo a non perdere il lavoro fatto.
"""

import json
import logging
import os
from datetime import datetime, timedelta

GIORNI_CONSERVAZIONE = 30


def _log():
    return logging.getLogger('rcs')


def cartella_bozze():
    """Dove finiscono le bozze dei preventivi aperti.
    La logica dei percorsi sta in utils/percorsi.py, in un posto solo."""
    from utils import percorsi
    return percorsi.cartella_bozze()


def _percorso(chiave):
    sicura = "".join(c for c in str(chiave) if c.isalnum() or c in "-_")
    return os.path.join(cartella_bozze(), "bozza_{}.json".format(sicura or "senza_nome"))


def salva_bozza(chiave, dati, modalita="nuovo", preventivo_id=None):
    """Salva (o aggiorna) la bozza di una finestra aperta.

    'chiave' identifica la finestra; 'dati' è il contenuto del preventivo così
    come verrebbe salvato nel database."""
    try:
        contenuto = {
            "salvata_il": datetime.now().isoformat(timespec="seconds"),
            "modalita": modalita,
            "preventivo_id": preventivo_id,
            "dati": dati,
        }
        percorso = _percorso(chiave)
        temporaneo = percorso + ".tmp"
        with open(temporaneo, "w", encoding="utf-8") as f:
            json.dump(contenuto, f, ensure_ascii=False, indent=2, default=str)
        os.replace(temporaneo, percorso)
        return True
    except Exception as e:
        _log().warning("Bozza non salvata (%s): %s", chiave, e)
        return False


def elimina_bozza(chiave):
    """Toglie la bozza: il preventivo è stato salvato o chiuso di proposito."""
    try:
        percorso = _percorso(chiave)
        if os.path.exists(percorso):
            os.remove(percorso)
    except Exception:
        pass


def elimina_bozza_da_file(bozza):
    """Cancella una bozza a partire dalla voce restituita da elenca_bozze().

    Serve dopo averla riaperta nel programma: da quel momento il lavoro e' di
    nuovo in una schermata, che salvera' la propria bozza per conto suo."""
    try:
        percorso = bozza.get("_file") if isinstance(bozza, dict) else None
        if percorso and os.path.exists(percorso):
            os.remove(percorso)
            return True
    except Exception as e:
        _log().warning("Bozza non eliminata: %s", e)
    return False


def elenca_bozze():
    """Ritorna le bozze presenti, dalla più recente."""
    trovate = []
    try:
        for nome in os.listdir(cartella_bozze()):
            if not (nome.startswith("bozza_") and nome.endswith(".json")):
                continue
            percorso = os.path.join(cartella_bozze(), nome)
            try:
                with open(percorso, "r", encoding="utf-8") as f:
                    contenuto = json.load(f)
                contenuto["_file"] = percorso
                trovate.append(contenuto)
            except Exception:
                continue
    except Exception:
        return []
    trovate.sort(key=lambda c: c.get("salvata_il", ""), reverse=True)
    return trovate


def descrivi_bozza(bozza):
    """Una riga comprensibile che descrive la bozza, per mostrarla all'utente."""
    dati = bozza.get("dati") or {}
    quando = bozza.get("salvata_il", "")
    try:
        quando = datetime.fromisoformat(quando).strftime("%d/%m/%Y alle %H:%M")
    except Exception:
        pass

    cliente = (dati.get("nome_cliente") or "").strip() or "cliente non indicato"
    ordine = (dati.get("numero_ordine") or "").strip()
    descrizione = (dati.get("descrizione") or "").strip()
    materiali = dati.get("materiali_utilizzati") or []
    try:
        prezzo = float(dati.get("prezzo_cliente") or 0)
    except (TypeError, ValueError):
        prezzo = 0.0

    pezzi = [cliente]
    if ordine:
        pezzi.append("ordine {}".format(ordine))
    if descrizione:
        pezzi.append(descrizione[:40])
    pezzi.append("{} material{}".format(len(materiali), "e" if len(materiali) == 1 else "i"))
    if prezzo:
        pezzi.append("€ {:.2f}".format(prezzo))

    return "{} — {}".format(quando, " · ".join(pezzi))


def _riga(etichetta, valore, larghezza=24):
    """Riga allineata con i puntini: 'Nome ......... Bianchi SpA'."""
    testo = "" if valore is None else str(valore)
    return "  {} {}".format((etichetta + " ").ljust(larghezza, "."), testo)


def _euro(valore):
    try:
        return "€ {:,.2f}".format(float(valore or 0)).replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "€ 0,00"


def _numero(valore, unita=""):
    try:
        n = float(valore or 0)
    except (TypeError, ValueError):
        return "0"
    testo = "{:g}".format(round(n, 2)).replace(".", ",")   # virgola decimale
    return "{} {}".format(testo, unita).strip()


def _blocco_bozza(bozza, progressivo):
    """Costruisce il testo di UNA bozza, pensato per essere letto accanto al
    programma mentre si ricompila il preventivo."""
    dati = bozza.get("dati") or {}
    righe = []

    quando = bozza.get("salvata_il", "")
    try:
        quando = datetime.fromisoformat(quando).strftime("%d/%m/%Y alle %H:%M")
    except Exception:
        pass

    righe.append("=" * 66)
    righe.append("PREVENTIVO NON SALVATO n. {}".format(progressivo))
    righe.append("Ultimo aggiornamento automatico: {}".format(quando or "sconosciuto"))
    modalita = bozza.get("modalita")
    if modalita and modalita != "nuovo":
        righe.append("Era una {} del preventivo esistente n. {}".format(
            modalita, bozza.get("preventivo_id") or "?"))
    righe.append("=" * 66)
    righe.append("")

    righe.append("DATI CLIENTE")
    righe.append(_riga("Cliente", dati.get("nome_cliente") or "(non indicato)"))
    righe.append(_riga("Numero ordine", dati.get("numero_ordine")))
    righe.append(_riga("Descrizione", dati.get("descrizione")))
    righe.append(_riga("Codice", dati.get("codice")))
    righe.append(_riga("Misura", dati.get("misura")))
    righe.append(_riga("Finitura", dati.get("finitura")))
    righe.append("")

    materiali = dati.get("materiali_utilizzati") or []
    righe.append("MATERIALI INSERITI ({})".format(len(materiali)))
    if not materiali:
        righe.append("  (nessun materiale era ancora stato inserito)")
    for indice, materiale in enumerate(materiali, start=1):
        if not isinstance(materiale, dict):
            continue
        nome = materiale.get("materiale_nome") or "materiale senza nome"
        righe.append("  {}. {}".format(indice, nome))
        righe.append(_riga("   diametro", _numero(materiale.get("diametro"), "mm"), 22))
        righe.append(_riga("   lunghezza", _numero(materiale.get("lunghezza"), "mm"), 22))
        righe.append(_riga("   giri", _numero(materiale.get("giri")), 22))
        righe.append(_riga("   spessore", _numero(materiale.get("spessore"), "mm"), 22))
        if materiale.get("is_conica"):
            righe.append(_riga("   conica", "sì", 22))
            righe.append(_riga("   conicità lato", _numero(materiale.get("conicita_lato")), 22))
        righe.append(_riga("   maggiorazione", _numero(materiale.get("maggiorazione"), "%"), 22))
        righe.append(_riga("   costo", _euro(materiale.get("costo_totale")), 22))
    righe.append("")

    righe.append("MINUTI DI LAVORAZIONE")
    righe.append(_riga("Taglio", _numero(dati.get("minuti_taglio"), "min")))
    righe.append(_riga("Avvolgimento", _numero(dati.get("minuti_avvolgimento"), "min")))
    righe.append(_riga("Pulizia", _numero(dati.get("minuti_pulizia"), "min")))
    righe.append(_riga("Rettifica", _numero(dati.get("minuti_rettifica"), "min")))
    righe.append(_riga("Imballaggio", _numero(dati.get("minuti_imballaggio"), "min")))
    righe.append("")

    righe.append("IMPORTI CALCOLATI")
    righe.append(_riga("Costo materiali", _euro(dati.get("costo_totale_materiali"))))
    righe.append(_riga("Costi accessori", _euro(dati.get("costi_accessori"))))
    righe.append(_riga("Manodopera", _euro(dati.get("tot_mano_opera"))))
    righe.append(_riga("Subtotale", _euro(dati.get("subtotale"))))
    righe.append(_riga("Maggiorazione 25%", _euro(dati.get("maggiorazione_25"))))
    righe.append(_riga("Preventivo finale", _euro(dati.get("preventivo_finale"))))
    righe.append(_riga("Prezzo al cliente", _euro(dati.get("prezzo_cliente"))))
    righe.append("")

    return "\n".join(righe)


def genera_file_recupero(elenco=None):
    """Scrive un file di testo con TUTTI i preventivi non salvati, formattato
    per essere tenuto aperto accanto al programma mentre si ricompila.

    Ritorna il percorso del file, oppure None se non c'era nulla da recuperare."""
    elenco = elenco if elenco is not None else elenca_bozze()
    if not elenco:
        return None

    testo = [
        "RECUPERO PREVENTIVI NON SALVATI",
        "Generato il {}".format(datetime.now().strftime("%d/%m/%Y alle %H:%M")),
        "",
        "Il programma si è chiuso in modo anomalo mentre {} in lavorazione.".format(
            "c'era 1 preventivo" if len(elenco) == 1
            else "c'erano {} preventivi".format(len(elenco))),
        "Qui sotto trovi tutti i dati che erano stati inseriti, così puoi",
        "ricompilarli senza doverli ricostruire a memoria.",
        "",
    ]
    for progressivo, bozza in enumerate(elenco, start=1):
        testo.append(_blocco_bozza(bozza, progressivo))

    testo.append("=" * 66)
    testo.append("Fine del recupero. Questo file può essere cancellato una volta")
    testo.append("reinseriti i preventivi.")

    try:
        nome = "RECUPERO_preventivi_{}.txt".format(datetime.now().strftime("%Y%m%d_%H%M%S"))
        percorso = os.path.join(cartella_bozze(), nome)
        with open(percorso, "w", encoding="utf-8") as f:
            f.write("\n".join(testo))
        return percorso
    except Exception as e:
        _log().error("File di recupero non scrivibile: %s", e)
        return None


def pulisci_vecchie(giorni=GIORNI_CONSERVAZIONE):
    """Elimina le bozze più vecchie di 'giorni'."""
    limite = datetime.now() - timedelta(days=giorni)
    for bozza in elenca_bozze():
        try:
            if datetime.fromisoformat(bozza.get("salvata_il", "")) < limite:
                os.remove(bozza["_file"])
        except Exception:
            continue
