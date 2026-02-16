#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
MagazzinoWindow - Gestione Magazzino Materiali
Uso riservato esclusivamente a RCS

Version: 1.0.0
Last Updated: 2026-02-16
"""

from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
                             QWidget, QLabel, QMessageBox, QGroupBox, QFrame,
                             QSizePolicy, QGraphicsDropShadowEffect, QScrollArea,
                             QComboBox, QDoubleSpinBox, QDialog, QFormLayout,
                             QLineEdit, QTextEdit, QTabWidget, QGridLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QColor, QPainter, QLinearGradient
from datetime import datetime, timedelta


class BarraScorta(QWidget):
    """Widget barra gradiente per visualizzare il livello di scorta"""

    def __init__(self, percentuale=0, parent=None):
        super().__init__(parent)
        self.percentuale = max(0, min(100, percentuale))
        self.setMinimumHeight(22)
        self.setMaximumHeight(22)
        self.setMinimumWidth(200)

    def set_percentuale(self, percentuale):
        self.percentuale = max(0, min(100, percentuale))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        radius = 6

        # Sfondo grigio chiaro
        painter.setBrush(QColor(226, 232, 240))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, radius, radius)

        # Barra riempita
        if self.percentuale > 0:
            fill_width = max(int(w * self.percentuale / 100), radius * 2)

            # Colore basato su HSV: 0% = rosso (hue=0), 100% = verde (hue=120)
            hue = min(self.percentuale, 100) * 1.2
            color = QColor.fromHsv(int(hue), 180, 200)

            painter.setBrush(color)
            painter.drawRoundedRect(0, 0, fill_width, h, radius, radius)

        # Testo percentuale
        painter.setPen(QColor(45, 55, 72))
        from PyQt5.QtGui import QFont
        font = QFont("system-ui", 10, QFont.Bold)
        painter.setFont(font)
        painter.drawText(0, 0, w, h, Qt.AlignCenter, f"{self.percentuale:.0f}%")

        painter.end()


class MagazzinoWindow(QMainWindow):
    magazzino_aggiornato = pyqtSignal()

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.init_ui()
        self.carica_scorte()

    def init_ui(self):
        self.setWindowTitle("Gestione Magazzino - Software Aziendale RCS")
        self.showMaximized()

        self.setStyleSheet("""
            QMainWindow {
                background-color: #fafbfc;
            }
            QLabel {
                color: #2d3748;
                font-family: system-ui, -apple-system, sans-serif;
                font-size: 14px;
                font-weight: 500;
            }
            QGroupBox {
                font-size: 16px;
                font-weight: 600;
                color: #4a5568;
                border: none;
                background-color: #ffffff;
                border-radius: 12px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 6px 0px;
                background-color: transparent;
                color: #4a5568;
            }
            QComboBox {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 14px;
                background-color: #ffffff;
                color: #2d3748;
                min-height: 18px;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QComboBox:hover {
                border-color: #a0aec0;
            }
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 600;
                font-family: system-ui, -apple-system, sans-serif;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #2d3748;
                border-color: #e2e8f0;
            }
            QTabBar::tab:hover {
                background-color: #edf2f7;
            }
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                font-size: 13px;
                gridline-color: #edf2f7;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QTableWidget::item {
                padding: 8px;
                color: #2d3748;
            }
            QHeaderView::section {
                background-color: #f7fafc;
                color: #4a5568;
                font-weight: 600;
                font-size: 13px;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                padding: 12px 24px;
                font-family: system-ui, -apple-system, sans-serif;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)

        # Header
        self.create_header(main_layout)

        # Tab widget
        self.tabs = QTabWidget()
        self.tab_scorte = QWidget()
        self.tab_consumi = QWidget()

        self.tabs.addTab(self.tab_scorte, "Scorte Magazzino")
        self.tabs.addTab(self.tab_consumi, "Consumi e Spese")

        self.setup_tab_scorte()
        self.setup_tab_consumi()

        main_layout.addWidget(self.tabs, 1)

        # Footer
        self.create_footer(main_layout)

    def create_shadow_effect(self, blur=10, opacity=12):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setColor(QColor(0, 0, 0, opacity))
        shadow.setOffset(0, 2)
        return shadow

    def create_header(self, parent_layout):
        header_container = QFrame()
        header_container.setStyleSheet("QFrame { background-color: transparent; border: none; padding: 20px 0px; }")

        header_layout = QVBoxLayout(header_container)
        header_layout.setSpacing(8)

        title_label = QLabel("Gestione Magazzino")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("QLabel { font-size: 32px; font-weight: 700; color: #2d3748; padding: 0; }")

        subtitle_label = QLabel("Visualizza scorte, gestisci carico/scarico e monitora i consumi")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("QLabel { font-size: 16px; font-weight: 400; color: #718096; padding: 0; }")

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        parent_layout.addWidget(header_container)

    # =================== TAB SCORTE ===================

    def setup_tab_scorte(self):
        layout = QVBoxLayout(self.tab_scorte)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(16)

        # Barra filtri
        filtri_layout = QHBoxLayout()

        lbl_ordina = QLabel("Ordina per:")
        lbl_ordina.setStyleSheet("font-weight: 600;")
        self.combo_ordinamento = QComboBox()
        self.combo_ordinamento.addItem("Scorte basse prima", "giacenza_asc")
        self.combo_ordinamento.addItem("Scorte alte prima", "giacenza_desc")
        self.combo_ordinamento.addItem("Nome A-Z", "nome")
        self.combo_ordinamento.currentIndexChanged.connect(self.carica_scorte)

        btn_carico = QPushButton("Carico Materiale")
        btn_carico.setStyleSheet("""
            QPushButton { background-color: #38a169; color: #ffffff; min-height: 36px; }
            QPushButton:hover { background-color: #2f855a; }
        """)
        btn_carico.clicked.connect(self.apri_dialog_carico)

        btn_scarico = QPushButton("Scarico Materiale")
        btn_scarico.setStyleSheet("""
            QPushButton { background-color: #e53e3e; color: #ffffff; min-height: 36px; }
            QPushButton:hover { background-color: #c53030; }
        """)
        btn_scarico.clicked.connect(self.apri_dialog_scarico)

        filtri_layout.addWidget(lbl_ordina)
        filtri_layout.addWidget(self.combo_ordinamento)
        filtri_layout.addStretch()
        filtri_layout.addWidget(btn_carico)
        filtri_layout.addSpacing(8)
        filtri_layout.addWidget(btn_scarico)

        layout.addLayout(filtri_layout)

        # Scroll area per le scorte
        self.scroll_scorte = QScrollArea()
        self.scroll_scorte.setWidgetResizable(True)
        self.scroll_scorte.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.scorte_container = QWidget()
        self.scorte_layout = QVBoxLayout(self.scorte_container)
        self.scorte_layout.setContentsMargins(0, 0, 0, 0)
        self.scorte_layout.setSpacing(8)
        self.scroll_scorte.setWidget(self.scorte_container)

        layout.addWidget(self.scroll_scorte)

    def carica_scorte(self):
        """Carica e visualizza le scorte di tutti i materiali"""
        # Pulisci layout
        while self.scorte_layout.count():
            child = self.scorte_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        ordina_per = self.combo_ordinamento.currentData() or 'giacenza_asc'
        scorte = self.db_manager.get_scorte(ordina_per)

        if not scorte:
            lbl_vuoto = QLabel("Nessun materiale nel database. Aggiungi materiali da 'Gestisci Materiali'.")
            lbl_vuoto.setAlignment(Qt.AlignCenter)
            lbl_vuoto.setStyleSheet("color: #718096; font-size: 16px; padding: 40px;")
            self.scorte_layout.addWidget(lbl_vuoto)
            self.scorte_layout.addStretch()
            return

        for mat in scorte:
            mat_id, nome, giacenza, capacita, fornitore, prezzo_fornitore = mat
            card = self._crea_card_scorta(mat_id, nome, giacenza, capacita, fornitore, prezzo_fornitore)
            self.scorte_layout.addWidget(card)

        self.scorte_layout.addStretch()

    def _crea_card_scorta(self, mat_id, nome, giacenza, capacita, fornitore, prezzo_fornitore):
        """Crea una card per un materiale con barra gradiente"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
            QFrame:hover {
                border-color: #a0aec0;
            }
        """)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 14, 20, 14)
        card_layout.setSpacing(20)

        # Info materiale
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        lbl_nome = QLabel(nome)
        lbl_nome.setStyleSheet("font-size: 16px; font-weight: 700; color: #2d3748;")

        dettagli = f"Giacenza: {giacenza:.2f} m²"
        if capacita > 0:
            dettagli += f" / {capacita:.2f} m²"
        if fornitore:
            dettagli += f"  |  Fornitore: {fornitore}"
        if prezzo_fornitore > 0:
            dettagli += f"  |  €{prezzo_fornitore:.2f}/m²"

        lbl_dettagli = QLabel(dettagli)
        lbl_dettagli.setStyleSheet("font-size: 12px; color: #718096;")

        info_layout.addWidget(lbl_nome)
        info_layout.addWidget(lbl_dettagli)

        card_layout.addLayout(info_layout)

        # Barra scorta
        percentuale = 0
        if capacita > 0:
            percentuale = (giacenza / capacita) * 100

        barra = BarraScorta(percentuale)
        card_layout.addWidget(barra)

        # Bottone storico
        btn_storico = QPushButton("Storico")
        btn_storico.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: 30px;
                padding: 4px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
        """)
        btn_storico.clicked.connect(lambda checked, mid=mat_id, mn=nome: self.mostra_storico(mid, mn))
        card_layout.addWidget(btn_storico)

        return card

    def mostra_storico(self, materiale_id, nome_materiale):
        """Mostra lo storico movimenti di un materiale"""
        movimenti = self.db_manager.get_movimenti_per_materiale(materiale_id)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Storico Movimenti - {nome_materiale}")
        dialog.setMinimumSize(600, 400)
        dialog.setStyleSheet("""
            QDialog { background-color: #fafbfc; }
            QLabel { color: #2d3748; font-family: system-ui, -apple-system, sans-serif; }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel(f"Storico Movimenti: {nome_materiale}")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        if not movimenti:
            lbl_vuoto = QLabel("Nessun movimento registrato per questo materiale.")
            lbl_vuoto.setStyleSheet("color: #718096; padding: 20px;")
            layout.addWidget(lbl_vuoto)
        else:
            table = QTableWidget(len(movimenti), 4)
            table.setHorizontalHeaderLabels(["Data", "Tipo", "Quantità (m²)", "Note"])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setAlternatingRowColors(True)
            table.setStyleSheet("""
                QTableWidget { border: 1px solid #e2e8f0; border-radius: 8px; }
                QTableWidget::item { padding: 6px; }
                QTableWidget::item:alternate { background-color: #f7fafc; }
            """)

            for row, mov in enumerate(movimenti):
                mov_id, tipo, quantita, data, note, prev_id = mov

                # Data formattata
                data_str = data.split('T')[0] if 'T' in data else data
                table.setItem(row, 0, QTableWidgetItem(data_str))

                # Tipo con colore
                tipo_item = QTableWidgetItem(tipo.upper())
                if tipo == 'carico':
                    tipo_item.setForeground(QColor(56, 161, 105))
                else:
                    tipo_item.setForeground(QColor(229, 62, 62))
                table.setItem(row, 1, tipo_item)

                table.setItem(row, 2, QTableWidgetItem(f"{quantita:.2f}"))
                table.setItem(row, 3, QTableWidgetItem(note or ""))

            layout.addWidget(table)

        btn_chiudi = QPushButton("Chiudi")
        btn_chiudi.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; min-height: 36px; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_chiudi.clicked.connect(dialog.accept)
        layout.addWidget(btn_chiudi, alignment=Qt.AlignRight)

        dialog.exec_()

    def apri_dialog_carico(self):
        """Dialog per aggiungere materiale al magazzino (carico)"""
        self._apri_dialog_movimento('carico')

    def apri_dialog_scarico(self):
        """Dialog per rimuovere materiale dal magazzino (scarico)"""
        self._apri_dialog_movimento('scarico')

    def _apri_dialog_movimento(self, tipo):
        """Dialog generico per carico/scarico"""
        dialog = QDialog(self)
        titolo = "Carico Materiale" if tipo == 'carico' else "Scarico Materiale"
        dialog.setWindowTitle(titolo)
        dialog.setFixedSize(450, 350)
        dialog.setStyleSheet("""
            QDialog { background-color: #fafbfc; font-family: system-ui, -apple-system, sans-serif; }
            QLabel { color: #2d3748; font-size: 14px; font-weight: 500; }
            QComboBox, QDoubleSpinBox, QLineEdit {
                border: 1px solid #e2e8f0; border-radius: 6px;
                padding: 10px 14px; font-size: 14px;
                background-color: #ffffff; color: #2d3748; min-height: 18px;
            }
            QPushButton {
                border: none; border-radius: 6px;
                font-size: 14px; font-weight: 600;
                padding: 12px 24px; min-height: 36px;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(20)

        lbl_titolo = QLabel(titolo)
        lbl_titolo.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(lbl_titolo)

        form = QFormLayout()
        form.setVerticalSpacing(16)

        # Selezione materiale
        combo_mat = QComboBox()
        materiali = self.db_manager.get_all_materiali()
        for mat in materiali:
            mat_id, nome = mat[0], mat[1]
            giacenza = mat[7] if len(mat) > 7 else 0.0
            combo_mat.addItem(f"{nome} (giacenza: {giacenza:.2f} m²)", mat_id)

        # Quantità
        edit_quantita = QDoubleSpinBox()
        edit_quantita.setDecimals(2)
        edit_quantita.setMaximum(99999.99)
        edit_quantita.setSuffix(" m²")
        edit_quantita.setMinimum(0.01)

        # Note
        edit_note = QLineEdit()
        edit_note.setPlaceholderText("Note opzionali...")

        form.addRow("Materiale:", combo_mat)
        form.addRow("Quantità:", edit_quantita)
        form.addRow("Note:", edit_note)

        layout.addLayout(form)

        # Pulsanti
        btn_layout = QHBoxLayout()

        btn_annulla = QPushButton("Annulla")
        btn_annulla.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_annulla.clicked.connect(dialog.reject)

        colore = "#38a169" if tipo == 'carico' else "#e53e3e"
        colore_hover = "#2f855a" if tipo == 'carico' else "#c53030"
        btn_conferma = QPushButton("Conferma " + titolo)
        btn_conferma.setStyleSheet(f"""
            QPushButton {{ background-color: {colore}; color: #ffffff; }}
            QPushButton:hover {{ background-color: {colore_hover}; }}
        """)

        def conferma():
            mat_id = combo_mat.currentData()
            quantita = edit_quantita.value()
            note = edit_note.text().strip()

            if not mat_id:
                QMessageBox.warning(dialog, "Attenzione", "Seleziona un materiale.")
                return
            if quantita <= 0:
                QMessageBox.warning(dialog, "Attenzione", "Inserisci una quantità valida.")
                return

            self.db_manager.registra_movimento(mat_id, tipo, quantita, note)
            verbo = "caricato" if tipo == 'carico' else "scaricato"
            QMessageBox.information(dialog, "Successo",
                                    f"Movimento registrato: {quantita:.2f} m² {verbo}.")
            dialog.accept()
            self.carica_scorte()
            self.magazzino_aggiornato.emit()

        btn_conferma.clicked.connect(conferma)

        btn_layout.addWidget(btn_annulla)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_conferma)

        layout.addLayout(btn_layout)
        dialog.exec_()

    # =================== TAB CONSUMI ===================

    def setup_tab_consumi(self):
        layout = QVBoxLayout(self.tab_consumi)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(16)

        # Filtri periodo
        filtri_layout = QHBoxLayout()

        lbl_periodo = QLabel("Periodo:")
        lbl_periodo.setStyleSheet("font-weight: 600;")

        self.combo_periodo = QComboBox()
        self.combo_periodo.addItem("Mese corrente", "mese_corrente")
        self.combo_periodo.addItem("Mese scorso", "mese_scorso")
        self.combo_periodo.addItem("Anno corrente", "anno_corrente")
        self.combo_periodo.addItem("Anno scorso", "anno_scorso")
        self.combo_periodo.addItem("Ultimi 3 mesi", "ultimi_3_mesi")
        self.combo_periodo.addItem("Ultimi 6 mesi", "ultimi_6_mesi")
        self.combo_periodo.currentIndexChanged.connect(self.carica_consumi)

        btn_aggiorna = QPushButton("Aggiorna")
        btn_aggiorna.setStyleSheet("""
            QPushButton { background-color: #4a5568; color: #ffffff; min-height: 36px; }
            QPushButton:hover { background-color: #2d3748; }
        """)
        btn_aggiorna.clicked.connect(self.carica_consumi)

        filtri_layout.addWidget(lbl_periodo)
        filtri_layout.addWidget(self.combo_periodo)
        filtri_layout.addStretch()
        filtri_layout.addWidget(btn_aggiorna)

        layout.addLayout(filtri_layout)

        # Riepilogo totale
        self.lbl_riepilogo_consumi = QLabel("")
        self.lbl_riepilogo_consumi.setStyleSheet("""
            font-size: 15px; font-weight: 600; color: #2d3748;
            background-color: #f0fff4; border: 1px solid #68d391;
            border-radius: 8px; padding: 12px 16px;
        """)
        layout.addWidget(self.lbl_riepilogo_consumi)

        # Tabella consumi
        self.tabella_consumi = QTableWidget()
        self.tabella_consumi.setColumnCount(4)
        self.tabella_consumi.setHorizontalHeaderLabels(["Materiale", "Consumato (m²)", "Prezzo Fornitore (€/m²)", "Spesa Totale (€)"])
        self.tabella_consumi.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabella_consumi.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabella_consumi.setAlternatingRowColors(True)
        self.tabella_consumi.setStyleSheet("""
            QTableWidget { border: 1px solid #e2e8f0; border-radius: 8px; }
            QTableWidget::item { padding: 8px; }
            QTableWidget::item:alternate { background-color: #f7fafc; }
        """)

        layout.addWidget(self.tabella_consumi, 1)

    def carica_consumi(self):
        """Carica e visualizza i consumi per il periodo selezionato"""
        periodo = self.combo_periodo.currentData() or 'mese_corrente'
        data_inizio, data_fine = self._calcola_date_periodo(periodo)

        consumi = self.db_manager.get_consumi_periodo(data_inizio, data_fine)

        self.tabella_consumi.setRowCount(len(consumi))

        totale_consumato = 0.0
        totale_spesa = 0.0

        for row, consumo in enumerate(consumi):
            mat_id, nome, prezzo_fornitore, quantita = consumo
            spesa = quantita * prezzo_fornitore

            totale_consumato += quantita
            totale_spesa += spesa

            self.tabella_consumi.setItem(row, 0, QTableWidgetItem(nome))
            self.tabella_consumi.setItem(row, 1, QTableWidgetItem(f"{quantita:.2f}"))
            self.tabella_consumi.setItem(row, 2, QTableWidgetItem(f"€ {prezzo_fornitore:.2f}"))

            spesa_item = QTableWidgetItem(f"€ {spesa:.2f}")
            spesa_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabella_consumi.setItem(row, 3, spesa_item)

        # Aggiorna riepilogo
        periodo_testo = self.combo_periodo.currentText()
        if consumi:
            self.lbl_riepilogo_consumi.setText(
                f"{periodo_testo}:  {totale_consumato:.2f} m² consumati  |  "
                f"Spesa totale: € {totale_spesa:.2f}"
            )
        else:
            self.lbl_riepilogo_consumi.setText(
                f"{periodo_testo}:  Nessun consumo registrato nel periodo selezionato"
            )

    def _calcola_date_periodo(self, periodo):
        """Calcola data inizio e fine per il periodo selezionato"""
        oggi = datetime.now()

        if periodo == 'mese_corrente':
            inizio = oggi.replace(day=1, hour=0, minute=0, second=0)
            fine = oggi
        elif periodo == 'mese_scorso':
            primo_mese = oggi.replace(day=1)
            fine = primo_mese - timedelta(days=1)
            inizio = fine.replace(day=1, hour=0, minute=0, second=0)
        elif periodo == 'anno_corrente':
            inizio = oggi.replace(month=1, day=1, hour=0, minute=0, second=0)
            fine = oggi
        elif periodo == 'anno_scorso':
            inizio = oggi.replace(year=oggi.year - 1, month=1, day=1, hour=0, minute=0, second=0)
            fine = oggi.replace(year=oggi.year - 1, month=12, day=31, hour=23, minute=59, second=59)
        elif periodo == 'ultimi_3_mesi':
            inizio = oggi - timedelta(days=90)
            fine = oggi
        elif periodo == 'ultimi_6_mesi':
            inizio = oggi - timedelta(days=180)
            fine = oggi
        else:
            inizio = oggi.replace(day=1)
            fine = oggi

        return inizio.isoformat(), fine.isoformat()

    # =================== FOOTER ===================

    def create_footer(self, parent_layout):
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        btn_chiudi = QPushButton("Chiudi Magazzino")
        btn_chiudi.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: 40px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
        """)
        btn_chiudi.clicked.connect(self.close)

        footer_layout.addWidget(btn_chiudi)
        parent_layout.addLayout(footer_layout)
