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
                             QWidget, QLabel, QTableWidget, QTableWidgetItem,
                             QMessageBox, QGroupBox, QFrame, QGraphicsDropShadowEffect,
                             QLineEdit, QComboBox, QAbstractItemView, QSizePolicy,
                             QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from typing import Optional, Any
from ui.responsive import get_metrics

class VisualizzaPreventiviWindow(QMainWindow):
    preventivo_modificato = pyqtSignal()  # Signal per notificare modifiche

    def __init__(self, db_manager: Any, parent: Optional[QWidget] = None) -> None:
        super().__init__(None)  # No parent per evitare bug ridimensionamento
        self.db_manager = db_manager
        self.parent_window = parent
        self.init_ui()
        self.load_clienti_filtro()
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
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                font-size: 13px;
                font-family: system-ui, -apple-system, sans-serif;
                gridline-color: #f0f4f8;
            }
            QTableWidget::item {
                padding: 6px 10px;
                color: #2d3748;
                border: none;
            }
            QTableWidget::item:hover {
                background-color: #ebf4ff;
            }
            QTableWidget::item:selected {
                background-color: #3b82f6;
                color: #ffffff;
            }
            QTableWidget::item:selected:hover {
                background-color: #2563eb;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #f7fafc;
                color: #4a5568;
                font-size: 12px;
                font-weight: 600;
                padding: 8px 10px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                border-right: 1px solid #e2e8f0;
            }
            QLineEdit, QComboBox {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                background-color: #ffffff;
                color: #2d3748;
                min-height: 16px;
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
                font-size: 13px;
                font-weight: 600;
                padding: 8px 16px;
                font-family: system-ui, -apple-system, sans-serif;
            }
        """)

        # Widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principale - margini ridotti per mostrare tutto
        _m = get_metrics()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(_m['mi'], _m['sf'], _m['mi'], _m['sf'])
        main_layout.setSpacing(_m['sf'])

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
        _hm = get_metrics()
        title_label = QLabel("Visualizza Preventivi")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {_hm['ft']}px;
                font-weight: 700;
                color: #2d3748;
                padding: 0;
            }}
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
        self.filtro_origine.setMinimumWidth(110 if get_metrics()['small'] else 140)

        filters_layout.addWidget(tipo_label)
        filters_layout.addWidget(self.filtro_origine)

        # Filtro Cliente
        cliente_label = QLabel("Cliente:")
        cliente_label.setStyleSheet("QLabel { font-weight: 500; color: #4a5568; }")
        self.filtro_cliente = QComboBox()
        self.filtro_cliente.addItem("Tutti i clienti", None)
        self.filtro_cliente.currentIndexChanged.connect(self.load_preventivi)
        self.filtro_cliente.setMinimumWidth(140 if get_metrics()['small'] else 180)

        filters_layout.addWidget(cliente_label)
        filters_layout.addWidget(self.filtro_cliente)

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
        """Tabella preventivi a tutta larghezza con nota sotto"""
        lista_group = QGroupBox("Preventivi")
        lista_group.setGraphicsEffect(self.create_shadow_effect())

        _lm = get_metrics()
        lista_layout = QVBoxLayout(lista_group)
        lista_layout.setContentsMargins(_lm['sf'], _lm['mi'], _lm['sf'], _lm['sf'])
        lista_layout.setSpacing(_lm['sf'])

        # Tabella principale
        self.lista_preventivi = QTableWidget()
        self.lista_preventivi.setColumnCount(7)
        self.lista_preventivi.setHorizontalHeaderLabels([
            "#", "Tipo", "Cliente", "Misura",
            "Descrizione", "Prev. €", "Prezzo €"
        ])
        self.lista_preventivi.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lista_preventivi.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lista_preventivi.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lista_preventivi.verticalHeader().setVisible(False)
        self.lista_preventivi.setShowGrid(False)          # niente griglia → riga = blocco unico
        self.lista_preventivi.setAlternatingRowColors(True)
        self.lista_preventivi.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lista_preventivi.setMinimumHeight(get_metrics()['dh'] // 4)

        hdr = self.lista_preventivi.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)   # #
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)   # Tipo
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)   # Cliente
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)   # Misura
        hdr.setSectionResizeMode(4, QHeaderView.Stretch)            # Descrizione (più lunga)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)   # Prev €
        hdr.setSectionResizeMode(6, QHeaderView.ResizeToContents)   # Prezzo €

        self.lista_preventivi.doubleClicked.connect(self.visualizza_preventivo)
        self.lista_preventivi.currentItemChanged.connect(self._on_selezione_cambiata)
        lista_layout.addWidget(self.lista_preventivi)

        # Area nota revisione (sotto la tabella)
        self.note_frame = QFrame()
        self.note_frame.setStyleSheet("""
            QFrame {
                background-color: #fffbeb;
                border: 1px solid #f6e05e;
                border-radius: 6px;
                padding: 2px;
            }
        """)
        note_row = QHBoxLayout(self.note_frame)
        note_row.setContentsMargins(12, 6, 12, 6)
        note_row.setSpacing(8)
        note_lbl = QLabel("Note revisione:")
        note_lbl.setStyleSheet("QLabel { font-weight: 600; color: #744210; font-size: 12px; min-width: 110px; }")
        self.lbl_nota_corrente = QLabel("—")
        self.lbl_nota_corrente.setWordWrap(True)
        self.lbl_nota_corrente.setStyleSheet("QLabel { color: #744210; font-size: 12px; }")
        note_row.addWidget(note_lbl)
        note_row.addWidget(self.lbl_nota_corrente, 1)
        lista_layout.addWidget(self.note_frame)

        # Conteggio
        self.lbl_conteggio = QLabel("0 preventivi caricati")
        self.lbl_conteggio.setStyleSheet("QLabel { color: #718096; font-size: 13px; font-weight: 500; }")
        lista_layout.addWidget(self.lbl_conteggio)

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

    def _get_current_preventivo_id(self):
        """Restituisce l'id del preventivo della riga selezionata nella tabella, o None"""
        item = self.lista_preventivi.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _on_selezione_cambiata(self, current, previous) -> None:
        """Aggiorna la nota revisione quando cambia la selezione"""
        if current is None:
            self.lbl_nota_corrente.setText("—")
            return
        row = self.lista_preventivi.currentRow()
        if row < 0:
            self.lbl_nota_corrente.setText("—")
            return
        id_item = self.lista_preventivi.item(row, 0)
        if not id_item:
            self.lbl_nota_corrente.setText("—")
            return
        preventivo_id = id_item.data(Qt.UserRole)
        prev = self.db_manager.get_preventivo_by_id(preventivo_id)
        nota = (prev.get('note_revisione') or '').strip() if prev else ''
        self.lbl_nota_corrente.setText(nota if nota else "—")

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
        self.lista_preventivi.setRowCount(0)
        self.lbl_nota_corrente.setText("—")

        # Ottieni i valori dei filtri
        filtro_origine_text = self.filtro_origine.currentText()
        filtro_cliente_data = self.filtro_cliente.currentData()
        filtro_keyword_text = self.filtro_keyword.text().lower().strip()

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

            # APPLICA FILTRO KEYWORD
            if filtro_keyword_text:
                campi_ricerca = [
                    str(id_prev), str(nome_cliente), str(misura), str(descrizione)
                ]
                testo_completo = " ".join(campi_ricerca).lower()
                if filtro_keyword_text not in testo_completo:
                    continue

            # Tipo con badge modifiche
            tipo_preventivo = "Originale" if numero_revisione == 1 else f"Rev.#{numero_revisione}"
            if storico_modifiche and len(storico_modifiche) > 0:
                tipo_preventivo += " ✎"

            # Prezzi
            p_finale = prev_completo.get('preventivo_finale')
            p_cliente = prev_completo.get('prezzo_cliente')
            prev_str = f"€ {p_finale:.2f}" if p_finale is not None else "—"
            prezzo_str = f"€ {p_cliente:.2f}" if p_cliente is not None else "—"

            # Aggiungi riga alla tabella
            row_idx = self.lista_preventivi.rowCount()
            self.lista_preventivi.insertRow(row_idx)

            def make_cell(text, align=Qt.AlignVCenter | Qt.AlignLeft):
                cell = QTableWidgetItem(str(text) if text else "")
                cell.setTextAlignment(align)
                cell.setData(Qt.UserRole, id_prev)  # id in ogni cella → compatibile con currentItem()
                return cell

            self.lista_preventivi.setItem(row_idx, 0, make_cell(f"#{id_prev:03d}", align=Qt.AlignCenter))
            self.lista_preventivi.setItem(row_idx, 1, make_cell(tipo_preventivo))
            self.lista_preventivi.setItem(row_idx, 2, make_cell(nome_cliente or "—"))
            self.lista_preventivi.setItem(row_idx, 3, make_cell(misura or "—"))
            self.lista_preventivi.setItem(row_idx, 4, make_cell(descrizione or "—"))
            self.lista_preventivi.setItem(row_idx, 5, make_cell(prev_str, align=Qt.AlignRight | Qt.AlignVCenter))
            self.lista_preventivi.setItem(row_idx, 6, make_cell(prezzo_str, align=Qt.AlignRight | Qt.AlignVCenter))
            count += 1

        self.lista_preventivi.resizeRowsToContents()
        # Aggiorna conteggio
        self.lbl_conteggio.setText(f"{count} preventivi visualizzati")

    def visualizza_preventivo(self) -> None:
        """Visualizza i dettagli del preventivo selezionato"""
        preventivo_id = self._get_current_preventivo_id()
        if preventivo_id is None:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo da visualizzare.")
            return

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
        preventivo_id = self._get_current_preventivo_id()
        if preventivo_id is None:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo da modificare.")
            return

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
        preventivo_id = self._get_current_preventivo_id()
        if preventivo_id is None:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo per creare una revisione.")
            return

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
        preventivo_id = self._get_current_preventivo_id()
        if preventivo_id is None:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo per visualizzare le modifiche.")
            return

        storico = self.db_manager.get_storico_modifiche(preventivo_id)
        if not storico:
            QMessageBox.information(self, "Info", "Questo preventivo non ha modifiche nello storico.")
            return

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
        if self._get_current_preventivo_id() is None:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo dalla lista per visualizzare l'anteprima.")
            return

        from ui.main_window_business_logic import MainWindowBusinessLogic
        MainWindowBusinessLogic.anteprima_documento_preventivo(self)

    def genera_documento(self) -> None:
        """Genera documento dal preventivo selezionato"""
        if self._get_current_preventivo_id() is None:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo dalla lista per generare il documento.")
            return

        from ui.main_window_business_logic import MainWindowBusinessLogic
        MainWindowBusinessLogic.genera_documento_preventivo(self)

    def elimina_preventivo(self) -> None:
        """Elimina il preventivo selezionato"""
        preventivo_id = self._get_current_preventivo_id()
        if preventivo_id is None:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo da eliminare.")
            return

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
        self.load_preventivi()
        self.preventivo_modificato.emit()
