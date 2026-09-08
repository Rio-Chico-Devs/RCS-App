#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Impostazioni di archiviazione: stato dei dati, copie di sicurezza, database.
Uso riservato esclusivamente a RCS

Questa finestra si limita a MOSTRARE: tutta la logica (verifica, elenco delle
copie, ripristino) sta in database/archivio.py, che è coperto dai test
automatici.
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTabWidget, QTextEdit,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QMessageBox, QGroupBox,
                             QApplication)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont, QDesktopServices

import os

from database import archivio
from ui.responsive import adatta_linguette

COLORE_TESTO = "#2d3748"
COLORE_TENUE = "#718096"
COLORE_BORDO = "#e2e8f0"


class ImpostazioniArchiviazioneWindow(QMainWindow):
    """Un'unica schermata per tutto ciò che riguarda i dati: come stanno, le
    copie di sicurezza e quale database si sta usando."""

    def __init__(self, db_manager, parent=None):
        super().__init__(None)
        self.db_manager = db_manager
        self.finestra_principale = parent
        self._backup = []

        self.setWindowTitle("Impostazioni di archiviazione")
        self._dimensiona_sullo_schermo()
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background-color: #ffffff; color: {COLORE_TESTO}; }}
            QLabel {{ color: {COLORE_TESTO}; }}
            QTabWidget::pane {{ border: 1px solid {COLORE_BORDO}; border-radius: 6px; }}
            QTabBar::tab {{
                background: #f7fafc; border: 1px solid {COLORE_BORDO};
                border-bottom: none; border-radius: 6px 6px 0 0;
                padding: 8px 22px; font-size: 13px; font-weight: 600;
                min-width: 140px;
            }}
            QTabBar::tab:selected {{ background: #ffffff; }}
            QPushButton {{
                background-color: #f7fafc; border: 1px solid {COLORE_BORDO};
                border-radius: 6px; padding: 8px 16px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #edf2f7; }}
            QTextEdit {{
                border: 1px solid {COLORE_BORDO}; border-radius: 6px;
                font-family: Consolas, 'Courier New', monospace; font-size: 12px;
            }}
            QTableWidget {{ border: 1px solid {COLORE_BORDO}; border-radius: 6px; font-size: 13px; }}
            QHeaderView::section {{
                background-color: #f7fafc; border: none;
                border-bottom: 1px solid {COLORE_BORDO}; padding: 8px; font-weight: 600;
            }}
        """)

        centrale = QWidget()
        layout = QVBoxLayout(centrale)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        titolo = QLabel("Impostazioni di archiviazione")
        font_titolo = QFont()
        font_titolo.setPointSize(14)
        font_titolo.setBold(True)
        titolo.setFont(font_titolo)
        layout.addWidget(titolo)

        sottotitolo = QLabel(
            "Da qui puoi controllare lo stato dei dati, gestire le copie di "
            "sicurezza e scegliere quale database usare.")
        sottotitolo.setStyleSheet(f"color: {COLORE_TENUE}; font-size: 12px;")
        sottotitolo.setWordWrap(True)
        layout.addWidget(sottotitolo)

        self.schede = QTabWidget()
        # Linguette dimensionate sul testo reale (va fatto prima di aggiungerle):
        # altrimenti il testo viene tagliato ai due lati su alcuni schermi.
        adatta_linguette(self.schede)
        self.schede.addTab(self._crea_scheda_stato(), "Stato")
        self.schede.addTab(self._crea_scheda_copie(), "Copie di sicurezza")
        self.schede.addTab(self._crea_scheda_database(), "Database in uso")
        layout.addWidget(self.schede)

        self.setCentralWidget(centrale)
        self.aggiorna_tutto()

    def _dimensiona_sullo_schermo(self):
        """Sceglie la dimensione in base allo schermo, senza mai superarlo.

        Un minimo fisso non va bene: su un portatile piccolo la finestra
        risulterebbe piu' alta dello spazio disponibile e i pulsanti in fondo
        finirebbero fuori dallo schermo."""
        try:
            disponibile = QApplication.primaryScreen().availableGeometry()
            largo = min(900, int(disponibile.width() * 0.75))
            alto = min(680, int(disponibile.height() * 0.80))
            self.resize(max(largo, 560), max(alto, 420))
            self.setMinimumSize(min(560, disponibile.width() - 40),
                                min(420, disponibile.height() - 40))
        except Exception:
            self.resize(820, 620)   # se lo schermo non e' interrogabile

    # ------------------------------------------------------------------
    # Scheda: Stato
    # ------------------------------------------------------------------

    def _crea_scheda_stato(self):
        scheda = QWidget()
        layout = QVBoxLayout(scheda)
        layout.setContentsMargins(14, 14, 14, 14)

        self.etichetta_sintesi = QLabel()
        self.etichetta_sintesi.setWordWrap(True)
        self.etichetta_sintesi.setStyleSheet(
            "font-size: 14px; font-weight: 600; padding: 10px; border-radius: 6px;")
        layout.addWidget(self.etichetta_sintesi)

        self.testo_stato = QTextEdit()
        self.testo_stato.setReadOnly(True)
        layout.addWidget(self.testo_stato)

        pulsanti = QHBoxLayout()
        btn_aggiorna = QPushButton("Ricontrolla adesso")
        btn_aggiorna.clicked.connect(self.aggiorna_tutto)
        pulsanti.addWidget(btn_aggiorna)

        btn_esporta = QPushButton("Esporta i dati per Excel")
        btn_esporta.setToolTip(
            "Salva una copia dei dati in file leggibili con Excel, "
            "che non dipendono da questo programma")
        btn_esporta.clicked.connect(self._esporta_dati)
        pulsanti.addWidget(btn_esporta)

        btn_segnala = QPushButton("Prepara segnalazione")
        btn_segnala.setToolTip(
            "Raccoglie i registri tecnici in un unico file da inviare "
            "all'assistenza (nessun dato aziendale)")
        btn_segnala.clicked.connect(self._prepara_segnalazione)
        pulsanti.addWidget(btn_segnala)

        pulsanti.addStretch()
        layout.addLayout(pulsanti)
        return scheda

    def _esporta_dati(self):
        """Scrive i dati in file CSV apribili con Excel."""
        from database import esportazione
        try:
            cartella, conteggi = esportazione.esporta(self.db_manager.db_path)
        except Exception as e:
            QMessageBox.critical(self, "Esportazione non riuscita", str(e))
            return

        righe = "\n".join("  {}: {} righe".format(t, n) for t, n in conteggi.items())
        risposta = QMessageBox.question(
            self, "Esportazione completata",
            "I dati sono stati salvati in file leggibili con Excel:\n\n{}\n\n"
            "Cartella:\n{}\n\nVuoi aprirla adesso?".format(righe, cartella),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if risposta == QMessageBox.Yes:
            self._apri_cartella(cartella)

    def _prepara_segnalazione(self):
        """Raccoglie i registri tecnici in un file da inviare all'assistenza."""
        from utils import segnalazione
        try:
            percorso = segnalazione.prepara(self.db_manager.db_path)
        except Exception as e:
            QMessageBox.critical(self, "Segnalazione non riuscita", str(e))
            return

        risposta = QMessageBox.question(
            self, "Segnalazione pronta",
            "È stato preparato un file con i registri tecnici, da inviare "
            "all'assistenza:\n\n{}\n\nNon contiene dati aziendali: nessun "
            "preventivo, nessun nominativo di clienti.\n\n"
            "Vuoi aprire la cartella che lo contiene?".format(percorso),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if risposta == QMessageBox.Yes:
            self._apri_cartella(os.path.dirname(percorso))

    def _apri_cartella(self, percorso):
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(percorso))
        except Exception:
            QMessageBox.information(self, "Percorso",
                                    "La trovi qui:\n{}".format(percorso))

    # ------------------------------------------------------------------
    # Scheda: Copie di sicurezza
    # ------------------------------------------------------------------

    def _crea_scheda_copie(self):
        scheda = QWidget()
        layout = QVBoxLayout(scheda)
        layout.setContentsMargins(14, 14, 14, 14)

        spiegazione = QLabel(
            "Le copie vengono create da sole a ogni apertura del programma. "
            "Seleziona una copia per vedere cosa contiene.")
        spiegazione.setStyleSheet(f"color: {COLORE_TENUE}; font-size: 12px;")
        spiegazione.setWordWrap(True)
        layout.addWidget(spiegazione)

        self.tabella = QTableWidget(0, 3)
        self.tabella.setHorizontalHeaderLabels(["Data e ora", "Tipo", "Dimensione"])
        self.tabella.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabella.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabella.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabella.verticalHeader().setVisible(False)
        self.tabella.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabella.itemSelectionChanged.connect(self._copia_selezionata)
        layout.addWidget(self.tabella)

        gruppo = QGroupBox("Contenuto della copia selezionata")
        layout_gruppo = QVBoxLayout(gruppo)
        self.etichetta_dettagli = QLabel("Seleziona una copia dall'elenco.")
        self.etichetta_dettagli.setWordWrap(True)
        layout_gruppo.addWidget(self.etichetta_dettagli)
        layout.addWidget(gruppo)

        pulsanti = QHBoxLayout()
        self.btn_ripristina = QPushButton("Ripristina questa copia")
        self.btn_ripristina.setEnabled(False)
        self.btn_ripristina.setStyleSheet(
            "background-color: #fff5f5; border: 1px solid #feb2b2; color: #9b2c2c;")
        self.btn_ripristina.clicked.connect(self._ripristina)
        pulsanti.addWidget(self.btn_ripristina)
        pulsanti.addStretch()
        layout.addLayout(pulsanti)
        return scheda

    def _copia_selezionata(self):
        righe = self.tabella.selectionModel().selectedRows() if self.tabella.selectionModel() else []
        if not righe:
            self.btn_ripristina.setEnabled(False)
            self.etichetta_dettagli.setText("Seleziona una copia dall'elenco.")
            return

        indice = righe[0].row()
        if indice >= len(self._backup):
            return
        voce = self._backup[indice]

        self.etichetta_dettagli.setText("Controllo in corso...")
        try:
            dettagli = archivio.dettagli_backup(voce["percorso"])
        except Exception as e:
            self.etichetta_dettagli.setText("Impossibile leggere la copia: {}".format(e))
            self.btn_ripristina.setEnabled(False)
            return

        if dettagli["integro"]:
            self.etichetta_dettagli.setText(
                "Copia del {}\nContiene: {}\nStato: nessun problema rilevato".format(
                    voce["quando_testo"], archivio.descrivi_contenuto(dettagli)))
            self.btn_ripristina.setEnabled(True)
        else:
            self.etichetta_dettagli.setText(
                "Copia del {}\nSTATO: DANNEGGIATA — non può essere ripristinata.\n({})".format(
                    voce["quando_testo"], dettagli["messaggio"]))
            self.btn_ripristina.setEnabled(False)

    def _ripristina(self):
        righe = self.tabella.selectionModel().selectedRows()
        if not righe:
            return
        voce = self._backup[righe[0].row()]

        conferma = QMessageBox.warning(
            self, "Confermi il ripristino?",
            "Stai per rimettere in uso la copia del {}.\n\n"
            "Il database attuale verrà sostituito. Una copia di quello attuale "
            "viene conservata automaticamente, quindi l'operazione è "
            "reversibile.\n\n"
            "I preventivi inseriti DOPO quella data andranno persi.\n\n"
            "Vuoi procedere?".format(voce["quando_testo"]),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if conferma != QMessageBox.Yes:
            return

        try:
            riuscito, messaggio, _copia = archivio.ripristina_backup(
                self.db_manager.db_path, voce["percorso"])

            # Bloccato perché altri computer risultano collegati: si può
            # forzare solo se l'utente conferma che in realtà sono chiusi
            # (capita dopo un blocco o uno spegnimento improvviso).
            if not riuscito and "altri computer" in messaggio:
                forzatura = QMessageBox(self)
                forzatura.setIcon(QMessageBox.Warning)
                forzatura.setWindowTitle("Altri computer collegati")
                forzatura.setText(
                    messaggio + "\n\nSe sei certo che su quelle postazioni "
                    "l'applicazione sia in realtà chiusa (per esempio dopo un "
                    "blocco), puoi procedere lo stesso — ma solo in quel caso.")
                btn_annulla = forzatura.addButton("Annulla", QMessageBox.RejectRole)
                forzatura.addButton("Sono chiuse, procedi",
                                    QMessageBox.DestructiveRole)
                forzatura.setDefaultButton(btn_annulla)
                forzatura.exec_()
                if forzatura.clickedButton() is btn_annulla:
                    return
                riuscito, messaggio, _copia = archivio.ripristina_backup(
                    self.db_manager.db_path, voce["percorso"], forza=True)
        except Exception as e:
            QMessageBox.critical(self, "Ripristino non riuscito",
                                 "Errore imprevisto: {}".format(e))
            return

        if riuscito:
            QMessageBox.information(
                self, "Ripristino completato",
                messaggio + "\n\nIl programma verrà chiuso: riaprilo per "
                            "lavorare sui dati ripristinati.")
            self.close()
            if self.finestra_principale is not None:
                self.finestra_principale.close()
        else:
            QMessageBox.critical(self, "Ripristino non eseguito", messaggio)
        self.aggiorna_tutto()

    # ------------------------------------------------------------------
    # Scheda: Database in uso
    # ------------------------------------------------------------------

    def _crea_scheda_database(self):
        scheda = QWidget()
        layout = QVBoxLayout(scheda)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.etichetta_percorso = QLabel()
        self.etichetta_percorso.setWordWrap(True)
        self.etichetta_percorso.setStyleSheet(
            f"border: 1px solid {COLORE_BORDO}; border-radius: 6px; padding: 12px; font-size: 13px;")
        layout.addWidget(self.etichetta_percorso)

        self.avviso_rete = QLabel()
        self.avviso_rete.setWordWrap(True)
        self.avviso_rete.setStyleSheet(
            "background-color: #fffaf0; border: 1px solid #f6e05e; "
            "border-radius: 6px; padding: 12px; font-size: 12px;")
        layout.addWidget(self.avviso_rete)

        btn_cambia = QPushButton("Cambia database...")
        btn_cambia.clicked.connect(self._cambia_database)
        layout.addWidget(btn_cambia, alignment=Qt.AlignLeft)

        layout.addStretch()
        return scheda

    def _cambia_database(self):
        if self.finestra_principale is None:
            QMessageBox.information(
                self, "Cambia database",
                "Chiudi questa finestra e usa la schermata principale.")
            return
        try:
            self.finestra_principale.cambia_database()
        except Exception as e:
            QMessageBox.critical(self, "Errore", str(e))
        self.aggiorna_tutto()

    # ------------------------------------------------------------------
    # Aggiornamento
    # ------------------------------------------------------------------

    def aggiorna_tutto(self):
        """Rilegge tutto e aggiorna le tre schede."""
        try:
            percorso_db = self.db_manager.db_path
            stato = archivio.riepilogo_stato(percorso_db)
        except Exception as e:
            self.testo_stato.setPlainText("Impossibile leggere lo stato: {}".format(e))
            return

        # --- sintesi in cima
        if stato["integro"] is True:
            self.etichetta_sintesi.setText("I dati stanno bene: nessun problema rilevato.")
            self.etichetta_sintesi.setStyleSheet(
                "background-color: #f0fff4; border: 1px solid #9ae6b4; color: #22543d;"
                "font-size: 14px; font-weight: 600; padding: 10px; border-radius: 6px;")
        else:
            self.etichetta_sintesi.setText(
                "ATTENZIONE: il database risulta danneggiato. "
                "Vai alla scheda 'Copie di sicurezza' per ripristinare una copia integra.")
            self.etichetta_sintesi.setStyleSheet(
                "background-color: #fff5f5; border: 1px solid #feb2b2; color: #9b2c2c;"
                "font-size: 14px; font-weight: 600; padding: 10px; border-radius: 6px;")

        self.testo_stato.setPlainText(archivio.testo_riepilogo(stato))

        # --- elenco delle copie
        try:
            self._backup = archivio.elenco_backup(percorso_db)
        except Exception:
            self._backup = []

        self.tabella.setRowCount(len(self._backup))
        for riga, voce in enumerate(self._backup):
            self.tabella.setItem(riga, 0, QTableWidgetItem(voce["quando_testo"]))
            self.tabella.setItem(riga, 1, QTableWidgetItem(voce["tipo"]))
            self.tabella.setItem(riga, 2, QTableWidgetItem(voce["dimensione_testo"]))
        self.btn_ripristina.setEnabled(False)
        self.etichetta_dettagli.setText(
            "Seleziona una copia dall'elenco." if self._backup
            else "Non ci sono ancora copie di sicurezza.")

        # --- database in uso
        self.etichetta_percorso.setText(
            "Database attualmente in uso:\n{}\n\nDimensione: {}".format(
                percorso_db, stato["dimensione_testo"]))
        if stato["su_rete"]:
            self.avviso_rete.setText(
                "Questo database si trova su una cartella di rete condivisa. "
                "È comodo perché più computer usano gli stessi dati, ma è anche "
                "la situazione in cui un'interruzione (rete che cade, PC che si "
                "spegne) può danneggiare il file. Per questo il programma "
                "controlla i dati a ogni avvio e conserva molte copie.")
            self.avviso_rete.setVisible(True)
        else:
            self.avviso_rete.setVisible(False)
