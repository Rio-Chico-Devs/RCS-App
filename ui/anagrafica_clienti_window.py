#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Anagrafica Clienti - Gestione anagrafica clienti
Uso riservato esclusivamente a RCS
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

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QTableWidget,
                             QTableWidgetItem, QMessageBox, QGroupBox, QFormLayout,
                             QFrame, QHeaderView, QDialog, QDialogButtonBox,
                             QTextEdit, QSizePolicy, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor


class AnagraficaClientiWindow(QMainWindow):
    """Finestra per la gestione dell'anagrafica clienti"""

    cliente_aggiunto = pyqtSignal(str)  # emette il nome del nuovo cliente

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.cliente_selezionato_id = None
        self._setup_ui()
        self._carica_clienti()

    def _setup_ui(self):
        self.setWindowTitle("Anagrafica Clienti")
        self.showMaximized()
        self.setStyleSheet("""
            QMainWindow { background-color: #fafbfc; }
            QLabel {
                color: #2d3748;
                font-family: system-ui, -apple-system, sans-serif;
                font-size: 14px;
                font-weight: 500;
            }
            QGroupBox {
                font-size: 15px;
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
            QLineEdit, QTextEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #ffffff;
                font-size: 14px;
                color: #2d3748;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #4a5568;
            }
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                font-size: 14px;
                gridline-color: #f7fafc;
            }
            QTableWidget::item {
                padding: 10px;
                color: #2d3748;
            }
            QTableWidget::item:selected {
                background-color: #edf2f7;
                color: #2d3748;
            }
            QHeaderView::section {
                background-color: #f7fafc;
                color: #4a5568;
                font-weight: 600;
                padding: 10px;
                border: none;
                border-bottom: 1px solid #e2e8f0;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 20px;
                font-family: system-ui, -apple-system, sans-serif;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)

        # Header
        header = QLabel("Anagrafica Clienti")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 28px; font-weight: 700; color: #2d3748; padding: 10px 0;")
        main_layout.addWidget(header)

        # Content: lista a sinistra, form a destra
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)

        # --- Lista clienti ---
        list_group = QGroupBox("Clienti")
        shadow1 = QGraphicsDropShadowEffect()
        shadow1.setBlurRadius(10)
        shadow1.setColor(QColor(0, 0, 0, 12))
        shadow1.setOffset(0, 2)
        list_group.setGraphicsEffect(shadow1)

        list_layout = QVBoxLayout(list_group)
        list_layout.setContentsMargins(20, 28, 20, 20)
        list_layout.setSpacing(12)

        # Search
        self.search_clienti = QLineEdit()
        self.search_clienti.setPlaceholderText("Cerca cliente...")
        self.search_clienti.textChanged.connect(self._filtra_clienti)
        list_layout.addWidget(self.search_clienti)

        # Tabella
        self.table_clienti = QTableWidget()
        self.table_clienti.setColumnCount(3)
        self.table_clienti.setHorizontalHeaderLabels(["Nome", "Email", "Telefono"])
        self.table_clienti.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_clienti.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_clienti.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_clienti.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_clienti.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_clienti.setAlternatingRowColors(True)
        self.table_clienti.verticalHeader().setVisible(False)
        self.table_clienti.itemSelectionChanged.connect(self._on_cliente_selezionato)
        list_layout.addWidget(self.table_clienti)

        # Buttons lista
        btn_layout_list = QHBoxLayout()
        self.btn_nuovo = QPushButton("Nuovo Cliente")
        self.btn_nuovo.setStyleSheet("""
            QPushButton { background-color: #4a5568; color: #ffffff; }
            QPushButton:hover { background-color: #2d3748; }
        """)
        self.btn_nuovo.clicked.connect(self._nuovo_cliente)

        self.btn_elimina = QPushButton("Elimina")
        self.btn_elimina.setEnabled(False)
        self.btn_elimina.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; }
            QPushButton:hover { background-color: #fed7d7; color: #c53030; border-color: #fc8181; }
            QPushButton:disabled { color: #a0aec0; }
        """)
        self.btn_elimina.clicked.connect(self._elimina_cliente)

        btn_layout_list.addWidget(self.btn_nuovo)
        btn_layout_list.addStretch()
        btn_layout_list.addWidget(self.btn_elimina)
        list_layout.addLayout(btn_layout_list)

        content_layout.addWidget(list_group, 1)

        # --- Form dettaglio ---
        self.form_group = QGroupBox("Dettaglio Cliente")
        shadow2 = QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(10)
        shadow2.setColor(QColor(0, 0, 0, 12))
        shadow2.setOffset(0, 2)
        self.form_group.setGraphicsEffect(shadow2)

        form_layout = QVBoxLayout(self.form_group)
        form_layout.setContentsMargins(20, 28, 20, 20)
        form_layout.setSpacing(16)

        fields_form = QFormLayout()
        fields_form.setSpacing(12)
        fields_form.setLabelAlignment(Qt.AlignRight)

        self.edit_nome = QLineEdit()
        self.edit_nome.setPlaceholderText("Nome cliente (obbligatorio)")
        fields_form.addRow("Nome:", self.edit_nome)

        self.edit_email = QLineEdit()
        self.edit_email.setPlaceholderText("email@esempio.com")
        fields_form.addRow("Email:", self.edit_email)

        self.edit_telefono = QLineEdit()
        self.edit_telefono.setPlaceholderText("+39 000 0000000")
        fields_form.addRow("Telefono:", self.edit_telefono)

        self.edit_note = QTextEdit()
        self.edit_note.setPlaceholderText("Note aggiuntive...")
        self.edit_note.setMaximumHeight(120)
        fields_form.addRow("Note:", self.edit_note)

        form_layout.addLayout(fields_form)
        form_layout.addStretch()

        # Buttons form
        btn_layout_form = QHBoxLayout()
        self.btn_salva = QPushButton("Salva Cliente")
        self.btn_salva.setStyleSheet("""
            QPushButton { background-color: #4a5568; color: #ffffff; }
            QPushButton:hover { background-color: #2d3748; }
        """)
        self.btn_salva.clicked.connect(self._salva_cliente)

        self.btn_annulla = QPushButton("Annulla")
        self.btn_annulla.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        self.btn_annulla.clicked.connect(self._annulla)

        btn_layout_form.addStretch()
        btn_layout_form.addWidget(self.btn_annulla)
        btn_layout_form.addWidget(self.btn_salva)
        form_layout.addLayout(btn_layout_form)

        content_layout.addWidget(self.form_group, 1)

        main_layout.addLayout(content_layout, 1)

        self._imposta_form_vuoto()

    def _carica_clienti(self):
        """Carica tutti i clienti nella tabella"""
        self._tutti_clienti = self.db_manager.get_all_clienti()
        self._aggiorna_tabella(self._tutti_clienti)

    def _aggiorna_tabella(self, clienti):
        self.table_clienti.setRowCount(0)
        for row_data in clienti:
            row = self.table_clienti.rowCount()
            self.table_clienti.insertRow(row)
            self.table_clienti.setItem(row, 0, QTableWidgetItem(row_data[1]))  # nome
            self.table_clienti.setItem(row, 1, QTableWidgetItem(row_data[2] or ""))  # email
            self.table_clienti.setItem(row, 2, QTableWidgetItem(row_data[3] or ""))  # telefono
            # Salva id nella colonna nascosta tramite UserRole
            self.table_clienti.item(row, 0).setData(Qt.UserRole, row_data[0])

    def _filtra_clienti(self, testo):
        testo = testo.lower().strip()
        if not testo:
            self._aggiorna_tabella(self._tutti_clienti)
        else:
            filtrati = [c for c in self._tutti_clienti if testo in c[1].lower()]
            self._aggiorna_tabella(filtrati)

    def _on_cliente_selezionato(self):
        selected = self.table_clienti.selectedItems()
        if not selected:
            self.cliente_selezionato_id = None
            self.btn_elimina.setEnabled(False)
            self._imposta_form_vuoto()
            return

        row = self.table_clienti.currentRow()
        cliente_id = self.table_clienti.item(row, 0).data(Qt.UserRole)
        self.cliente_selezionato_id = cliente_id

        cliente = self.db_manager.get_cliente_by_id(cliente_id)
        if cliente:
            self.edit_nome.setText(cliente[1] or "")
            self.edit_email.setText(cliente[2] or "")
            self.edit_telefono.setText(cliente[3] or "")
            self.edit_note.setPlainText(cliente[4] or "")
        self.btn_elimina.setEnabled(True)

    def _imposta_form_vuoto(self):
        self.edit_nome.clear()
        self.edit_email.clear()
        self.edit_telefono.clear()
        self.edit_note.clear()

    def _nuovo_cliente(self):
        self.table_clienti.clearSelection()
        self.cliente_selezionato_id = None
        self._imposta_form_vuoto()
        self.btn_elimina.setEnabled(False)
        self.edit_nome.setFocus()

    def _salva_cliente(self):
        nome = self.edit_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Attenzione", "Il nome del cliente è obbligatorio.")
            return

        email = self.edit_email.text().strip()
        telefono = self.edit_telefono.text().strip()
        note = self.edit_note.toPlainText().strip()

        if self.cliente_selezionato_id is not None:
            # Aggiorna esistente
            ok = self.db_manager.update_cliente(self.cliente_selezionato_id, nome, email, telefono, note)
            if ok is False:
                QMessageBox.warning(self, "Errore", f"Un cliente con nome '{nome}' esiste già.")
                return
        else:
            # Nuovo cliente
            result = self.db_manager.add_cliente(nome, email, telefono, note)
            if result is False:
                QMessageBox.warning(self, "Errore", f"Un cliente con nome '{nome}' esiste già.")
                return
            self.cliente_aggiunto.emit(nome)

        self._carica_clienti()

    def _elimina_cliente(self):
        if self.cliente_selezionato_id is None:
            return
        nome = self.edit_nome.text().strip()
        reply = QMessageBox.question(
            self, "Conferma eliminazione",
            f"Eliminare il cliente '{nome}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db_manager.delete_cliente(self.cliente_selezionato_id)
            self.cliente_selezionato_id = None
            self.btn_elimina.setEnabled(False)
            self._imposta_form_vuoto()
            self._carica_clienti()

    def _annulla(self):
        self.table_clienti.clearSelection()
        self.cliente_selezionato_id = None
        self._imposta_form_vuoto()
        self.btn_elimina.setEnabled(False)


class NuovoClienteQuickDialog(QDialog):
    """Dialog rapido per aggiungere un nuovo cliente direttamente dal preventivo"""

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.nome_aggiunto = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Nuovo Cliente")
        self.setFixedWidth(420)
        self.setStyleSheet("""
            QDialog { background-color: #fafbfc; }
            QLabel { font-size: 14px; color: #2d3748; font-weight: 500; }
            QLineEdit, QTextEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                color: #2d3748;
                background-color: #ffffff;
            }
            QLineEdit:focus, QTextEdit:focus { border-color: #4a5568; }
            QPushButton {
                border: none; border-radius: 6px;
                font-size: 14px; font-weight: 600;
                padding: 10px 20px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(QLabel("Aggiungi nuovo cliente"))

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        self.edit_nome = QLineEdit()
        self.edit_nome.setPlaceholderText("Nome cliente (obbligatorio)")
        form.addRow("Nome:", self.edit_nome)

        self.edit_email = QLineEdit()
        self.edit_email.setPlaceholderText("email@esempio.com")
        form.addRow("Email:", self.edit_email)

        self.edit_telefono = QLineEdit()
        self.edit_telefono.setPlaceholderText("+39 000 0000000")
        form.addRow("Telefono:", self.edit_telefono)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_annulla = QPushButton("Annulla")
        btn_annulla.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_annulla.clicked.connect(self.reject)

        btn_salva = QPushButton("Aggiungi")
        btn_salva.setStyleSheet("""
            QPushButton { background-color: #4a5568; color: #ffffff; }
            QPushButton:hover { background-color: #2d3748; }
        """)
        btn_salva.clicked.connect(self._salva)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_annulla)
        btn_layout.addWidget(btn_salva)
        layout.addLayout(btn_layout)

    def _salva(self):
        nome = self.edit_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Attenzione", "Il nome del cliente è obbligatorio.")
            return
        email = self.edit_email.text().strip()
        telefono = self.edit_telefono.text().strip()
        result = self.db_manager.add_cliente(nome, email, telefono)
        if result is False:
            QMessageBox.warning(self, "Errore", f"Un cliente con nome '{nome}' esiste già.")
            return
        self.nome_aggiunto = nome
        self.accept()
