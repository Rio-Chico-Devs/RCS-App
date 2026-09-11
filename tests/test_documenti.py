#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rete di sicurezza sui documenti generati per il cliente.

A cosa serve
------------
ui/document_utils.py e' il file piu' aggrovigliato del programma: tre funzioni
da 363, 280 e 218 righe. E' anche l'unico che produce qualcosa che ESCE
dall'azienda - la scheda di taglio - quindi e' quello in cui un difetto si
vede piu' tardi e costa di piu'.

Rimetterlo in ordine sarebbe utile, ma nessuno lo tocca volentieri: non c'e'
modo di sapere se dopo il documento e' ancora quello di prima. Questi test
risolvono proprio quello.

Come funziona
-------------
Per ogni preventivo del database di prova si genera il documento e se ne
calcola l'impronta. Le impronte sono scritte in documenti_attesi.json, in
questa stessa cartella. Se una modifica cambia anche un solo carattere di un
documento, il test lo dice e indica quale preventivo.

Non e' un giudizio sulla BELLEZZA del documento: dice soltanto che e' rimasto
IDENTICO a com'era. Che e' esattamente cio' che serve per riordinare il codice
senza doversi fidare.

Quando il cambiamento e' voluto
-------------------------------
Si rigenerano le impronte:  python tests/test_documenti.py --aggiorna
e si guarda il diff di documenti_attesi.json: deve cambiare solo cio' che ci si
aspettava. Il file va poi committato, cosi' resta scritto che la modifica era
consapevole e non un incidente.

Limite dichiarato: il formato DOCX non e' coperto, perche' richiede la libreria
python-docx che nell'ambiente di sviluppo non e' installabile. Quel formato va
provato a mano.

Esegui con:  python -m unittest tests.test_documenti -v
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import unittest
from datetime import datetime

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RADICE)
sys.path.insert(0, os.path.join(RADICE, "tests"))

import finto_qt
finto_qt.installa()

from ui.document_utils import DocumentUtils

DATABASE_DI_PROVA = os.path.join(RADICE, "data", "materiali.db")
IMPRONTE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "documenti_attesi.json")


class PreventivoPerIlDocumento:
    """La forma che DocumentUtils si aspetta (vedi
    main_window_business_logic.genera_documento_preventivo)."""

    def __init__(self, codice, materiali):
        self.codice_preventivo = codice
        self.materiali = materiali or []


def _senza_la_data_di_oggi(testo):
    """Toglie la data corrente dal documento.

    Il documento riporta la data in cui e' stato generato: senza questo
    passaggio l'impronta cambierebbe ogni giorno e il controllo diventerebbe
    un fastidio da disattivare."""
    oggi = datetime.now()
    for formato in ("%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y%m%d"):
        testo = testo.replace(oggi.strftime(formato), "<DATA>")
    # anche eventuali orari sfuggiti al secondo di scarto
    return re.sub(r"\d{2}/\d{2}/\d{4}", "<DATA>", testo)


def preventivi_di_prova():
    """I preventivi del database versionato insieme al programma."""
    if not os.path.exists(DATABASE_DI_PROVA):
        return []
    conn = sqlite3.connect(DATABASE_DI_PROVA)
    conn.row_factory = sqlite3.Row
    try:
        righe = [dict(r) for r in conn.execute(
            "SELECT * FROM preventivi ORDER BY id")]
    finally:
        conn.close()

    preparati = []
    for riga in righe:
        try:
            materiali = json.loads(riga.get("materiali_utilizzati") or "[]")
        except ValueError:
            materiali = []
        dati_cliente = {
            "nome_cliente": riga.get("nome_cliente") or "",
            "numero_ordine": riga.get("numero_ordine") or "",
            "oggetto_preventivo": riga.get("descrizione") or "",
            "codice": riga.get("codice") or "PREV_{:03d}".format(riga["id"]),
            "misura": riga.get("misura") or "",
            "finitura": riga.get("finitura") or "",
        }
        preparati.append((
            riga["id"],
            PreventivoPerIlDocumento(dati_cliente["codice"], materiali),
            dati_cliente,
        ))
    return preparati


def genera(formato, preventivo, dati_cliente):
    """Il contenuto del documento, senza scriverlo su disco."""
    if formato == "html":
        return DocumentUtils._genera_html_template_specifico(preventivo, dati_cliente)
    if formato == "odt":
        scala = DocumentUtils._calcola_scala(len(preventivo.materiali))
        return DocumentUtils._odt_content(preventivo, dati_cliente, scala)
    raise ValueError(formato)


def impronte_attuali():
    trovate = {}
    for identificativo, preventivo, dati_cliente in preventivi_di_prova():
        for formato in ("html", "odt"):
            contenuto = _senza_la_data_di_oggi(genera(formato, preventivo, dati_cliente))
            chiave = "{}:{}".format(formato, identificativo)
            trovate[chiave] = hashlib.sha256(contenuto.encode("utf-8")).hexdigest()
    return trovate


def impronte_attese():
    if not os.path.exists(IMPRONTE):
        return {}
    with open(IMPRONTE, encoding="utf-8") as f:
        return json.load(f)


class TestDocumentiInvariati(unittest.TestCase):

    def test_ci_sono_preventivi_su_cui_provare(self):
        """Senza questo, i test sotto passerebbero a vuoto non provando nulla:
        e' il difetto peggiore in un controllo."""
        preventivi = preventivi_di_prova()
        self.assertGreaterEqual(len(preventivi), 10,
                                "servono abbastanza preventivi diversi fra loro")
        quanti_materiali = [len(p.materiali) for _i, p, _d in preventivi]
        self.assertGreater(max(quanti_materiali), 5,
                           "deve esserci almeno un preventivo con molti materiali")

    def test_tutti_i_documenti_si_generano(self):
        errori = []
        for identificativo, preventivo, dati_cliente in preventivi_di_prova():
            for formato in ("html", "odt"):
                try:
                    contenuto = genera(formato, preventivo, dati_cliente)
                    self.assertTrue(contenuto, "documento vuoto")
                except Exception as e:
                    errori.append("preventivo {} formato {}: {}: {}".format(
                        identificativo, formato, type(e).__name__, e))
        self.assertEqual(errori, [], "\n".join(errori))

    def test_lodt_e_xml_valido(self):
        """Un ODT con l'XML rotto si apre male o non si apre: meglio saperlo
        qui che davanti al cliente."""
        import xml.dom.minidom
        for identificativo, preventivo, dati_cliente in preventivi_di_prova():
            with self.subTest(preventivo=identificativo):
                xml.dom.minidom.parseString(genera("odt", preventivo, dati_cliente))

    def test_la_generazione_e_ripetibile(self):
        """Se generando due volte lo stesso preventivo uscissero documenti
        diversi, il confronto con le impronte non varrebbe nulla."""
        for identificativo, preventivo, dati_cliente in preventivi_di_prova()[:5]:
            for formato in ("html", "odt"):
                primo = _senza_la_data_di_oggi(genera(formato, preventivo, dati_cliente))
                secondo = _senza_la_data_di_oggi(genera(formato, preventivo, dati_cliente))
                self.assertEqual(primo, secondo,
                                 "preventivo %s, formato %s" % (identificativo, formato))

    def test_i_documenti_sono_identici_a_quelli_di_riferimento(self):
        attese = impronte_attese()
        self.assertTrue(attese,
                        "manca il file delle impronte. Crealo con:\n"
                        "   python tests/test_documenti.py --aggiorna")
        attuali = impronte_attuali()

        mancanti = sorted(set(attese) - set(attuali))
        nuovi = sorted(set(attuali) - set(attese))
        cambiati = sorted(k for k in set(attuali) & set(attese)
                          if attuali[k] != attese[k])

        self.assertEqual(
            (cambiati, mancanti, nuovi), ([], [], []),
            "Il documento prodotto NON e' piu' quello di prima.\n"
            "  cambiati: {}\n  spariti: {}\n  nuovi: {}\n\n"
            "Se la modifica era voluta, rigenera le impronte con\n"
            "   python tests/test_documenti.py --aggiorna\n"
            "e controlla il diff di documenti_attesi.json prima di committarlo."
            .format(cambiati, mancanti, nuovi))

    def test_il_contenuto_del_cliente_finisce_davvero_nel_documento(self):
        """Le impronte dicono 'identico', non 'giusto': serve almeno una prova
        che i dati del preventivo compaiano nel documento."""
        provati = 0
        for identificativo, preventivo, dati_cliente in preventivi_di_prova():
            if not dati_cliente["codice"]:
                continue
            for formato in ("html", "odt"):
                contenuto = genera(formato, preventivo, dati_cliente)
                self.assertIn(dati_cliente["codice"], contenuto,
                              "il codice del preventivo %s non compare nel %s"
                              % (identificativo, formato))
            provati += 1
        self.assertGreater(provati, 0, "nessun preventivo aveva un codice da cercare")


def aggiorna_impronte():
    attuali = impronte_attuali()
    with open(IMPRONTE, "w", encoding="utf-8") as f:
        json.dump(attuali, f, indent=2, sort_keys=True)
        f.write("\n")
    print("Scritte {} impronte in {}".format(len(attuali), IMPRONTE))


if __name__ == "__main__":
    if "--aggiorna" in sys.argv:
        aggiorna_impronte()
    else:
        unittest.main(verbosity=2)
