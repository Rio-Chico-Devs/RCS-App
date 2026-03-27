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
                             QTableWidgetItem, QMessageBox, QGroupBox,
                             QHeaderView, QDialog, QFormLayout,
                             QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor


class AnagraficaClientiWindow(QMainWindow):
    """Finestra per la gestione dell'anagrafica clienti"""

    cliente_aggiunto = pyqtSignal(str)

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
            QLineEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #ffffff;
                font-size: 14px;
                color: #2d3748;
            }
            QLineEdit:focus { border-color: #4a5568; }
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                font-size: 14px;
                gridline-color: #f7fafc;
            }
            QTableWidget::item { padding: 12px; color: #2d3748; }
            QTableWidget::item:selected {
                background-color: #edf2f7;
                color: #2d3748;
            }
            QHeaderView::section {
                background-color: #f7fafc;
                color: #4a5568;
                font-weight: 600;
                padding: 12px;
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
        main_layout.setContentsMargins(60, 40, 60, 40)
        main_layout.setSpacing(24)

        # Header
        header = QLabel("Anagrafica Clienti")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 28px; font-weight: 700; color: #2d3748; padding: 10px 0;")
        main_layout.addWidget(header)

        # Card principale
        card = QGroupBox()
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 12))
        shadow.setOffset(0, 2)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(16)

        # Barra azioni: search + input nuovo + pulsanti
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)

        self.search_clienti = QLineEdit()
        self.search_clienti.setPlaceholderText("Cerca cliente...")
        self.search_clienti.textChanged.connect(self._filtra_clienti)
        actions_row.addWidget(self.search_clienti, 1)

        self.edit_nuovo_nome = QLineEdit()
        self.edit_nuovo_nome.setPlaceholderText("Nome nuovo cliente...")
        actions_row.addWidget(self.edit_nuovo_nome, 1)

        self.btn_aggiungi = QPushButton("Aggiungi")
        self.btn_aggiungi.setStyleSheet("""
            QPushButton { background-color: #4a5568; color: #ffffff; }
            QPushButton:hover { background-color: #2d3748; }
        """)
        self.btn_aggiungi.clicked.connect(self._aggiungi_cliente)
        actions_row.addWidget(self.btn_aggiungi)

        self.btn_rinomina = QPushButton("Rinomina")
        self.btn_rinomina.setEnabled(False)
        self.btn_rinomina.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; }
            QPushButton:hover { background-color: #edf2f7; }
            QPushButton:disabled { color: #a0aec0; }
        """)
        self.btn_rinomina.clicked.connect(self._rinomina_cliente)
        actions_row.addWidget(self.btn_rinomina)

        self.btn_elimina = QPushButton("Elimina")
        self.btn_elimina.setEnabled(False)
        self.btn_elimina.setStyleSheet("""
            QPushButton { background-color: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; }
            QPushButton:hover { background-color: #fed7d7; color: #c53030; border-color: #fc8181; }
            QPushButton:disabled { color: #a0aec0; }
        """)
        self.btn_elimina.clicked.connect(self._elimina_cliente)
        actions_row.addWidget(self.btn_elimina)

        card_layout.addLayout(actions_row)

        # Tabella: Nome | N° Preventivi
        self.table_clienti = QTableWidget()
        self.table_clienti.setColumnCount(2)
        self.table_clienti.setHorizontalHeaderLabels(["Nome Cliente", "Preventivi"])
        self.table_clienti.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_clienti.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_clienti.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_clienti.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_clienti.setAlternatingRowColors(True)
        self.table_clienti.verticalHeader().setVisible(False)
        self.table_clienti.itemSelectionChanged.connect(self._on_selezione)
        card_layout.addWidget(self.table_clienti, 1)

        main_layout.addWidget(card, 1)

    def _carica_clienti(self):
        self._tutti_clienti = self.db_manager.get_all_clienti()
        self._aggiorna_tabella(self._tutti_clienti)

    def _aggiorna_tabella(self, clienti):
        self.table_clienti.setRowCount(0)
        for row_data in clienti:
            # row_data: (id, nome, n_preventivi)
            row = self.table_clienti.rowCount()
            self.table_clienti.insertRow(row)
            nome_item = QTableWidgetItem(row_data[1])
            nome_item.setData(Qt.UserRole, row_data[0])
            self.table_clienti.setItem(row, 0, nome_item)
            count_item = QTableWidgetItem(str(row_data[2]))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.table_clienti.setItem(row, 1, count_item)

    def _filtra_clienti(self, testo):
        testo = testo.lower().strip()
        if not testo:
            self._aggiorna_tabella(self._tutti_clienti)
        else:
            filtrati = [c for c in self._tutti_clienti if testo in c[1].lower()]
            self._aggiorna_tabella(filtrati)

    def _on_selezione(self):
        selected = self.table_clienti.selectedItems()
        ha_selezione = bool(selected)
        self.btn_elimina.setEnabled(ha_selezione)
        self.btn_rinomina.setEnabled(ha_selezione)
        if ha_selezione:
            row = self.table_clienti.currentRow()
            self.cliente_selezionato_id = self.table_clienti.item(row, 0).data(Qt.UserRole)
            self.edit_nuovo_nome.setText(self.table_clienti.item(row, 0).text())
        else:
            self.cliente_selezionato_id = None

    def _aggiungi_cliente(self):
        nome = self.edit_nuovo_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Attenzione", "Inserisci il nome del cliente.")
            return
        if len(nome) > 100:
            QMessageBox.warning(self, "Attenzione", "Il nome del cliente non può superare 100 caratteri.")
            return
        result = self.db_manager.add_cliente(nome)
        if result is False:
            QMessageBox.warning(self, "Errore", f"Un cliente con nome '{nome}' esiste già.")
            return
        self.edit_nuovo_nome.clear()
        self.cliente_aggiunto.emit(nome)
        self._carica_clienti()

    def _rinomina_cliente(self):
        if self.cliente_selezionato_id is None:
            return
        nuovo_nome = self.edit_nuovo_nome.text().strip()
        if not nuovo_nome:
            QMessageBox.warning(self, "Attenzione", "Inserisci il nuovo nome.")
            return
        ok = self.db_manager.update_cliente(self.cliente_selezionato_id, nuovo_nome)
        if ok is False:
            QMessageBox.warning(self, "Errore", f"Un cliente con nome '{nuovo_nome}' esiste già.")
            return
        self._carica_clienti()

    def _elimina_cliente(self):
        if self.cliente_selezionato_id is None:
            return
        row = self.table_clienti.currentRow()
        nome = self.table_clienti.item(row, 0).text()
        n_prev = int(self.table_clienti.item(row, 1).text())
        msg = f"Eliminare il cliente '{nome}'?"
        if n_prev > 0:
            msg += f"\n\nAttenzione: ha {n_prev} preventivi associati (non verranno eliminati)."
        reply = QMessageBox.question(self, "Conferma eliminazione", msg,
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_manager.delete_cliente(self.cliente_selezionato_id)
            self.cliente_selezionato_id = None
            self.btn_elimina.setEnabled(False)
            self.btn_rinomina.setEnabled(False)
            self.edit_nuovo_nome.clear()
            self._carica_clienti()


class NuovoClienteQuickDialog(QDialog):
    """Dialog rapido per aggiungere un nuovo cliente direttamente dal preventivo"""

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.nome_aggiunto = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Nuovo Cliente")
        self.setFixedWidth(380)
        self.setStyleSheet("""
            QDialog { background-color: #fafbfc; }
            QLabel { font-size: 14px; color: #2d3748; font-weight: 500; }
            QLineEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                color: #2d3748;
                background-color: #ffffff;
            }
            QLineEdit:focus { border-color: #4a5568; }
            QPushButton {
                border: none; border-radius: 6px;
                font-size: 14px; font-weight: 600;
                padding: 10px 20px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(QLabel("Nome del nuovo cliente:"))

        self.edit_nome = QLineEdit()
        self.edit_nome.setPlaceholderText("Es. Rossi S.r.l.")
        layout.addWidget(self.edit_nome)

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
        if len(nome) > 100:
            QMessageBox.warning(self, "Attenzione", "Il nome del cliente non può superare 100 caratteri.")
            return
        result = self.db_manager.add_cliente(nome)
        if result is False:
            QMessageBox.warning(self, "Errore", f"Un cliente con nome '{nome}' esiste già.")
            return
        self.nome_aggiunto = nome
        self.accept()
