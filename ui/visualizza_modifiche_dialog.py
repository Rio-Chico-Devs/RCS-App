#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Dialog Visualizzazione Modifiche Preventivo - Sistema di Versioning
Uso riservato esclusivamente a RCS

Version: 1.0.0
Last Updated: 2026-02-07
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

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QListWidget, QListWidgetItem, QMessageBox,
                             QFrame, QGraphicsDropShadowEffect, QGroupBox,
                             QTextEdit, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from datetime import datetime
import json
from typing import Any, Optional


class VisualizzaModificheDialog(QDialog):
    """Dialog per visualizzare e gestire le modifiche di un preventivo"""

    versione_ripristinata = pyqtSignal()

    def __init__(self, db_manager: Any, preventivo_id: int, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.db_manager = db_manager
        self.preventivo_id = preventivo_id
        self.storico = []
        self.preventivo_corrente = None

        self.init_ui()
        self.load_storico()

    def init_ui(self) -> None:
        """Inizializza l'interfaccia"""
        self.setWindowTitle(f"Storico Modifiche - Preventivo #{self.preventivo_id:03d}")
        self.setModal(True)
        self.resize(1000, 700)

        # Stile unificato
        self.setStyleSheet("""
            QDialog {
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
            QTextEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                background-color: #ffffff;
                color: #2d3748;
                font-family: 'Courier New', monospace;
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

        # Layout principale
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # Header
        self.create_header(main_layout)

        # Info
        info_label = QLabel("Seleziona una versione per visualizzare i dettagli o ripristinarla")
        info_label.setStyleSheet("color: #718096; font-size: 13px;")
        main_layout.addWidget(info_label)

        # Splitter per lista e dettagli
        splitter = QSplitter(Qt.Horizontal)

        # Lista versioni
        lista_group = QGroupBox("Versioni Disponibili")
        lista_group.setGraphicsEffect(self.create_shadow_effect())
        lista_layout = QVBoxLayout(lista_group)
        lista_layout.setContentsMargins(15, 20, 15, 15)

        self.lista_versioni = QListWidget()
        self.lista_versioni.itemSelectionChanged.connect(self.on_versione_selezionata)
        lista_layout.addWidget(self.lista_versioni)

        splitter.addWidget(lista_group)

        # Dettagli versione
        dettagli_group = QGroupBox("Dettagli Versione")
        dettagli_group.setGraphicsEffect(self.create_shadow_effect())
        dettagli_layout = QVBoxLayout(dettagli_group)
        dettagli_layout.setContentsMargins(15, 20, 15, 15)

        self.text_dettagli = QTextEdit()
        self.text_dettagli.setReadOnly(True)
        dettagli_layout.addWidget(self.text_dettagli)

        splitter.addWidget(dettagli_group)

        # Proporzioni splitter
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        # Pulsanti azione
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
        """Header del dialog"""
        title_label = QLabel(f"Storico Modifiche - Preventivo #{self.preventivo_id:03d}")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: 700;
                color: #2d3748;
                padding: 0;
            }
        """)
        parent_layout.addWidget(title_label)

    def create_action_buttons(self, parent_layout: QVBoxLayout) -> None:
        """Pulsanti azioni"""
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        buttons_frame.setGraphicsEffect(self.create_shadow_effect())

        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setSpacing(12)

        # Confronta versioni
        self.btn_confronta = QPushButton("Confronta con Corrente")
        self.btn_confronta.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
            QPushButton:disabled {
                background-color: #f7fafc;
                color: #a0aec0;
            }
        """)
        self.btn_confronta.clicked.connect(self.confronta_con_corrente)
        self.btn_confronta.setEnabled(False)

        # Ripristina versione
        self.btn_ripristina = QPushButton("Ripristina Questa Versione")
        self.btn_ripristina.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
            QPushButton:disabled {
                background-color: #cbd5e0;
                color: #a0aec0;
            }
        """)
        self.btn_ripristina.clicked.connect(self.ripristina_versione)
        self.btn_ripristina.setEnabled(False)

        buttons_layout.addWidget(self.btn_confronta)
        buttons_layout.addWidget(self.btn_ripristina)
        buttons_layout.addStretch()

        parent_layout.addWidget(buttons_frame)

    def create_footer(self, parent_layout: QVBoxLayout) -> None:
        """Footer con pulsante chiudi"""
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        btn_chiudi = QPushButton("Chiudi")
        btn_chiudi.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: 32px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
        """)
        btn_chiudi.clicked.connect(self.accept)

        footer_layout.addWidget(btn_chiudi)
        parent_layout.addLayout(footer_layout)

    def load_storico(self) -> None:
        """Carica lo storico modifiche dal database"""
        self.storico = self.db_manager.get_storico_modifiche(self.preventivo_id)
        self.preventivo_corrente = self.db_manager.get_preventivo_by_id(self.preventivo_id)

        self.lista_versioni.clear()

        if not self.storico:
            item = QListWidgetItem("Nessuna modifica trovata")
            item.setFlags(Qt.NoItemFlags)
            self.lista_versioni.addItem(item)
            return

        # Aggiungi versione corrente
        item_corrente = QListWidgetItem("📌 VERSIONE CORRENTE")
        item_corrente.setData(Qt.UserRole, "corrente")
        item_corrente.setBackground(QColor("#f0fff4"))
        self.lista_versioni.addItem(item_corrente)

        # Aggiungi versioni nello storico
        for i, snapshot in enumerate(reversed(self.storico)):
            timestamp = snapshot.get('timestamp', 'Data sconosciuta')
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp_str = dt.strftime("%d/%m/%Y %H:%M:%S")
            except Exception:
                timestamp_str = timestamp

            testo = f"🕒 Versione #{len(self.storico) - i}\n{timestamp_str}"

            item = QListWidgetItem(testo)
            item.setData(Qt.UserRole, timestamp)
            self.lista_versioni.addItem(item)

    def on_versione_selezionata(self) -> None:
        """Gestisce selezione versione"""
        current_item = self.lista_versioni.currentItem()
        if not current_item:
            self.btn_confronta.setEnabled(False)
            self.btn_ripristina.setEnabled(False)
            return

        timestamp = current_item.data(Qt.UserRole)

        if timestamp == "corrente":
            # Versione corrente
            self.mostra_dettagli_corrente()
            self.btn_confronta.setEnabled(False)
            self.btn_ripristina.setEnabled(False)
        else:
            # Versione storico
            self.mostra_dettagli_versione(timestamp)
            self.btn_confronta.setEnabled(True)
            self.btn_ripristina.setEnabled(True)

    def mostra_dettagli_corrente(self) -> None:
        """Mostra dettagli della versione corrente"""
        if not self.preventivo_corrente:
            self.text_dettagli.setText("Errore: impossibile caricare i dati correnti")
            return

        dettagli = self.formatta_dettagli_preventivo(self.preventivo_corrente, "VERSIONE CORRENTE")
        self.text_dettagli.setText(dettagli)

    def mostra_dettagli_versione(self, timestamp: str) -> None:
        """Mostra dettagli di una versione storica"""
        for snapshot in self.storico:
            if snapshot['timestamp'] == timestamp:
                data = snapshot['data']

                try:
                    dt = datetime.fromisoformat(timestamp)
                    timestamp_str = dt.strftime("%d/%m/%Y %H:%M:%S")
                except Exception:
                    timestamp_str = timestamp

                dettagli = self.formatta_dettagli_preventivo(data, f"VERSIONE DEL {timestamp_str}")
                self.text_dettagli.setText(dettagli)
                return

        self.text_dettagli.setText("Errore: versione non trovata")

    def formatta_dettagli_preventivo(self, data: Any, titolo: str) -> str:
        """Formatta i dettagli del preventivo per la visualizzazione"""
        try:
            if isinstance(data, dict):
                nome_cliente = data.get('nome_cliente', '')
                numero_ordine = data.get('numero_ordine', '')
                descrizione = data.get('descrizione', '')
                codice = data.get('codice', '')
                costo_materiali = float(data.get('costo_totale_materiali', 0.0))
                costi_accessori = float(data.get('costi_accessori', 0.0))
                preventivo_finale = float(data.get('preventivo_finale', 0.0))
                prezzo_cliente = float(data.get('prezzo_cliente', 0.0))

                # Materiali
                materiali_json = data.get('materiali_utilizzati', '[]')
                if isinstance(materiali_json, str):
                    try:
                        materiali = json.loads(materiali_json)
                    except (json.JSONDecodeError, TypeError):
                        materiali = []
                else:
                    materiali = materiali_json if isinstance(materiali_json, list) else []
            else:
                return f"=== {titolo} ===\n\nErrore: formato dati non valido"

            output = f"=== {titolo} ===\n\n"
            output += "INFORMAZIONI CLIENTE\n"
            output += "─" * 50 + "\n"
            output += f"Nome Cliente:     {nome_cliente or 'Non specificato'}\n"
            output += f"Numero Ordine:    {numero_ordine or 'Non specificato'}\n"
            output += f"Codice:           {codice or 'Non specificato'}\n"
            output += f"Descrizione:      {descrizione or 'Non specificato'}\n"
            output += "\n"

            output += "COSTI\n"
            output += "─" * 50 + "\n"
            output += f"Costo Materiali:  € {costo_materiali:,.2f}\n"
            output += f"Costi Accessori:  € {costi_accessori:,.2f}\n"
            output += f"Preventivo Final: € {preventivo_finale:,.2f}\n"
            output += f"Prezzo Cliente:   € {prezzo_cliente:,.2f}\n"
            output += "\n"

            output += "MATERIALI UTILIZZATI\n"
            output += "─" * 50 + "\n"
            if materiali:
                for i, mat in enumerate(materiali, 1):
                    nome_mat = mat.get('materiale_nome', mat.get('nome', 'Sconosciuto'))
                    output += f"{i}. {nome_mat}\n"
            else:
                output += "Nessun materiale\n"

            return output

        except Exception as e:
            return f"=== {titolo} ===\n\nErrore nella formattazione: {str(e)}"

    def confronta_con_corrente(self) -> None:
        """Confronta la versione selezionata con quella corrente"""
        current_item = self.lista_versioni.currentItem()
        if not current_item:
            return

        timestamp = current_item.data(Qt.UserRole)
        if timestamp == "corrente":
            return

        # Trova la versione selezionata
        versione_selezionata = None
        for snapshot in self.storico:
            if snapshot['timestamp'] == timestamp:
                versione_selezionata = snapshot['data']
                break

        if not versione_selezionata or not self.preventivo_corrente:
            QMessageBox.warning(self, "Errore", "Impossibile effettuare il confronto")
            return

        # Dialog di confronto
        dialog = QDialog(self)
        dialog.setWindowTitle("Confronto Versioni")
        dialog.resize(1200, 700)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Confronto: Versione Selezionata vs Versione Corrente")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #2d3748;")
        layout.addWidget(title)

        splitter = QSplitter(Qt.Horizontal)

        # Versione selezionata
        left_group = QGroupBox("Versione Selezionata")
        left_layout = QVBoxLayout(left_group)
        text_left = QTextEdit()
        text_left.setReadOnly(True)

        try:
            dt = datetime.fromisoformat(timestamp)
            timestamp_str = dt.strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            timestamp_str = timestamp

        text_left.setText(self.formatta_dettagli_preventivo(versione_selezionata, f"VERSIONE DEL {timestamp_str}"))
        left_layout.addWidget(text_left)
        splitter.addWidget(left_group)

        # Versione corrente
        right_group = QGroupBox("Versione Corrente")
        right_layout = QVBoxLayout(right_group)
        text_right = QTextEdit()
        text_right.setReadOnly(True)
        text_right.setText(self.formatta_dettagli_preventivo(self.preventivo_corrente, "VERSIONE CORRENTE"))
        right_layout.addWidget(text_right)
        splitter.addWidget(right_group)

        layout.addWidget(splitter)

        # Pulsante chiudi
        btn_chiudi_confronto = QPushButton("Chiudi")
        btn_chiudi_confronto.clicked.connect(dialog.accept)
        layout.addWidget(btn_chiudi_confronto)

        dialog.exec_()

    def ripristina_versione(self) -> None:
        """Ripristina la versione selezionata"""
        current_item = self.lista_versioni.currentItem()
        if not current_item:
            return

        timestamp = current_item.data(Qt.UserRole)
        if timestamp == "corrente":
            return

        # Conferma
        risposta = QMessageBox.question(
            self,
            "Conferma Ripristino",
            "Sei sicuro di voler ripristinare questa versione?\n\n"
            "La versione corrente verrà salvata nello storico.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if risposta != QMessageBox.Yes:
            return

        # Ripristina
        success = self.db_manager.ripristina_versione_preventivo(self.preventivo_id, timestamp)

        if success:
            QMessageBox.information(self, "Successo", "Versione ripristinata con successo!")
            self.versione_ripristinata.emit()
            self.load_storico()
        else:
            QMessageBox.error(self, "Errore", "Errore durante il ripristino della versione")
