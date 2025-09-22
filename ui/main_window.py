#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
MainWindow - Interfaccia principale con gestione completa preventivi e revisioni
Uso riservato esclusivamente a RCS

Version: 2.2.0
Last Updated: 22/09/2025
Author: Sviluppatore PyQt5 + Claude

CHANGELOG:
v2.2.0 (22/09/2025):
- ADDED: Toggle per visualizzare separatamente Preventivi e Revisioni
- ADDED: Sezione dedicata per consultare le revisioni
- FIXED: Colori pulsanti coerenti con palette generale
- IMPROVED: Visualizzazione lista preventivi più leggibile
- MAINTAINED: Design system originale identico
"""

from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QWidget, QLabel, QListWidget, QMessageBox, QListWidgetItem,
                             QGroupBox, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
                             QDialog, QTextEdit, QFormLayout, QDialogButtonBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from database.db_manager import DatabaseManager
from ui.preventivo_window import PreventivoWindow
from ui.gestione_materiali_window import GestioneMaterialiWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.preventivo_window = None
        self.gestione_materiali_window = None
        self.init_ui()
        self.load_preventivi()
    
    def init_ui(self):
        """Design system unificato - finestra massimizzata con controlli"""
        self.setWindowTitle("Software Aziendale RCS")
        
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
        
        # Layout principale con margini generosi
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(30)
        
        # Header principale
        self.create_header(main_layout)
        
        # Contenuto principale - layout responsive
        content_layout = QHBoxLayout()
        content_layout.setSpacing(40)
        
        # Colonna principale (pulsanti azioni)
        self.create_main_actions_column(content_layout)
        
        # Colonna preventivi (inizialmente nascosta)
        self.create_preventivi_column(content_layout)
        
        main_layout.addLayout(content_layout, 1)
        
        # Footer informativo
        self.create_footer(main_layout)
    
    def create_shadow_effect(self, blur=10, opacity=12):
        """Effetto ombra standardizzato"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setColor(QColor(0, 0, 0, opacity))
        shadow.setOffset(0, 2)
        return shadow
    
    def create_header(self, parent_layout):
        """Header unificato con titolo principale - senza bordi"""
        header_container = QFrame()
        header_container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                padding: 20px 0px;
            }
        """)
        
        header_layout = QVBoxLayout(header_container)
        header_layout.setSpacing(8)
        
        # Titolo principale
        title_label = QLabel("Software Aziendale RCS")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: 700;
                color: #2d3748;
                padding: 0;
            }
        """)
        
        # Sottotitolo
        subtitle_label = QLabel("Sistema di calcolo preventivi e statistiche RCS")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 400;
                color: #718096;
                padding: 0;
            }
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        parent_layout.addWidget(header_container)
    
    def create_main_actions_column(self, parent_layout):
        """Colonna principale con azioni principali - senza messaggi di benvenuto"""
        main_column = QWidget()
        main_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(main_column)
        layout.setSpacing(20)
        
        # Sezione azioni principali
        actions_group = QGroupBox("Azioni Principali")
        actions_group.setGraphicsEffect(self.create_shadow_effect())
        
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setContentsMargins(30, 35, 30, 30)
        actions_layout.setSpacing(20)
        
        # Pulsanti principali senza card descrittiva
        self.create_main_buttons(actions_layout)
        
        layout.addWidget(actions_group)
        layout.addStretch()
        
        parent_layout.addWidget(main_column)
        
        # Inizialmente mostra solo la colonna principale
        self.main_column = main_column
    
    def create_main_buttons(self, parent_layout):
        """Pulsanti principali standardizzati"""
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(16)
        
        # Pulsante Nuovo Preventivo - primario
        self.btn_nuovo_preventivo = QPushButton("Calcola Nuovo Preventivo")
        self.btn_nuovo_preventivo.setMinimumHeight(50)
        self.btn_nuovo_preventivo.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                min-height: 50px;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
            QPushButton:pressed {
                background-color: #1a202c;
            }
        """)
        self.btn_nuovo_preventivo.clicked.connect(self.apri_preventivo)
        
        # Pulsante Visualizza Preventivi - secondario
        self.btn_visualizza_preventivi = QPushButton("Visualizza Preventivi Salvati")
        self.btn_visualizza_preventivi.setMinimumHeight(50)
        self.btn_visualizza_preventivi.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: 50px;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
        """)
        self.btn_visualizza_preventivi.clicked.connect(self.mostra_nascondi_preventivi)
        
        # Pulsante Gestisci Materiali
        self.btn_gestisci_materiali = QPushButton("Gestisci Materiali")
        self.btn_gestisci_materiali.setMinimumHeight(50)
        self.btn_gestisci_materiali.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: 50px;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
        """)
        self.btn_gestisci_materiali.clicked.connect(self.apri_gestione_materiali)
        
        buttons_layout.addWidget(self.btn_nuovo_preventivo)
        buttons_layout.addWidget(self.btn_visualizza_preventivi)
        buttons_layout.addWidget(self.btn_gestisci_materiali)
        
        parent_layout.addLayout(buttons_layout)
    
    def create_preventivi_column(self, parent_layout):
        """Colonna preventivi salvati CON TOGGLE PREVENTIVI/REVISIONI"""
        self.preventivi_column = QWidget()
        self.preventivi_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(self.preventivi_column)
        layout.setSpacing(20)
        
        # Sezione preventivi salvati
        preventivi_group = QGroupBox("Preventivi Salvati")
        preventivi_group.setGraphicsEffect(self.create_shadow_effect())
        
        preventivi_layout = QVBoxLayout(preventivi_group)
        preventivi_layout.setContentsMargins(30, 35, 30, 30)
        preventivi_layout.setSpacing(16)
        
        # Info preventivi
        self.create_preventivi_info_card(preventivi_layout)
        
        # Toggle per visualizzare Preventivi o Revisioni
        self.create_view_toggle(preventivi_layout)
        
        # Lista preventivi
        self.lista_preventivi = QListWidget()
        self.lista_preventivi.setMinimumHeight(300)
        self.lista_preventivi.itemDoubleClicked.connect(self.visualizza_preventivo)
        preventivi_layout.addWidget(self.lista_preventivi)
        
        # Pulsanti gestione preventivi aggiornati
        self.create_preventivi_buttons(preventivi_layout)
        
        layout.addWidget(preventivi_group)
        layout.addStretch()
        
        parent_layout.addWidget(self.preventivi_column)
        
        # Inizialmente nascondi la colonna preventivi
        self.preventivi_column.hide()
        self.preventivi_visibili = False
        self.modalita_visualizzazione = 'preventivi'  # 'preventivi' o 'revisioni'
    
    def create_preventivi_info_card(self, parent_layout):
        """Card informativa preventivi"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #f0fff4;
                border: 1px solid #68d391;
                border-radius: 8px;
                padding: 16px;
                margin: 2px 0px;
            }
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        info_label = QLabel("Seleziona un preventivo per visualizzarlo, modificarlo o crearne una revisione")
        info_label.setStyleSheet("""
            QLabel {
                color: #2d3748;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        
        layout.addWidget(info_label)
        layout.addStretch()
        
        parent_layout.addWidget(container)
    
    def create_view_toggle(self, parent_layout):
        """Toggle per cambiare visualizzazione tra Preventivi e Revisioni"""
        toggle_container = QFrame()
        toggle_container.setStyleSheet("""
            QFrame {
                background-color: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px;
                margin: 2px 0px;
            }
        """)
        
        toggle_layout = QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(8)
        
        # Label
        toggle_label = QLabel("Visualizza:")
        toggle_label.setStyleSheet("""
            QLabel {
                color: #4a5568;
                font-size: 14px;
                font-weight: 600;
            }
        """)
        toggle_layout.addWidget(toggle_label)
        
        # Pulsante Preventivi
        self.btn_mostra_preventivi = QPushButton("Preventivi")
        self.btn_mostra_preventivi.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                min-height: 28px;
                min-width: 100px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
        """)
        self.btn_mostra_preventivi.clicked.connect(lambda: self.cambia_visualizzazione('preventivi'))
        toggle_layout.addWidget(self.btn_mostra_preventivi)
        
        # Pulsante Revisioni
        self.btn_mostra_revisioni = QPushButton("Revisioni")
        self.btn_mostra_revisioni.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: 28px;
                min-width: 100px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
        """)
        self.btn_mostra_revisioni.clicked.connect(lambda: self.cambia_visualizzazione('revisioni'))
        toggle_layout.addWidget(self.btn_mostra_revisioni)
        
        toggle_layout.addStretch()
        parent_layout.addWidget(toggle_container)
    
    def create_preventivi_buttons(self, parent_layout):
        """Pulsanti gestione preventivi con nuove funzionalità e colori migliorati"""
        # Prima riga di pulsanti
        buttons_layout_1 = QHBoxLayout()
        buttons_layout_1.setSpacing(12)
        
        # Visualizza dettagli
        self.btn_visualizza_dettagli = QPushButton("Visualizza Dettagli")
        self.btn_visualizza_dettagli.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
        """)
        self.btn_visualizza_dettagli.clicked.connect(self.visualizza_preventivo)
        
        # Modifica preventivo - colore più coerente con la palette
        self.btn_modifica_preventivo = QPushButton("Modifica")
        self.btn_modifica_preventivo.setStyleSheet("""
            QPushButton {
                background-color: #718096;
                color: #ffffff;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #4a5568;
            }
        """)
        self.btn_modifica_preventivo.clicked.connect(self.modifica_preventivo)
        
        # Crea revisione - colore più coerente con la palette
        self.btn_crea_revisione = QPushButton("Crea Revisione")
        self.btn_crea_revisione.setStyleSheet("""
            QPushButton {
                background-color: #a0aec0;
                color: #2d3748;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #718096;
                color: #ffffff;
            }
        """)
        self.btn_crea_revisione.clicked.connect(self.crea_revisione)
        
        buttons_layout_1.addWidget(self.btn_visualizza_dettagli)
        buttons_layout_1.addWidget(self.btn_modifica_preventivo)
        buttons_layout_1.addWidget(self.btn_crea_revisione)
        
        # Seconda riga di pulsanti
        buttons_layout_2 = QHBoxLayout()
        buttons_layout_2.setSpacing(12)
        
        # Elimina preventivo
        self.btn_elimina_preventivo = QPushButton("Elimina")
        self.btn_elimina_preventivo.setStyleSheet("""
            QPushButton {
                background-color: #e53e3e;
                color: #ffffff;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #c53030;
            }
        """)
        self.btn_elimina_preventivo.clicked.connect(self.elimina_preventivo)
        
        # Nascondi preventivi
        self.btn_nascondi_preventivi = QPushButton("Nascondi Preventivi")
        self.btn_nascondi_preventivi.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
        """)
        self.btn_nascondi_preventivi.clicked.connect(self.mostra_nascondi_preventivi)
        
        buttons_layout_2.addWidget(self.btn_elimina_preventivo)
        buttons_layout_2.addStretch()
        buttons_layout_2.addWidget(self.btn_nascondi_preventivi)
        
        parent_layout.addLayout(buttons_layout_1)
        parent_layout.addLayout(buttons_layout_2)
    
    def create_footer(self, parent_layout):
        """Footer informativo"""
        footer_container = QFrame()
        footer_container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                padding: 20px 0px;
            }
        """)
        
        footer_layout = QHBoxLayout(footer_container)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        
        footer_label = QLabel("Software Aziendale RCS v2.2 | Sistema di calcolo preventivi e gestione revisioni")
        footer_label.setStyleSheet("""
            QLabel {
                color: #a0aec0;
                font-size: 12px;
                font-weight: 400;
            }
        """)
        
        footer_layout.addWidget(footer_label)
        footer_layout.addStretch()
        
        parent_layout.addWidget(footer_container)
    
    def cambia_visualizzazione(self, modalita):
        """Cambia tra visualizzazione Preventivi e Revisioni"""
        self.modalita_visualizzazione = modalita
        
        # Aggiorna stili pulsanti
        if modalita == 'preventivi':
            self.btn_mostra_preventivi.setStyleSheet("""
                QPushButton {
                    background-color: #4a5568;
                    color: #ffffff;
                    min-height: 28px;
                    min-width: 100px;
                    padding: 6px 16px;
                }
                QPushButton:hover {
                    background-color: #2d3748;
                }
            """)
            self.btn_mostra_revisioni.setStyleSheet("""
                QPushButton {
                    background-color: #f7fafc;
                    color: #4a5568;
                    border: 1px solid #e2e8f0;
                    min-height: 28px;
                    min-width: 100px;
                    padding: 6px 16px;
                }
                QPushButton:hover {
                    background-color: #edf2f7;
                }
            """)
        else:  # revisioni
            self.btn_mostra_revisioni.setStyleSheet("""
                QPushButton {
                    background-color: #4a5568;
                    color: #ffffff;
                    min-height: 28px;
                    min-width: 100px;
                    padding: 6px 16px;
                }
                QPushButton:hover {
                    background-color: #2d3748;
                }
            """)
            self.btn_mostra_preventivi.setStyleSheet("""
                QPushButton {
                    background-color: #f7fafc;
                    color: #4a5568;
                    border: 1px solid #e2e8f0;
                    min-height: 28px;
                    min-width: 100px;
                    padding: 6px 16px;
                }
                QPushButton:hover {
                    background-color: #edf2f7;
                }
            """)
        
        # Ricarica la lista con la modalità corretta
        self.load_preventivi()
    
    def load_preventivi(self):
        """Carica preventivi o revisioni in base alla modalità di visualizzazione"""
        self.lista_preventivi.clear()
        
        if self.modalita_visualizzazione == 'preventivi':
            # Mostra solo preventivi originali (ultima revisione di ogni gruppo)
            preventivi = self.db_manager.get_all_preventivi_latest()
        else:
            # Mostra solo le revisioni (escludendo i preventivi originali)
            preventivi = self.db_manager.get_all_preventivi()  # Tutti i preventivi
            # Filtra per mostrare solo le revisioni (numero_revisione > 1)
            preventivi_filtrati = []
            for prev in preventivi:
                if len(prev) >= 9:
                    numero_revisione = prev[8] if len(prev) > 8 else 1
                    if numero_revisione > 1:
                        preventivi_filtrati.append(prev)
                
            preventivi = preventivi_filtrati
        
        for preventivo in preventivi:
            # Nuovo formato: id, data_creazione, preventivo_finale, prezzo_cliente, 
            # nome_cliente, numero_ordine, descrizione, codice, numero_revisione
            if len(preventivo) >= 9:
                id_prev, data_creazione, preventivo_finale, prezzo_cliente, nome_cliente, numero_ordine, descrizione, codice, numero_revisione = preventivo[:9]
                tipo = 'R' if numero_revisione > 1 else 'O'
            else:
                # Fallback per compatibilità
                id_prev, data_creazione, preventivo_finale, prezzo_cliente = preventivo[:4]
                nome_cliente, numero_ordine, descrizione, codice, numero_revisione, tipo = "", "", "", "", 1, 'O'
            
            # Formatta la data
            data_formattata = data_creazione.split('T')[0] if 'T' in data_creazione else data_creazione
            
            # Crea il testo per la lista
            if self.modalita_visualizzazione == 'revisioni':
                # Per revisioni, mostra anche il numero di revisione
                prefisso_tipo = f"REV {numero_revisione}"
                cliente_info = nome_cliente if nome_cliente else "Cliente non specificato"
                ordine_info = f" | {numero_ordine}" if numero_ordine else ""
                
                testo = f"#{id_prev:03d} [{prefisso_tipo}] • {data_formattata} • {cliente_info}{ordine_info}"
                testo += f"\n💰 Preventivo: €{preventivo_finale:,.2f} • Cliente: €{prezzo_cliente:,.2f}"
                if descrizione:
                    testo += f"\n📝 {descrizione[:60]}{'...' if len(descrizione) > 60 else ''}"
            else:
                # Per preventivi originali, usa la visualizzazione standard
                prefisso_tipo = "REV" if tipo == 'R' else "ORG"
                cliente_info = nome_cliente if nome_cliente else "Cliente non specificato"
                ordine_info = f" | {numero_ordine}" if numero_ordine else ""
                
                testo = f"#{id_prev:03d} [{prefisso_tipo}] • {data_formattata} • {cliente_info}{ordine_info}"
                testo += f"\n💰 Preventivo: €{preventivo_finale:,.2f} • Cliente: €{prezzo_cliente:,.2f}"
                if descrizione:
                    testo += f"\n📝 {descrizione[:60]}{'...' if len(descrizione) > 60 else ''}"
            
            item = QListWidgetItem(testo)
            item.setData(Qt.UserRole, id_prev)  # Salva l'ID del preventivo
            self.lista_preventivi.addItem(item)
    
    def apri_preventivo(self):
        """Apre la finestra per creare un nuovo preventivo"""
        self.preventivo_window = PreventivoWindow(self.db_manager, self, modalita='nuovo')
        self.preventivo_window.preventivo_salvato.connect(self.preventivo_salvato)
        self.preventivo_window.show()
    
    def modifica_preventivo(self):
        """Apre un preventivo esistente per la modifica DIRETTA (sovrascrive)"""
        current_item = self.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo da modificare.")
            return
        
        preventivo_id = current_item.data(Qt.UserRole)
        self.preventivo_window = PreventivoWindow(
            self.db_manager, 
            self, 
            preventivo_id=preventivo_id, 
            modalita='modifica'  # Nuova modalità specifica per modifiche
        )
        self.preventivo_window.preventivo_salvato.connect(self.preventivo_salvato)
        self.preventivo_window.show()
    
    def crea_revisione(self):
        """Crea una revisione di un preventivo esistente"""
        current_item = self.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo per creare una revisione.")
            return
        
        preventivo_id = current_item.data(Qt.UserRole)
        
        # Dialog per inserire note sulla revisione
        note_revisione = self.richiedi_note_revisione()
        if note_revisione is None:  # L'utente ha annullato
            return
        
        self.preventivo_window = PreventivoWindow(
            self.db_manager, 
            self, 
            preventivo_id=preventivo_id, 
            modalita='revisione',
            note_revisione=note_revisione
        )
        self.preventivo_window.preventivo_salvato.connect(self.preventivo_salvato)
        self.preventivo_window.show()
    
    def richiedi_note_revisione(self):
        """Dialog per inserire note sulla revisione"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Note Revisione")
        dialog.setFixedSize(400, 250)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #fafbfc;
            }
            QLabel {
                color: #2d3748;
                font-size: 14px;
                font-weight: 500;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QTextEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                background-color: #ffffff;
                color: #2d3748;
                font-family: system-ui, -apple-system, sans-serif;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        
        # Label descrittiva
        label = QLabel("Inserisci le note per questa revisione (opzionale):")
        layout.addWidget(label)
        
        # Campo di testo per le note
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Describe le modifiche apportate o il motivo della revisione...")
        layout.addWidget(text_edit)
        
        # Pulsanti
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec_() == QDialog.Accepted:
            return text_edit.toPlainText().strip()
        else:
            return None
    
    def apri_gestione_materiali(self):
        """Apre la finestra per gestire i materiali"""
        self.gestione_materiali_window = GestioneMaterialiWindow(self.db_manager, self)
        
        # Collega il signal per aggiornare i preventivi aperti
        self.gestione_materiali_window.materiali_modificati.connect(self.aggiorna_preventivi_aperti)
        
        self.gestione_materiali_window.show()
    
    def aggiorna_preventivi_aperti(self):
        """Aggiorna i preventivi aperti quando i materiali vengono modificati"""
        if self.preventivo_window and self.preventivo_window.isVisible():
            self.preventivo_window.aggiorna_prezzi_materiali()
    
    def mostra_nascondi_preventivi(self):
        """Mostra o nasconde la sezione dei preventivi con transizione layout"""
        if self.preventivi_visibili:
            # Nascondi preventivi - torna al layout a colonna singola
            self.preventivi_column.hide()
            self.btn_visualizza_preventivi.setText("Visualizza Preventivi Salvati")
            self.preventivi_visibili = False
        else:
            # Mostra preventivi - layout a due colonne
            self.preventivi_column.show()
            self.btn_visualizza_preventivi.setText("Nascondi Preventivi")
            self.preventivi_visibili = True
            self.load_preventivi()  # Ricarica i preventivi quando li mostra
    
    def visualizza_preventivo(self):
        """Visualizza i dettagli del preventivo selezionato"""
        current_item = self.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo da visualizzare.")
            return
        
        preventivo_id = current_item.data(Qt.UserRole)
        
        # Apre in modalità visualizzazione (sola lettura)
        self.preventivo_window = PreventivoWindow(
            self.db_manager, 
            self, 
            preventivo_id=preventivo_id, 
            modalita='visualizza'
        )
        self.preventivo_window.show()
    
    def mostra_dettagli_preventivo(self, preventivo):
        """Mostra dettagli preventivo con nuovi campi"""
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Dettagli Preventivo")
        dialog.setStyleSheet("""
            QMessageBox {
                background-color: #fafbfc;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QMessageBox QLabel {
                color: #2d3748;
                font-size: 13px;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QMessageBox QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #2d3748;
            }
        """)
        
        data_formattata = preventivo['data_creazione'].split('T')[0] if 'T' in preventivo['data_creazione'] else preventivo['data_creazione']
        
        # Include i nuovi campi se disponibili
        cliente_info = ""
        if preventivo.get('nome_cliente'):
            cliente_info = f"""<b>👤 INFORMAZIONI CLIENTE</b><br>
• Nome: {preventivo.get('nome_cliente', 'N/A')}<br>
• Numero Ordine: {preventivo.get('numero_ordine', 'N/A')}<br>
• Codice: {preventivo.get('codice', 'N/A')}<br>
• Descrizione: {preventivo.get('descrizione', 'N/A')}<br><br>"""
        
        dettagli = f"""<b>PREVENTIVO #{preventivo['id']:03d}</b><br>
<b>Data Creazione:</b> {data_formattata}<br><br>

{cliente_info}

<b>💰 COSTI</b><br>
• Costo Totale Materiali: €{preventivo['costo_totale_materiali']:,.2f}<br>
• Costi Accessori: €{preventivo['costi_accessori']:,.2f}<br><br>

<b>⏱️ TEMPI LAVORAZIONE</b><br>
• Minuti Taglio: {preventivo['minuti_taglio']}<br>
• Minuti Avvolgimento: {preventivo['minuti_avvolgimento']}<br>
• Minuti Pulizia: {preventivo['minuti_pulizia']}<br>
• Minuti Rettifica: {preventivo['minuti_rettifica']}<br>
• Minuti Imballaggio: {preventivo['minuti_imballaggio']}<br>
• <b>Tot Mano d'Opera: {preventivo['tot_mano_opera']}</b><br><br>

<b>📊 TOTALI</b><br>
• Subtotale: €{preventivo['subtotale']:,.2f}<br>
• Maggiorazione 25%: €{preventivo['maggiorazione_25']:,.2f}<br>
• <b>Preventivo Finale: €{preventivo['preventivo_finale']:,.2f}</b><br>
• <b>Prezzo Cliente: €{preventivo['prezzo_cliente']:,.2f}</b><br><br>

<b>📦 MATERIALI</b><br>
• Materiali utilizzati: {len(preventivo['materiali_utilizzati'])} materiali"""
        
        dialog.setText(dettagli)
        dialog.setIcon(QMessageBox.Information)
        dialog.exec_()
    
    def elimina_preventivo(self):
        """Elimina preventivo utilizzando il nuovo metodo del database"""
        current_item = self.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo da eliminare.")
            return
        
        # Dialog di conferma con stile unificato
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Conferma Eliminazione")
        dialog.setText("Sei sicuro di voler eliminare questo preventivo?\n\nQuesta azione eliminerà anche tutte le sue revisioni e non può essere annullata.")
        dialog.setIcon(QMessageBox.Question)
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)
        dialog.setStyleSheet("""
            QMessageBox {
                background-color: #fafbfc;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QMessageBox QLabel {
                color: #2d3748;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
                min-width: 80px;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QMessageBox QPushButton[text="Yes"] {
                background-color: #e53e3e;
                color: #ffffff;
            }
            QMessageBox QPushButton[text="Yes"]:hover {
                background-color: #c53030;
            }
            QMessageBox QPushButton[text="No"] {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
            }
            QMessageBox QPushButton[text="No"]:hover {
                background-color: #edf2f7;
            }
        """)
        
        risposta = dialog.exec_()
        
        if risposta == QMessageBox.Yes:
            preventivo_id = current_item.data(Qt.UserRole)
            
            # Usa il nuovo metodo per eliminare preventivo e revisioni
            if self.db_manager.delete_preventivo_e_revisioni(preventivo_id):
                QMessageBox.information(self, "Successo", 
                                      "Preventivo e tutte le sue revisioni sono stati eliminati con successo.")
                self.load_preventivi()  # Ricarica la lista
            else:
                QMessageBox.error(self, "Errore", 
                                "Errore durante l'eliminazione del preventivo.")
    
    def preventivo_salvato(self):
        """Callback chiamato quando un preventivo viene salvato"""
        self.load_preventivi()
        
        # Se i preventivi sono visibili, aggiorna la visualizzazione
        if self.preventivi_visibili:
            pass  # La lista è già aggiornata da load_preventivi()
        else:
            # Mostra un messaggio di successo
            QMessageBox.information(self, "Successo", 
                                  "Preventivo salvato con successo!\n\nUsa 'Visualizza Preventivi Salvati' per vederlo nella lista.")
        