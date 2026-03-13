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
                             QListWidget, QListWidgetItem, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QColor, QPainter, QLinearGradient
from ui.materiale_ui_components import NoScrollDoubleSpinBox
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

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 15, 30, 15)
        main_layout.setSpacing(12)

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

        title_label = QLabel("Gestione Magazzino")
        title_label.setStyleSheet("QLabel { font-size: 24px; font-weight: 700; color: #2d3748; }")

        subtitle_label = QLabel("Visualizza scorte, gestisci carico/scarico e monitora i consumi")
        subtitle_label.setStyleSheet("QLabel { font-size: 14px; font-weight: 400; color: #718096; }")

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

        self.btn_vista_categorie = QPushButton("Per Categoria")
        self.btn_vista_categorie.setStyleSheet(_toggle_style_inactive)
        self.btn_vista_categorie.clicked.connect(self._vista_categorie)

        self._scorte_vista = 'singoli'  # 'singoli' | 'categorie'

        top_layout.addWidget(self.btn_vista_singoli)
        top_layout.addWidget(self.btn_vista_categorie)
        top_layout.addSpacing(16)

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

        top_layout.addStretch()
        top_layout.addWidget(lbl_ordina)
        top_layout.addWidget(self.combo_ordinamento)
        top_layout.addSpacing(8)
        top_layout.addWidget(btn_carico)
        top_layout.addSpacing(8)
        top_layout.addWidget(btn_scarico)
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
        self.btn_vista_categorie.setStyleSheet(self._toggle_style_inactive)
        self.carica_scorte()

    def _vista_categorie(self):
        self._scorte_vista = 'categorie'
        self.btn_vista_categorie.setStyleSheet(self._toggle_style_active)
        self.btn_vista_singoli.setStyleSheet(self._toggle_style_inactive)
        self.carica_scorte()

    def carica_scorte(self):
        """Carica e visualizza le scorte nella vista corrente (singoli o categorie)"""
        # Pulisci layout
        while self.scorte_layout.count():
            child = self.scorte_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        vista = getattr(self, '_scorte_vista', 'singoli')
        if vista == 'categorie':
            self._carica_scorte_categorie()
        else:
            self._carica_scorte_singoli()

    def _carica_scorte_singoli(self):
        """Visualizza le scorte dei materiali (aggregate per materiale)"""
        ordina_per = self.combo_ordinamento.currentData() or 'giacenza_asc'
        scorte = self.db_manager.get_scorte(ordina_per)

        if not scorte:
            lbl_vuoto = QLabel("Nessun materiale presente in magazzino.")
            lbl_vuoto.setAlignment(Qt.AlignCenter)
            lbl_vuoto.setStyleSheet("color: #718096; font-size: 16px; padding: 40px;")
            self.scorte_layout.addWidget(lbl_vuoto)
            self.scorte_layout.addStretch()
            return

        for mat in scorte:
            # get_scorte restituisce: id, nome, giacenza_totale, scorta_massima, n_fornitori, prezzo_min
            mat_id, nome, giacenza_totale, scorta_massima, n_fornitori, prezzo_min = mat
            card = self._crea_card_scorta(mat_id, nome, giacenza_totale, scorta_massima, n_fornitori, prezzo_min)
            self.scorte_layout.addWidget(card)

        self.scorte_layout.addStretch()

    def _carica_scorte_categorie(self):
        """Visualizza le scorte aggregate per categoria"""
        ordina_per = self.combo_ordinamento.currentData() or 'giacenza_asc'
        categorie = self.db_manager.get_scorte_per_categoria(ordina_per)

        if not categorie:
            lbl_vuoto = QLabel("Nessuna categoria definita. Aggiungile da Gestione Materiali → Categorie.")
            lbl_vuoto.setAlignment(Qt.AlignCenter)
            lbl_vuoto.setWordWrap(True)
            lbl_vuoto.setStyleSheet("color: #718096; font-size: 16px; padding: 40px;")
            self.scorte_layout.addWidget(lbl_vuoto)
            self.scorte_layout.addStretch()
            return

        for cat in categorie:
            cat_id, nome, giacenza_totale, capacita, giacenza_minima, giacenza_desiderata, num_materiali, note = cat
            card = self._crea_card_categoria(
                cat_id, nome, giacenza_totale or 0.0, capacita or 0.0,
                giacenza_minima or 0.0, giacenza_desiderata or 0.0,
                num_materiali or 0
            )
            self.scorte_layout.addWidget(card)

        self.scorte_layout.addStretch()

    def _crea_card_categoria(self, cat_id, nome, giacenza_totale, capacita,
                              giacenza_minima, giacenza_desiderata, num_materiali):
        """Crea una card per una categoria con barra gradiente e informazioni aggregate"""
        card = QFrame()

        # Determine alert color based on thresholds
        border_color = "#e2e8f0"
        if giacenza_minima > 0 and giacenza_totale < giacenza_minima:
            border_color = "#fc8181"  # red – below minimum
        elif giacenza_desiderata > 0 and giacenza_totale < giacenza_desiderata:
            border_color = "#f6ad55"  # orange – below desired

        card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: #a0aec0;
            }}
        """)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 14, 20, 14)
        card_layout.setSpacing(20)

        # Info categoria
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        lbl_nome = QLabel(nome)
        lbl_nome.setStyleSheet("font-size: 16px; font-weight: 700; color: #2d3748;")

        dettagli = f"Giacenza totale: {giacenza_totale:.2f} m²"
        if capacita > 0:
            dettagli += f" / {capacita:.2f} m²"
        dettagli += f"  |  {num_materiali} materiali"
        if giacenza_minima > 0:
            dettagli += f"  |  Min: {giacenza_minima:.1f} m²"
        if giacenza_desiderata > 0:
            dettagli += f"  |  Desiderata: {giacenza_desiderata:.1f} m²"

        lbl_dettagli = QLabel(dettagli)
        lbl_dettagli.setStyleSheet("font-size: 12px; color: #718096;")

        # Alert label
        if giacenza_minima > 0 and giacenza_totale < giacenza_minima:
            lbl_alert = QLabel("⚠ Scorta sotto il minimo!")
            lbl_alert.setStyleSheet("font-size: 11px; color: #c53030; font-weight: 700;")
            info_layout.addWidget(lbl_alert)
        elif giacenza_desiderata > 0 and giacenza_totale < giacenza_desiderata:
            lbl_alert = QLabel("Scorta sotto il livello desiderato")
            lbl_alert.setStyleSheet("font-size: 11px; color: #c05621; font-weight: 600;")
            info_layout.addWidget(lbl_alert)

        info_layout.addWidget(lbl_nome)
        info_layout.addWidget(lbl_dettagli)

        card_layout.addLayout(info_layout)

        # Barra scorta (basata su capacità se presente, altrimenti su desiderata)
        ref_capacity = capacita if capacita > 0 else giacenza_desiderata
        percentuale = (giacenza_totale / ref_capacity * 100) if ref_capacity > 0 else 0
        barra = BarraScorta(percentuale)
        card_layout.addWidget(barra)

        # Bottone mostra materiali
        btn_dettagli = QPushButton("Materiali")
        btn_dettagli.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc; color: #4a5568;
                border: 1px solid #e2e8f0; min-height: 30px;
                padding: 4px 12px; font-size: 12px;
            }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_dettagli.clicked.connect(
            lambda checked, cid=cat_id, cn=nome: self._mostra_materiali_categoria(cid, cn)
        )
        card_layout.addWidget(btn_dettagli)

        return card

    def _mostra_materiali_categoria(self, categoria_id, nome_categoria):
        """Mostra i materiali di una categoria con giacenza aggregata e barre scorte per fornitore"""
        mats = self.db_manager.get_materiali_per_categoria_con_fornitori(categoria_id)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Materiali – {nome_categoria}")
        dialog.setMinimumSize(760, 480)
        dialog.setStyleSheet("""
            QDialog { background-color: #fafbfc; }
            QLabel { color: #2d3748; font-family: system-ui, -apple-system, sans-serif; }
            QScrollArea { border: none; background: transparent; }
        """)

        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.setContentsMargins(25, 25, 25, 25)
        dlg_layout.setSpacing(12)

        title = QLabel(f"Categoria: {nome_categoria}")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        dlg_layout.addWidget(title)

        if not mats:
            lbl = QLabel("Nessun materiale assegnato a questa categoria.")
            lbl.setStyleSheet("color: #718096;")
            dlg_layout.addWidget(lbl)
        else:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            container = QWidget()
            cont_layout = QVBoxLayout(container)
            cont_layout.setSpacing(8)
            cont_layout.setContentsMargins(0, 0, 0, 0)

            totale = 0.0
            for mat in mats:
                # get_materiali_per_categoria_con_fornitori: id, nome, giacenza_totale, scorta_massima, n_fornitori
                mat_id, nome, giacenza_totale, scorta_massima, n_fornitori = mat
                totale += giacenza_totale

                # Riga materiale (card collassabile)
                mat_frame = QFrame()
                mat_frame.setStyleSheet("""
                    QFrame { background-color: #ffffff; border: 1px solid #e2e8f0;
                             border-radius: 8px; }
                """)
                mat_layout = QVBoxLayout(mat_frame)
                mat_layout.setContentsMargins(16, 10, 16, 10)
                mat_layout.setSpacing(6)

                # Header materiale
                header = QHBoxLayout()
                lbl_mat = QLabel(nome)
                lbl_mat.setStyleSheet("font-size: 14px; font-weight: 700; color: #2d3748;")
                lbl_giac = QLabel(f"Totale: {giacenza_totale:.2f} m²  |  {n_fornitori} fornitore/i")
                lbl_giac.setStyleSheet("font-size: 12px; color: #718096;")
                header.addWidget(lbl_mat)
                header.addWidget(lbl_giac)
                header.addStretch()
                mat_layout.addLayout(header)

                # Barre per-fornitore
                fornitori = self.db_manager.get_fornitori_per_materiale(mat_id)
                for mf in fornitori:
                    mf_id, forn_nome, prezzo_forn, s_min, s_max, giacenza = mf
                    forn_row = QHBoxLayout()
                    forn_row.setSpacing(12)

                    lbl_f = QLabel(forn_nome)
                    lbl_f.setStyleSheet("font-size: 12px; color: #4a5568; font-weight: 600;")
                    lbl_f.setFixedWidth(120)
                    forn_row.addWidget(lbl_f)

                    perc = (giacenza / s_max * 100) if s_max > 0 else 0
                    barra = BarraScorta(perc)
                    barra.setMinimumHeight(20)
                    forn_row.addWidget(barra, 1)

                    lbl_val = QLabel(f"{giacenza:.1f} / {s_max:.1f} m²")
                    lbl_val.setStyleSheet("font-size: 11px; color: #718096;")
                    lbl_val.setFixedWidth(100)
                    forn_row.addWidget(lbl_val)

                    mat_layout.addLayout(forn_row)

                cont_layout.addWidget(mat_frame)

            cont_layout.addStretch()
            scroll.setWidget(container)
            dlg_layout.addWidget(scroll)

            lbl_tot = QLabel(f"Giacenza totale categoria: {totale:.2f} m²")
            lbl_tot.setStyleSheet("font-size: 13px; font-weight: 600; color: #4a5568;")
            dlg_layout.addWidget(lbl_tot)

        btn_close = QPushButton("Chiudi")
        btn_close.setStyleSheet("""
            QPushButton { background-color: #4a5568; color: #ffffff; min-height: 36px; padding: 8px 20px; }
            QPushButton:hover { background-color: #2d3748; }
        """)
        btn_close.clicked.connect(dialog.accept)
        dlg_layout.addWidget(btn_close, alignment=Qt.AlignRight)

        dialog.exec_()

    def _crea_card_scorta(self, mat_id, nome, giacenza_totale, scorta_massima, n_fornitori, prezzo_min):
        """Crea una card per un materiale (giacenza aggregata su tutti i fornitori)"""
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

        dettagli = f"Giacenza totale: {giacenza_totale:.2f} m²"
        if scorta_massima > 0:
            dettagli += f" / {scorta_massima:.2f} m²"
        if n_fornitori > 0:
            dettagli += f"  |  {n_fornitori} fornitore/i"
            if prezzo_min and prezzo_min > 0:
                dettagli += f"  |  da €{prezzo_min:.2f}/m²"

        lbl_dettagli = QLabel(dettagli)
        lbl_dettagli.setStyleSheet("font-size: 12px; color: #718096;")

        info_layout.addWidget(lbl_nome)
        info_layout.addWidget(lbl_dettagli)
        card_layout.addLayout(info_layout)

        # Barra scorta aggregata
        percentuale = (giacenza_totale / scorta_massima * 100) if scorta_massima > 0 else 0
        barra = BarraScorta(percentuale)
        card_layout.addWidget(barra)

        # Bottone fornitori (drill-down) - sempre visibile, disabilitato se <=1 fornitore
        btn_forn = QPushButton("Fornitori")
        if n_fornitori > 1:
            btn_forn.setStyleSheet("""
                QPushButton {
                    background-color: #ebf8ff; color: #2b6cb0;
                    border: 1px solid #bee3f8; min-height: 30px;
                    padding: 4px 12px; font-size: 12px; font-weight: 600;
                }
                QPushButton:hover { background-color: #bee3f8; }
            """)
            btn_forn.clicked.connect(lambda checked, mid=mat_id, mn=nome: self._mostra_fornitori_materiale(mid, mn))
        else:
            btn_forn.setStyleSheet("""
                QPushButton {
                    background-color: #f7fafc; color: #a0aec0;
                    border: 1px solid #e2e8f0; min-height: 30px;
                    padding: 4px 12px; font-size: 12px; font-weight: 600;
                }
            """)
            btn_forn.setEnabled(False)
        card_layout.addWidget(btn_forn)

        # Bottone storico
        btn_storico = QPushButton("Storico")
        btn_storico.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc; color: #4a5568;
                border: 1px solid #e2e8f0; min-height: 30px;
                padding: 4px 12px; font-size: 12px;
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
        """Mostra le scorte dei materiali di un fornitore in un dialog"""
        scorte = self.db_manager.get_scorte_per_fornitore(nome_fornitore)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Scorte - {nome_fornitore}")
        dialog.setMinimumSize(700, 500)
        dialog.setStyleSheet("""
            QDialog { background-color: #fafbfc; }
            QLabel { color: #2d3748; font-family: system-ui, -apple-system, sans-serif; }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(16)

        title = QLabel(f"Materiali forniti da: {nome_fornitore}")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        if not scorte:
            lbl_vuoto = QLabel("Nessun materiale associato a questo fornitore.\nAssegna il fornitore ai materiali da 'Gestione Materiali'.")
            lbl_vuoto.setStyleSheet("color: #718096; font-size: 14px; padding: 20px;")
            lbl_vuoto.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl_vuoto)
        else:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; }")

            container = QWidget()
            cont_layout = QVBoxLayout(container)
            cont_layout.setContentsMargins(0, 0, 0, 0)
            cont_layout.setSpacing(8)

            for mat_id, nome, giacenza, capacita, fornitore, prezzo_fornitore in scorte:
                card = self._crea_card_scorta(mat_id, nome, giacenza, capacita, fornitore, prezzo_fornitore)
                cont_layout.addWidget(card)

            cont_layout.addStretch()
            scroll.setWidget(container)
            layout.addWidget(scroll)

        btn_chiudi = QPushButton("Chiudi")
        btn_chiudi.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; min-height: 36px; min-width: 120px; }
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
