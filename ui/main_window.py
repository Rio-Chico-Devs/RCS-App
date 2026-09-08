#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
MainWindow - Interfaccia principale REFACTORIZZATA con gestione preventivi e documenti
Uso riservato esclusivamente a RCS

Version: 2.3.0 - REFACTORED
Last Updated: 24/09/2025
Author: Antonio VB

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
        self.magazzino_window = None
        self.anagrafica_clienti_window = None
        self.impostazioni_archiviazione_window = None

        # Inizializzazione UI delegata al modulo
        MainWindowUIComponents.init_ui(self)

        # Se il controllo di integrità all'avvio ha rilevato un problema,
        # avvisa subito l'utente invece di lasciarlo lavorare su dati rovinati.
        if getattr(self.db_manager, "avviso_integrita", None):
            QMessageBox.critical(self, "Problema con il database",
                                 self.db_manager.avviso_integrita)

        # Dopo uno spegnimento improvviso: proponi di riaprire i preventivi
        # rimasti non salvati. Va fatto qui e non prima, perché serve
        # l'interfaccia già pronta per poterli riaprire davvero.
        try:
            MainWindowBusinessLogic.proponi_recupero_bozze(self)
        except Exception:
            pass   # il recupero non deve mai impedire l'uso del programma

    def closeEvent(self, event):
        """Chiusura regolare: toglie questo PC dall'elenco delle sessioni aperte
        e cancella il marcatore, così al prossimo avvio si sa che la chiusura
        è avvenuta correttamente."""
        try:
            from database import backup_manager
            backup_manager.chiudi_sessione(self.db_manager.db_path)
        except Exception:
            pass
        try:
            from utils import diagnostica
            diagnostica.segna_chiusura_regolare()
        except Exception:
            pass
        super().closeEvent(event)

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

    def apri_magazzino(self):
        """Apre la finestra per gestire il magazzino"""
        MainWindowBusinessLogic.apri_magazzino(self)

    def apri_anagrafica_clienti(self):
        """Apre la finestra per gestire l'anagrafica clienti"""
        MainWindowBusinessLogic.apri_anagrafica_clienti(self)
    
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

    def cambia_database(self):
        """Permette di selezionare un database diverso (es. cartella condivisa in rete)"""
        MainWindowBusinessLogic.cambia_database(self)

    def apri_impostazioni_archiviazione(self):
        """Apre la schermata con stato dei dati, copie di sicurezza e database"""
        MainWindowBusinessLogic.apri_impostazioni_archiviazione(self)

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
            
        