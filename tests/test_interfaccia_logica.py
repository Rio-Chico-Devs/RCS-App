#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Esecuzione vera della logica delle finestre, con un PyQt5 finto.

Perche' questo file esiste
--------------------------
Ogni difetto sfuggito alle verifiche precedenti (testo tagliato nelle
linguette, e prima ancora la finestra che spariva) stava nel codice
dell'interfaccia, l'unico che non potevo eseguire. L'analisi statica trova i
nomi sbagliati, ma non trova un parametro che non combacia, un flusso che si
interrompe a meta' o un attributo usato prima di essere creato.

Qui PyQt5 viene sostituito da classi finte (tests/finto_qt.py) e le funzioni
vengono ESEGUITE per davvero. Non si verifica l'aspetto - quello resta da
guardare a occhio - ma si verifica che il codice arrivi in fondo.

Esegui con:  python -m unittest tests.test_interfaccia_logica -v
"""

import os
import shutil
import sys
import tempfile
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RADICE)
sys.path.insert(0, os.path.join(RADICE, "tests"))

import finto_qt
finto_qt.installa()

from database import backup_manager as bm
from database.db_manager import DatabaseManager
from ui import finestre_preventivo
from ui.main_window_business_logic import MainWindowBusinessLogic
from utils import bozze, diagnostica, segnalazione


def dati_preventivo(cliente="Bianchi SpA"):
    return {
        "nome_cliente": cliente, "numero_ordine": "ORD-77", "misura": "1200 mm",
        "descrizione": "Tubo carbonio", "codice": "TC-1", "finitura": "Lucida",
        "costo_totale_materiali": 100.0, "costi_accessori": 10.0,
        "minuti_taglio": 15.0, "minuti_avvolgimento": 40.0, "minuti_pulizia": 10.0,
        "minuti_rettifica": 5.0, "minuti_imballaggio": 8.0, "tot_mano_opera": 78.0,
        "subtotale": 188.0, "maggiorazione_25": 47.0, "preventivo_finale": 235.0,
        "prezzo_cliente": 300.0,
        "materiali_utilizzati": [
            {"materiale_nome": "Fibra 200g", "diametro": 40.0, "lunghezza": 1200.0,
             "giri": 6, "spessore": 0.25, "costo_totale": 180.0, "maggiorazione": 10.0},
        ],
    }


class FintaFinestraPrincipale:
    """Sta al posto di MainWindow: le funzioni di logica ricevono questo."""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.preventivo_window = None
        self.impostazioni_archiviazione_window = None
        self.visualizza_preventivi_window = None
        self.lista_preventivi = finto_qt._Base()

    def preventivo_salvato(self):
        pass


class BaseInterfaccia(unittest.TestCase):
    def setUp(self):
        finto_qt.RispostaAutomatica.azzera()
        finestre_preventivo._aperte.clear()
        bm._esito_avvio_cache.clear()

        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "materiali.db")
        self._orig_app = bm.cartella_app
        self._orig_bozze = bozze.cartella_bozze
        self._orig_diag = diagnostica.cartella_locale
        self._orig_segn = segnalazione.cartella_app
        bm.cartella_app = lambda: self.tmp
        # Senza questo la segnalazione finirebbe nella cartella del progetto
        segnalazione.cartella_app = lambda: self.tmp

        # IMPORTANTE: MainWindow crea DatabaseManager() senza argomenti, quindi
        # userebbe il database VERO del progetto. Senza questa deviazione i test
        # scriverebbero backup sui dati reali e ne cancellerebbero di vecchi
        # applicando la rotazione: e' successo davvero mentre scrivevo questi test.
        import database.db_manager as modulo_db
        self._orig_risolvi = modulo_db.risolvi_percorso_db
        modulo_db.risolvi_percorso_db = lambda: (self.db, {})
        os.makedirs(os.path.join(self.tmp, "bozze"), exist_ok=True)
        os.makedirs(os.path.join(self.tmp, "logs"), exist_ok=True)
        bozze.cartella_bozze = lambda: os.path.join(self.tmp, "bozze")
        diagnostica.cartella_locale = lambda: os.path.join(self.tmp, "logs")

        self.gestore = DatabaseManager(db_path=self.db)
        self.finestra = FintaFinestraPrincipale(self.gestore)

    def tearDown(self):
        bm.cartella_app = self._orig_app
        bozze.cartella_bozze = self._orig_bozze
        diagnostica.cartella_locale = self._orig_diag
        segnalazione.cartella_app = self._orig_segn
        import database.db_manager as modulo_db
        modulo_db.risolvi_percorso_db = self._orig_risolvi
        finestre_preventivo._aperte.clear()
        bm._esito_avvio_cache.clear()
        shutil.rmtree(self.tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Apertura delle schermate di preventivo
# ---------------------------------------------------------------------------

class TestAperturaPreventivi(BaseInterfaccia):

    def test_apre_una_schermata(self):
        MainWindowBusinessLogic.apri_preventivo(self.finestra)
        self.assertEqual(finestre_preventivo.quante(), 1,
                         "la schermata deve risultare registrata")
        self.assertIsNotNone(self.finestra.preventivo_window)

    def test_apre_piu_schermate_scegliendo_nuova_scheda(self):
        """La correzione del difetto per cui la prima spariva."""
        MainWindowBusinessLogic.apri_preventivo(self.finestra)
        finto_qt.RispostaAutomatica.scelta_pulsante = 2   # "Apri nuova scheda"
        MainWindowBusinessLogic.apri_preventivo(self.finestra)
        MainWindowBusinessLogic.apri_preventivo(self.finestra)

        self.assertEqual(finestre_preventivo.quante(), 3,
                         "devono restare aperte tutte e tre")

    def test_continua_la_compilazione_non_apre_nulla(self):
        MainWindowBusinessLogic.apri_preventivo(self.finestra)
        finto_qt.RispostaAutomatica.scelta_pulsante = 1   # "Continua la compilazione"
        MainWindowBusinessLogic.apri_preventivo(self.finestra)
        self.assertEqual(finestre_preventivo.quante(), 1)

    def test_il_dialogo_dice_le_parole_giuste(self):
        MainWindowBusinessLogic.apri_preventivo(self.finestra)
        finto_qt.RispostaAutomatica.scelta_pulsante = 1
        MainWindowBusinessLogic.apri_preventivo(self.finestra)

        testi = " ".join(finto_qt.RispostaAutomatica.dialoghi_mostrati)
        self.assertIn("schermata già aperta", testi)
        self.assertIn("Come vuoi procedere", testi)

    def test_nessun_dialogo_alla_prima_apertura(self):
        MainWindowBusinessLogic.apri_preventivo(self.finestra)
        self.assertEqual(finto_qt.RispostaAutomatica.dialoghi_mostrati, [],
                         "alla prima apertura non si deve chiedere nulla")


# ---------------------------------------------------------------------------
# Recupero dei preventivi non salvati
# ---------------------------------------------------------------------------

class TestRecuperoBozze(BaseInterfaccia):

    def _prepara_chiusura_anomala(self, quante=2):
        diagnostica.segna_avvio(self.db)
        diagnostica.segna_avvio(self.db)      # senza chiusura regolare
        for i in range(quante):
            bozze.salva_bozza(f"f{i}", dati_preventivo(f"Cliente {i}"))

    def test_riapre_i_preventivi_gia_compilati(self):
        self._prepara_chiusura_anomala(quante=3)
        finto_qt.RispostaAutomatica.scelta_pulsante = 0   # "Riapri i preventivi"

        MainWindowBusinessLogic.proponi_recupero_bozze(self.finestra)

        self.assertEqual(finestre_preventivo.quante(), 3,
                         "devono essere riaperte tutte e tre le schermate")
        self.assertEqual(bozze.elenca_bozze(), [],
                         "le bozze riaperte non devono restare in giro")

    def test_solo_il_foglio_non_apre_schermate(self):
        self._prepara_chiusura_anomala(quante=2)
        finto_qt.RispostaAutomatica.scelta_pulsante = 1   # "Apri solo il foglio"

        MainWindowBusinessLogic.proponi_recupero_bozze(self.finestra)

        self.assertEqual(finestre_preventivo.quante(), 0)
        self.assertEqual(len(bozze.elenca_bozze()), 2,
                         "senza riaprirle, le bozze restano disponibili")
        file_recupero = [f for f in os.listdir(bozze.cartella_bozze())
                         if f.startswith("RECUPERO")]
        self.assertTrue(file_recupero, "il foglio di recupero deve essere stato creato")

    def test_rimandare_lascia_tutto_com_era(self):
        self._prepara_chiusura_anomala(quante=2)
        finto_qt.RispostaAutomatica.scelta_pulsante = 2   # "Per ora niente"

        MainWindowBusinessLogic.proponi_recupero_bozze(self.finestra)

        self.assertEqual(finestre_preventivo.quante(), 0)
        self.assertEqual(len(bozze.elenca_bozze()), 2)

    def test_chiusura_regolare_non_chiede_nulla(self):
        diagnostica.segna_avvio(self.db)
        diagnostica.segna_chiusura_regolare()
        diagnostica.segna_avvio(self.db)
        bozze.salva_bozza("f", dati_preventivo())

        MainWindowBusinessLogic.proponi_recupero_bozze(self.finestra)
        self.assertEqual(finto_qt.RispostaAutomatica.dialoghi_mostrati, [],
                         "dopo una chiusura regolare non si disturba l'utente")

    def test_nessuna_bozza_nessun_dialogo(self):
        diagnostica.segna_avvio(self.db)
        diagnostica.segna_avvio(self.db)
        MainWindowBusinessLogic.proponi_recupero_bozze(self.finestra)
        self.assertEqual(finto_qt.RispostaAutomatica.dialoghi_mostrati, [])

    def test_il_dialogo_elenca_i_preventivi(self):
        self._prepara_chiusura_anomala(quante=2)
        finto_qt.RispostaAutomatica.scelta_pulsante = 2
        MainWindowBusinessLogic.proponi_recupero_bozze(self.finestra)

        testo = " ".join(finto_qt.RispostaAutomatica.dialoghi_mostrati)
        self.assertIn("Cliente 0", testo)
        self.assertIn("Cliente 1", testo)


# ---------------------------------------------------------------------------
# Ricarica dei dati dentro la schermata
# ---------------------------------------------------------------------------

class TestPopolamentoSchermata(BaseInterfaccia):

    def test_i_dati_della_bozza_finiscono_nella_schermata(self):
        """Il cuore del recupero: la schermata deve ritrovarsi i dati."""
        from ui.preventivo_window import PreventivoWindow

        finestra = PreventivoWindow(self.gestore, None, modalita='nuovo',
                                    dati_bozza=dati_preventivo("Verdi Srl"))

        self.assertEqual(finestra.nome_cliente_data, "Verdi Srl")
        self.assertEqual(finestra.numero_ordine_data, "ORD-77")
        self.assertEqual(finestra.misura_data, "1200 mm")
        self.assertEqual(finestra.preventivo.minuti_avvolgimento, 40.0)
        self.assertEqual(finestra.preventivo.costi_accessori, 10.0)
        self.assertEqual(len(finestra.preventivo.materiali_calcolati), 1)

        materiale = finestra.preventivo.materiali_calcolati[0]
        self.assertEqual(materiale.materiale_nome, "Fibra 200g")
        self.assertEqual(materiale.giri, 6)
        self.assertEqual(materiale.diametro, 40.0)

    def test_bozza_incompleta_non_fa_saltare_la_schermata(self):
        from ui.preventivo_window import PreventivoWindow
        finestra = PreventivoWindow(self.gestore, None, modalita='nuovo',
                                    dati_bozza={"nome_cliente": "Solo nome"})
        self.assertEqual(finestra.nome_cliente_data, "Solo nome")
        self.assertEqual(finestra.preventivo.materiali_calcolati, [])

    def test_bozza_con_dati_sbagliati_non_blocca_lapertura(self):
        from ui.preventivo_window import PreventivoWindow
        finestra = PreventivoWindow(self.gestore, None, modalita='nuovo',
                                    dati_bozza={"minuti_taglio": "non un numero"})
        self.assertIsNotNone(finestra, "la schermata deve aprirsi comunque")


# ---------------------------------------------------------------------------
# Impostazioni di archiviazione
# ---------------------------------------------------------------------------

class TestImpostazioniArchiviazione(BaseInterfaccia):

    def _finestra(self):
        from ui.impostazioni_archiviazione_window import ImpostazioniArchiviazioneWindow
        return ImpostazioniArchiviazioneWindow(self.gestore, self.finestra)

    def test_si_apre_e_legge_lo_stato(self):
        finestra = self._finestra()
        self.assertIsNotNone(finestra)
        self.assertIsInstance(finestra._backup, list)

    def test_esportazione_dalla_finestra(self):
        self.gestore.add_preventivo(dati_preventivo())
        finestra = self._finestra()
        finestra._esporta_dati()

        from database import esportazione
        cartella = esportazione.cartella_esportazioni(self.db)
        self.assertTrue(os.path.isdir(cartella))
        prodotte = os.listdir(cartella)
        self.assertTrue(prodotte, "l'esportazione deve aver prodotto qualcosa")

    def test_segnalazione_dalla_finestra(self):
        finestra = self._finestra()
        finestra._prepara_segnalazione()
        zip_creati = [f for f in os.listdir(self.tmp) if f.endswith(".zip")]
        self.assertTrue(zip_creati, "deve essere stato creato il file da inviare")

    def test_aggiorna_tutto_non_solleva_eccezioni(self):
        finestra = self._finestra()
        finestra.aggiorna_tutto()       # ricarica: e' il pulsante "Ricontrolla adesso"

    def test_funziona_anche_con_database_danneggiato(self):
        with open(self.db, "r+b") as f:
            f.seek(4096)
            f.write(b"\xff" * 4096)
        finestra = self._finestra()
        self.assertIsNotNone(finestra, "la finestra deve aprirsi anche col database rotto")


# ---------------------------------------------------------------------------
# Linguette
# ---------------------------------------------------------------------------

class TestTutteLeFinestre(BaseInterfaccia):
    """Ogni finestra deve almeno costruirsi senza errori.

    Sembra poco, ma e' proprio cio' che mancava: un attributo usato prima di
    essere creato, o un metodo con il nome sbagliato, qui si vede subito
    invece che davanti all'utente."""

    def test_tutte_le_finestre_si_costruiscono(self):
        from ui.anagrafica_clienti_window import AnagraficaClientiWindow
        from ui.confronto_preventivi_window import ConfrontoPreventiviWindow
        from ui.gestione_materiali_window import GestioneMaterialiWindow
        from ui.impostazioni_archiviazione_window import ImpostazioniArchiviazioneWindow
        from ui.magazzino_window import MagazzinoWindow
        from ui.main_window import MainWindow
        from ui.preventivo_window import PreventivoWindow
        from ui.visualizza_preventivi_window import VisualizzaPreventiviWindow

        costruttori = [
            ("MainWindow", lambda: MainWindow()),
            ("VisualizzaPreventivi", lambda: VisualizzaPreventiviWindow(self.gestore)),
            ("Magazzino", lambda: MagazzinoWindow(self.gestore)),
            ("GestioneMateriali", lambda: GestioneMaterialiWindow(self.gestore)),
            ("AnagraficaClienti", lambda: AnagraficaClientiWindow(self.gestore)),
            ("ImpostazioniArchiviazione",
             lambda: ImpostazioniArchiviazioneWindow(self.gestore, None)),
            ("Preventivo nuovo",
             lambda: PreventivoWindow(self.gestore, None, modalita='nuovo')),
            ("ConfrontoPreventivi", lambda: ConfrontoPreventiviWindow(self.gestore)),
        ]
        for nome, costruttore in costruttori:
            with self.subTest(finestra=nome):
                costruttore()

    def test_avvio_completo_dopo_una_chiusura_anomala(self):
        """Il percorso piu' delicato: l'applicazione si apre dopo che il PC si
        era spento con dei preventivi aperti."""
        from ui.main_window import MainWindow

        diagnostica.segna_avvio(self.db)
        diagnostica.segna_avvio(self.db)          # nessuna chiusura regolare
        bozze.salva_bozza("rimasta", dati_preventivo("Recuperata"))

        finto_qt.RispostaAutomatica.scelta_pulsante = 0   # "Riapri i preventivi"
        MainWindow()

        self.assertEqual(finestre_preventivo.quante(), 1,
                         "il preventivo doveva essere riaperto all'avvio")

    def test_avvio_con_database_danneggiato(self):
        """Deve avvisare, non esplodere."""
        from ui.main_window import MainWindow
        with open(self.db, "r+b") as f:
            f.seek(4096)
            f.write(b"\xff" * 4096)
        bm._esito_avvio_cache.clear()

        MainWindow()                       # non deve sollevare eccezioni

        testi = " ".join(finto_qt.RispostaAutomatica.dialoghi_mostrati).lower()
        self.assertTrue(testi, "l'utente deve essere avvisato, non lasciato al buio")
        self.assertIn("danneggia", testi,
                      "il messaggio deve dire chiaramente che il database è danneggiato")


class TestLinguette(BaseInterfaccia):

    def test_la_barra_calcola_una_larghezza_sufficiente(self):
        from ui.responsive import BarraLinguette
        barra = BarraLinguette()
        barra.tabText = lambda i: "Copie di sicurezza"

        dimensione = barra.tabSizeHint(0)
        larghezza_testo = len("Copie di sicurezza") * 8    # metriche finte
        self.assertGreaterEqual(dimensione.width(), larghezza_testo,
                                "la linguetta non deve essere piu' stretta del testo")

    def test_adatta_linguette_non_solleva_eccezioni(self):
        from ui.responsive import adatta_linguette
        from PyQt5.QtWidgets import QTabWidget
        adatta_linguette(QTabWidget())


if __name__ == "__main__":
    unittest.main(verbosity=2)
