#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prove di resistenza: uso prolungato, grandi quantita' di dati, crescita nel
tempo.

Servono a rispondere a domande che i test normali non toccano:
  - dopo due anni di lavoro il programma e' ancora sano?
  - i backup si accumulano all'infinito o restano sotto controllo?
  - con migliaia di preventivi quanto ci mette ad aprirsi?
  - qualcosa cresce senza limite (memoria, file, righe di registro)?

Esegui con:  python -m unittest tests.test_resistenza -v
Per la versione lunga:  RCS_TEST_PESANTE=1 python -m unittest tests.test_resistenza
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import archivio
from database import backup_manager as bm
from database.db_manager import DatabaseManager

PESANTE = os.environ.get("RCS_TEST_PESANTE") == "1"


def preventivo_finto(indice=0):
    return {
        'nome_cliente': f'Cliente {indice % 40}',
        'numero_ordine': f'ORD-{indice:05d}',
        'misura': '1200 mm', 'descrizione': f'Tubo carbonio {indice}',
        'codice': f'TC-{indice}', 'finitura': 'Lucida',
        'costo_totale_materiali': 100.0 + indice, 'costi_accessori': 10.0,
        'minuti_taglio': 15.0, 'minuti_avvolgimento': 40.0, 'minuti_pulizia': 10.0,
        'minuti_rettifica': 5.0, 'minuti_imballaggio': 8.0, 'tot_mano_opera': 78.0,
        'subtotale': 188.0 + indice, 'maggiorazione_25': 47.0,
        'preventivo_finale': 235.0 + indice, 'prezzo_cliente': 300.0 + indice,
        'materiali_utilizzati': [
            {'materiale_nome': 'Fibra 200g', 'diametro': 40, 'lunghezza': 1200,
             'costo_totale': 90.0},
        ],
    }


class BaseResistenza(unittest.TestCase):
    def setUp(self):
        bm._esito_avvio_cache.clear()
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "materiali.db")
        self.backup_dir = os.path.join(self.tmp, "backup")
        # niente copie locali sul disco dell'ambiente di prova
        self._orig_app = bm.cartella_app
        bm.cartella_app = lambda: self.tmp

    def tearDown(self):
        bm.cartella_app = self._orig_app
        bm._esito_avvio_cache.clear()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _nuovo_avvio(self):
        """Simula la chiusura e riapertura del programma."""
        bm._esito_avvio_cache.clear()
        return DatabaseManager(db_path=self.db)


# ---------------------------------------------------------------------------
# Uso prolungato
# ---------------------------------------------------------------------------

class TestUsoProlungato(BaseResistenza):

    def test_due_anni_di_backup_non_si_accumulano(self):
        """Due anni di aperture quotidiane: le copie devono restare poche
        decine, non migliaia, e devono coprire tutto il periodo utile."""
        os.makedirs(self.backup_dir, exist_ok=True)
        gestore = DatabaseManager(db_path=self.db)
        gestore.add_preventivo(preventivo_finto())

        giorni = 730
        aperture_al_giorno = 3
        adesso = datetime(2026, 9, 1, 18, 0, 0)
        creati = 0

        for giorno in range(giorni, 0, -1):
            data = adesso - timedelta(days=giorno)
            for apertura in range(aperture_al_giorno):
                momento = data.replace(hour=8 + apertura * 4)
                nome = bm.PREFISSO_BACKUP + momento.strftime(bm.FORMATO_TIMESTAMP) + ".db"
                shutil.copy2(self.db, os.path.join(self.backup_dir, nome))
                creati += 1
            # la pulizia gira a ogni apertura, come nella realta'
            bm.applica_retention(self.backup_dir, adesso=data.replace(hour=20))

        rimasti = bm.elenca_backup(self.backup_dir)
        print(f"\n    [uso prolungato] {creati} copie create in 2 anni "
              f"-> {len(rimasti)} conservate")

        self.assertLess(len(rimasti), 80,
                        "le copie non devono accumularsi senza limite")
        self.assertGreater(len(rimasti), 25,
                           "devono restare abbastanza copie da coprire il periodo")

        # Deve esserci copertura del mese appena passato
        recenti = [t for t, _n in rimasti if t > adesso - timedelta(days=31)]
        self.assertGreaterEqual(len(recenti), 20,
                                "l'ultimo mese deve essere coperto giorno per giorno")

        # e copertura dei mesi piu' lontani
        vecchie = [t for t, _n in rimasti if t < adesso - timedelta(days=90)]
        self.assertGreaterEqual(len(vecchie), 3,
                                "devono restare copie anche dei mesi lontani")

    def test_lo_spazio_occupato_resta_prevedibile(self):
        """Con un database da mezzo mega, due anni di copie non devono
        occupare piu' di poche decine di mega."""
        os.makedirs(self.backup_dir, exist_ok=True)
        gestore = DatabaseManager(db_path=self.db)
        for i in range(50):
            gestore.add_preventivo(preventivo_finto(i))

        adesso = datetime(2026, 9, 1, 18, 0, 0)
        for giorno in range(400, 0, -1):
            data = adesso - timedelta(days=giorno)
            nome = bm.PREFISSO_BACKUP + data.strftime(bm.FORMATO_TIMESTAMP) + ".db"
            shutil.copy2(self.db, os.path.join(self.backup_dir, nome))
            bm.applica_retention(self.backup_dir, adesso=data)

        totale = sum(os.path.getsize(os.path.join(self.backup_dir, n))
                     for _t, n in bm.elenca_backup(self.backup_dir))
        singolo = os.path.getsize(self.db)
        print(f"\n    [spazio] database {singolo//1024} KB -> "
              f"copie totali {totale//1024} KB")
        self.assertLess(totale, singolo * 60,
                        "lo spazio occupato dalle copie deve restare proporzionato")

    def test_molti_avvii_consecutivi(self):
        """Il programma aperto e chiuso molte volte di seguito: nessun errore,
        nessun accumulo anomalo."""
        gestore = DatabaseManager(db_path=self.db)
        gestore.add_preventivo(preventivo_finto())

        quanti = 60 if PESANTE else 25
        for _ in range(quanti):
            gestore = self._nuovo_avvio()
            integro, messaggio = gestore.verifica_integrita()
            self.assertTrue(integro, f"database rovinato dopo un riavvio: {messaggio}")

        copie = bm.elenca_backup(self.backup_dir)
        print(f"\n    [avvii] {quanti} aperture -> {len(copie)} copie")
        # Verifica esatta: con l'assertion debole di prima (<= quanti+2) il
        # difetto per cui le copie fatte nello stesso secondo si sovrascrivevano
        # passava inosservato (25 aperture producevano 1 sola copia).
        self.assertEqual(len(copie), quanti,
                         "ogni apertura deve produrre la propria copia, "
                         "anche se avviene nello stesso secondo di un'altra")
        self.assertEqual(len(gestore.get_all_preventivi()), 1,
                         "i dati non devono cambiare per il solo riavvio")


# ---------------------------------------------------------------------------
# Grandi quantita' di dati
# ---------------------------------------------------------------------------

class TestGrandiQuantita(BaseResistenza):

    def _riempi(self, quanti):
        gestore = DatabaseManager(db_path=self.db)
        gestore.verifica_dopo_scrittura = False   # altrimenti si verifica a ogni riga
        inizio = time.time()
        with sqlite3.connect(self.db) as conn:
            cur = conn.cursor()
            for i in range(quanti):
                dati = preventivo_finto(i)
                cur.execute("""
                    INSERT INTO preventivi (data_creazione, numero_revisione,
                        nome_cliente, numero_ordine, misura, descrizione, codice, finitura,
                        costo_totale_materiali, costi_accessori, minuti_taglio,
                        minuti_avvolgimento, minuti_pulizia, minuti_rettifica,
                        minuti_imballaggio, tot_mano_opera, subtotale, maggiorazione_25,
                        preventivo_finale, prezzo_cliente, materiali_utilizzati,
                        note_revisione, storico_modifiche)
                    VALUES (?,1,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'','[]')
                """, (datetime.now().isoformat(), dati['nome_cliente'],
                      dati['numero_ordine'], dati['misura'], dati['descrizione'],
                      dati['codice'], dati['finitura'], dati['costo_totale_materiali'],
                      dati['costi_accessori'], dati['minuti_taglio'],
                      dati['minuti_avvolgimento'], dati['minuti_pulizia'],
                      dati['minuti_rettifica'], dati['minuti_imballaggio'],
                      dati['tot_mano_opera'], dati['subtotale'], dati['maggiorazione_25'],
                      dati['preventivo_finale'], dati['prezzo_cliente'],
                      str(dati['materiali_utilizzati'])))
            conn.commit()
        return gestore, time.time() - inizio

    def test_diecimila_preventivi(self):
        """Quanti anni di lavoro sono 10.000 preventivi? Al ritmo attuale
        (circa 100 all'anno) sono un secolo. Il programma deve reggere."""
        quanti = 20000 if PESANTE else 10000
        gestore, secondi_scrittura = self._riempi(quanti)
        dimensione = os.path.getsize(self.db)

        inizio = time.time()
        tutti = gestore.get_all_preventivi()
        lettura = time.time() - inizio

        inizio = time.time()
        integro, _msg = gestore.verifica_integrita()
        verifica = time.time() - inizio

        inizio = time.time()
        bm._esito_avvio_cache.clear()
        bm.esegui_backup_avvio(self.db)
        backup = time.time() - inizio

        print(f"\n    [grandi quantita'] {quanti} preventivi, "
              f"database {dimensione//1024} KB")
        print(f"      scrittura : {secondi_scrittura:.2f} s")
        print(f"      lettura   : {lettura:.2f} s  ({len(tutti)} righe)")
        print(f"      verifica  : {verifica:.2f} s")
        print(f"      backup    : {backup:.2f} s")

        self.assertEqual(len(tutti), quanti)
        self.assertTrue(integro)
        self.assertLess(lettura, 5.0, "l'elenco preventivi diventa troppo lento")
        self.assertLess(verifica, 5.0, "il controllo all'avvio diventa troppo lento")
        self.assertLess(backup, 15.0, "il backup all'avvio diventa troppo lento")

    def test_ricerca_con_molti_dati(self):
        """Le ricerche per cliente devono restare rapide anche con molti dati."""
        quanti = 10000 if PESANTE else 4000
        gestore, _s = self._riempi(quanti)

        inizio = time.time()
        with sqlite3.connect(self.db) as conn:
            righe = conn.execute(
                "SELECT COUNT(*) FROM preventivi WHERE nome_cliente = ?",
                ("Cliente 7",)).fetchone()[0]
        durata = time.time() - inizio
        print(f"\n    [ricerca] {righe} risultati su {quanti} in {durata:.3f} s")
        self.assertGreater(righe, 0)
        self.assertLess(durata, 2.0)

    def test_preventivo_enorme(self):
        """Un preventivo con moltissimi materiali e testi lunghi: il campo
        materiali_utilizzati finisce in pagine di overflow di SQLite, che e'
        proprio la zona dove il database si era danneggiato."""
        gestore = DatabaseManager(db_path=self.db)
        dati = preventivo_finto()
        dati['materiali_utilizzati'] = [
            {'materiale_nome': f'Materiale {i} ' + 'x' * 200,
             'diametro': i, 'lunghezza': 1000 + i, 'costo_totale': float(i)}
            for i in range(300)
        ]
        dati['descrizione'] = 'D' * 5000

        nuovo_id = gestore.add_preventivo(dati)
        self.assertIsNotNone(nuovo_id)

        integro, messaggio = gestore.verifica_integrita()
        self.assertTrue(integro, f"database rovinato da un preventivo grande: {messaggio}")

        riletto = gestore.get_preventivo_by_id(nuovo_id)
        self.assertIsNotNone(riletto)
        print(f"\n    [preventivo enorme] salvato e riletto, "
              f"database {os.path.getsize(self.db)//1024} KB")


# ---------------------------------------------------------------------------
# Crescita nel tempo (perdite di memoria e di spazio)
# ---------------------------------------------------------------------------

class TestCrescitaNelTempo(BaseResistenza):

    def test_il_registro_delle_finestre_non_cresce(self):
        """Aprendo e chiudendo molte schermate, l'elenco non deve gonfiarsi."""
        from ui import finestre_preventivo as reg
        reg._aperte.clear()

        class FintaFinestra:
            def __init__(self): self.viva = True
            def isVisible(self): return self.viva

        for _ in range(500):
            finestra = reg.registra(FintaFinestra())
            finestra.viva = False        # l'utente la chiude

        rimaste = reg.quante()
        print(f"\n    [memoria] 500 schermate aperte e chiuse -> {rimaste} in elenco")
        self.assertLessEqual(rimaste, 1,
                             "le schermate chiuse devono uscire dall'elenco")
        reg._aperte.clear()

    def test_le_bozze_non_si_accumulano(self):
        from utils import bozze
        cartella = os.path.join(self.tmp, "bozze")
        os.makedirs(cartella, exist_ok=True)
        originale = bozze.cartella_bozze
        bozze.cartella_bozze = lambda: cartella
        try:
            # bozze vecchie di mesi
            for i in range(50):
                bozze.salva_bozza(f"vecchia{i}", {"nome_cliente": f"C{i}"})
            for nome in os.listdir(cartella):
                percorso = os.path.join(cartella, nome)
                vecchio = (datetime.now() - timedelta(days=90)).timestamp()
                os.utime(percorso, (vecchio, vecchio))
                import json
                with open(percorso, encoding="utf-8") as f:
                    contenuto = json.load(f)
                contenuto["salvata_il"] = (datetime.now() - timedelta(days=90)).isoformat()
                with open(percorso, "w", encoding="utf-8") as f:
                    json.dump(contenuto, f)

            bozze.pulisci_vecchie(giorni=30)
            rimaste = len(bozze.elenca_bozze())
            print(f"\n    [bozze] 50 bozze vecchie di 90 giorni -> {rimaste} rimaste")
            self.assertEqual(rimaste, 0)
        finally:
            bozze.cartella_bozze = originale

    def test_il_registro_scritture_cresce_lentamente(self):
        """Il registro delle scritture e' un file di testo: deve restare
        piccolo anche dopo anni."""
        from utils import diagnostica
        cartella = os.path.join(self.tmp, "logs")
        os.makedirs(cartella, exist_ok=True)
        originale = diagnostica.cartella_locale
        diagnostica.cartella_locale = lambda: cartella
        try:
            scritture_al_giorno = 30
            giorni = 365
            for _ in range(scritture_al_giorno * giorni // 10):   # campione
                diagnostica.registra_scrittura("add_preventivo", "id 1", "ok", 40)

            percorso = os.path.join(cartella, f"scritture_{datetime.now():%Y%m}.log")
            dimensione = os.path.getsize(percorso)
            stimato_anno = dimensione * 10
            print(f"\n    [registro] stima per un anno di lavoro: "
                  f"{stimato_anno//1024} KB")
            self.assertLess(stimato_anno, 5 * 1024 * 1024,
                            "il registro non deve superare qualche megabyte l'anno")
        finally:
            diagnostica.cartella_locale = originale

    def test_le_copie_protette_hanno_un_limite(self):
        """Anche le copie 'protette dalla rotazione' devono avere un tetto,
        altrimenti sono loro a riempire il disco."""
        os.makedirs(self.backup_dir, exist_ok=True)
        DatabaseManager(db_path=self.db)
        sicurezza = os.path.join(self.backup_dir, "sicurezza")

        for i in range(20):
            momento = datetime.now() - timedelta(minutes=i)
            nome = bm.PREFISSO_SICUREZZA + momento.strftime(bm.FORMATO_TIMESTAMP) + ".db"
            os.makedirs(sicurezza, exist_ok=True)
            shutil.copy2(self.db, os.path.join(sicurezza, nome))
        bm._limita_numero_file(sicurezza, bm.PREFISSO_SICUREZZA, bm.MAX_SICUREZZA)

        rimaste = len(os.listdir(sicurezza))
        print(f"\n    [copie protette] 20 create -> {rimaste} conservate "
              f"(limite {bm.MAX_SICUREZZA})")
        self.assertLessEqual(rimaste, bm.MAX_SICUREZZA)


if __name__ == "__main__":
    unittest.main(verbosity=2)
