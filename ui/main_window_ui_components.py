#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Main Window UI Components - Componenti dell'interfaccia utente per MainWindow
Uso riservato esclusivamente a RCS

Version: 1.0.0
Last Updated: 24/09/2025
Author: Sviluppatore PyQt5 + Claude
"""

from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QWidget, 
                             QLabel, QListWidget, QGroupBox, QFrame, QSizePolicy, 
                             QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

class MainWindowUIComponents:
    
    @staticmethod
    def init_ui(window_instance):
        """Inizializzazione completa dell'interfaccia MainWindow"""
        # Design system unificato - finestra massimizzata con controlli
        window_instance.setWindowTitle("Software Aziendale RCS")
        window_instance.showMaximized()
        
        # Applica stili globali
        MainWindowUIComponents.apply_global_styles(window_instance)
        
        # Widget centrale
        central_widget = QWidget()
        window_instance.setCentralWidget(central_widget)
        
        # Layout principale con margini generosi
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(30)
        
        # Header principale
        MainWindowUIComponents.create_header(window_instance, main_layout)
        
        # Contenuto principale - layout responsive
        content_layout = QHBoxLayout()
        content_layout.setSpacing(40)
        
        # Colonna principale (pulsanti azioni)
        MainWindowUIComponents.create_main_actions_column(window_instance, content_layout)
        
        # Colonna preventivi (inizialmente nascosta)
        MainWindowUIComponents.create_preventivi_column(window_instance, content_layout)
        
        main_layout.addLayout(content_layout, 1)
        
        # Footer informativo
        MainWindowUIComponents.create_footer(window_instance, main_layout)
    
    @staticmethod
    def apply_global_styles(window_instance):
        """Applica stili globali unificati"""
        window_instance.setStyleSheet("""
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
    
    @staticmethod
    def create_shadow_effect(blur=10, opacity=12):
        """Effetto ombra standardizzato"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setColor(QColor(0, 0, 0, opacity))
        shadow.setOffset(0, 2)
        return shadow
    
    @staticmethod
    def create_header(window_instance, parent_layout):
        """Header unificato con titolo principale"""
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
    
    @staticmethod
    def create_main_actions_column(window_instance, parent_layout):
        """Colonna principale con azioni principali"""
        main_column = QWidget()
        main_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(main_column)
        layout.setSpacing(20)
        
        # Sezione azioni principali
        actions_group = QGroupBox("Azioni Principali")
        actions_group.setGraphicsEffect(MainWindowUIComponents.create_shadow_effect())
        
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setContentsMargins(30, 35, 30, 30)
        actions_layout.setSpacing(20)
        
        # Pulsanti principali
        MainWindowUIComponents.create_main_buttons(window_instance, actions_layout)
        
        layout.addWidget(actions_group)
        layout.addStretch()
        
        parent_layout.addWidget(main_column)
        window_instance.main_column = main_column
    
    @staticmethod
    def create_main_buttons(window_instance, parent_layout):
        """Pulsanti principali standardizzati"""
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(16)
        
        # Pulsante Nuovo Preventivo - primario
        window_instance.btn_nuovo_preventivo = QPushButton("Calcola Nuovo Preventivo")
        window_instance.btn_nuovo_preventivo.setMinimumHeight(50)
        window_instance.btn_nuovo_preventivo.setStyleSheet("""
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
        window_instance.btn_nuovo_preventivo.clicked.connect(window_instance.apri_preventivo)
        
        # Pulsante Visualizza Preventivi - secondario
        window_instance.btn_visualizza_preventivi = QPushButton("Visualizza Preventivi Salvati")
        window_instance.btn_visualizza_preventivi.setMinimumHeight(50)
        window_instance.btn_visualizza_preventivi.setStyleSheet("""
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
        window_instance.btn_visualizza_preventivi.clicked.connect(window_instance.mostra_nascondi_preventivi)
        
        # Pulsante Gestisci Materiali
        window_instance.btn_gestisci_materiali = QPushButton("Gestisci Materiali")
        window_instance.btn_gestisci_materiali.setMinimumHeight(50)
        window_instance.btn_gestisci_materiali.setStyleSheet("""
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
        window_instance.btn_gestisci_materiali.clicked.connect(window_instance.apri_gestione_materiali)
        
        buttons_layout.addWidget(window_instance.btn_nuovo_preventivo)
        buttons_layout.addWidget(window_instance.btn_visualizza_preventivi)
        buttons_layout.addWidget(window_instance.btn_gestisci_materiali)
        
        parent_layout.addLayout(buttons_layout)
    
    @staticmethod
    def create_preventivi_column(window_instance, parent_layout):
        """Colonna preventivi salvati con nuovo pulsante Genera Documento"""
        window_instance.preventivi_column = QWidget()
        window_instance.preventivi_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(window_instance.preventivi_column)
        layout.setSpacing(20)
        
        # Sezione preventivi salvati
        preventivi_group = QGroupBox("Preventivi Salvati")
        preventivi_group.setGraphicsEffect(MainWindowUIComponents.create_shadow_effect())
        
        preventivi_layout = QVBoxLayout(preventivi_group)
        preventivi_layout.setContentsMargins(30, 35, 30, 30)
        preventivi_layout.setSpacing(16)
        
        # Info preventivi
        MainWindowUIComponents.create_preventivi_info_card(window_instance, preventivi_layout)
        
        # Toggle per visualizzare Preventivi o Revisioni
        MainWindowUIComponents.create_view_toggle(window_instance, preventivi_layout)
        
        # Lista preventivi
        window_instance.lista_preventivi = QListWidget()
        window_instance.lista_preventivi.setMinimumHeight(300)
        window_instance.lista_preventivi.itemDoubleClicked.connect(window_instance.visualizza_preventivo)
        preventivi_layout.addWidget(window_instance.lista_preventivi)
        
        # Pulsanti gestione preventivi CON NUOVO PULSANTE GENERA DOCUMENTO
        MainWindowUIComponents.create_preventivi_buttons(window_instance, preventivi_layout)
        
        layout.addWidget(preventivi_group)
        layout.addStretch()
        
        parent_layout.addWidget(window_instance.preventivi_column)
        
        # Inizialmente nascondi la colonna preventivi
        window_instance.preventivi_column.hide()
    
    @staticmethod
    def create_preventivi_info_card(window_instance, parent_layout):
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
        
        info_label = QLabel("Seleziona un preventivo per visualizzarlo, modificarlo, generare documenti o crearne una revisione")
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
    
    @staticmethod
    def create_view_toggle(window_instance, parent_layout):
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
        window_instance.btn_mostra_preventivi = QPushButton("Preventivi")
        window_instance.btn_mostra_preventivi.setStyleSheet("""
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
        window_instance.btn_mostra_preventivi.clicked.connect(lambda: window_instance.cambia_visualizzazione('preventivi'))
        toggle_layout.addWidget(window_instance.btn_mostra_preventivi)
        
        # Pulsante Revisioni
        window_instance.btn_mostra_revisioni = QPushButton("Revisioni")
        window_instance.btn_mostra_revisioni.setStyleSheet("""
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
        window_instance.btn_mostra_revisioni.clicked.connect(lambda: window_instance.cambia_visualizzazione('revisioni'))
        toggle_layout.addWidget(window_instance.btn_mostra_revisioni)
        
        toggle_layout.addStretch()
        parent_layout.addWidget(toggle_container)
    
    @staticmethod
    def create_preventivi_buttons(window_instance, parent_layout):
        """Pulsanti gestione preventivi CON NUOVO PULSANTE GENERA DOCUMENTO"""
        # Prima riga di pulsanti - aggiunta Genera Documento
        buttons_layout_1 = QHBoxLayout()
        buttons_layout_1.setSpacing(12)
        
        # Visualizza dettagli
        window_instance.btn_visualizza_dettagli = QPushButton("Visualizza")
        window_instance.btn_visualizza_dettagli.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
        """)
        window_instance.btn_visualizza_dettagli.clicked.connect(window_instance.visualizza_preventivo)
        
        # Modifica preventivo
        window_instance.btn_modifica_preventivo = QPushButton("Modifica")
        window_instance.btn_modifica_preventivo.setStyleSheet("""
            QPushButton {
                background-color: #718096;
                color: #ffffff;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #4a5568;
            }
        """)
        window_instance.btn_modifica_preventivo.clicked.connect(window_instance.modifica_preventivo)
        
        # NUOVO: Genera Documento
        window_instance.btn_genera_documento = QPushButton("📄 Genera Documento")
        window_instance.btn_genera_documento.setStyleSheet("""
            QPushButton {
                background-color: #48bb78;
                color: #ffffff;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #38a169;
            }
            QPushButton:disabled {
                background-color: #a0aec0;
                color: #718096;
            }
        """)
        window_instance.btn_genera_documento.clicked.connect(window_instance.genera_documento_preventivo)
        
        # Crea revisione
        window_instance.btn_crea_revisione = QPushButton("Crea Revisione")
        window_instance.btn_crea_revisione.setStyleSheet("""
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
        window_instance.btn_crea_revisione.clicked.connect(window_instance.crea_revisione)
        
        buttons_layout_1.addWidget(window_instance.btn_visualizza_dettagli)
        buttons_layout_1.addWidget(window_instance.btn_modifica_preventivo)
        buttons_layout_1.addWidget(window_instance.btn_genera_documento)
        buttons_layout_1.addWidget(window_instance.btn_crea_revisione)
        
        # Seconda riga di pulsanti
        buttons_layout_2 = QHBoxLayout()
        buttons_layout_2.setSpacing(12)
        
        # Elimina preventivo
        window_instance.btn_elimina_preventivo = QPushButton("Elimina")
        window_instance.btn_elimina_preventivo.setStyleSheet("""
            QPushButton {
                background-color: #e53e3e;
                color: #ffffff;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #c53030;
            }
        """)
        window_instance.btn_elimina_preventivo.clicked.connect(window_instance.elimina_preventivo)
        
        # Nascondi preventivi
        window_instance.btn_nascondi_preventivi = QPushButton("Nascondi Preventivi")
        window_instance.btn_nascondi_preventivi.setStyleSheet("""
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
        window_instance.btn_nascondi_preventivi.clicked.connect(window_instance.mostra_nascondi_preventivi)
        
        buttons_layout_2.addWidget(window_instance.btn_elimina_preventivo)
        buttons_layout_2.addStretch()
        buttons_layout_2.addWidget(window_instance.btn_nascondi_preventivi)
        
        parent_layout.addLayout(buttons_layout_1)
        parent_layout.addLayout(buttons_layout_2)
    
    @staticmethod
    def create_footer(window_instance, parent_layout):
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
        
        footer_label = QLabel("Software Aziendale RCS v2.3.0 | Sistema di calcolo preventivi, gestione revisioni e generazione documenti")
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