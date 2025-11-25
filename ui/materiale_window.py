#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MaterialeWindow - Interfaccia di calcolo materiali REFACTORIZZATA con FIX sviluppo manuale

Version: 2.2.0 - REFACTORED
Last Updated: 23/09/2025
Author: Antonio VB & Claude

CHANGELOG:
v2.2.0 (23/09/2025):
- REFACTORED: Estratta logica UI in materiale_ui_components.py
- REFACTORED: Estratta business logic in materiale_business_logic.py
- FIXED: Problema sviluppo manuale - reset quando cambiano parametri
- FIXED: Solo campo "Sviluppo Manuale" non resetta sviluppo manuale
- MAINTAINED: Design originale identico
- IMPROVED: Codice modulare e debug integrato
"""

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import pyqtSignal
from models.materiale import MaterialeCalcolato

# MODULI REFACTORIZZATI
from ui.materiale_ui_components import MaterialeUIComponents
from ui.materiale_business_logic import MaterialeBusinessLogic

class MaterialeWindow(QMainWindow):
    materiale_confermato = pyqtSignal(MaterialeCalcolato, object)
    
    def __init__(self, db_manager, diametro_iniziale=0.0, materiale_esistente=None, indice_modifica=None, parent=None, modalita_sola_lettura=False):
        super().__init__(parent)
        self.db_manager = db_manager
        self.diametro_iniziale = diametro_iniziale
        self.materiale_esistente = materiale_esistente
        self.indice_modifica = indice_modifica
        self.modalita_sola_lettura = modalita_sola_lettura
        self.materiale_calcolato = MaterialeCalcolato()
        self.materiali_disponibili = []
        
        # Flag per controllo sviluppo manuale - FIX
        self.arrotondamento_modificato_manualmente = False
        
        if materiale_esistente:
            self.materiale_calcolato = MaterialeBusinessLogic.copia_materiale(materiale_esistente)
        
        # Inizializza UI - DELEGATO
        MaterialeUIComponents.init_ui(self)
        
        # Carica materiali - DELEGATO
        MaterialeBusinessLogic.carica_materiali(self)
        
        # Carica dati esistenti se necessario - DELEGATO
        if materiale_esistente:
            MaterialeBusinessLogic.carica_dati_esistenti(self)
        elif diametro_iniziale > 0:
            self.edit_diametro.setValue(diametro_iniziale)
            self.materiale_calcolato.diametro = diametro_iniziale
    
    # ========== CALLBACK METHODS - FIX SVILUPPO MANUALE ==========
    
    def on_materiale_changed(self):
        """FIX: Gestisce cambio materiale e reset sviluppo manuale - DELEGATO"""
        MaterialeBusinessLogic.on_materiale_changed(self)
    
    def on_parametro_changed(self):
        """FIX: Gestisce cambio parametri e reset sviluppo manuale - DELEGATO"""
        MaterialeBusinessLogic.on_parametro_changed(self)
    
    def on_sviluppo_manuale_changed(self):
        """FIX: Gestisce SOLO il cambio del campo sviluppo manuale - DELEGATO"""
        MaterialeBusinessLogic.on_sviluppo_manuale_changed(self)
    
    # ========== BUSINESS LOGIC METHODS - DELEGATI ==========
    
    def materiale_selezionato(self):
        """Gestisce la selezione di un materiale - DELEGATO"""
        MaterialeBusinessLogic.materiale_selezionato(self)
    
    def ricalcola_tutto(self):
        """Ricalcola tutti i valori con logica sviluppo manuale - DELEGATO"""
        MaterialeBusinessLogic.ricalcola_tutto(self)
    
    def aggiorna_display(self):
        """Aggiorna tutti i valori mostrati nell'interfaccia - DELEGATO"""
        MaterialeBusinessLogic.aggiorna_display(self)
    
    def concludi_operazione(self):
        """Valida e conferma il materiale - DELEGATO"""
        MaterialeBusinessLogic.concludi_operazione(self)
    
    # ========== COMPATIBILITY METHODS ==========
    
    def copia_materiale(self, materiale_originale):
        """Copia un materiale esistente - DELEGATO per compatibilità"""
        return MaterialeBusinessLogic.copia_materiale(materiale_originale)
    
    def carica_materiali(self):
        """Carica la lista dei materiali disponibili - DELEGATO per compatibilità"""
        MaterialeBusinessLogic.carica_materiali(self)
    
    def carica_dati_esistenti(self):
        """Carica i dati di un materiale esistente - DELEGATO per compatibilità"""
        MaterialeBusinessLogic.carica_dati_esistenti(self)
    
    def arrotondamento_modificato(self):
        """Compatibilità con codice esistente - DELEGATO"""
        self.on_sviluppo_manuale_changed()
    
    # ========== EVENT HANDLERS ==========
    
    def closeEvent(self, event):
        """Gestisce chiusura finestra - DELEGATO"""
        MaterialeBusinessLogic.gestisci_chiusura_finestra(self, event)