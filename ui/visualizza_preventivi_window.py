"""
VisualizzaPreventiviWindow - Interfaccia per visualizzare e gestire i preventivi con sistema di versioning

Version: 2.0.0
Last Updated: 2026-02-07
Author: Sviluppatore PyQt5

CHANGELOG:
v2.0.0 (2026-02-07):
- ADDED: Filtro "Con modifiche" per vedere preventivi con storico modifiche
- ADDED: Pulsante "Visualizza Modifiche" per aprire dialog storico
- UPDATED: Integrazione con sistema di versioning Git-like
v1.0.0 (2026-02-06):
- CREATED: Nuova finestra dedicata per visualizzare preventivi
- ADDED: Design system unificato con MainWindow e altre finestre
- ADDED: Filtri avanzati (origine, cliente, keyword)
- ADDED: Apertura a schermo intero con controlli finestra
- ADDED: Azioni preventivi (visualizza, modifica, elimina, revisione, confronta, genera documento)
"""
# type: ignore
# pyright: reportUnknownParameterType=false, reportMissingParameterType=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportAttributeAccessIssue=false
# pyright: reportUnusedVariable=false
# type: ignore
# pyright: reportUnusedImport=false
# type: ignore
# pyright: reportUnknownLambdaType=false

from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
                             QWidget, QLabel, QListWidget, QMessageBox, QListWidgetItem,
                             QGroupBox, QFrame, QGraphicsDropShadowEffect,
                             QLineEdit, QComboBox, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from typing import Optional, Any

class VisualizzaPreventiviWindow(QMainWindow):
    preventivo_modificato = pyqtSignal()  # Signal per notificare modifiche

    def __init__(self, db_manager: Any, parent: Optional[QWidget] = None) -> None:
        super().__init__(None)  # No parent per evitare bug ridimensionamento
        self.db_manager = db_manager
        self.parent_window = parent
        self.init_ui()
        self.load_clienti_filtro()
        self.load_categorie_filtro()
        self.load_sottocategorie_filtro()
        self.load_preventivi()

    def init_ui(self) -> None:
        """Design system unificato - apertura a schermo intero"""
        self.setWindowTitle("Visualizza Preventivi - Software Aziendale RCS")

        # Apertura massimizzata mantenendo i controlli della finestra
        self.showMaximized()

        # Stile unificato con design system coerente
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
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                font-size: 14px;
                padding: 8px;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QListWidget::item {
                border-radius: 6px;
                padding: 12px;
                margin: 2px 0px;
                border-bottom: 1px solid #f7fafc;
                color: #2d3748;
            }
            QListWidget::item:hover {
                background-color: #f7fafc;
            }
            QListWidget::item:selected {
                background-color: #edf2f7;
                color: #2d3748;
            }
            QLineEdit, QComboBox {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 14px;
                background-color: #ffffff;
                color: #2d3748;
                min-height: 18px;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #718096;
                outline: none;
            }
            QLineEdit:hover, QComboBox:hover {
                border-color: #a0aec0;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #4a5568;
                width: 0;
                height: 0;
                margin-right: 10px;
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

        # Widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principale - margini ridotti per mostrare tutto
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(12)

        # Header
        self.create_header(main_layout)

        # Filtri
        self.create_filters_section(main_layout)

        # Lista preventivi
        self.create_lista_preventivi(main_layout)

        # Pulsanti azioni
        self.create_action_buttons(main_layout)

        # Footer
        self.create_footer(main_layout)

    def create_shadow_effect(self, blur: int = 10, opacity: int = 12) -> QGraphicsDropShadowEffect:
        """Effetto ombra standardizzato"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setColor(QColor(0, 0, 0, opacity))
        shadow.setOffset(0, 2)
        return shadow

    def create_header(self, parent_layout: QVBoxLayout) -> None:
        """Header unificato - compatto"""
        header_container = QFrame()
        header_container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                padding: 5px 0px;
            }
        """)

        header_layout = QVBoxLayout(header_container)
        header_layout.setSpacing(4)

        # Titolo principale
        title_label = QLabel("Visualizza Preventivi")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 700;
                color: #2d3748;
                padding: 0;
            }
        """)

        # Sottotitolo
        subtitle_label = QLabel("Esplora, filtra e gestisci tutti i preventivi salvati")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 400;
                color: #718096;
                padding: 0;
            }
        """)

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)

        parent_layout.addWidget(header_container)

    def create_filters_section(self, parent_layout: QVBoxLayout) -> None:
        """Sezione filtri per preventivi - inline compatto CON FILTRO "CON MODIFICHE" """
        filters_container = QFrame()
        filters_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 12px;
            }
        """)
        filters_container.setGraphicsEffect(self.create_shadow_effect())

        # Layout orizzontale per tutti i filtri inline
        filters_layout = QHBoxLayout(filters_container)
        filters_layout.setSpacing(15)

        # Filtro Tipo Preventivo (sempre visibile)
        tipo_label = QLabel("Tipo:")
        tipo_label.setStyleSheet("QLabel { font-weight: 500; color: #4a5568; }")
        self.filtro_origine = QComboBox()
        self.filtro_origine.addItems(["Tutti", "Originali", "Revisionati", "Con modifiche"])
        self.filtro_origine.currentIndexChanged.connect(self.load_preventivi)
        self.filtro_origine.setMinimumWidth(140)

        filters_layout.addWidget(tipo_label)
        filters_layout.addWidget(self.filtro_origine)

        # Filtro Cliente
        cliente_label = QLabel("Cliente:")
        cliente_label.setStyleSheet("QLabel { font-weight: 500; color: #4a5568; }")
        self.filtro_cliente = QComboBox()
        self.filtro_cliente.addItem("Tutti i clienti", None)
        self.filtro_cliente.currentIndexChanged.connect(self.load_preventivi)
        self.filtro_cliente.setMinimumWidth(180)

        filters_layout.addWidget(cliente_label)
        filters_layout.addWidget(self.filtro_cliente)

        # Filtro Categoria
        categoria_label = QLabel("Categoria:")
        categoria_label.setStyleSheet("QLabel { font-weight: 500; color: #4a5568; }")
        self.filtro_categoria = QComboBox()
        self.filtro_categoria.addItem("Tutte le categorie", None)
        self.filtro_categoria.currentIndexChanged.connect(self.load_preventivi)
        self.filtro_categoria.setMinimumWidth(160)

        filters_layout.addWidget(categoria_label)
        filters_layout.addWidget(self.filtro_categoria)

        # Filtro Sottocategoria
        sottocategoria_label = QLabel("Sottocategoria:")
        sottocategoria_label.setStyleSheet("QLabel { font-weight: 500; color: #4a5568; }")
        self.filtro_sottocategoria = QComboBox()
        self.filtro_sottocategoria.addItem("Tutte le sottocategorie", None)
        self.filtro_sottocategoria.currentIndexChanged.connect(self.load_preventivi)
        self.filtro_sottocategoria.setMinimumWidth(180)

        filters_layout.addWidget(sottocategoria_label)
        filters_layout.addWidget(self.filtro_sottocategoria)

        # Filtro Keyword
        keyword_label = QLabel("Cerca:")
        keyword_label.setStyleSheet("QLabel { font-weight: 500; color: #4a5568; }")
        self.filtro_keyword = QLineEdit()
        self.filtro_keyword.setPlaceholderText("ID, cliente, descrizione, codice, prezzo...")
        self.filtro_keyword.textChanged.connect(self.load_preventivi)

        filters_layout.addWidget(keyword_label)
        filters_layout.addWidget(self.filtro_keyword, 1)  # Stretch per occupare spazio rimanente

        parent_layout.addWidget(filters_container)

    def create_lista_preventivi(self, parent_layout: QVBoxLayout) -> None:
        """Lista preventivi con pannello dettaglio a destra"""
        lista_group = QGroupBox("Preventivi")
        lista_group.setGraphicsEffect(self.create_shadow_effect())

        lista_group_layout = QVBoxLayout(lista_group)
        lista_group_layout.setContentsMargins(15, 20, 15, 15)
        lista_group_layout.setSpacing(8)

        # Contenuto orizzontale: lista a sinistra, dettaglio a destra
        split_layout = QHBoxLayout()
        split_layout.setSpacing(16)

        # --- Colonna sinistra: lista + conteggio ---
        left_col = QVBoxLayout()
        left_col.setSpacing(6)

        self.lista_preventivi = QListWidget()
        self.lista_preventivi.setMinimumHeight(200)
        self.lista_preventivi.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.lista_preventivi.itemDoubleClicked.connect(self.visualizza_preventivo)
        self.lista_preventivi.currentItemChanged.connect(self._on_selezione_cambiata)
        left_col.addWidget(self.lista_preventivi)

        self.lbl_conteggio = QLabel("0 preventivi caricati")
        self.lbl_conteggio.setStyleSheet("QLabel { color: #718096; font-size: 13px; font-weight: 500; }")
        left_col.addWidget(self.lbl_conteggio)

        left_widget = QWidget()
        left_widget.setLayout(left_col)
        left_widget.setMinimumWidth(320)
        left_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # --- Colonna destra: pannello dettaglio ---
        self.detail_panel = QFrame()
        self.detail_panel.setStyleSheet("""
            QFrame {
                background-color: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        self.detail_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        detail_outer = QVBoxLayout(self.detail_panel)
        detail_outer.setContentsMargins(0, 0, 0, 0)

        # Scroll area per il dettaglio
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.detail_layout = QVBoxLayout(scroll_content)
        self.detail_layout.setContentsMargins(20, 16, 20, 16)
        self.detail_layout.setSpacing(10)
        self.detail_layout.setAlignment(Qt.AlignTop)

        # Placeholder iniziale
        self.detail_placeholder = QLabel("Seleziona un preventivo per vedere i dettagli")
        self.detail_placeholder.setAlignment(Qt.AlignCenter)
        self.detail_placeholder.setStyleSheet("QLabel { color: #a0aec0; font-size: 14px; font-style: italic; }")
        self.detail_layout.addWidget(self.detail_placeholder)

        scroll.setWidget(scroll_content)
        detail_outer.addWidget(scroll)

        split_layout.addWidget(left_widget, 2)
        split_layout.addWidget(self.detail_panel, 3)

        lista_group_layout.addLayout(split_layout)
        parent_layout.addWidget(lista_group)

    def create_action_buttons(self, parent_layout: QVBoxLayout) -> None:
        """Pulsanti azioni preventivi - compatti CON PULSANTE "VISUALIZZA MODIFICHE" """
        buttons_container = QFrame()
        buttons_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        buttons_container.setGraphicsEffect(self.create_shadow_effect())

        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setSpacing(8)

        # Prima riga
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        # Visualizza
        self.btn_visualizza = QPushButton("Visualizza Dettagli")
        self.btn_visualizza.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                min-height: 38px;
                min-width: 140px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
        """)
        self.btn_visualizza.clicked.connect(self.visualizza_preventivo)

        # Modifica
        self.btn_modifica = QPushButton("Modifica")
        self.btn_modifica.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                min-height: 38px;
                min-width: 100px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
        """)
        self.btn_modifica.clicked.connect(self.modifica_preventivo)

        # Crea Revisione
        self.btn_revisione = QPushButton("Crea Revisione")
        self.btn_revisione.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                min-height: 38px;
                min-width: 130px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
        """)
        self.btn_revisione.clicked.connect(self.crea_revisione)

        # NUOVO: Visualizza Modifiche
        self.btn_visualizza_modifiche = QPushButton("Visualizza Modifiche")
        self.btn_visualizza_modifiche.setStyleSheet("""
            QPushButton {
                background-color: #805ad5;
                color: #ffffff;
                min-height: 38px;
                min-width: 160px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #6b46c1;
            }
        """)
        self.btn_visualizza_modifiche.clicked.connect(self.visualizza_modifiche)

        row1.addWidget(self.btn_visualizza)
        row1.addWidget(self.btn_modifica)
        row1.addWidget(self.btn_revisione)
        row1.addWidget(self.btn_visualizza_modifiche)

        # Seconda riga
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        # Confronta
        self.btn_confronta = QPushButton("Confronta Preventivi")
        self.btn_confronta.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: 38px;
                min-width: 160px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
        """)
        self.btn_confronta.clicked.connect(self.confronta_preventivi)

        # Anteprima Documento
        self.btn_anteprima = QPushButton("Anteprima Documento")
        self.btn_anteprima.setStyleSheet("""
            QPushButton {
                background-color: #ebf8ff;
                color: #2b6cb0;
                border: 1px solid #bee3f8;
                min-height: 38px;
                min-width: 160px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #bee3f8;
            }
        """)
        self.btn_anteprima.clicked.connect(self.anteprima_documento)

        # Genera Documento
        self.btn_genera = QPushButton("Genera Documento")
        self.btn_genera.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: 38px;
                min-width: 150px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
        """)
        self.btn_genera.clicked.connect(self.genera_documento)

        # Elimina
        self.btn_elimina = QPushButton("Elimina")
        self.btn_elimina.setStyleSheet("""
            QPushButton {
                background-color: #e53e3e;
                color: #ffffff;
                min-height: 32px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #c53030;
            }
        """)
        self.btn_elimina.clicked.connect(self.elimina_preventivo)

        row2.addWidget(self.btn_confronta)
        row2.addWidget(self.btn_anteprima)
        row2.addWidget(self.btn_genera)
        row2.addWidget(self.btn_elimina)

        buttons_layout.addLayout(row1)
        buttons_layout.addLayout(row2)

        parent_layout.addWidget(buttons_container)

    def create_footer(self, parent_layout: QVBoxLayout) -> None:
        """Footer con pulsante chiudi - compatto"""
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        # Chiudi finestra
        btn_chiudi = QPushButton("Chiudi")
        btn_chiudi.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: 32px;
                min-width: 120px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
        """)
        btn_chiudi.clicked.connect(lambda: self.close())

        footer_layout.addWidget(btn_chiudi)
        parent_layout.addLayout(footer_layout)

    # =============================================================================
    # METODI FUNZIONALI
    # =============================================================================

    def load_categorie_filtro(self) -> None:
        """Popola il filtro categorie con i valori esistenti nel DB"""
        current_data = self.filtro_categoria.currentData()
        self.filtro_categoria.blockSignals(True)
        self.filtro_categoria.clear()
        self.filtro_categoria.addItem("Tutte le categorie", None)
        try:
            preventivi = self.db_manager.get_all_preventivi()
            categorie = set()
            for prev in preventivi:
                prev_c = self.db_manager.get_preventivo_by_id(prev[0])
                if prev_c:
                    cat = (prev_c.get('categoria') or '').strip()
                    if cat:
                        categorie.add(cat)
            for cat in sorted(categorie):
                self.filtro_categoria.addItem(cat, cat)
            # Ripristina selezione precedente se ancora presente
            idx = self.filtro_categoria.findData(current_data)
            if idx >= 0:
                self.filtro_categoria.setCurrentIndex(idx)
        except Exception as e:
            print(f"Errore nel caricamento categorie filtro: {str(e)}")
        self.filtro_categoria.blockSignals(False)

    def load_sottocategorie_filtro(self) -> None:
        """Popola il filtro sottocategorie con i valori esistenti nel DB"""
        current_data = self.filtro_sottocategoria.currentData()
        self.filtro_sottocategoria.blockSignals(True)
        self.filtro_sottocategoria.clear()
        self.filtro_sottocategoria.addItem("Tutte le sottocategorie", None)
        try:
            preventivi = self.db_manager.get_all_preventivi()
            sottocategorie = set()
            for prev in preventivi:
                prev_c = self.db_manager.get_preventivo_by_id(prev[0])
                if prev_c:
                    sc = (prev_c.get('sottocategoria') or '').strip()
                    if sc:
                        sottocategorie.add(sc)
            for sc in sorted(sottocategorie):
                self.filtro_sottocategoria.addItem(sc, sc)
            idx = self.filtro_sottocategoria.findData(current_data)
            if idx >= 0:
                self.filtro_sottocategoria.setCurrentIndex(idx)
        except Exception as e:
            print(f"Errore nel caricamento sottocategorie filtro: {str(e)}")
        self.filtro_sottocategoria.blockSignals(False)

    def _on_selezione_cambiata(self, current, previous) -> None:
        """Aggiorna il pannello dettaglio quando cambia la selezione"""
        if current is None:
            self._clear_detail_panel()
            return
        preventivo_id = current.data(Qt.UserRole)
        self._update_detail_panel(preventivo_id)

    def _clear_detail_panel(self) -> None:
        """Svuota il pannello dettaglio"""
        for i in reversed(range(self.detail_layout.count())):
            w = self.detail_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        self.detail_placeholder = QLabel("Seleziona un preventivo per vedere i dettagli")
        self.detail_placeholder.setAlignment(Qt.AlignCenter)
        self.detail_placeholder.setStyleSheet("QLabel { color: #a0aec0; font-size: 14px; font-style: italic; }")
        self.detail_layout.addWidget(self.detail_placeholder)

    def _update_detail_panel(self, preventivo_id: int) -> None:
        """Mostra i dettagli del preventivo nel pannello laterale"""
        # Svuota il pannello
        for i in reversed(range(self.detail_layout.count())):
            w = self.detail_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        prev = self.db_manager.get_preventivo_by_id(preventivo_id)
        if not prev:
            return

        def add_field(label_text: str, value: str, value_style: str = "") -> None:
            row = QHBoxLayout()
            row.setSpacing(8)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("QLabel { font-weight: 600; color: #4a5568; font-size: 13px; min-width: 130px; max-width: 130px; }")
            lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            val = QLabel(value or "—")
            val.setWordWrap(True)
            val.setStyleSheet(f"QLabel {{ color: #2d3748; font-size: 13px; {value_style} }}")
            val.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            row.addWidget(lbl)
            row.addWidget(val, 1)
            container = QWidget()
            container.setStyleSheet("background: transparent;")
            container.setLayout(row)
            self.detail_layout.addWidget(container)

        def add_separator() -> None:
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet("QFrame { color: #e2e8f0; background: #e2e8f0; max-height: 1px; }")
            self.detail_layout.addWidget(sep)

        # Titolo
        numero_rev = prev.get('numero_revisione', 1)
        tipo = "Originale" if numero_rev == 1 else f"Revisione #{numero_rev}"
        title = QLabel(f"#{preventivo_id:03d} — {tipo}")
        title.setStyleSheet("QLabel { font-size: 16px; font-weight: 700; color: #2d3748; }")
        self.detail_layout.addWidget(title)

        # Data
        data_raw = prev.get('data_creazione', '')
        data_display = data_raw[:10] if data_raw else '—'
        add_field("Data creazione:", data_display)
        add_separator()

        # Campi cliente
        add_field("Cliente:", prev.get('nome_cliente', ''))
        add_field("Numero ordine:", prev.get('numero_ordine', ''))
        add_field("Codice:", prev.get('codice', ''))
        add_field("Misura:", prev.get('misura', ''))
        add_field("Finitura:", prev.get('finitura', ''))
        add_field("Categoria:", prev.get('categoria', ''))
        add_field("Sottocategoria:", prev.get('sottocategoria', ''))
        add_field("Descrizione:", prev.get('descrizione', ''))
        add_separator()

        # Prezzi
        p_finale = prev.get('preventivo_finale')
        p_cliente = prev.get('prezzo_cliente')
        add_field("Preventivo finale:", f"€ {p_finale:.2f}" if p_finale is not None else "—")
        add_field("Prezzo cliente:", f"€ {p_cliente:.2f}" if p_cliente is not None else "—")
        add_separator()

        # Note revisione
        note = (prev.get('note_revisione') or '').strip()
        note_title = QLabel("Note revisione:")
        note_title.setStyleSheet("QLabel { font-weight: 600; color: #4a5568; font-size: 13px; }")
        self.detail_layout.addWidget(note_title)

        note_box = QFrame()
        note_box.setStyleSheet("""
            QFrame {
                background-color: #fffbeb;
                border: 1px solid #f6e05e;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        note_box_layout = QVBoxLayout(note_box)
        note_box_layout.setContentsMargins(10, 8, 10, 8)
        note_val = QLabel(note if note else "Nessuna nota")
        note_val.setWordWrap(True)
        note_val.setStyleSheet(
            "QLabel { color: #744210; font-size: 13px; }" if note
            else "QLabel { color: #a0aec0; font-size: 13px; font-style: italic; }"
        )
        note_box_layout.addWidget(note_val)
        self.detail_layout.addWidget(note_box)

    def load_clienti_filtro(self) -> None:
        """Carica la lista dei clienti nel filtro"""
        self.filtro_cliente.clear()
        self.filtro_cliente.addItem("Tutti i clienti", None)

        try:
            preventivi = self.db_manager.get_all_preventivi()
            clienti = set()
            for prev in preventivi:
                if len(prev) >= 5:
                    nome_cliente = prev[4].strip() if prev[4] else ''
                    if nome_cliente:
                        clienti.add(nome_cliente)

            for cliente in sorted(clienti):
                self.filtro_cliente.addItem(cliente, cliente)
        except Exception as e:
            print(f"Errore nel caricamento clienti filtro: {str(e)}")

    def load_preventivi(self) -> None:
        """Carica TUTTI i preventivi con filtri"""
        self.lista_preventivi.clear()
        self._clear_detail_panel()

        # Ottieni i valori dei filtri
        filtro_origine_text = self.filtro_origine.currentText()
        filtro_cliente_data = self.filtro_cliente.currentData()
        filtro_keyword_text = self.filtro_keyword.text().lower().strip()
        filtro_categoria_data = self.filtro_categoria.currentData()
        filtro_sottocategoria_data = self.filtro_sottocategoria.currentData()

        # Carica SEMPRE tutti i preventivi
        if filtro_origine_text == "Con modifiche":
            preventivi = self.db_manager.get_preventivi_con_modifiche()
        else:
            preventivi = self.db_manager.get_all_preventivi()

        count = 0
        for preventivo in preventivi:
            # Ottieni i dati del preventivo - LEGGI MISURA DAL DB
            prev_completo = self.db_manager.get_preventivo_by_id(preventivo[0])
            if not prev_completo:
                continue

            id_prev = prev_completo['id']
            nome_cliente = prev_completo.get('nome_cliente', '')
            misura = prev_completo.get('misura', '')
            descrizione = prev_completo.get('descrizione', '')
            numero_revisione = prev_completo.get('numero_revisione', 1)
            storico_modifiche = prev_completo.get('storico_modifiche', [])

            # APPLICA FILTRO TIPO
            if filtro_origine_text == "Originali" and numero_revisione != 1:
                continue
            elif filtro_origine_text == "Revisionati" and numero_revisione == 1:
                continue

            # APPLICA FILTRO CLIENTE
            if filtro_cliente_data and nome_cliente.strip() != filtro_cliente_data:
                continue

            # APPLICA FILTRO CATEGORIA
            categoria = prev_completo.get('categoria', '') or ''
            if filtro_categoria_data and categoria.strip() != filtro_categoria_data:
                continue

            # APPLICA FILTRO SOTTOCATEGORIA
            sottocategoria = prev_completo.get('sottocategoria', '') or ''
            if filtro_sottocategoria_data and sottocategoria.strip() != filtro_sottocategoria_data:
                continue

            # APPLICA FILTRO KEYWORD
            if filtro_keyword_text:
                campi_ricerca = [
                    str(id_prev), str(nome_cliente), str(misura), str(descrizione)
                ]
                testo_completo = " ".join(campi_ricerca).lower()
                if filtro_keyword_text not in testo_completo:
                    continue

            # Determina il tipo tra parentesi
            tipo_preventivo = "Originale" if numero_revisione == 1 else "Revisionato"

            # Aggiungi badge modifiche se presenti
            badge_modifiche = ""
            if storico_modifiche and len(storico_modifiche) > 0:
                badge_modifiche = f"/Con modifiche"

            # Formatta visualizzazione PULITA
            # Riga 1: #ID [Tipo] - Cliente: NOME
            cliente_display = nome_cliente if nome_cliente else "Senza nome"
            riga1 = f"#{id_prev:03d} [{tipo_preventivo}{badge_modifiche}] - Cliente: {cliente_display}"

            # Riga 2: Misura: XXX | Descrizione: YYY
            misura_display = misura if misura else "N/D"
            desc_display = descrizione[:80] + "..." if len(descrizione) > 80 else descrizione
            desc_display = desc_display if desc_display else "Nessuna descrizione"
            riga2 = f"Misura: {misura_display} | Descrizione: {desc_display}"

            testo = f"{riga1}\n{riga2}"

            item = QListWidgetItem(testo)
            item.setData(Qt.UserRole, id_prev)
            self.lista_preventivi.addItem(item)
            count += 1

        # Aggiorna conteggio
        self.lbl_conteggio.setText(f"{count} preventivi visualizzati")

    def visualizza_preventivo(self) -> None:
        """Visualizza i dettagli del preventivo selezionato"""
        current_item = self.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo da visualizzare.")
            return

        preventivo_id = current_item.data(Qt.UserRole)

        # Importa qui per evitare circular import
        from ui.preventivo_window import PreventivoWindow

        self.preventivo_window = PreventivoWindow(
            self.db_manager,
            self,
            preventivo_id=preventivo_id,
            modalita='visualizza'
        )
        self.preventivo_window.preventivo_salvato.connect(self.on_preventivo_modificato)
        self.preventivo_window.show()

    def modifica_preventivo(self) -> None:
        """Apre un preventivo per la modifica DIRETTA (con versioning)"""
        current_item = self.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo da modificare.")
            return

        preventivo_id = current_item.data(Qt.UserRole)

        from ui.preventivo_window import PreventivoWindow

        self.preventivo_window = PreventivoWindow(
            self.db_manager,
            self,
            preventivo_id=preventivo_id,
            modalita='modifica'
        )
        self.preventivo_window.preventivo_salvato.connect(self.on_preventivo_modificato)
        self.preventivo_window.show()

    def crea_revisione(self) -> None:
        """Crea una revisione di un preventivo esistente"""
        current_item = self.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo per creare una revisione.")
            return

        preventivo_id = current_item.data(Qt.UserRole)

        # Dialog per note revisione
        from ui.main_window_business_logic import MainWindowBusinessLogic
        note_revisione = MainWindowBusinessLogic.richiedi_note_revisione(self)
        if note_revisione is None:
            return

        from ui.preventivo_window import PreventivoWindow

        self.preventivo_window = PreventivoWindow(
            self.db_manager,
            self,
            preventivo_id=preventivo_id,
            modalita='revisione',
            note_revisione=note_revisione
        )
        self.preventivo_window.preventivo_salvato.connect(self.on_preventivo_modificato)
        self.preventivo_window.show()

    def visualizza_modifiche(self) -> None:
        """NUOVO: Apre il dialog per visualizzare lo storico modifiche"""
        current_item = self.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo per visualizzare le modifiche.")
            return

        preventivo_id = current_item.data(Qt.UserRole)

        # Verifica se il preventivo ha modifiche
        storico = self.db_manager.get_storico_modifiche(preventivo_id)
        if not storico:
            QMessageBox.information(self, "Info", "Questo preventivo non ha modifiche nello storico.")
            return

        # Importa e apri il dialog
        from ui.visualizza_modifiche_dialog import VisualizzaModificheDialog

        dialog = VisualizzaModificheDialog(self.db_manager, preventivo_id, self)
        dialog.versione_ripristinata.connect(self.on_preventivo_modificato)
        dialog.exec_()

    def confronta_preventivi(self) -> None:
        """Apre la finestra confronto preventivi"""
        from ui.confronto_preventivi_window import ConfrontoPreventiviWindow

        confronto_window = ConfrontoPreventiviWindow(self.db_manager, self)
        confronto_window.show()

    def anteprima_documento(self) -> None:
        """Mostra anteprima del documento nel browser senza salvarlo"""
        current_item = self.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo dalla lista per visualizzare l'anteprima.")
            return

        from ui.main_window_business_logic import MainWindowBusinessLogic
        MainWindowBusinessLogic.anteprima_documento_preventivo(self)

    def genera_documento(self) -> None:
        """Genera documento dal preventivo selezionato"""
        current_item = self.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo dalla lista per generare il documento.")
            return

        # Usa la stessa logica di MainWindowBusinessLogic
        from ui.main_window_business_logic import MainWindowBusinessLogic

        # self ha già db_manager e lista_preventivi come attributi (è un QMainWindow)
        MainWindowBusinessLogic.genera_documento_preventivo(self)

    def elimina_preventivo(self) -> None:
        """Elimina il preventivo selezionato"""
        current_item = self.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo da eliminare.")
            return

        preventivo_id = current_item.data(Qt.UserRole)

        # Determina se è una revisione o l'originale per mostrare il messaggio corretto
        prev_data = self.db_manager.get_preventivo_by_id(preventivo_id)
        is_revisione = prev_data is not None and prev_data.get('preventivo_originale_id') is not None

        if is_revisione:
            testo_conferma = "Sei sicuro di voler eliminare questa revisione?\n\nSolo questa revisione verrà eliminata. Il preventivo originale e le altre revisioni rimarranno invariati."
            testo_successo = "Revisione eliminata con successo."
        else:
            revisioni = self.db_manager.get_revisioni_preventivo(preventivo_id)
            # get_revisioni_preventivo restituisce originale + revisioni, quindi le revisioni sono len-1
            n_revisioni = max(0, len(revisioni) - 1)
            if n_revisioni > 0:
                avviso = f"\n\nAttenzione: questo preventivo ha {n_revisioni} revision{'e' if n_revisioni == 1 else 'i'} collegate che verranno eliminate insieme ad esso."
            else:
                avviso = ""
            testo_conferma = f"Sei sicuro di voler eliminare questo preventivo?{avviso}\n\nQuesta azione non può essere annullata."
            testo_successo = "Preventivo e tutte le sue revisioni sono stati eliminati con successo." if n_revisioni > 0 else "Preventivo eliminato con successo."

        # Dialog di conferma
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Conferma Eliminazione")
        dialog.setText(testo_conferma)
        dialog.setIcon(QMessageBox.Question)
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)

        risposta = dialog.exec_()

        if risposta == QMessageBox.Yes:
            if self.db_manager.delete_preventivo_e_revisioni(preventivo_id):
                QMessageBox.information(self, "Successo", testo_successo)
                self.load_preventivi()
                self.preventivo_modificato.emit()
            else:
                QMessageBox.critical(self, "Errore",
                                "Errore durante l'eliminazione del preventivo.")

    def on_preventivo_modificato(self) -> None:
        """Callback quando un preventivo viene modificato"""
        self.load_clienti_filtro()
        self.load_categorie_filtro()
        self.load_sottocategorie_filtro()
        self.load_preventivi()
        self.preventivo_modificato.emit()
