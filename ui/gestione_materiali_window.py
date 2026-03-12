"""
GestioneMaterialiWindow - Interfaccia per gestire i materiali con design system unificato

Version: 2.0.0
Last Updated: 2026-03-11
"""

from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
                             QWidget, QLabel, QListWidget, QMessageBox, QListWidgetItem,
                             QGroupBox, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
                             QLineEdit, QDoubleSpinBox, QFormLayout, QDialog, QGridLayout,
                             QComboBox, QTabWidget, QTextEdit, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
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
        border-radius: 6px 6px 0 0; padding: 10px 28px;
        font-size: 14px; font-weight: 600;
        margin-right: 4px;
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
"""


# ===========================================================================
# GestioneMaterialiWindow
# ===========================================================================

class GestioneMaterialiWindow(QMainWindow):
    materiali_modificati = pyqtSignal()

    def __init__(self, db_manager, parent=None):
        super().__init__(None)
        self.db_manager = db_manager
        self.init_ui()
        self.carica_categorie_combo()
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
        subtitle = QLabel("Modifica materiali e gestisci le categorie di raggruppamento")
        subtitle.setStyleSheet("QLabel { font-size: 14px; font-weight: 400; color: #718096; }")
        header_layout.addWidget(title)
        header_layout.addSpacing(20)
        header_layout.addWidget(subtitle)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)

        # Tab materiali
        self.tab_materiali = QWidget()
        self._build_tab_materiali(self.tab_materiali)
        self.tab_widget.addTab(self.tab_materiali, "Singoli Materiali")

        # Tab categorie
        self.tab_categorie = QWidget()
        self._build_tab_categorie(self.tab_categorie)
        self.tab_widget.addTab(self.tab_categorie, "Categorie")

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
        layout = QHBoxLayout(parent)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 12, 0, 0)

        # Left: lista
        left = QWidget()
        left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(20)

        lista_group = QGroupBox("Materiali Disponibili")
        lista_group.setGraphicsEffect(_make_shadow())
        lista_inner = QVBoxLayout(lista_group)
        lista_inner.setContentsMargins(20, 28, 20, 15)
        lista_inner.setSpacing(10)

        # Search bar
        search_container = QFrame()
        search_container.setStyleSheet("""
            QFrame { background-color: #f7fafc; border: 1px solid #e2e8f0;
                     border-radius: 8px; padding: 12px; margin: 2px 0px; }
        """)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.addWidget(QLabel("Cerca:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Inserisci nome materiale...")
        self.search_edit.textChanged.connect(self.filtra_materiali)
        search_layout.addWidget(self.search_edit)
        lista_inner.addWidget(search_container)

        self.lista_materiali = QListWidget()
        self.lista_materiali.itemSelectionChanged.connect(self.on_materiale_selezionato)
        lista_inner.addWidget(self.lista_materiali)

        self.lbl_conteggio = QLabel("0 materiali caricati")
        self.lbl_conteggio.setStyleSheet("QLabel { color: #718096; font-size: 13px; font-weight: 500; }")
        lista_inner.addWidget(self.lbl_conteggio)

        # List buttons
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

        left_layout.addWidget(lista_group)
        layout.addWidget(left)

        # Right: form
        right = QWidget()
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout = QVBoxLayout(right)
        right_layout.setSpacing(20)

        form_group = QGroupBox("Dettagli Materiale")
        form_group.setGraphicsEffect(_make_shadow())
        form_inner = QVBoxLayout(form_group)
        form_inner.setContentsMargins(20, 28, 20, 15)
        form_inner.setSpacing(10)

        # Selection info
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

        # Form fields
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

        self.edit_fornitore = QLineEdit()
        self.edit_fornitore.setPlaceholderText("es. Toray, Hexcel...")

        self.edit_prezzo_fornitore = NoScrollDoubleSpinBox()
        self.edit_prezzo_fornitore.setDecimals(2)
        self.edit_prezzo_fornitore.setMaximum(9999.99)
        self.edit_prezzo_fornitore.setSuffix(" €/m²")
        self.edit_prezzo_fornitore.setMinimumHeight(36)

        self.edit_capacita_magazzino = NoScrollDoubleSpinBox()
        self.edit_capacita_magazzino.setDecimals(2)
        self.edit_capacita_magazzino.setMaximum(99999.99)
        self.edit_capacita_magazzino.setSuffix(" m²")
        self.edit_capacita_magazzino.setMinimumHeight(36)

        self.edit_giacenza = NoScrollDoubleSpinBox()
        self.edit_giacenza.setDecimals(2)
        self.edit_giacenza.setMaximum(99999.99)
        self.edit_giacenza.setSuffix(" m²")
        self.edit_giacenza.setMinimumHeight(36)

        # Categoria dropdown (opzionale)
        self.combo_categoria = QComboBox()
        self.combo_categoria.setMinimumHeight(36)
        self.combo_categoria.setToolTip("Categoria opzionale per raggruppare materiali simili")

        form_fields.addRow(_std_label("Nome Materiale:"), self.edit_nome)
        form_fields.addRow(_std_label("Spessore:"), self.edit_spessore)
        form_fields.addRow(_std_label("Prezzo (Preventivo):"), self.edit_prezzo)
        form_fields.addRow(_std_label("Fornitore:"), self.edit_fornitore)
        form_fields.addRow(_std_label("Prezzo Fornitore:"), self.edit_prezzo_fornitore)
        form_fields.addRow(_std_label("Capacità Magazzino:"), self.edit_capacita_magazzino)
        form_fields.addRow(_std_label("Giacenza:"), self.edit_giacenza)
        form_fields.addRow(_std_label("Categoria (opzionale):"), self.combo_categoria)

        form_inner.addLayout(form_fields)

        # Form buttons
        form_btns = QHBoxLayout()
        form_btns.setSpacing(12)

        self.btn_salva = QPushButton("Salva Modifiche")
        self.btn_salva.setStyleSheet("""
            QPushButton { background-color: #4a5568; color: #ffffff; min-height: 40px; }
            QPushButton:hover { background-color: #2d3748; }
            QPushButton:disabled { background-color: #a0aec0; color: #ffffff; }
        """)
        self.btn_salva.clicked.connect(self.salva_materiale)

        self.btn_elimina = QPushButton("Elimina Materiale")
        self.btn_elimina.setStyleSheet("""
            QPushButton { background-color: #e53e3e; color: #ffffff; min-height: 40px; }
            QPushButton:hover { background-color: #c53030; }
            QPushButton:disabled { background-color: #a0aec0; color: #ffffff; }
        """)
        self.btn_elimina.clicked.connect(self.elimina_materiale)

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568;
                          border: 1px solid #e2e8f0; min-height: 40px; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        self.btn_reset.clicked.connect(self.reset_form)

        form_btns.addWidget(self.btn_salva)
        form_btns.addWidget(self.btn_elimina)
        form_btns.addStretch()
        form_btns.addWidget(self.btn_reset)
        form_inner.addLayout(form_btns)

        right_layout.addWidget(form_group)
        right_layout.addStretch()
        layout.addWidget(right)

        self.abilita_form(False)
        self.abilita_pulsanti_form(False)

    # ------------------------------------------------------------------
    # Tab: Categorie
    # ------------------------------------------------------------------

    def _build_tab_categorie(self, parent):
        layout = QHBoxLayout(parent)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 12, 0, 0)

        # Left: lista categorie
        left = QWidget()
        left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(20)

        cat_list_group = QGroupBox("Categorie Materiale")
        cat_list_group.setGraphicsEffect(_make_shadow())
        cat_list_inner = QVBoxLayout(cat_list_group)
        cat_list_inner.setContentsMargins(20, 28, 20, 15)
        cat_list_inner.setSpacing(10)

        self.lista_categorie = QListWidget()
        self.lista_categorie.itemSelectionChanged.connect(self.on_categoria_selezionata)
        cat_list_inner.addWidget(self.lista_categorie)

        self.lbl_conteggio_cat = QLabel("0 categorie")
        self.lbl_conteggio_cat.setStyleSheet("QLabel { color: #718096; font-size: 13px; font-weight: 500; }")
        cat_list_inner.addWidget(self.lbl_conteggio_cat)

        cat_btns = QHBoxLayout()
        self.btn_nuova_categoria = QPushButton("Nuova Categoria")
        self.btn_nuova_categoria.setStyleSheet("""
            QPushButton { background-color: #4a5568; color: #ffffff; min-height: 36px; }
            QPushButton:hover { background-color: #2d3748; }
        """)
        self.btn_nuova_categoria.clicked.connect(self.nuova_categoria)

        btn_aggiorna_cat = QPushButton("Aggiorna Lista")
        btn_aggiorna_cat.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568;
                          border: 1px solid #e2e8f0; min-height: 36px; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_aggiorna_cat.clicked.connect(self.carica_categorie)

        cat_btns.addWidget(self.btn_nuova_categoria)
        cat_btns.addWidget(btn_aggiorna_cat)
        cat_btns.addStretch()
        cat_list_inner.addLayout(cat_btns)

        left_layout.addWidget(cat_list_group)
        layout.addWidget(left)

        # Right: form categoria
        right = QWidget()
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout = QVBoxLayout(right)
        right_layout.setSpacing(20)

        cat_form_group = QGroupBox("Dettagli Categoria")
        cat_form_group.setGraphicsEffect(_make_shadow())
        cat_form_inner = QVBoxLayout(cat_form_group)
        cat_form_inner.setContentsMargins(20, 28, 20, 15)
        cat_form_inner.setSpacing(10)

        # Info selezione categoria
        self.cat_info_container = QFrame()
        self.cat_info_container.setStyleSheet("""
            QFrame { background-color: #ebf8ff; border: 1px solid #63b3ed;
                     border-radius: 8px; padding: 8px; margin: 0px; }
        """)
        cat_info_inner = QVBoxLayout(self.cat_info_container)
        cat_info_inner.setSpacing(4)
        self.lbl_cat_selezione = QLabel("Seleziona una categoria per modificarla")
        self.lbl_cat_selezione.setStyleSheet("QLabel { color: #2d3748; font-size: 14px; font-weight: 600; }")
        self.lbl_cat_materiali = QLabel("")
        self.lbl_cat_materiali.setStyleSheet("QLabel { color: #4a5568; font-size: 13px; font-weight: 500; }")
        cat_info_inner.addWidget(self.lbl_cat_selezione)
        cat_info_inner.addWidget(self.lbl_cat_materiali)
        cat_form_inner.addWidget(self.cat_info_container)

        # Form fields categoria
        cat_fields = QFormLayout()
        cat_fields.setVerticalSpacing(8)
        cat_fields.setHorizontalSpacing(12)

        self.cat_edit_nome = QLineEdit()
        self.cat_edit_nome.setPlaceholderText("es. Twill, Plain Weave, UD...")

        self.cat_edit_giacenza_minima = NoScrollDoubleSpinBox()
        self.cat_edit_giacenza_minima.setDecimals(2)
        self.cat_edit_giacenza_minima.setMaximum(99999.99)
        self.cat_edit_giacenza_minima.setSuffix(" m²")
        self.cat_edit_giacenza_minima.setMinimumHeight(36)
        self.cat_edit_giacenza_minima.setToolTip("Sotto questa soglia la categoria è considerata a scorta bassa")

        self.cat_edit_giacenza_desiderata = NoScrollDoubleSpinBox()
        self.cat_edit_giacenza_desiderata.setDecimals(2)
        self.cat_edit_giacenza_desiderata.setMaximum(99999.99)
        self.cat_edit_giacenza_desiderata.setSuffix(" m²")
        self.cat_edit_giacenza_desiderata.setMinimumHeight(36)
        self.cat_edit_giacenza_desiderata.setToolTip("Quantità ottimale da mantenere in magazzino")

        self.cat_edit_capacita = NoScrollDoubleSpinBox()
        self.cat_edit_capacita.setDecimals(2)
        self.cat_edit_capacita.setMaximum(99999.99)
        self.cat_edit_capacita.setSuffix(" m²")
        self.cat_edit_capacita.setMinimumHeight(36)
        self.cat_edit_capacita.setToolTip("Capacità massima di magazzino per questa categoria")

        self.cat_edit_note = QTextEdit()
        self.cat_edit_note.setPlaceholderText("Note sulla categoria...")
        self.cat_edit_note.setMaximumHeight(80)

        cat_fields.addRow(_std_label("Nome Categoria:"), self.cat_edit_nome)
        cat_fields.addRow(_std_label("Giacenza Minima:"), self.cat_edit_giacenza_minima)
        cat_fields.addRow(_std_label("Giacenza Desiderata:"), self.cat_edit_giacenza_desiderata)
        cat_fields.addRow(_std_label("Capacità Magazzino:"), self.cat_edit_capacita)
        cat_fields.addRow(_std_label("Note:"), self.cat_edit_note)

        cat_form_inner.addLayout(cat_fields)

        # Form buttons categoria
        cat_form_btns = QHBoxLayout()
        cat_form_btns.setSpacing(12)

        self.btn_salva_cat = QPushButton("Salva Modifiche")
        self.btn_salva_cat.setStyleSheet("""
            QPushButton { background-color: #4a5568; color: #ffffff; min-height: 40px; }
            QPushButton:hover { background-color: #2d3748; }
            QPushButton:disabled { background-color: #a0aec0; color: #ffffff; }
        """)
        self.btn_salva_cat.clicked.connect(self.salva_categoria)

        self.btn_elimina_cat = QPushButton("Elimina Categoria")
        self.btn_elimina_cat.setStyleSheet("""
            QPushButton { background-color: #e53e3e; color: #ffffff; min-height: 40px; }
            QPushButton:hover { background-color: #c53030; }
            QPushButton:disabled { background-color: #a0aec0; color: #ffffff; }
        """)
        self.btn_elimina_cat.clicked.connect(self.elimina_categoria)

        self.btn_reset_cat = QPushButton("Reset")
        self.btn_reset_cat.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568;
                          border: 1px solid #e2e8f0; min-height: 40px; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        self.btn_reset_cat.clicked.connect(self.reset_form_categoria)

        cat_form_btns.addWidget(self.btn_salva_cat)
        cat_form_btns.addWidget(self.btn_elimina_cat)
        cat_form_btns.addStretch()
        cat_form_btns.addWidget(self.btn_reset_cat)
        cat_form_inner.addLayout(cat_form_btns)

        right_layout.addWidget(cat_form_group)
        right_layout.addStretch()
        layout.addWidget(right)

        self.abilita_form_categoria(False)
        self.abilita_pulsanti_categoria(False)

    # ==================================================================
    # Materiali – logic
    # ==================================================================

    def carica_categorie_combo(self):
        """Popola il combo delle categorie nella form materiale"""
        self.combo_categoria.clear()
        self.combo_categoria.addItem("— Nessuna categoria —", None)
        for cat in self.db_manager.get_all_categorie():
            cat_id, nome = cat[0], cat[1]
            self.combo_categoria.addItem(nome, cat_id)

    def carica_materiali(self):
        self.lista_materiali.clear()
        self.materiali_data = self.db_manager.get_all_materiali()

        # Build a quick id→nome map for categories
        cat_map = {c[0]: c[1] for c in self.db_manager.get_all_categorie()}

        for mat in self.materiali_data:
            id_mat, nome, spessore, prezzo = mat[:4]
            fornitore = mat[4] if len(mat) > 4 else ""
            categoria_id = mat[8] if len(mat) > 8 else None
            testo = f"{nome} • {spessore}mm • €{prezzo:.2f}"
            if fornitore:
                testo += f" • {fornitore}"
            if categoria_id and categoria_id in cat_map:
                testo += f" • [{cat_map[categoria_id]}]"

            item = QListWidgetItem(testo)
            item.setData(Qt.UserRole, mat)
            self.lista_materiali.addItem(item)

        self.lbl_conteggio.setText(f"{self.lista_materiali.count()} materiali caricati")
        self.filtra_materiali()

    def filtra_materiali(self):
        search_text = self.search_edit.text().lower()
        for i in range(self.lista_materiali.count()):
            item = self.lista_materiali.item(i)
            nome = item.data(Qt.UserRole)[1].lower()
            item.setHidden(search_text not in nome)

    def on_materiale_selezionato(self):
        current_item = self.lista_materiali.currentItem()
        if not current_item:
            self.abilita_form(False)
            self.abilita_pulsanti_form(False)
            self.lbl_selezione.setText("Seleziona un materiale per modificarlo")
            self.lbl_info_materiale.setText("")
            return

        mat = current_item.data(Qt.UserRole)
        self.materiale_corrente = mat
        id_mat, nome, spessore, prezzo = mat[:4]
        fornitore = mat[4] if len(mat) > 4 else ""
        prezzo_fornitore = mat[5] if len(mat) > 5 else 0.0
        capacita_magazzino = mat[6] if len(mat) > 6 else 0.0
        giacenza = mat[7] if len(mat) > 7 else 0.0
        categoria_id = mat[8] if len(mat) > 8 else None

        self.lbl_selezione.setText(f"Materiale selezionato: {nome}")
        self.lbl_info_materiale.setText(f"ID: {id_mat} • Creato nel database")

        self.edit_nome.setText(nome)
        self.edit_spessore.setValue(spessore)
        self.edit_prezzo.setValue(prezzo)
        self.edit_fornitore.setText(fornitore)
        self.edit_prezzo_fornitore.setValue(prezzo_fornitore)
        self.edit_capacita_magazzino.setValue(capacita_magazzino)
        self.edit_giacenza.setValue(giacenza)

        # Set categoria combo
        idx = self.combo_categoria.findData(categoria_id)
        self.combo_categoria.setCurrentIndex(idx if idx >= 0 else 0)

        self.abilita_form(True)
        self.abilita_pulsanti_form(True)

    def abilita_form(self, enabled):
        for w in [self.edit_nome, self.edit_spessore, self.edit_prezzo,
                  self.edit_fornitore, self.edit_prezzo_fornitore,
                  self.edit_capacita_magazzino, self.edit_giacenza, self.combo_categoria]:
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
            self.edit_fornitore.clear()
            self.edit_prezzo_fornitore.setValue(0.0)
            self.edit_capacita_magazzino.setValue(0.0)
            self.edit_giacenza.setValue(0.0)
            self.combo_categoria.setCurrentIndex(0)

    def nuovo_materiale(self):
        dialog = NuovoMaterialeDialog(self.db_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            self.carica_materiali()
            self.carica_categorie_combo()
            QMessageBox.information(self, "Successo", "Nuovo materiale aggiunto con successo!")

    def salva_materiale(self):
        if not hasattr(self, 'materiale_corrente'):
            return

        nome = self.edit_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Errore", "Il nome del materiale è obbligatorio.")
            return

        spessore = self.edit_spessore.value()
        if spessore <= 0:
            QMessageBox.warning(self, "Errore", "Lo spessore deve essere maggiore di 0.")
            return

        prezzo = self.edit_prezzo.value()
        if prezzo <= 0:
            QMessageBox.warning(self, "Errore", "Il prezzo deve essere maggiore di 0.")
            return

        risposta = QMessageBox.question(
            self, "Conferma Modifiche",
            f"Salvare le modifiche al materiale '{nome}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )

        if risposta == QMessageBox.Yes:
            try:
                categoria_id = self.combo_categoria.currentData()
                success = self.db_manager.update_materiale(
                    self.materiale_corrente[0], nome, spessore, prezzo,
                    self.edit_fornitore.text().strip(),
                    self.edit_prezzo_fornitore.value(),
                    self.edit_capacita_magazzino.value(),
                    self.edit_giacenza.value(),
                    categoria_id
                )
                if success:
                    QMessageBox.information(self, "Successo", "Materiale aggiornato con successo!")
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
                    QMessageBox.information(self, "Successo", f"Materiale '{nome_materiale}' eliminato con successo!")
                    self.carica_materiali()
                    self.reset_form()
                    self.abilita_form(False)
                    self.abilita_pulsanti_form(False)
                    self.materiali_modificati.emit()
                else:
                    QMessageBox.critical(self, "Errore", "Errore durante l'eliminazione del materiale.")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore durante l'eliminazione:\n{str(e)}")

    # ==================================================================
    # Categorie – logic
    # ==================================================================

    def carica_categorie(self):
        self.lista_categorie.clear()
        categorie = self.db_manager.get_all_categorie()

        for cat in categorie:
            cat_id, nome, giacenza_minima, giacenza_desiderata, capacita, note = cat
            # Count materials in this category
            mats = self.db_manager.get_materiali_per_categoria(cat_id)
            num_mat = len(mats)
            giacenza_totale = sum(m[2] for m in mats)

            testo = f"{nome} • {num_mat} materiali • {giacenza_totale:.1f} m² in giacenza"

            item = QListWidgetItem(testo)
            item.setData(Qt.UserRole, cat)
            self.lista_categorie.addItem(item)

        self.lbl_conteggio_cat.setText(f"{self.lista_categorie.count()} categorie")
        # Also refresh combo in materiali tab
        self.carica_categorie_combo()

    def on_categoria_selezionata(self):
        current_item = self.lista_categorie.currentItem()
        if not current_item:
            self.abilita_form_categoria(False)
            self.abilita_pulsanti_categoria(False)
            self.lbl_cat_selezione.setText("Seleziona una categoria per modificarla")
            self.lbl_cat_materiali.setText("")
            return

        cat = current_item.data(Qt.UserRole)
        self.categoria_corrente = cat
        cat_id, nome, giacenza_minima, giacenza_desiderata, capacita, note = cat

        # Count materials
        mats = self.db_manager.get_materiali_per_categoria(cat_id)
        num_mat = len(mats)
        giacenza_totale = sum(m[2] for m in mats)
        nomi_mat = ", ".join(m[1] for m in mats[:5])
        if num_mat > 5:
            nomi_mat += f" ... (+{num_mat - 5})"

        self.lbl_cat_selezione.setText(f"Categoria selezionata: {nome}")
        self.lbl_cat_materiali.setText(
            f"ID: {cat_id} • {num_mat} materiali • {giacenza_totale:.1f} m² totale"
            + (f"\nMateriali: {nomi_mat}" if nomi_mat else "")
        )

        self.cat_edit_nome.setText(nome)
        self.cat_edit_giacenza_minima.setValue(giacenza_minima or 0.0)
        self.cat_edit_giacenza_desiderata.setValue(giacenza_desiderata or 0.0)
        self.cat_edit_capacita.setValue(capacita or 0.0)
        self.cat_edit_note.setPlainText(note or "")

        self.abilita_form_categoria(True)
        self.abilita_pulsanti_categoria(True)

    def abilita_form_categoria(self, enabled):
        for w in [self.cat_edit_nome, self.cat_edit_giacenza_minima,
                  self.cat_edit_giacenza_desiderata, self.cat_edit_capacita,
                  self.cat_edit_note]:
            w.setEnabled(enabled)

    def abilita_pulsanti_categoria(self, enabled):
        self.btn_salva_cat.setEnabled(enabled)
        self.btn_elimina_cat.setEnabled(enabled)

    def reset_form_categoria(self):
        if hasattr(self, 'categoria_corrente'):
            self.on_categoria_selezionata()
        else:
            self.cat_edit_nome.clear()
            self.cat_edit_giacenza_minima.setValue(0.0)
            self.cat_edit_giacenza_desiderata.setValue(0.0)
            self.cat_edit_capacita.setValue(0.0)
            self.cat_edit_note.clear()

    def nuova_categoria(self):
        dialog = NuovaCategoriaDialog(self.db_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            self.carica_categorie()
            QMessageBox.information(self, "Successo", "Nuova categoria aggiunta con successo!")

    def salva_categoria(self):
        if not hasattr(self, 'categoria_corrente'):
            return

        nome = self.cat_edit_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Errore", "Il nome della categoria è obbligatorio.")
            return

        risposta = QMessageBox.question(
            self, "Conferma Modifiche",
            f"Salvare le modifiche alla categoria '{nome}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )

        if risposta == QMessageBox.Yes:
            try:
                success = self.db_manager.update_categoria(
                    self.categoria_corrente[0], nome,
                    self.cat_edit_giacenza_minima.value(),
                    self.cat_edit_giacenza_desiderata.value(),
                    self.cat_edit_capacita.value(),
                    self.cat_edit_note.toPlainText().strip()
                )
                if success:
                    QMessageBox.information(self, "Successo", "Categoria aggiornata con successo!")
                    self.carica_categorie()
                    self.carica_materiali()
                else:
                    QMessageBox.critical(self, "Errore", "Nome categoria già esistente o errore nel database.")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio:\n{str(e)}")

    def elimina_categoria(self):
        if not hasattr(self, 'categoria_corrente'):
            return

        nome_cat = self.categoria_corrente[1]
        risposta = QMessageBox.question(
            self, "Conferma Eliminazione",
            f"Eliminare la categoria '{nome_cat}'?\n\nI materiali collegati verranno scollegati dalla categoria (non verranno eliminati).",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if risposta == QMessageBox.Yes:
            try:
                success = self.db_manager.delete_categoria(self.categoria_corrente[0])
                if success:
                    QMessageBox.information(self, "Successo", f"Categoria '{nome_cat}' eliminata con successo!")
                    del self.categoria_corrente
                    self.carica_categorie()
                    self.carica_materiali()
                    self.abilita_form_categoria(False)
                    self.abilita_pulsanti_categoria(False)
                    self.lbl_cat_selezione.setText("Seleziona una categoria per modificarla")
                    self.lbl_cat_materiali.setText("")
                else:
                    QMessageBox.critical(self, "Errore", "Errore durante l'eliminazione della categoria.")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore durante l'eliminazione:\n{str(e)}")

    def showEvent(self, event):
        super().showEvent(event)
        self.carica_categorie()


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
        self.setFixedSize(450, 560)
        self.setStyleSheet(_DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(20)

        title = QLabel("Aggiungi Nuovo Materiale")
        title.setStyleSheet("QLabel { font-size: 18px; font-weight: 700; color: #2d3748; padding-bottom: 10px; }")
        layout.addWidget(title)

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

        self.edit_fornitore = QLineEdit()
        self.edit_fornitore.setPlaceholderText("es. Toray, Hexcel...")

        self.edit_prezzo_fornitore = NoScrollDoubleSpinBox()
        self.edit_prezzo_fornitore.setDecimals(2)
        self.edit_prezzo_fornitore.setMaximum(9999.99)
        self.edit_prezzo_fornitore.setSuffix(" €/m²")

        self.edit_capacita_magazzino = NoScrollDoubleSpinBox()
        self.edit_capacita_magazzino.setDecimals(2)
        self.edit_capacita_magazzino.setMaximum(99999.99)
        self.edit_capacita_magazzino.setSuffix(" m²")

        self.edit_giacenza = NoScrollDoubleSpinBox()
        self.edit_giacenza.setDecimals(2)
        self.edit_giacenza.setMaximum(99999.99)
        self.edit_giacenza.setSuffix(" m²")

        self.combo_categoria = QComboBox()
        self.combo_categoria.addItem("— Nessuna categoria —", None)
        for cat in self.db_manager.get_all_categorie():
            self.combo_categoria.addItem(cat[1], cat[0])

        form.addRow("Nome Materiale:", self.edit_nome)
        form.addRow("Spessore:", self.edit_spessore)
        form.addRow("Prezzo (Preventivo):", self.edit_prezzo)
        form.addRow("Fornitore:", self.edit_fornitore)
        form.addRow("Prezzo Fornitore:", self.edit_prezzo_fornitore)
        form.addRow("Capacità Magazzino:", self.edit_capacita_magazzino)
        form.addRow("Giacenza Iniziale:", self.edit_giacenza)
        form.addRow("Categoria (opzionale):", self.combo_categoria)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.setSpacing(12)

        btn_annulla = QPushButton("Annulla")
        btn_annulla.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_annulla.clicked.connect(self.reject)

        btn_salva = QPushButton("Salva Materiale")
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
            QMessageBox.warning(self, "Errore", "Il nome del materiale è obbligatorio.")
            return

        spessore = self.edit_spessore.value()
        if spessore <= 0:
            QMessageBox.warning(self, "Errore", "Lo spessore deve essere maggiore di 0.")
            return

        prezzo = self.edit_prezzo.value()
        if prezzo <= 0:
            QMessageBox.warning(self, "Errore", "Il prezzo deve essere maggiore di 0.")
            return

        try:
            categoria_id = self.combo_categoria.currentData()
            mat_id = self.db_manager.add_materiale(
                nome, spessore, prezzo,
                self.edit_fornitore.text().strip(),
                self.edit_prezzo_fornitore.value(),
                self.edit_capacita_magazzino.value(),
                self.edit_giacenza.value(),
                categoria_id
            )
            if mat_id:
                self.accept()
            else:
                QMessageBox.critical(self, "Errore", "Nome materiale già esistente.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio:\n{str(e)}")


class NuovaCategoriaDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Nuova Categoria")
        self.setFixedSize(420, 420)
        self.setStyleSheet(_DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(20)

        title = QLabel("Aggiungi Nuova Categoria")
        title.setStyleSheet("QLabel { font-size: 18px; font-weight: 700; color: #2d3748; padding-bottom: 10px; }")
        layout.addWidget(title)

        form = QFormLayout()
        form.setVerticalSpacing(16)

        self.edit_nome = QLineEdit()
        self.edit_nome.setPlaceholderText("es. Twill, Plain Weave, UD...")

        self.edit_giacenza_minima = NoScrollDoubleSpinBox()
        self.edit_giacenza_minima.setDecimals(2)
        self.edit_giacenza_minima.setMaximum(99999.99)
        self.edit_giacenza_minima.setSuffix(" m²")

        self.edit_giacenza_desiderata = NoScrollDoubleSpinBox()
        self.edit_giacenza_desiderata.setDecimals(2)
        self.edit_giacenza_desiderata.setMaximum(99999.99)
        self.edit_giacenza_desiderata.setSuffix(" m²")

        self.edit_capacita = NoScrollDoubleSpinBox()
        self.edit_capacita.setDecimals(2)
        self.edit_capacita.setMaximum(99999.99)
        self.edit_capacita.setSuffix(" m²")

        self.edit_note = QTextEdit()
        self.edit_note.setPlaceholderText("Note opzionali sulla categoria...")
        self.edit_note.setMaximumHeight(70)

        form.addRow("Nome Categoria:", self.edit_nome)
        form.addRow("Giacenza Minima:", self.edit_giacenza_minima)
        form.addRow("Giacenza Desiderata:", self.edit_giacenza_desiderata)
        form.addRow("Capacità Magazzino:", self.edit_capacita)
        form.addRow("Note:", self.edit_note)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.setSpacing(12)

        btn_annulla = QPushButton("Annulla")
        btn_annulla.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_annulla.clicked.connect(self.reject)

        btn_salva = QPushButton("Salva Categoria")
        btn_salva.setStyleSheet("""
            QPushButton { background-color: #4a5568; color: #ffffff; }
            QPushButton:hover { background-color: #2d3748; }
        """)
        btn_salva.clicked.connect(self.salva_nuova_categoria)

        btns.addWidget(btn_annulla)
        btns.addWidget(btn_salva)
        layout.addLayout(btns)

    def salva_nuova_categoria(self):
        nome = self.edit_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Errore", "Il nome della categoria è obbligatorio.")
            return

        try:
            cat_id = self.db_manager.add_categoria(
                nome,
                self.edit_giacenza_minima.value(),
                self.edit_giacenza_desiderata.value(),
                self.edit_capacita.value(),
                self.edit_note.toPlainText().strip()
            )
            if cat_id:
                self.accept()
            else:
                QMessageBox.critical(self, "Errore", "Nome categoria già esistente.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio:\n{str(e)}")
