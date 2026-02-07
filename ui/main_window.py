#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
MainWindow - Interfaccia principale REFACTORIZZATA con gestione preventivi e documenti
Uso riservato esclusivamente a RCS

Version: 2.3.0 - REFACTORED
Last Updated: 24/09/2025
Author: Sviluppatore PyQt5 + Claude

CHANGELOG:
v2.3.0 (24/09/2025):
- REFACTORED: Estratta logica UI in main_window_ui_components.py
- REFACTORED: Estratta business logic in main_window_business_logic.py
- ADDED: Pulsante "Genera Documento" per creare documenti di produzione
- IMPROVED: Codice modulare e mantenibile (~60% più corto)
- MAINTAINED: Tutte le funzionalità esistenti e design system
"""

# type: ignore
# pyright: reportUnknownParameterType=false, reportMissingParameterType=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportAttributeAccessIssue=false
# pyright: reportUnusedVariable=false
# type: ignore
# pyright: reportUnusedImport=false

from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QWidget, QLabel, QListWidget, QMessageBox, QListWidgetItem,
                             QGroupBox, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
                             QDialog, QTextEdit, QFormLayout, QDialogButtonBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from database.db_manager import DatabaseManager
from ui.preventivo_window import PreventivoWindow
from ui.gestione_materiali_window import GestioneMaterialiWindow

# NUOVI MODULI REFACTORIZZATI
from ui.main_window_ui_components import MainWindowUIComponents
from ui.main_window_business_logic import MainWindowBusinessLogic
from ui.document_utils import DocumentUtils

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.preventivo_window = None
        self.gestione_materiali_window = None
        self.visualizza_preventivi_window = None

        # Inizializzazione UI delegata al modulo
        MainWindowUIComponents.init_ui(self)
    
    # =============================================================================
    # CALLBACK METHODS - Delegano alla business logic
    # =============================================================================
    
    def cambia_visualizzazione(self, modalita):
        """Cambia tra visualizzazione Preventivi e Revisioni"""
        MainWindowBusinessLogic.cambia_visualizzazione(self, modalita)
    
    def apri_preventivo(self):
        """Apre la finestra per creare un nuovo preventivo"""
        MainWindowBusinessLogic.apri_preventivo(self)
    
    def modifica_preventivo(self):
        """Apre un preventivo esistente per la modifica DIRETTA"""
        MainWindowBusinessLogic.modifica_preventivo(self)
    
    def crea_revisione(self):
        """Crea una revisione di un preventivo esistente"""
        MainWindowBusinessLogic.crea_revisione(self)
    
    def apri_gestione_materiali(self):
        """Apre la finestra per gestire i materiali"""
        MainWindowBusinessLogic.apri_gestione_materiali(self)
    
    def mostra_nascondi_preventivi(self):
        """Mostra o nasconde la sezione dei preventivi"""
        MainWindowBusinessLogic.mostra_nascondi_preventivi(self)
    
    def visualizza_preventivo(self):
        """Visualizza i dettagli del preventivo selezionato"""
        MainWindowBusinessLogic.visualizza_preventivo(self)
    
    def elimina_preventivo(self):
        """Elimina preventivo"""
        MainWindowBusinessLogic.elimina_preventivo(self)
    
    def genera_documento_preventivo(self):
        """NUOVO: Genera documento di produzione dal preventivo selezionato"""
        MainWindowBusinessLogic.genera_documento_preventivo(self)

    def apri_confronto_preventivi(self):
        """NUOVO: Apre la finestra per confrontare due preventivi"""
        MainWindowBusinessLogic.apri_confronto_preventivi(self)

    # =============================================================================
    # COMPATIBILITY METHODS - Per retrocompatibilità
    # =============================================================================
    
    def load_preventivi(self):
        """Carica preventivi - delegato alla business logic"""
        MainWindowBusinessLogic.load_preventivi(self)
    
    def richiedi_note_revisione(self):
        """Dialog per inserire note sulla revisione"""
        return MainWindowBusinessLogic.richiedi_note_revisione(self)
    
    def aggiorna_preventivi_aperti(self):
        """Aggiorna i preventivi aperti quando i materiali vengono modificati"""
        MainWindowBusinessLogic.aggiorna_preventivi_aperti(self)
    
    def preventivo_salvato(self):
        """Callback chiamato quando un preventivo viene salvato"""
        MainWindowBusinessLogic.preventivo_salvato(self)
