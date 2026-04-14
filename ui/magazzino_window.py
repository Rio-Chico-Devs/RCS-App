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
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QListWidget, QListWidgetItem, QAbstractItemView,
                             QDialogButtonBox)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QColor, QPainter, QLinearGradient
from ui.materiale_ui_components import NoScrollDoubleSpinBox
from ui.responsive import get_metrics
from datetime import datetime, timedelta


class BarraScorta(QWidget):
    """Widget barra gradiente per visualizzare il livello di scorta"""

    def __init__(self, percentuale=0, parent=None):
        super().__init__(parent)
        self.percentuale = max(0, min(100, percentuale))
        self.setMinimumHeight(32)
        self.setMaximumHeight(32)
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
        font = QFont("system-ui", 12, QFont.Bold)
        painter.setFont(font)
        painter.drawText(0, 0, w, h, Qt.AlignCenter, f"{self.percentuale:.0f}%")

        painter.end()


class MagazzinoWindow(QMainWindow):
    magazzino_aggiornato = pyqtSignal()

    def __init__(self, db_manager, parent=None):
        super().__init__(None)  # No parent per evitare bug ridimensionamento
        self.db_manager = db_manager
        self.init_ui()
        self.carica_fornitori()
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
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
                font-family: system-ui, -apple-system, sans-serif;
                margin-right: 4px;
                min-width: 160px;
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

        _m = get_metrics()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(_m['mo'], _m['sf'], _m['mo'], _m['sf'])
        main_layout.setSpacing(_m['sf'])

        # Header
        self.create_header(main_layout)

        # Tab widget
        self.tabs = QTabWidget()
        self.tab_scorte = QWidget()
        self.tab_consumi = QWidget()
        self.tab_fornitori = QWidget()

        self.tabs.addTab(self.tab_scorte, "Scorte Magazzino")
        self.tabs.addTab(self.tab_consumi, "Consumi e Spese")
        self.tabs.addTab(self.tab_fornitori, "Gestione Fornitori")

        self.setup_tab_scorte()
        self.setup_tab_consumi()
        self.setup_tab_fornitori()

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
        header_layout = QHBoxLayout()

        _hm = get_metrics()
        title_label = QLabel("Gestione Magazzino")
        title_label.setStyleSheet(f"QLabel {{ font-size: {_hm['ft']}px; font-weight: 700; color: #2d3748; }}")

        subtitle_label = QLabel("Visualizza scorte, gestisci carico/scarico e monitora i consumi")
        subtitle_label.setStyleSheet(f"QLabel {{ font-size: {_hm['fb']}px; font-weight: 400; color: #718096; }}")
        subtitle_label.setWordWrap(True)

        header_layout.addWidget(title_label)
        header_layout.addSpacing(20)
        header_layout.addWidget(subtitle_label)
        header_layout.addStretch()

        parent_layout.addLayout(header_layout)

    # =================== TAB SCORTE ===================

    def setup_tab_scorte(self):
        layout = QVBoxLayout(self.tab_scorte)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(16)

        # Barra superiore: toggle vista + ordina + carico/scarico
        top_layout = QHBoxLayout()

        # Toggle singoli/categorie
        _toggle_style_active = """
            QPushButton { background-color: #4a5568; color: #ffffff;
                          border-radius: 6px; min-height: 34px; padding: 6px 18px;
                          font-size: 13px; font-weight: 700; }
        """
        _toggle_style_inactive = """
            QPushButton { background-color: #f7fafc; color: #4a5568;
                          border: 1px solid #e2e8f0; border-radius: 6px;
                          min-height: 34px; padding: 6px 18px;
                          font-size: 13px; font-weight: 600; }
            QPushButton:hover { background-color: #edf2f7; }
        """
        self._toggle_style_active = _toggle_style_active
        self._toggle_style_inactive = _toggle_style_inactive

        self.btn_vista_singoli = QPushButton("Singoli Materiali")
        self.btn_vista_singoli.setStyleSheet(_toggle_style_active)
        self.btn_vista_singoli.clicked.connect(self._vista_singoli)

        self._scorte_vista = 'singoli'

        top_layout.addWidget(self.btn_vista_singoli)
        top_layout.addSpacing(16)

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

        # Search field
        self.search_scorte = QLineEdit()
        self.search_scorte.setPlaceholderText("Cerca materiale...")
        self.search_scorte.setFixedWidth(200)
        self.search_scorte.setStyleSheet("""
            QLineEdit { border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 12px;
                        font-size: 13px; background-color: #ffffff; min-height: 22px; }
            QLineEdit:focus { border-color: #718096; }
        """)
        self.search_scorte.textChanged.connect(self.carica_scorte)

        lbl_filtro = QLabel("Mostra:")
        lbl_filtro.setStyleSheet("font-weight: 600;")
        self.combo_filtro_scorte = QComboBox()
        self.combo_filtro_scorte.addItem("Tutte le scorte", "tutte")
        self.combo_filtro_scorte.addItem("Scorte basse", "basse")
        self.combo_filtro_scorte.addItem("Scorte alte", "alte")
        self.combo_filtro_scorte.currentIndexChanged.connect(self.carica_scorte)

        lbl_fornitore = QLabel("Fornitore:")
        lbl_fornitore.setStyleSheet("font-weight: 600;")
        self.combo_fornitore_filtro = QComboBox()
        self.combo_fornitore_filtro.addItem("Tutti", None)
        for nome_f in self.db_manager.get_fornitori_nomi_attivi():
            self.combo_fornitore_filtro.addItem(nome_f, nome_f)
        self.combo_fornitore_filtro.currentIndexChanged.connect(self.carica_scorte)

        top_layout.addSpacing(8)
        top_layout.addWidget(self.search_scorte)
        top_layout.addSpacing(8)
        top_layout.addWidget(lbl_filtro)
        top_layout.addWidget(self.combo_filtro_scorte)
        top_layout.addSpacing(8)
        top_layout.addWidget(lbl_fornitore)
        top_layout.addWidget(self.combo_fornitore_filtro)
        btn_stampa = QPushButton("Stampa Inventario")
        btn_stampa.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568;
                          border: 1px solid #e2e8f0; min-height: 36px; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_stampa.clicked.connect(self.stampa_inventario)

        btn_azzera = QPushButton("Azzera Giacenze")
        btn_azzera.setStyleSheet("""
            QPushButton { background-color: #dd6b20; color: #ffffff; min-height: 36px; }
            QPushButton:hover { background-color: #c05621; }
        """)
        btn_azzera.clicked.connect(self.azzera_tutte_giacenze)

        top_layout.addStretch()
        top_layout.addWidget(btn_stampa)
        top_layout.addSpacing(8)
        top_layout.addWidget(btn_carico)
        top_layout.addSpacing(8)
        top_layout.addWidget(btn_scarico)
        top_layout.addSpacing(8)
        top_layout.addWidget(btn_azzera)
        layout.addLayout(top_layout)

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

    def _vista_singoli(self):
        self._scorte_vista = 'singoli'
        self.btn_vista_singoli.setStyleSheet(self._toggle_style_active)
        self.carica_scorte()

    def carica_scorte(self):
        """Carica e visualizza le scorte nella vista corrente"""
        # Pulisci layout
        while self.scorte_layout.count():
            child = self.scorte_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._carica_scorte_singoli()

    def _carica_scorte_singoli(self):
        """Visualizza le scorte dei materiali (aggregate per materiale)"""
        ordina_per = 'nome'
        scorte = self.db_manager.get_scorte(ordina_per)

        # Applica filtri
        search_text = self.search_scorte.text().lower()
        filtro_val = self.combo_filtro_scorte.currentData()
        fornitore_sel = self.combo_fornitore_filtro.currentData()

        if search_text:
            scorte = [m for m in scorte if search_text in m[1].lower()]
        if filtro_val == 'basse':
            scorte = [m for m in scorte if m[3] > 0 and m[2] < m[3] * 0.3]
        elif filtro_val == 'alte':
            scorte = [m for m in scorte if m[3] == 0 or m[2] >= m[3] * 0.7]
        if fornitore_sel:
            ids = self.db_manager.get_materiali_ids_per_fornitore(fornitore_sel)
            scorte = [m for m in scorte if m[0] in ids]

        if not scorte:
            lbl_vuoto = QLabel("Nessun materiale presente in magazzino.")
            lbl_vuoto.setAlignment(Qt.AlignCenter)
            lbl_vuoto.setStyleSheet("color: #718096; font-size: 16px; padding: 40px;")
            self.scorte_layout.addWidget(lbl_vuoto)
            self.scorte_layout.addStretch()
            return

        for mat in scorte:
            # get_scorte restituisce: id, nome, giacenza_totale, scorta_massima, n_fornitori, prezzo_min, scorta_minima
            mat_id, nome, giacenza_totale, scorta_massima, n_fornitori, prezzo_min = mat[:6]
            scorta_minima = mat[6] if len(mat) > 6 else 0.0
            card = self._crea_card_scorta(mat_id, nome, giacenza_totale, scorta_massima, scorta_minima, n_fornitori, prezzo_min)
            self.scorte_layout.addWidget(card)

        self.scorte_layout.addStretch()

    def _crea_card_scorta(self, mat_id, nome, giacenza_totale, scorta_massima, scorta_minima, n_fornitori, prezzo_min):
        """Crea una card per un materiale (giacenza aggregata su tutti i fornitori)"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: none;
                border-bottom: 1px solid #f0f0f0;
            }
            QFrame:hover { background-color: #fafbfc; }
        """)

        _cm = get_metrics()
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(_cm['mi'], _cm['sf'], _cm['mi'], _cm['sf'])
        card_layout.setSpacing(_cm['sc'])

        # Nome materiale
        lbl_nome = QLabel(nome)
        lbl_nome.setWordWrap(True)
        lbl_nome.setStyleSheet(f"font-size: {_cm['ft'] - 4}px; font-weight: 700; color: #2d3748; min-width: 140px;")
        card_layout.addWidget(lbl_nome)

        # Giacenza totale
        lbl_giacenza = QLabel(f"{giacenza_totale:.2f} m²")
        lbl_giacenza.setStyleSheet(f"font-size: {_cm['ft'] - 6}px; font-weight: 600; color: #38a169; min-width: 100px;")
        lbl_giacenza_label = QLabel("Giacenza")
        lbl_giacenza_label.setStyleSheet("font-size: 11px; color: #a0aec0; font-weight: 500;")
        giacenza_col = QVBoxLayout()
        giacenza_col.setSpacing(2)
        giacenza_col.addWidget(lbl_giacenza_label)
        giacenza_col.addWidget(lbl_giacenza)
        card_layout.addLayout(giacenza_col)

        # Numero fornitori
        forn_text = f"{n_fornitori}" if n_fornitori > 0 else "—"
        lbl_forn = QLabel(forn_text)
        lbl_forn.setWordWrap(True)
        lbl_forn.setStyleSheet(f"font-size: {_cm['ft'] - 6}px; font-weight: 600; color: #4a5568; min-width: 40px;")
        lbl_forn_label = QLabel("Fornitori")
        lbl_forn_label.setStyleSheet("font-size: 11px; color: #a0aec0; font-weight: 500;")
        forn_col = QVBoxLayout()
        forn_col.setSpacing(2)
        forn_col.addWidget(lbl_forn_label)
        forn_col.addWidget(lbl_forn)
        card_layout.addLayout(forn_col)

        # Scorta minima (se impostata)
        if scorta_minima > 0 or scorta_massima > 0:
            lbl_min_val = QLabel(f"min {scorta_minima:.1f} / max {scorta_massima:.1f} m²")
            lbl_min_val.setStyleSheet("font-size: 12px; color: #718096; min-width: 140px;")
            card_layout.addWidget(lbl_min_val)

        # Barra scorta
        percentuale = (giacenza_totale / scorta_massima * 100) if scorta_massima > 0 else 0
        barra = BarraScorta(percentuale)
        barra.setMinimumWidth(160)
        card_layout.addWidget(barra, 1)

        # Bottone fornitori (drill-down)
        btn_forn = QPushButton("Fornitori")
        if n_fornitori > 1:
            btn_forn.setStyleSheet("""
                QPushButton {
                    background-color: #ebf8ff; color: #2b6cb0;
                    border: none; border-radius: 6px;
                    min-height: 34px; padding: 6px 18px;
                    font-size: 13px; font-weight: 600;
                }
                QPushButton:hover { background-color: #bee3f8; }
            """)
            btn_forn.clicked.connect(lambda checked, mid=mat_id, mn=nome: self._mostra_fornitori_materiale(mid, mn))
        else:
            btn_forn.setStyleSheet("""
                QPushButton {
                    background-color: #f7fafc; color: #cbd5e0;
                    border: none; border-radius: 6px;
                    min-height: 34px; padding: 6px 18px;
                    font-size: 13px; font-weight: 600;
                }
            """)
            btn_forn.setEnabled(False)
        card_layout.addWidget(btn_forn)

        # Bottone storico
        btn_storico = QPushButton("Storico")
        btn_storico.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc; color: #4a5568;
                border: none; border-radius: 6px;
                min-height: 34px; padding: 6px 18px; font-size: 13px;
            }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_storico.clicked.connect(lambda checked, mid=mat_id, mn=nome: self.mostra_storico(mid, mn))
        card_layout.addWidget(btn_storico)

        return card

    def _mostra_fornitori_materiale(self, materiale_id, nome_materiale):
        """Mostra inline (nel pannello scorte) la tabella fornitori del materiale selezionato"""
        fornitori = self.db_manager.get_fornitori_per_materiale(materiale_id)

        # Pulisci layout scorte
        while self.scorte_layout.count():
            child = self.scorte_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Header: bottone indietro + titolo
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        btn_back = QPushButton("← Tutti i materiali")
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc; color: #4a5568;
                border: 1px solid #e2e8f0; min-height: 42px;
                padding: 6px 20px; font-size: 15px; font-weight: 600;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_back.clicked.connect(self.carica_scorte)

        lbl_title = QLabel(f"Fornitori — {nome_materiale}")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: 700; color: #2d3748;")

        header_layout.addWidget(btn_back)
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        self.scorte_layout.addWidget(header)

        # Tabella fornitori
        if not fornitori:
            lbl = QLabel("Nessun fornitore configurato per questo materiale.\nAggiungili da Gestione Materiali.")
            lbl.setStyleSheet("color: #718096; font-size: 14px; padding: 40px;")
            lbl.setAlignment(Qt.AlignCenter)
            self.scorte_layout.addWidget(lbl)
        else:
            table = QTableWidget(len(fornitori), 5)
            table.setHorizontalHeaderLabels(["Fornitore", "Scorta Min", "Barra Scorte", "Giacenza", "Scorta Max"])
            table.setStyleSheet("""
                QTableWidget { background-color: #ffffff; border: 1px solid #e2e8f0;
                               border-radius: 8px; font-size: 16px; }
                QHeaderView::section { background-color: #f7fafc; color: #4a5568;
                                       font-weight: 700; font-size: 15px; padding: 12px 10px;
                                       border: none; border-bottom: 2px solid #e2e8f0; }
            """)
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.verticalHeader().setVisible(False)
            table.setAlternatingRowColors(True)

            for row, mf in enumerate(fornitori):
                mf_id, forn_nome, prezzo_forn, s_min, s_max, giacenza = mf
                table.setItem(row, 0, QTableWidgetItem(forn_nome))
                table.setItem(row, 1, QTableWidgetItem(f"{s_min:.1f} m²"))

                barra = BarraScorta((giacenza / s_max * 100) if s_max > 0 else 0)
                barra.setMinimumHeight(32)
                table.setCellWidget(row, 2, barra)

                item_giac = QTableWidgetItem(f"{giacenza:.2f} m²")
                item_giac.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, 3, item_giac)
                table.setItem(row, 4, QTableWidgetItem(f"{s_max:.1f} m²"))
                table.setRowHeight(row, 52)

            self.scorte_layout.addWidget(table)

            totale = sum(mf[5] for mf in fornitori)
            lbl_tot = QLabel(f"Giacenza totale: {totale:.2f} m²")
            lbl_tot.setStyleSheet("font-size: 16px; font-weight: 600; color: #4a5568; padding: 8px 0;")
            self.scorte_layout.addWidget(lbl_tot)

        self.scorte_layout.addStretch()

    def stampa_inventario(self):
        """Genera report inventario come tabella HTML e lo mostra in anteprima stampabile"""
        from datetime import datetime as _dt
        now = _dt.now().strftime("%d/%m/%Y %H:%M")
        scorte = self.db_manager.get_scorte('nome')

        # Costruisci la tabella HTML
        td = 'style="border:1px solid #cbd5e0; padding:8px 12px; font-size:14px;"'
        td_num = 'style="border:1px solid #cbd5e0; padding:8px 12px; font-size:14px; text-align:right;"'
        td_sub = 'style="border:1px solid #cbd5e0; padding:6px 12px 6px 28px; font-size:13px; color:#4a5568; background:#f7fafc;"'
        td_sub_num = 'style="border:1px solid #cbd5e0; padding:6px 12px; font-size:13px; color:#4a5568; text-align:right; background:#f7fafc;"'
        th = 'style="border:1px solid #a0aec0; padding:10px 12px; background:#edf2f7; font-size:14px; font-weight:bold; text-align:left;"'
        th_num = 'style="border:1px solid #a0aec0; padding:10px 12px; background:#edf2f7; font-size:14px; font-weight:bold; text-align:right;"'

        rows_html = ""
        for row in scorte:
            mat_id, nome, giacenza_totale, scorta_massima, n_fornitori, prezzo_min = row[:6]
            scorta_minima = row[6] if len(row) > 6 else 0.0
            pct = f"{(giacenza_totale / scorta_massima * 100):.0f}%" if scorta_massima > 0 else "—"

            rows_html += f"""
            <tr>
              <td {td}><b>{nome}</b></td>
              <td {td_num}><b>{giacenza_totale:.2f}</b></td>
              <td {td_num}>{scorta_minima:.2f}</td>
              <td {td_num}>{scorta_massima:.2f}</td>
              <td {td_num}>{pct}</td>
              <td {td}>—</td>
              <td {td_num}>—</td>
              <td {td_num}>—</td>
              <td {td_num}>—</td>
            </tr>"""

            if n_fornitori > 0:
                fornitori = self.db_manager.get_fornitori_per_materiale(mat_id)
                for mf in fornitori:
                    _, forn_nome, _, s_min, s_max, giacenza = mf
                    pct_f = f"{(giacenza / s_max * 100):.0f}%" if s_max > 0 else "—"
                    rows_html += f"""
            <tr>
              <td {td_sub}></td>
              <td {td_sub_num}></td>
              <td {td_sub_num}></td>
              <td {td_sub_num}></td>
              <td {td_sub_num}></td>
              <td {td_sub}>↳ {forn_nome}</td>
              <td {td_sub_num}>{giacenza:.2f}</td>
              <td {td_sub_num}>{s_min:.2f}</td>
              <td {td_sub_num}>{pct_f}</td>
            </tr>"""

        html = f"""
        <html><body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">
        <h2 style="font-size:18px; margin-bottom:4px; margin-top:0;">Inventario Magazzino — Software Aziendale RCS</h2>
        <p style="font-size:12px; color:#718096; margin-top:0; margin-bottom:8px;">Generato il {now}</p>
        <table style="border-collapse:collapse; width:100%;">
          <thead>
            <tr>
              <th {th}>Materiale</th>
              <th {th_num}>Giac. Tot (m²)</th>
              <th {th_num}>Scorta Min</th>
              <th {th_num}>Scorta Max</th>
              <th {th_num}>% Agg.</th>
              <th {th}>Fornitore</th>
              <th {th_num}>Giac. Forn (m²)</th>
              <th {th_num}>Min Forn</th>
              <th {th_num}>% Forn</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
        </body></html>"""

        try:
            from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
            from PyQt5.QtGui import QTextDocument
            from PyQt5.QtCore import QSizeF
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOrientation(QPrinter.Landscape)
            printer.setPageSize(QPrinter.A4)
            printer.setPageMargins(10, 10, 10, 10, QPrinter.Millimeter)
            pdlg = QPrintDialog(printer, self)
            if pdlg.exec_() == QPrintDialog.Accepted:
                doc = QTextDocument()
                doc.setHtml(html)
                page_rect = printer.pageRect(QPrinter.Point)
                doc.setPageSize(QSizeF(page_rect.width(), page_rect.height()))
                doc.print_(printer)
        except Exception as e:
            QMessageBox.warning(self, "Stampa", f"Impossibile stampare:\n{str(e)}")

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

    def azzera_tutte_giacenze(self):
        """Azzera la giacenza di tutti i materiali e cancella tutti i movimenti."""
        from PyQt5.QtWidgets import QMessageBox
        risposta = QMessageBox.question(
            self,
            "Conferma azzeramento",
            "Stai per azzerare la giacenza di TUTTI i materiali e cancellare tutti i movimenti.\n\n"
            "Questa operazione non è reversibile.\n\nProcedere?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if risposta == QMessageBox.Yes:
            ok = self.db_manager.reset_tutte_giacenze()
            if ok:
                QMessageBox.information(self, "Completato", "Giacenze azzerate con successo.")
                self.carica_scorte()
            else:
                QMessageBox.critical(self, "Errore", "Si è verificato un errore durante l'azzeramento.")

    def apri_dialog_carico(self):
        """Dialog per aggiungere materiale al magazzino (carico)"""
        self._apri_dialog_movimento('carico')

    def apri_dialog_scarico(self):
        """Dialog per rimuovere materiale dal magazzino (scarico)"""
        self._apri_dialog_movimento('scarico')

    def _apri_dialog_movimento(self, tipo):
        """Dialog generico per carico/scarico con selezione fornitore"""
        dialog = QDialog(self)
        titolo = "Carico Materiale" if tipo == 'carico' else "Scarico Materiale"
        dialog.setWindowTitle(titolo)
        dialog.setFixedSize(500, 440)
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
        tutti_materiali = self.db_manager.get_all_materiali()
        combo_mat = QComboBox()
        for mat in tutti_materiali:
            mat_id, nome = mat[0], mat[1]
            combo_mat.addItem(nome, mat_id)

        # Selezione fornitore (aggiornata in base al materiale)
        lbl_forn = QLabel("Fornitore:")
        combo_forn_mat = QComboBox()

        def aggiorna_fornitori_per_mat():
            mat_id = combo_mat.currentData()
            combo_forn_mat.clear()
            if mat_id:
                fornitori = self.db_manager.get_fornitori_per_materiale(mat_id)
                if fornitori:
                    for mf_id, forn_nome, prezzo_forn, s_min, s_max, giacenza in fornitori:
                        combo_forn_mat.addItem(
                            f"{forn_nome}  (giac: {giacenza:.1f} m²)", forn_nome
                        )
                    combo_forn_mat.setEnabled(True)
                    lbl_forn.setEnabled(True)
                else:
                    combo_forn_mat.addItem("— Nessun fornitore configurato —", "")
                    combo_forn_mat.setEnabled(False)
                    lbl_forn.setEnabled(False)

        combo_mat.currentIndexChanged.connect(aggiorna_fornitori_per_mat)
        aggiorna_fornitori_per_mat()

        # Quantità
        edit_quantita = NoScrollDoubleSpinBox()
        edit_quantita.setDecimals(2)
        edit_quantita.setMaximum(99999.99)
        edit_quantita.setSuffix(" m²")
        edit_quantita.setMinimum(0.01)

        # Note
        edit_note = QLineEdit()
        edit_note.setPlaceholderText("Note opzionali...")

        form.addRow("Materiale:", combo_mat)
        form.addRow(lbl_forn, combo_forn_mat)
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
            forn_nome = combo_forn_mat.currentData() or ""
            quantita = edit_quantita.value()
            note = edit_note.text().strip()

            if not mat_id:
                QMessageBox.warning(dialog, "Attenzione", "Seleziona un materiale.")
                return
            if not forn_nome:
                QMessageBox.warning(dialog, "Attenzione", "Seleziona un fornitore per questo materiale.")
                return
            if quantita <= 0:
                QMessageBox.warning(dialog, "Attenzione", "Inserisci una quantità valida.")
                return

            giacenza_attuale, scorta_massima = self.db_manager.get_giacenza_scorta_fornitore(mat_id, forn_nome)

            if tipo == 'scarico' and quantita > giacenza_attuale:
                QMessageBox.warning(
                    dialog, "Quantità insufficiente",
                    f"Non è possibile scaricare {quantita:.2f} m².\n"
                    f"Giacenza disponibile per {forn_nome}: {giacenza_attuale:.2f} m²."
                )
                return

            if tipo == 'carico' and scorta_massima > 0:
                giacenza_dopo = giacenza_attuale + quantita
                if giacenza_dopo > scorta_massima:
                    risposta = QMessageBox.question(
                        dialog, "Capacità superata",
                        f"Il carico porterà la giacenza a {giacenza_dopo:.2f} m²,\n"
                        f"superiore alla scorta massima ({scorta_massima:.2f} m²).\n\n"
                        f"Vuoi procedere comunque?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if risposta == QMessageBox.No:
                        return

            self.db_manager.registra_movimento(mat_id, tipo, quantita, note, fornitore_nome=forn_nome)
            verbo = "caricato" if tipo == 'carico' else "scaricato"
            QMessageBox.information(dialog, "Successo",
                                    f"Movimento registrato: {quantita:.2f} m² {verbo} ({forn_nome}).")
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

        # Tabella movimenti individuali
        self.tabella_consumi = QTableWidget()
        self.tabella_consumi.setColumnCount(7)
        self.tabella_consumi.setHorizontalHeaderLabels(
            ["Data", "Tipo", "Materiale", "Quantità (m²)", "Fornitore", "Note", ""]
        )
        self.tabella_consumi.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabella_consumi.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabella_consumi.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabella_consumi.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabella_consumi.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tabella_consumi.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.tabella_consumi.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.tabella_consumi.setColumnWidth(6, 170)
        self.tabella_consumi.verticalHeader().setVisible(False)
        self.tabella_consumi.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabella_consumi.setAlternatingRowColors(True)
        self.tabella_consumi.setStyleSheet("""
            QTableWidget { border: 1px solid #e2e8f0; border-radius: 8px; }
            QTableWidget::item { padding: 8px; }
            QTableWidget::item:alternate { background-color: #f7fafc; }
        """)

        layout.addWidget(self.tabella_consumi, 1)

    def carica_consumi(self):
        """Carica e visualizza i movimenti individuali per il periodo selezionato"""
        periodo = self.combo_periodo.currentData() or 'mese_corrente'
        data_inizio, data_fine = self._calcola_date_periodo(periodo)

        movimenti = self.db_manager.get_movimenti_periodo(data_inizio, data_fine)

        self.tabella_consumi.setRowCount(len(movimenti))

        totale_scarico = 0.0
        n_scarichi = 0

        for row, mov in enumerate(movimenti):
            mov_id, nome, tipo, quantita, data, note, fornitore_nome, mat_id = mov

            if tipo == 'scarico':
                totale_scarico += quantita
                n_scarichi += 1

            # Data
            data_str = data[:10] if len(data) >= 10 else data
            self.tabella_consumi.setItem(row, 0, QTableWidgetItem(data_str))

            # Tipo con colore
            tipo_item = QTableWidgetItem(tipo.upper())
            tipo_item.setForeground(QColor(56, 161, 105) if tipo == 'carico' else QColor(229, 62, 62))
            tipo_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.tabella_consumi.setItem(row, 1, tipo_item)

            self.tabella_consumi.setItem(row, 2, QTableWidgetItem(nome))

            q_item = QTableWidgetItem(f"{quantita:.2f}")
            q_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabella_consumi.setItem(row, 3, q_item)

            self.tabella_consumi.setItem(row, 4, QTableWidgetItem(fornitore_nome or "—"))
            self.tabella_consumi.setItem(row, 5, QTableWidgetItem(note or ""))

            # Pulsanti Modifica / Elimina
            btn_frame = QFrame()
            btn_layout = QHBoxLayout(btn_frame)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(6)

            btn_mod = QPushButton("Modifica")
            btn_mod.setFixedHeight(30)
            btn_mod.setStyleSheet("""
                QPushButton { background-color: #edf2f7; color: #2d3748; border: none;
                              border-radius: 4px; padding: 2px 10px; font-size: 12px; font-weight: 600; }
                QPushButton:hover { background-color: #e2e8f0; }
            """)
            btn_mod.clicked.connect(lambda checked, mid=mov_id, q=quantita, n=note or "":
                                    self._modifica_movimento(mid, q, n))

            btn_del = QPushButton("Elimina")
            btn_del.setFixedHeight(30)
            btn_del.setStyleSheet("""
                QPushButton { background-color: #fff5f5; color: #c53030; border: 1px solid #fed7d7;
                              border-radius: 4px; padding: 2px 10px; font-size: 12px; font-weight: 600; }
                QPushButton:hover { background-color: #fed7d7; }
            """)
            btn_del.clicked.connect(lambda checked, mid=mov_id, mn=nome, t=tipo, q=quantita:
                                    self._elimina_movimento(mid, mn, t, q))

            btn_layout.addWidget(btn_mod)
            btn_layout.addWidget(btn_del)
            self.tabella_consumi.setCellWidget(row, 6, btn_frame)
            self.tabella_consumi.setRowHeight(row, 44)

        # Aggiorna riepilogo
        periodo_testo = self.combo_periodo.currentText()
        if movimenti:
            self.lbl_riepilogo_consumi.setText(
                f"{periodo_testo}:  {len(movimenti)} movimenti  |  "
                f"Totale scaricato: {totale_scarico:.2f} m²  ({n_scarichi} scarichi)"
            )
        else:
            self.lbl_riepilogo_consumi.setText(
                f"{periodo_testo}:  Nessun movimento registrato nel periodo selezionato"
            )

    def _modifica_movimento(self, movimento_id, quantita_attuale, note_attuale):
        """Dialog per modificare quantità e note di un movimento"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Modifica Movimento")
        dialog.setFixedSize(400, 220)
        dialog.setStyleSheet("""
            QDialog { background-color: #fafbfc; }
            QLabel { color: #2d3748; font-size: 14px; font-weight: 500; }
            QDoubleSpinBox, QLineEdit {
                border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 12px;
                font-size: 14px; background-color: #ffffff; min-height: 18px; }
            QPushButton { border: none; border-radius: 6px; font-size: 14px;
                          font-weight: 600; padding: 10px 20px; min-height: 36px; }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setVerticalSpacing(10)

        spin_q = QDoubleSpinBox()
        spin_q.setDecimals(2)
        spin_q.setMaximum(99999.99)
        spin_q.setSuffix(" m²")
        spin_q.setValue(quantita_attuale)
        spin_q.setMinimumHeight(get_metrics()['fh'])

        edit_note = QLineEdit()
        edit_note.setText(note_attuale)
        edit_note.setPlaceholderText("Note opzionali...")

        form.addRow("Quantità:", spin_q)
        form.addRow("Note:", edit_note)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_salva = QPushButton("Salva")
        btn_salva.setStyleSheet("QPushButton { background-color: #4a5568; color: #ffffff; } QPushButton:hover { background-color: #2d3748; }")
        btn_annulla = QPushButton("Annulla")
        btn_annulla.setStyleSheet("QPushButton { background-color: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; } QPushButton:hover { background-color: #edf2f7; }")
        btns.addWidget(btn_salva)
        btns.addWidget(btn_annulla)
        layout.addLayout(btns)

        btn_annulla.clicked.connect(dialog.reject)
        btn_salva.clicked.connect(dialog.accept)

        if dialog.exec_() == QDialog.Accepted:
            nuova_q = spin_q.value()
            if nuova_q <= 0:
                QMessageBox.warning(self, "Errore", "La quantità deve essere maggiore di 0.")
                return
            ok = self.db_manager.modifica_movimento(movimento_id, nuova_q, edit_note.text().strip())
            if ok:
                self.carica_consumi()
                self.carica_scorte()
            else:
                QMessageBox.critical(self, "Errore", "Errore durante la modifica del movimento.")

    def _elimina_movimento(self, movimento_id, nome_materiale, tipo, quantita):
        """Conferma ed elimina un movimento, aggiornando automaticamente la giacenza"""
        risposta = QMessageBox.question(
            self, "Elimina Movimento",
            f"Eliminare il movimento '{tipo.upper()}' di {quantita:.2f} m² per '{nome_materiale}'?\n\n"
            f"La giacenza in magazzino verrà aggiornata automaticamente.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if risposta == QMessageBox.Yes:
            ok = self.db_manager.elimina_movimento(movimento_id)
            if ok:
                self.carica_consumi()
                self.carica_scorte()
            else:
                QMessageBox.critical(self, "Errore", "Errore durante l'eliminazione del movimento.")

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

    # =================== TAB FORNITORI ===================

    def setup_tab_fornitori(self):
        layout = QVBoxLayout(self.tab_fornitori)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        lbl_title = QLabel("Fornitori")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #2d3748;")

        btn_aggiungi = QPushButton("Aggiungi Fornitore")
        btn_aggiungi.setStyleSheet("""
            QPushButton { background-color: #4a5568; color: #ffffff; min-height: 36px; min-width: 160px; }
            QPushButton:hover { background-color: #2d3748; }
        """)
        btn_aggiungi.clicked.connect(self.apri_dialog_nuovo_fornitore)

        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(btn_aggiungi)
        layout.addLayout(header_layout)

        # Scroll area per le card fornitori
        self.scroll_fornitori = QScrollArea()
        self.scroll_fornitori.setWidgetResizable(True)
        self.scroll_fornitori.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.fornitori_container = QWidget()
        self.fornitori_layout = QGridLayout(self.fornitori_container)
        self.fornitori_layout.setContentsMargins(0, 0, 0, 0)
        self.fornitori_layout.setSpacing(16)
        self.scroll_fornitori.setWidget(self.fornitori_container)

        layout.addWidget(self.scroll_fornitori)

    def carica_fornitori(self):
        """Carica e visualizza le card dei fornitori"""
        # Pulisci layout
        while self.fornitori_layout.count():
            child = self.fornitori_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        fornitori = self.db_manager.get_all_fornitori()

        if not fornitori:
            lbl_vuoto = QLabel("Nessun fornitore presente. Aggiungine uno con il pulsante qui sopra.")
            lbl_vuoto.setAlignment(Qt.AlignCenter)
            lbl_vuoto.setStyleSheet("color: #718096; font-size: 16px; padding: 40px;")
            self.fornitori_layout.addWidget(lbl_vuoto, 0, 0)
            return

        col_count = 3
        for idx, (forn_id, nome) in enumerate(fornitori):
            row = idx // col_count
            col = idx % col_count
            card = self._crea_card_fornitore(nome)
            self.fornitori_layout.addWidget(card, row, col)

        # Spacer per evitare che le card si espandano verticalmente
        self.fornitori_layout.setRowStretch(len(fornitori) // col_count + 1, 1)

    def _crea_card_fornitore(self, nome):
        """Crea una card cliccabile per un fornitore"""
        # Conta i materiali del fornitore
        materiali = self.db_manager.get_scorte_per_fornitore(nome)
        n_materiali = len(materiali)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
            QFrame:hover {
                border-color: #4a5568;
                background-color: #f7fafc;
            }
        """)
        card.setCursor(Qt.PointingHandCursor)
        card.setMinimumHeight(120)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(8)

        lbl_nome = QLabel(nome)
        lbl_nome.setStyleSheet("font-size: 20px; font-weight: 700; color: #2d3748;")
        lbl_nome.setAlignment(Qt.AlignCenter)

        lbl_mat = QLabel(f"{n_materiali} materiali")
        lbl_mat.setStyleSheet("font-size: 13px; color: #718096;")
        lbl_mat.setAlignment(Qt.AlignCenter)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_vedi = QPushButton("Vedi Scorte")
        btn_vedi.setStyleSheet("""
            QPushButton { background-color: #edf2f7; color: #2d3748; border: none; border-radius: 6px; min-height: 32px; font-size: 13px; font-weight: 600; }
            QPushButton:hover { background-color: #e2e8f0; }
        """)
        btn_vedi.clicked.connect(lambda checked, n=nome: self.mostra_scorte_fornitore(n))

        btn_modifica = QPushButton("Modifica")
        btn_modifica.setStyleSheet("""
            QPushButton { background-color: #ebf8ff; color: #2b6cb0; border: 1px solid #bee3f8; border-radius: 6px; min-height: 32px; font-size: 13px; font-weight: 600; padding: 4px 12px; }
            QPushButton:hover { background-color: #bee3f8; }
        """)
        btn_modifica.clicked.connect(lambda checked, n=nome: self.apri_dialog_modifica_fornitore(n))

        btn_row.addWidget(btn_vedi)
        btn_row.addWidget(btn_modifica)

        card_layout.addWidget(lbl_nome)
        card_layout.addWidget(lbl_mat)
        card_layout.addLayout(btn_row)

        return card

    def mostra_scorte_fornitore(self, nome_fornitore):
        """Mostra le scorte dei materiali di un fornitore in una tabella compatta"""
        scorte = self.db_manager.get_scorte_per_fornitore(nome_fornitore)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Scorte - {nome_fornitore}")
        dialog.setMinimumSize(750, 420)
        dialog.setStyleSheet("""
            QDialog { background-color: #fafbfc; font-family: system-ui, -apple-system, sans-serif; }
            QLabel { color: #2d3748; }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        title = QLabel(f"Scorte — {nome_fornitore}")
        title.setStyleSheet("font-size: 17px; font-weight: 700; color: #1a202c;")
        layout.addWidget(title)

        if not scorte:
            lbl_vuoto = QLabel("Nessun materiale associato a questo fornitore.\nAssegna il fornitore ai materiali da 'Gestione Materiali'.")
            lbl_vuoto.setStyleSheet("color: #718096; font-size: 14px; padding: 20px;")
            lbl_vuoto.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl_vuoto)
        else:
            colonne = ["Materiale", "Giacenza (m²)", "Min (m²)", "Max (m²)", "Stato", "Prezzo/m²"]
            table = QTableWidget(len(scorte), len(colonne))
            table.setHorizontalHeaderLabels(colonne)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setAlternatingRowColors(True)
            table.verticalHeader().setVisible(False)
            table.setShowGrid(False)
            table.setStyleSheet("""
                QTableWidget {
                    background-color: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    font-size: 13px;
                    color: #2d3748;
                }
                QTableWidget::item { padding: 6px 10px; border: none; }
                QTableWidget::item:selected { background-color: #ebf8ff; color: #2b6cb0; }
                QTableWidget::item:alternate { background-color: #f7fafc; }
                QHeaderView::section {
                    background-color: #edf2f7;
                    color: #4a5568;
                    font-weight: 600;
                    font-size: 12px;
                    padding: 6px 10px;
                    border: none;
                    border-bottom: 1px solid #e2e8f0;
                }
            """)

            for row_idx, row_data in enumerate(scorte):
                mat_id, nome, giacenza, capacita, fornitore, prezzo, scorta_min = row_data

                # Materiale
                item_nome = QTableWidgetItem(nome)
                item_nome.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                item_nome.setFont(item_nome.font())
                table.setItem(row_idx, 0, item_nome)

                # Giacenza
                item_giac = QTableWidgetItem(f"{giacenza:.2f}")
                item_giac.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                table.setItem(row_idx, 1, item_giac)

                # Min
                item_min = QTableWidgetItem(f"{scorta_min:.2f}" if scorta_min else "—")
                item_min.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                item_min.setForeground(QColor("#718096"))
                table.setItem(row_idx, 2, item_min)

                # Max
                item_max = QTableWidgetItem(f"{capacita:.2f}" if capacita else "—")
                item_max.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                item_max.setForeground(QColor("#718096"))
                table.setItem(row_idx, 3, item_max)

                # Stato (etichetta colorata)
                if capacita and capacita > 0:
                    pct = giacenza / capacita
                    if pct >= 0.6:
                        stato, colore_bg, colore_txt = "OK", "#c6f6d5", "#276749"
                    elif pct >= 0.25:
                        stato, colore_bg, colore_txt = "Bassa", "#fefcbf", "#744210"
                    else:
                        stato, colore_bg, colore_txt = "Critica", "#fed7d7", "#9b2c2c"
                else:
                    stato, colore_bg, colore_txt = "N/D", "#edf2f7", "#718096"
                item_stato = QTableWidgetItem(stato)
                item_stato.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                item_stato.setBackground(QColor(colore_bg))
                item_stato.setForeground(QColor(colore_txt))
                table.setItem(row_idx, 4, item_stato)

                # Prezzo
                item_prezzo = QTableWidgetItem(f"€ {prezzo:.2f}" if prezzo else "—")
                item_prezzo.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                table.setItem(row_idx, 5, item_prezzo)

            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            for col in range(1, len(colonne)):
                header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
            table.setRowHeight(0, 36)
            for row_idx in range(len(scorte)):
                table.setRowHeight(row_idx, 36)

            layout.addWidget(table)

        btn_chiudi = QPushButton("Chiudi")
        btn_chiudi.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; min-height: 34px; min-width: 100px; border-radius: 6px; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_chiudi.clicked.connect(dialog.accept)
        layout.addWidget(btn_chiudi, alignment=Qt.AlignRight)

        dialog.exec_()

    def apri_dialog_nuovo_fornitore(self):
        """Dialog per aggiungere un nuovo fornitore"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Aggiungi Fornitore")
        dialog.setFixedSize(500, 480)
        dialog.setStyleSheet("""
            QDialog { background-color: #fafbfc; font-family: system-ui, -apple-system, sans-serif; }
            QLabel { color: #2d3748; font-size: 14px; font-weight: 500; }
            QLineEdit {
                border: 1px solid #e2e8f0; border-radius: 6px;
                padding: 10px 14px; font-size: 14px;
                background-color: #ffffff; color: #2d3748; min-height: 18px;
            }
            QPushButton {
                border: none; border-radius: 6px;
                font-size: 14px; font-weight: 600;
                padding: 10px 20px; min-height: 36px;
            }
            QListWidget {
                border: 1px solid #e2e8f0; border-radius: 6px;
                background-color: #ffffff; font-size: 13px; padding: 4px;
            }
            QListWidget::item { padding: 6px; border-radius: 4px; }
            QListWidget::item:hover { background-color: #f7fafc; }
            QListWidget::item:selected { background-color: #edf2f7; color: #2d3748; }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(16)

        lbl_titolo = QLabel("Nuovo Fornitore")
        lbl_titolo.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(lbl_titolo)

        form = QFormLayout()
        form.setVerticalSpacing(12)

        edit_nome = QLineEdit()
        edit_nome.setPlaceholderText("es. NUOVO FORNITORE SRL")
        form.addRow("Nome Fornitore:", edit_nome)
        layout.addLayout(form)

        lbl_mat = QLabel("Materiali forniti (seleziona uno o più):")
        lbl_mat.setStyleSheet("font-weight: 600; margin-top: 8px;")
        layout.addWidget(lbl_mat)

        lista_mat = QListWidget()
        lista_mat.setSelectionMode(QAbstractItemView.MultiSelection)

        tutti_materiali = self.db_manager.get_all_materiali()
        for mat in tutti_materiali:
            mat_id, nome_mat = mat[0], mat[1]
            fornitore_attuale = mat[4] if len(mat) > 4 else ""
            testo = nome_mat
            if fornitore_attuale:
                testo += f"  ({fornitore_attuale})"
            item = QListWidgetItem(testo)
            item.setData(Qt.UserRole, mat_id)
            lista_mat.addItem(item)

        layout.addWidget(lista_mat)

        btn_layout = QHBoxLayout()
        btn_annulla = QPushButton("Annulla")
        btn_annulla.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_annulla.clicked.connect(dialog.reject)

        btn_salva = QPushButton("Salva Fornitore")
        btn_salva.setStyleSheet("""
            QPushButton { background-color: #4a5568; color: #ffffff; }
            QPushButton:hover { background-color: #2d3748; }
        """)

        def salva():
            nome = edit_nome.text().strip().upper()
            if not nome:
                QMessageBox.warning(dialog, "Attenzione", "Inserisci il nome del fornitore.")
                return

            result = self.db_manager.add_fornitore(nome)
            if not result:
                QMessageBox.warning(dialog, "Attenzione", f"Il fornitore '{nome}' esiste già.")
                return

            # Assegna i materiali selezionati
            selected_ids = [lista_mat.item(i).data(Qt.UserRole)
                            for i in range(lista_mat.count())
                            if lista_mat.item(i).isSelected()]
            if selected_ids:
                self.db_manager.assegna_materiali_a_fornitore(nome, selected_ids)

            QMessageBox.information(dialog, "Successo", f"Fornitore '{nome}' aggiunto con successo!")
            dialog.accept()
            self.carica_fornitori()

        btn_salva.clicked.connect(salva)

        btn_layout.addWidget(btn_annulla)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_salva)
        layout.addLayout(btn_layout)

        dialog.exec_()

    def apri_dialog_modifica_fornitore(self, nome_attuale):
        """Dialog per modificare il nome di un fornitore esistente"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Modifica Fornitore - {nome_attuale}")
        dialog.setFixedSize(420, 200)
        dialog.setStyleSheet("""
            QDialog { background-color: #fafbfc; font-family: system-ui, -apple-system, sans-serif; }
            QLabel { color: #2d3748; font-size: 14px; font-weight: 500; }
            QLineEdit {
                border: 1px solid #e2e8f0; border-radius: 6px;
                padding: 10px 14px; font-size: 14px;
                background-color: #ffffff; color: #2d3748; min-height: 18px;
            }
            QPushButton { border: none; border-radius: 6px; font-size: 14px; font-weight: 600; padding: 10px 20px; min-height: 36px; }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(16)

        lbl_titolo = QLabel(f"Modifica nome fornitore")
        lbl_titolo.setStyleSheet("font-size: 17px; font-weight: 700;")
        layout.addWidget(lbl_titolo)

        form = QFormLayout()
        edit_nome = QLineEdit()
        edit_nome.setText(nome_attuale)
        form.addRow("Nuovo nome:", edit_nome)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_annulla = QPushButton("Annulla")
        btn_annulla.setStyleSheet("QPushButton { background-color: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; } QPushButton:hover { background-color: #edf2f7; }")
        btn_annulla.clicked.connect(dialog.reject)

        btn_salva = QPushButton("Salva")
        btn_salva.setStyleSheet("QPushButton { background-color: #4a5568; color: #ffffff; } QPushButton:hover { background-color: #2d3748; }")

        def salva():
            nuovo_nome = edit_nome.text().strip().upper()
            if not nuovo_nome:
                QMessageBox.warning(dialog, "Attenzione", "Il nome non può essere vuoto.")
                return
            if nuovo_nome == nome_attuale:
                dialog.accept()
                return
            result = self.db_manager.rename_fornitore(nome_attuale, nuovo_nome)
            if not result:
                QMessageBox.warning(dialog, "Attenzione", f"Il nome '{nuovo_nome}' è già in uso.")
                return
            QMessageBox.information(dialog, "Successo", f"Fornitore rinominato in '{nuovo_nome}'.")
            dialog.accept()
            self.carica_fornitori()
            self.carica_scorte()

        btn_salva.clicked.connect(salva)
        btn_layout.addWidget(btn_annulla)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_salva)
        layout.addLayout(btn_layout)

        dialog.exec_()

    # =================== FOOTER ===================

    def create_footer(self, parent_layout):
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        btn_chiudi = QPushButton("Chiudi Magazzino")
        _fbh = get_metrics()['bh']
        btn_chiudi.setStyleSheet(f"""
            QPushButton {{
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: {_fbh}px;
                min-width: 200px;
            }}
            QPushButton:hover {{
                background-color: #edf2f7;
            }}
        """)
        btn_chiudi.clicked.connect(self.close)

        footer_layout.addWidget(btn_chiudi)
        parent_layout.addLayout(footer_layout)
