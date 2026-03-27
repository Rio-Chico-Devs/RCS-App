"""
GestioneMaterialiWindow - Interfaccia per gestire i materiali con design system unificato

Version: 3.0.0
Last Updated: 2026-03-12
"""

from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
                             QWidget, QLabel, QListWidget, QMessageBox, QListWidgetItem,
                             QGroupBox, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
                             QLineEdit, QDoubleSpinBox, QFormLayout, QDialog, QGridLayout,
                             QComboBox, QTabWidget, QTextEdit, QAbstractItemView,
                             QCheckBox, QScrollArea, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractScrollArea, QStackedWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen
from ui.materiale_ui_components import NoScrollDoubleSpinBox


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_shadow(blur=10, opacity=12):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setColor(QColor(0, 0, 0, opacity))
    shadow.setOffset(0, 2)
    return shadow


def _std_label(text):
    lbl = QLabel(text)
    lbl.setStyleSheet("QLabel { color: #4a5568; font-size: 14px; font-weight: 500; }")
    return lbl


_BASE_STYLE = """
    QMainWindow { background-color: #fafbfc; }
    QTabWidget::pane { border: none; background: transparent; }
    QTabBar::tab {
        background: #edf2f7; color: #4a5568;
        border-radius: 6px 6px 0 0; padding: 10px 20px;
        font-size: 14px; font-weight: 600;
        margin-right: 4px; min-width: 140px;
    }
    QTabBar::tab:selected { background: #ffffff; color: #2d3748; }
    QLabel { color: #2d3748; font-family: system-ui, -apple-system, sans-serif;
             font-size: 14px; font-weight: 500; }
    QGroupBox { font-size: 16px; font-weight: 600; color: #4a5568;
                border: none; background-color: #ffffff;
                border-radius: 12px; margin-top: 16px; padding-top: 16px; }
    QGroupBox::title { subcontrol-origin: margin; left: 20px;
                       padding: 6px 0px; background-color: transparent; color: #4a5568; }
    QListWidget { background-color: #ffffff; border: 1px solid #e2e8f0;
                  border-radius: 8px; font-size: 14px; padding: 8px;
                  font-family: system-ui, -apple-system, sans-serif; }
    QListWidget::item { border-radius: 6px; padding: 12px; margin: 2px 0px;
                        border-bottom: 1px solid #f7fafc; color: #2d3748; }
    QListWidget::item:hover { background-color: #f7fafc; }
    QListWidget::item:selected { background-color: #edf2f7; color: #2d3748; }
    QLineEdit, QDoubleSpinBox, QComboBox, QTextEdit {
        border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 14px;
        font-size: 14px; background-color: #ffffff; color: #2d3748;
        min-height: 18px; font-family: system-ui, -apple-system, sans-serif; }
    QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {
        border-color: #718096; }
    QLineEdit:hover, QDoubleSpinBox:hover, QComboBox:hover, QTextEdit:hover {
        border-color: #a0aec0; }
    QPushButton { border: none; border-radius: 6px; font-size: 14px;
                  font-weight: 600; padding: 12px 24px;
                  font-family: system-ui, -apple-system, sans-serif; }
    QCheckBox { font-size: 13px; color: #4a5568; font-weight: 500; }
    QTableWidget { background-color: #ffffff; border: 1px solid #e2e8f0;
                   border-radius: 8px; font-size: 13px; gridline-color: #f0f0f0; }
    QTableWidget::item { padding: 8px; color: #2d3748; }
    QTableWidget::item:selected { background-color: #edf2f7; color: #2d3748; }
    QHeaderView::section { background-color: #f7fafc; color: #4a5568;
                           font-size: 13px; font-weight: 600; padding: 8px;
                           border: none; border-bottom: 1px solid #e2e8f0; }
"""


# ---------------------------------------------------------------------------
# Stock Bar Widget
# ---------------------------------------------------------------------------

class StockBarWidget(QWidget):
    """
    Barra delle scorte con tre zone colorate:
      - Rosso:   0 → scorta_minima
      - Giallo:  scorta_minima → metà della zona rimanente
      - Verde:   metà della zona rimanente → scorta_massima
    Il livello attuale (giacenza) è indicato da una lineetta verticale nera.
    """

    def __init__(self, scorta_minima=0.0, scorta_massima=100.0, giacenza=0.0, parent=None):
        super().__init__(parent)
        self.scorta_minima = max(scorta_minima, 0.0)
        self.scorta_massima = max(scorta_massima, 0.01)
        self.giacenza = max(giacenza, 0.0)
        self.setMinimumHeight(22)
        self.setMinimumWidth(80)

    def update_values(self, scorta_minima, scorta_massima, giacenza):
        self.scorta_minima = max(scorta_minima, 0.0)
        self.scorta_massima = max(scorta_massima, 0.01)
        self.giacenza = max(giacenza, 0.0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        r = 4  # border radius

        smin = self.scorta_minima
        smax = self.scorta_massima
        smid = smin + (smax - smin) / 2.0

        def x_of(val):
            return int((min(val, smax) / smax) * w)

        x_min = x_of(smin)
        x_mid = x_of(smid)
        x_max = w

        # Background (grigio chiaro)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#e2e8f0")))
        painter.drawRoundedRect(0, 0, w, h, r, r)

        # Zona rossa: 0 → scorta_minima
        if x_min > 0:
            painter.setBrush(QBrush(QColor("#fc8181")))
            painter.drawRoundedRect(0, 0, x_min, h, r, r)
            # sovrascrive angoli destri per unirsi alla zona gialla
            if x_mid > x_min:
                painter.drawRect(max(0, x_min - r), 0, r, h)

        # Zona gialla: scorta_minima → metà
        if x_mid > x_min:
            painter.setBrush(QBrush(QColor("#f6e05e")))
            painter.drawRect(x_min, 0, x_mid - x_min, h)

        # Zona verde: metà → massima
        if x_max > x_mid:
            painter.setBrush(QBrush(QColor("#68d391")))
            painter.drawRoundedRect(x_mid, 0, x_max - x_mid, h, r, r)
            painter.drawRect(x_mid, 0, r, h)  # angolo sinistro piatto

        # Indicatore giacenza attuale (linea verticale nera)
        if self.giacenza > 0:
            x_giac = min(x_of(self.giacenza), w - 2)
            painter.setPen(QPen(QColor("#1a202c"), 2))
            painter.drawLine(x_giac, 2, x_giac, h - 2)

        # Bordo esterno
        painter.setPen(QPen(QColor("#cbd5e0"), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(0, 0, w - 1, h - 1, r, r)

        painter.end()


# ===========================================================================
# GestioneMaterialiWindow
# ===========================================================================

class GestioneMaterialiWindow(QMainWindow):
    materiali_modificati = pyqtSignal()

    def __init__(self, db_manager, parent=None):
        super().__init__(None)
        self.db_manager = db_manager
        self.init_ui()
        self.carica_materiali()
        self.showMaximized()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def init_ui(self):
        self.setWindowTitle("Gestione Materiali - Software Aziendale RCS")
        self.setStyleSheet(_BASE_STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(30, 15, 30, 15)
        main_layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Gestione Materiali")
        title.setStyleSheet("QLabel { font-size: 24px; font-weight: 700; color: #2d3748; }")
        subtitle = QLabel("Modifica materiali")
        subtitle.setStyleSheet("QLabel { font-size: 14px; font-weight: 400; color: #718096; }")
        header_layout.addWidget(title)
        header_layout.addSpacing(20)
        header_layout.addWidget(subtitle)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)

        self.tab_materiali = QWidget()
        self._build_tab_materiali(self.tab_materiali)
        self.tab_widget.addTab(self.tab_materiali, "Singoli Materiali")

        main_layout.addWidget(self.tab_widget, 1)

        # Footer
        footer = QHBoxLayout()
        footer.addStretch()
        btn_chiudi = QPushButton("Chiudi Gestione Materiali")
        btn_chiudi.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568;
                          border: 1px solid #e2e8f0; min-height: 40px; min-width: 200px; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_chiudi.clicked.connect(self.close)
        footer.addWidget(btn_chiudi)
        main_layout.addLayout(footer)

    # ------------------------------------------------------------------
    # Tab: Singoli Materiali
    # ------------------------------------------------------------------

    def _build_tab_materiali(self, parent):
        layout = QVBoxLayout(parent)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 12, 0, 0)

        self.stack_materiali = QStackedWidget()
        layout.addWidget(self.stack_materiali)

        # Pagina 0: lista materiali (fullscreen)
        page_list = QWidget()
        self._build_page_list(page_list)
        self.stack_materiali.addWidget(page_list)

        # Pagina 1: dettaglio materiale
        page_detail = QWidget()
        self._build_page_detail(page_detail)
        self.stack_materiali.addWidget(page_detail)

        self.abilita_form(False)
        self.abilita_pulsanti_form(False)

    def _build_page_list(self, parent):
        """Pagina 0: lista materiali a tutto schermo con solo ricerca"""
        layout = QVBoxLayout(parent)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        lista_group = QGroupBox("Materiali Disponibili")
        lista_group.setGraphicsEffect(_make_shadow())
        lista_inner = QVBoxLayout(lista_group)
        lista_inner.setContentsMargins(20, 28, 20, 15)
        lista_inner.setSpacing(10)

        # Barra ricerca
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Cerca:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Inserisci nome materiale...")
        self.search_edit.textChanged.connect(self._applica_filtri)
        search_row.addWidget(self.search_edit)
        lista_inner.addLayout(search_row)

        self.lista_materiali = QListWidget()
        self.lista_materiali.itemSelectionChanged.connect(self.on_materiale_selezionato)
        lista_inner.addWidget(self.lista_materiali, 1)

        self.lbl_conteggio = QLabel("0 materiali caricati")
        self.lbl_conteggio.setStyleSheet("QLabel { color: #718096; font-size: 13px; font-weight: 500; }")
        lista_inner.addWidget(self.lbl_conteggio)

        list_btns = QHBoxLayout()
        self.btn_nuovo_materiale = QPushButton("Nuovo Materiale")
        self.btn_nuovo_materiale.setStyleSheet("""
            QPushButton { background-color: #4a5568; color: #ffffff; min-height: 36px; }
            QPushButton:hover { background-color: #2d3748; }
        """)
        self.btn_nuovo_materiale.clicked.connect(self.nuovo_materiale)

        btn_aggiorna = QPushButton("Aggiorna Lista")
        btn_aggiorna.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568;
                          border: 1px solid #e2e8f0; min-height: 36px; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_aggiorna.clicked.connect(self.carica_materiali)

        list_btns.addWidget(self.btn_nuovo_materiale)
        list_btns.addWidget(btn_aggiorna)
        list_btns.addStretch()
        lista_inner.addLayout(list_btns)

        layout.addWidget(lista_group, 1)

    def _build_page_detail(self, parent):
        """Pagina 1: dettaglio materiale con form + scorte aggregate + fornitori"""
        layout = QVBoxLayout(parent)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)

        # Pulsante Indietro
        back_row = QHBoxLayout()
        btn_back = QPushButton("◀  Torna alla lista")
        btn_back.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568;
                          border: 1px solid #e2e8f0; min-height: 36px; padding: 6px 18px; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_back.clicked.connect(self._torna_alla_lista)
        back_row.addWidget(btn_back)
        back_row.addStretch()
        layout.addLayout(back_row)

        # Layout a due colonne 50/50: sinistra = form, destra = fornitori
        columns = QHBoxLayout()
        columns.setSpacing(20)
        columns.setContentsMargins(0, 0, 0, 0)

        # ── Colonna sinistra: form dettagli ──────────────────────────
        form_group = QGroupBox("Dettagli Materiale")
        form_group.setGraphicsEffect(_make_shadow())
        form_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        form_inner = QVBoxLayout(form_group)
        form_inner.setContentsMargins(20, 28, 20, 15)
        form_inner.setSpacing(10)

        self.info_container = QFrame()
        self.info_container.setStyleSheet("""
            QFrame { background-color: #f0fff4; border: 1px solid #68d391;
                     border-radius: 8px; padding: 8px; margin: 0px; }
        """)
        info_inner = QVBoxLayout(self.info_container)
        info_inner.setSpacing(4)
        self.lbl_selezione = QLabel("Seleziona un materiale per modificarlo")
        self.lbl_selezione.setStyleSheet("QLabel { color: #2d3748; font-size: 14px; font-weight: 600; }")
        self.lbl_info_materiale = QLabel("")
        self.lbl_info_materiale.setStyleSheet("QLabel { color: #4a5568; font-size: 13px; font-weight: 500; }")
        info_inner.addWidget(self.lbl_selezione)
        info_inner.addWidget(self.lbl_info_materiale)
        form_inner.addWidget(self.info_container)

        form_fields = QFormLayout()
        form_fields.setVerticalSpacing(8)
        form_fields.setHorizontalSpacing(12)

        self.edit_nome = QLineEdit()
        self.edit_nome.setPlaceholderText("es. HS300")

        self.edit_spessore = NoScrollDoubleSpinBox()
        self.edit_spessore.setDecimals(2)
        self.edit_spessore.setMaximum(999.99)
        self.edit_spessore.setSuffix(" mm")
        self.edit_spessore.setMinimumHeight(36)

        self.edit_prezzo = NoScrollDoubleSpinBox()
        self.edit_prezzo.setDecimals(2)
        self.edit_prezzo.setMaximum(9999.99)
        self.edit_prezzo.setSuffix(" €")
        self.edit_prezzo.setMinimumHeight(36)

        self.edit_scorta_min_mat = NoScrollDoubleSpinBox()
        self.edit_scorta_min_mat.setDecimals(2)
        self.edit_scorta_min_mat.setMaximum(99999.99)
        self.edit_scorta_min_mat.setSuffix(" m²")
        self.edit_scorta_min_mat.setMinimumHeight(36)
        self.edit_scorta_min_mat.setToolTip("Scorta minima aggregata del materiale (indipendente dai fornitori)")

        self.edit_scorta_max_mat = NoScrollDoubleSpinBox()
        self.edit_scorta_max_mat.setDecimals(2)
        self.edit_scorta_max_mat.setMaximum(99999.99)
        self.edit_scorta_max_mat.setSuffix(" m²")
        self.edit_scorta_max_mat.setMinimumHeight(36)
        self.edit_scorta_max_mat.setToolTip("Scorta massima aggregata del materiale (indipendente dai fornitori)")

        form_fields.addRow(_std_label("Nome Materiale:"), self.edit_nome)
        form_fields.addRow(_std_label("Spessore:"), self.edit_spessore)
        form_fields.addRow(_std_label("Prezzo (Preventivo):"), self.edit_prezzo)
        form_fields.addRow(_std_label("Scorta Min (aggregata):"), self.edit_scorta_min_mat)
        form_fields.addRow(_std_label("Scorta Max (aggregata):"), self.edit_scorta_max_mat)

        form_inner.addLayout(form_fields)

        form_btns = QHBoxLayout()
        form_btns.setSpacing(12)

        self.btn_salva = QPushButton("Salva Materiale")
        self.btn_salva.setStyleSheet("""
            QPushButton { background-color: #4a5568; color: #ffffff; min-height: 32px; }
            QPushButton:hover { background-color: #2d3748; }
            QPushButton:disabled { background-color: #a0aec0; color: #ffffff; }
        """)
        self.btn_salva.clicked.connect(self.salva_materiale)

        self.btn_elimina = QPushButton("Elimina Materiale")
        self.btn_elimina.setStyleSheet("""
            QPushButton { background-color: #e53e3e; color: #ffffff; min-height: 32px; }
            QPushButton:hover { background-color: #c53030; }
            QPushButton:disabled { background-color: #a0aec0; color: #ffffff; }
        """)
        self.btn_elimina.clicked.connect(self.elimina_materiale)

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568;
                          border: 1px solid #e2e8f0; min-height: 32px; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        self.btn_reset.clicked.connect(self.reset_form)

        form_btns.addWidget(self.btn_salva)
        form_btns.addWidget(self.btn_elimina)
        form_btns.addStretch()
        form_btns.addWidget(self.btn_reset)
        form_inner.addLayout(form_btns)
        form_inner.addStretch()

        columns.addWidget(form_group, 1)

        # ── Colonna destra: fornitori ─────────────────────────────────
        self.fornitori_group = QGroupBox("Fornitori del Materiale")
        self.fornitori_group.setGraphicsEffect(_make_shadow())
        self.fornitori_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        forn_inner = QVBoxLayout(self.fornitori_group)
        forn_inner.setContentsMargins(20, 28, 20, 15)
        forn_inner.setSpacing(10)

        self.tabella_fornitori_mat = QTableWidget()
        self.tabella_fornitori_mat.setColumnCount(6)
        self.tabella_fornitori_mat.setHorizontalHeaderLabels(
            ["Fornitore", "€/m²", "Scorta Min (m²)", "Scorta Max (m²)", "Giacenza (m²)", ""]
        )
        self.tabella_fornitori_mat.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabella_fornitori_mat.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabella_fornitori_mat.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabella_fornitori_mat.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabella_fornitori_mat.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tabella_fornitori_mat.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.tabella_fornitori_mat.setColumnWidth(5, 200)
        self.tabella_fornitori_mat.verticalHeader().setVisible(False)
        self.tabella_fornitori_mat.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabella_fornitori_mat.setSelectionBehavior(QTableWidget.SelectRows)
        forn_inner.addWidget(self.tabella_fornitori_mat, 1)

        btn_aggiungi_forn = QPushButton("+ Aggiungi Fornitore")
        btn_aggiungi_forn.setStyleSheet("""
            QPushButton { background-color: #38a169; color: #ffffff; min-height: 34px; padding: 6px 16px; }
            QPushButton:hover { background-color: #2f855a; }
        """)
        btn_aggiungi_forn.clicked.connect(self._aggiungi_fornitore_materiale)
        forn_inner.addWidget(btn_aggiungi_forn, alignment=Qt.AlignLeft)

        columns.addWidget(self.fornitori_group, 1)

        layout.addLayout(columns, 1)

    # ==================================================================
    # Materiali – logic
    # ==================================================================

    def carica_materiali(self):
        self.lista_materiali.clear()
        self.materiali_data = self.db_manager.get_all_materiali()
        forn_counts = self.db_manager.get_fornitori_counts()

        for mat in self.materiali_data:
            id_mat, nome, spessore, prezzo = mat[:4]
            n_forn = forn_counts.get(id_mat, 0)
            testo = f"{nome} | {spessore}mm | €{prezzo:.2f} | {n_forn} fornitore/i"

            item = QListWidgetItem(testo)
            item.setData(Qt.UserRole, mat)
            self.lista_materiali.addItem(item)

        self.lbl_conteggio.setText(f"{self.lista_materiali.count()} materiali caricati")
        self._applica_filtri()

    def _applica_filtri(self):
        """Applica filtro di ricerca per nome."""
        search_text = self.search_edit.text().lower()
        for i in range(self.lista_materiali.count()):
            item = self.lista_materiali.item(i)
            mat = item.data(Qt.UserRole)
            nome = mat[1].lower()
            item.setHidden(search_text not in nome)

    def on_materiale_selezionato(self):
        current_item = self.lista_materiali.currentItem()
        if not current_item:
            return

        mat = current_item.data(Qt.UserRole)
        self.materiale_corrente = mat
        id_mat, nome, spessore, prezzo = mat[:4]
        scorta_min = mat[8] if len(mat) > 8 else 0.0
        scorta_max = mat[9] if len(mat) > 9 else 0.0

        fornitori = self.db_manager.get_fornitori_per_materiale(id_mat)
        n_forn = len(fornitori)
        self.lbl_selezione.setText(f"Materiale selezionato: {nome}")
        self.lbl_info_materiale.setText(f"ID: {id_mat}  •  {n_forn} fornitore/i")

        self.edit_nome.setText(nome)
        self.edit_spessore.setValue(spessore)
        self.edit_prezzo.setValue(prezzo)
        self.edit_scorta_min_mat.setValue(scorta_min)
        self.edit_scorta_max_mat.setValue(scorta_max)

        self.abilita_form(True)
        self.abilita_pulsanti_form(True)
        self._carica_tabella_fornitori(id_mat)

        # Naviga alla pagina dettaglio
        self.stack_materiali.setCurrentIndex(1)

    def _torna_alla_lista(self):
        """Torna alla pagina lista e deseleziona il materiale."""
        self.lista_materiali.clearSelection()
        self.stack_materiali.setCurrentIndex(0)

    def _carica_tabella_fornitori(self, materiale_id):
        """Ricarica la tabella dei fornitori per il materiale selezionato"""
        fornitori = self.db_manager.get_fornitori_per_materiale(materiale_id)
        self.tabella_fornitori_mat.setRowCount(len(fornitori))

        for row, mf in enumerate(fornitori):
            mf_id, forn_nome, prezzo_forn, s_min, s_max, giacenza = mf
            self.tabella_fornitori_mat.setItem(row, 0, QTableWidgetItem(forn_nome))
            self.tabella_fornitori_mat.setItem(row, 1, QTableWidgetItem(f"€ {prezzo_forn:.2f}"))
            self.tabella_fornitori_mat.setItem(row, 2, QTableWidgetItem(f"{s_min:.2f}"))
            self.tabella_fornitori_mat.setItem(row, 3, QTableWidgetItem(f"{s_max:.2f}"))
            self.tabella_fornitori_mat.setItem(row, 4, QTableWidgetItem(f"{giacenza:.2f}"))
            for col in range(5):
                item = self.tabella_fornitori_mat.item(row, col)
                if item:
                    item.setData(Qt.UserRole, mf_id)

            # Pulsanti azioni
            btn_frame = QFrame()
            btn_layout_row = QHBoxLayout(btn_frame)
            btn_layout_row.setContentsMargins(4, 2, 4, 2)
            btn_layout_row.setSpacing(6)

            btn_mod = QPushButton("Modifica")
            btn_mod.setFixedSize(86, 32)
            btn_mod.setStyleSheet("""
                QPushButton { background-color: #edf2f7; color: #2d3748; border: none;
                              border-radius: 4px; padding: 2px 4px; font-size: 12px; font-weight: 600; }
                QPushButton:hover { background-color: #e2e8f0; }
            """)
            btn_mod.clicked.connect(lambda checked, mid=mf_id, mn=forn_nome,
                                    pf=prezzo_forn, sm=s_min, sx=s_max:
                                    self._modifica_fornitore_materiale(mid, mn, pf, sm, sx))

            btn_del = QPushButton("Elimina")
            btn_del.setFixedSize(78, 32)
            btn_del.setStyleSheet("""
                QPushButton { background-color: #fff5f5; color: #c53030; border: 1px solid #fed7d7;
                              border-radius: 4px; padding: 2px 4px; font-size: 12px; font-weight: 600; }
                QPushButton:hover { background-color: #fed7d7; }
            """)
            btn_del.clicked.connect(lambda checked, mid=mf_id, mn=forn_nome:
                                    self._elimina_fornitore_materiale(mid, mn))

            btn_layout_row.addWidget(btn_mod)
            btn_layout_row.addWidget(btn_del)
            self.tabella_fornitori_mat.setCellWidget(row, 5, btn_frame)
            self.tabella_fornitori_mat.setRowHeight(row, 44)

    def _aggiungi_fornitore_materiale(self):
        if not hasattr(self, 'materiale_corrente'):
            return
        mat_id = self.materiale_corrente[0]
        mat_nome = self.materiale_corrente[1]
        dialog = FornitoreDialog(self.db_manager, mat_nome, None, self)
        if dialog.exec_() == QDialog.Accepted:
            d = dialog.get_data()
            res = self.db_manager.add_fornitore_a_materiale(
                mat_id, d['fornitore_nome'], d['prezzo_fornitore'], d['scorta_minima'], d['scorta_massima']
            )
            if res:
                self._carica_tabella_fornitori(mat_id)
                self.lbl_info_materiale.setText(
                    f"ID: {mat_id}  •  {len(self.db_manager.get_fornitori_per_materiale(mat_id))} fornitore/i"
                )
            else:
                QMessageBox.warning(self, "Attenzione", "Fornitore già presente per questo materiale.")

    def _modifica_fornitore_materiale(self, mf_id, forn_nome, prezzo_forn, s_min, s_max):
        if not hasattr(self, 'materiale_corrente'):
            return
        mat_id = self.materiale_corrente[0]
        mat_nome = self.materiale_corrente[1]
        dati_correnti = {'fornitore_nome': forn_nome, 'prezzo_fornitore': prezzo_forn,
                         'scorta_minima': s_min, 'scorta_massima': s_max}
        dialog = FornitoreDialog(self.db_manager, mat_nome, dati_correnti, self)
        if dialog.exec_() == QDialog.Accepted:
            d = dialog.get_data()
            res = self.db_manager.update_fornitore_materiale(
                mf_id, d['fornitore_nome'], d['prezzo_fornitore'], d['scorta_minima'], d['scorta_massima']
            )
            if res:
                self._carica_tabella_fornitori(mat_id)
            else:
                QMessageBox.warning(self, "Attenzione", "Errore durante la modifica.")

    def _elimina_fornitore_materiale(self, mf_id, forn_nome):
        if not hasattr(self, 'materiale_corrente'):
            return
        mat_id = self.materiale_corrente[0]
        risposta = QMessageBox.question(
            self, "Elimina Fornitore",
            f"Rimuovere il fornitore '{forn_nome}' da questo materiale?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if risposta == QMessageBox.Yes:
            self.db_manager.delete_fornitore_materiale(mf_id)
            self._carica_tabella_fornitori(mat_id)

    def abilita_form(self, enabled):
        for w in [self.edit_nome, self.edit_spessore, self.edit_prezzo,
                  self.edit_scorta_min_mat, self.edit_scorta_max_mat]:
            w.setEnabled(enabled)

    def abilita_pulsanti_form(self, enabled):
        self.btn_salva.setEnabled(enabled)
        self.btn_elimina.setEnabled(enabled)

    def reset_form(self):
        if hasattr(self, 'materiale_corrente'):
            self.on_materiale_selezionato()
        else:
            self.edit_nome.clear()
            self.edit_spessore.setValue(0.0)
            self.edit_prezzo.setValue(0.0)
            self.edit_scorta_min_mat.setValue(0.0)
            self.edit_scorta_max_mat.setValue(0.0)

    def nuovo_materiale(self):
        dialog = NuovoMaterialeDialog(self.db_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            self.carica_materiali()
            QMessageBox.information(self, "Successo", "Nuovo materiale aggiunto con successo!")

    def salva_materiale(self):
        if not hasattr(self, 'materiale_corrente'):
            return

        nome = self.edit_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Attenzione", "Il nome del materiale non può essere vuoto.")
            return
        if len(nome) > 100:
            QMessageBox.warning(self, "Attenzione", "Il nome del materiale non può superare 100 caratteri.")
            return
        spessore = self.edit_spessore.value()
        prezzo = self.edit_prezzo.value()
        if spessore <= 0:
            QMessageBox.warning(self, "Attenzione", "Lo spessore deve essere maggiore di zero.")
            return
        if prezzo < 0:
            QMessageBox.warning(self, "Attenzione", "Il prezzo non può essere negativo.")
            return

        try:
            scorta_min = self.edit_scorta_min_mat.value()
            scorta_max = self.edit_scorta_max_mat.value()
            success = self.db_manager.update_materiale_base(
                self.materiale_corrente[0], nome, spessore, prezzo
            )
            if success:
                self.db_manager.update_materiale_scorte(self.materiale_corrente[0], scorta_min, scorta_max)
                self.carica_materiali()
                self.materiali_modificati.emit()
            else:
                QMessageBox.critical(self, "Errore", "Nome materiale già esistente o errore nel database.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio:\n{str(e)}")

    def elimina_materiale(self):
        if not hasattr(self, 'materiale_corrente'):
            return

        nome_materiale = self.materiale_corrente[1]
        risposta = QMessageBox.question(
            self, "Conferma Eliminazione",
            f"Eliminare definitivamente il materiale '{nome_materiale}'?\n\nQuesta azione non può essere annullata.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if risposta == QMessageBox.Yes:
            try:
                success = self.db_manager.delete_materiale(self.materiale_corrente[0])
                if success:
                    QMessageBox.information(self, "Successo", f"Materiale '{nome_materiale}' eliminato!")
                    del self.materiale_corrente
                    self.carica_materiali()
                    self.reset_form()
                    self.abilita_form(False)
                    self.abilita_pulsanti_form(False)
                    self.materiali_modificati.emit()
                    self.stack_materiali.setCurrentIndex(0)
                else:
                    QMessageBox.critical(self, "Errore", "Errore durante l'eliminazione del materiale.")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore durante l'eliminazione:\n{str(e)}")



# ===========================================================================
# Dialogs
# ===========================================================================

_DIALOG_STYLE = """
    QDialog { background-color: #fafbfc; font-family: system-ui, -apple-system, sans-serif; }
    QLabel { color: #2d3748; font-size: 14px; font-weight: 500; }
    QLineEdit, QDoubleSpinBox, QComboBox, QTextEdit {
        border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 14px;
        font-size: 14px; background-color: #ffffff; color: #2d3748; min-height: 18px; }
    QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {
        border-color: #718096; }
    QPushButton { border: none; border-radius: 6px; font-size: 14px;
                  font-weight: 600; padding: 12px 24px; min-height: 36px; }
"""


class NuovoMaterialeDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Nuovo Materiale")
        self.setFixedSize(420, 320)
        self.setStyleSheet(_DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(20)

        title = QLabel("Aggiungi Nuovo Materiale")
        title.setStyleSheet("QLabel { font-size: 18px; font-weight: 700; color: #2d3748; padding-bottom: 10px; }")
        layout.addWidget(title)

        lbl_info = QLabel("I fornitori si aggiungono dopo la creazione, dalla sezione 'Fornitori del Materiale'.")
        lbl_info.setStyleSheet("QLabel { color: #718096; font-size: 12px; }")
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)

        form = QFormLayout()
        form.setVerticalSpacing(16)

        self.edit_nome = QLineEdit()
        self.edit_nome.setPlaceholderText("es. HS400")

        self.edit_spessore = NoScrollDoubleSpinBox()
        self.edit_spessore.setDecimals(2)
        self.edit_spessore.setMaximum(999.99)
        self.edit_spessore.setSuffix(" mm")

        self.edit_prezzo = NoScrollDoubleSpinBox()
        self.edit_prezzo.setDecimals(2)
        self.edit_prezzo.setMaximum(9999.99)
        self.edit_prezzo.setSuffix(" €")

        form.addRow("Nome Materiale:", self.edit_nome)
        form.addRow("Spessore:", self.edit_spessore)
        form.addRow("Prezzo (Preventivo):", self.edit_prezzo)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.setSpacing(12)

        btn_annulla = QPushButton("Annulla")
        btn_annulla.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_annulla.clicked.connect(self.reject)

        btn_salva = QPushButton("Crea Materiale")
        btn_salva.setStyleSheet("""
            QPushButton { background-color: #4a5568; color: #ffffff; }
            QPushButton:hover { background-color: #2d3748; }
        """)
        btn_salva.clicked.connect(self.salva_nuovo_materiale)

        btns.addWidget(btn_annulla)
        btns.addWidget(btn_salva)
        layout.addLayout(btns)

    def salva_nuovo_materiale(self):
        nome = self.edit_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Attenzione", "Il nome del materiale non può essere vuoto.")
            return
        if len(nome) > 100:
            QMessageBox.warning(self, "Attenzione", "Il nome del materiale non può superare 100 caratteri.")
            return
        spessore = self.edit_spessore.value()
        prezzo = self.edit_prezzo.value()
        if spessore <= 0:
            QMessageBox.warning(self, "Attenzione", "Lo spessore deve essere maggiore di zero.")
            return
        if prezzo < 0:
            QMessageBox.warning(self, "Attenzione", "Il prezzo non può essere negativo.")
            return

        try:
            mat_id = self.db_manager.add_materiale(
                nome, spessore, prezzo, "", 0.0, 0.0, 0.0
            )
            if mat_id:
                self.accept()
            else:
                QMessageBox.critical(self, "Errore", "Nome materiale già esistente.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio:\n{str(e)}")


class FornitoreDialog(QDialog):
    """Dialog per aggiungere/modificare un fornitore per un materiale"""

    def __init__(self, db_manager, nome_materiale, dati_correnti=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.dati_correnti = dati_correnti  # None = nuovo, dict = modifica
        self.setWindowTitle(f"{'Modifica' if dati_correnti else 'Aggiungi'} Fornitore – {nome_materiale}")
        self.setFixedSize(420, 360)
        self.setStyleSheet(_DIALOG_STYLE)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(20)

        modifica = self.dati_correnti is not None
        title = QLabel("Modifica Fornitore" if modifica else "Aggiungi Fornitore")
        title.setStyleSheet("QLabel { font-size: 18px; font-weight: 700; color: #2d3748; }")
        layout.addWidget(title)

        form = QFormLayout()
        form.setVerticalSpacing(14)

        # Combo fornitore dalla lista registrata
        self.combo_fornitore = QComboBox()
        fornitori = self.db_manager.get_all_fornitori()
        for fid, fnome in fornitori:
            self.combo_fornitore.addItem(fnome, fnome)
        # Se modifica, preseleziona il fornitore attuale
        if modifica and self.dati_correnti.get('fornitore_nome'):
            idx = self.combo_fornitore.findData(self.dati_correnti['fornitore_nome'])
            if idx >= 0:
                self.combo_fornitore.setCurrentIndex(idx)

        self.edit_prezzo = NoScrollDoubleSpinBox()
        self.edit_prezzo.setDecimals(2)
        self.edit_prezzo.setMaximum(9999.99)
        self.edit_prezzo.setSuffix(" €/m²")
        if modifica:
            self.edit_prezzo.setValue(self.dati_correnti.get('prezzo_fornitore', 0.0))

        self.edit_scorta_minima = NoScrollDoubleSpinBox()
        self.edit_scorta_minima.setDecimals(2)
        self.edit_scorta_minima.setMaximum(99999.99)
        self.edit_scorta_minima.setSuffix(" m²")
        self.edit_scorta_minima.setToolTip("Soglia minima: la barra diventa rossa sotto questo valore")
        if modifica:
            self.edit_scorta_minima.setValue(self.dati_correnti.get('scorta_minima', 0.0))

        self.edit_scorta_massima = NoScrollDoubleSpinBox()
        self.edit_scorta_massima.setDecimals(2)
        self.edit_scorta_massima.setMaximum(99999.99)
        self.edit_scorta_massima.setSuffix(" m²")
        if modifica:
            self.edit_scorta_massima.setValue(self.dati_correnti.get('scorta_massima', 0.0))

        form.addRow("Fornitore:", self.combo_fornitore)
        form.addRow("Prezzo Fornitore:", self.edit_prezzo)
        form.addRow("Scorta Minima:", self.edit_scorta_minima)
        form.addRow("Scorta Massima:", self.edit_scorta_massima)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.setSpacing(12)
        btn_annulla = QPushButton("Annulla")
        btn_annulla.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_annulla.clicked.connect(self.reject)

        btn_salva = QPushButton("Salva")
        btn_salva.setStyleSheet("""
            QPushButton { background-color: #4a5568; color: #ffffff; }
            QPushButton:hover { background-color: #2d3748; }
        """)
        btn_salva.clicked.connect(self._salva)

        btns.addWidget(btn_annulla)
        btns.addWidget(btn_salva)
        layout.addLayout(btns)

    def _salva(self):
        forn_nome = self.combo_fornitore.currentData()
        if not forn_nome:
            QMessageBox.warning(self, "Attenzione", "Seleziona un fornitore.")
            return
        self.accept()

    def get_data(self):
        return {
            'fornitore_nome': self.combo_fornitore.currentData(),
            'prezzo_fornitore': self.edit_prezzo.value(),
            'scorta_minima': self.edit_scorta_minima.value(),
            'scorta_massima': self.edit_scorta_massima.value(),
        }


