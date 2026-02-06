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
                             QLabel, QGroupBox, QFrame, QSizePolicy,
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

        # Colonna principale (pulsanti azioni) - ora occupa tutta la larghezza
        MainWindowUIComponents.create_main_actions_column(window_instance, content_layout)

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