#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
PreventivoWindow - Interfaccia calcolo preventivi con nuovi campi cliente
Uso riservato esclusivamente a RCS

Version: 2.3.1
Last Updated: 22/09/2025
Author: Antonio VB C.ass

CHANGELOG:
v2.3.1 (22/09/2025):
- FIXED: Problema caricamento valori mano d'opera rimossa chiamata aggiorna_totali() dal costruttore
v2.3.0 (22/09/2025):
- ADDED: Campi cliente (nome_cliente, numero_ordine, descrizione, codice)
- ADDED: Sezione "Informazioni Cliente" nell'interfaccia
- UPDATED: Metodi salvataggio per includere i nuovi campi
- MAINTAINED: Design system e funzionalità esistenti identiche
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
                             QWidget, QLabel, QLineEdit, QFormLayout, QMessageBox,
                             QScrollArea, QGroupBox, QSpinBox, QDoubleSpinBox,
                             QDialog, QListWidget, QListWidgetItem, QGridLayout, QFrame,
                             QSizePolicy, QApplication, QGraphicsDropShadowEffect, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QDoubleValidator, QColor
from models.preventivo import Preventivo
from models.materiale import MaterialeCalcolato
from ui.materiale_window import MaterialeWindow
import json

class PreventivoWindow(QMainWindow):
    preventivo_salvato = pyqtSignal()
    
    def __init__(self, db_manager, parent=None, preventivo_id=None, modalita='nuovo', note_revisione=""):
        super().__init__(None)  # No parent per evitare bug ridimensionamento
        self.db_manager = db_manager
        
        # Parametri per sistema revisioni
        self.preventivo_id = preventivo_id
        self.modalita = modalita  # 'nuovo', 'visualizza', 'revisione'
        self.note_revisione = note_revisione
        self.preventivo_originale_id = None
        
        self.preventivo = Preventivo()
        self.materiale_windows = []
        self.operazione_completata = False  # Flag per evitare popup se operazione completata
        
        # Se stiamo caricando un preventivo esistente
        if preventivo_id:
            self.carica_preventivo_esistente()
        
        self.init_ui()
        # RIMOSSA: self.aggiorna_totali() - causava azzeramento dei valori caricati
    
    def carica_preventivo_esistente(self):
        """Carica un preventivo esistente dal database"""
        preventivo_data = self.db_manager.get_preventivo_by_id(self.preventivo_id)
        if not preventivo_data:
            QMessageBox.critical(self, "Errore", "Preventivo non trovato nel database.")
            return
        
        # Carica i dati del preventivo (inclusi i nuovi campi)
        self.nome_cliente_data = preventivo_data.get('nome_cliente', '')
        self.numero_ordine_data = preventivo_data.get('numero_ordine', '')
        self.descrizione_data = preventivo_data.get('descrizione', '')
        self.codice_data = preventivo_data.get('codice', '')
        self.misura_data = preventivo_data.get('misura', '')

        # IMPORTANTE: Carica TUTTI i valori numerici e verifica che siano validi
        self.preventivo.costi_accessori = float(preventivo_data.get('costi_accessori', 0.0))
        self.preventivo.minuti_taglio = float(preventivo_data.get('minuti_taglio', 0.0))
        self.preventivo.minuti_avvolgimento = float(preventivo_data.get('minuti_avvolgimento', 0.0))
        self.preventivo.minuti_pulizia = float(preventivo_data.get('minuti_pulizia', 0.0))
        self.preventivo.minuti_rettifica = float(preventivo_data.get('minuti_rettifica', 0.0))
        self.preventivo.minuti_imballaggio = float(preventivo_data.get('minuti_imballaggio', 0.0))
        self.preventivo.prezzo_cliente = float(preventivo_data.get('prezzo_cliente', 0.0))
        
        # Carica i materiali
        materiali_json = preventivo_data.get('materiali_utilizzati', '[]')
        try:
            materiali_data = json.loads(materiali_json) if isinstance(materiali_json, str) else materiali_json
            for mat_data in materiali_data:
                materiale = MaterialeCalcolato()
                materiale.diametro = mat_data.get('diametro', 0.0)
                materiale.lunghezza = mat_data.get('lunghezza', 0.0)
                materiale.materiale_id = mat_data.get('materiale_id', None)
                materiale.materiale_nome = mat_data.get('materiale_nome', "")
                materiale.giri = mat_data.get('giri', 0)
                materiale.spessore = mat_data.get('spessore', 0.0)
                materiale.diametro_finale = mat_data.get('diametro_finale', 0.0)
                # Compatibilità stratifica/sviluppo
                materiale.sviluppo = mat_data.get('sviluppo', mat_data.get('stratifica', 0.0))
                materiale.arrotondamento_manuale = mat_data.get('arrotondamento_manuale', 0.0)
                materiale.costo_materiale = mat_data.get('costo_materiale', 0.0)
                materiale.lunghezza_utilizzata = mat_data.get('lunghezza_utilizzata', 0.0)
                materiale.costo_totale = mat_data.get('costo_totale', 0.0)
                materiale.maggiorazione = mat_data.get('maggiorazione', 0.0)
                
                self.preventivo.materiali_calcolati.append(materiale)
        except (json.JSONDecodeError, TypeError):
            QMessageBox.warning(self, "Attenzione", "Errore nel caricamento dei materiali del preventivo.")
        
        # Salva l'ID originale per le revisioni
        if preventivo_data.get('preventivo_originale_id'):
            self.preventivo_originale_id = preventivo_data['preventivo_originale_id']
        else:
            self.preventivo_originale_id = self.preventivo_id
        
        # Ricalcola tutto DOPO aver caricato i dati
        self.preventivo.ricalcola_tutto()
    
    def init_ui(self):
        """Design system unificato con nuovi campi cliente"""
        # Titolo dinamico basato sulla modalità
        if self.modalita == 'visualizza':
            title = f"Visualizzazione Preventivo #{self.preventivo_id:03d}"
        elif self.modalita == 'revisione':
            title = f"Revisione Preventivo #{self.preventivo_originale_id:03d}"
        elif self.modalita == 'modifica':
            title = f"Modifica Preventivo #{self.preventivo_id:03d}"
        else:
            title = "Calcolo Preventivo"
            
        self.setWindowTitle(title)

        # Stile unificato (IDENTICO ALL'ORIGINALE)
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
            QDoubleSpinBox, QSpinBox, QLineEdit, QTextEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 14px;
                background-color: #ffffff;
                color: #2d3748;
                min-height: 18px;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QDoubleSpinBox:focus, QSpinBox:focus, QLineEdit:focus, QTextEdit:focus {
                border-color: #718096;
                outline: none;
            }
            QDoubleSpinBox:hover, QSpinBox:hover, QLineEdit:hover, QTextEdit:hover {
                border-color: #a0aec0;
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
        
        # Layout principale
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(20)
        
        # Header
        self.create_header(main_layout)
        
        # NUOVO: Sezione informazioni cliente
        self.create_client_info_section(main_layout)
        
        # Contenuto principale - layout responsive a tre colonne
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)
        
        self.create_left_column(content_layout)   # Materiali
        self.create_middle_column(content_layout) # Tempi
        self.create_right_column(content_layout)  # Costi e Totali
        
        main_layout.addLayout(content_layout, 1)
        
        # Footer
        self.create_footer(main_layout)
        
        # Imposta dimensione minima ragionevole per schermi 1080p e apri massimizzato
        self.setMinimumSize(800, 600)
        self.showMaximized()

        # IMPORTANTE: Carica i valori nei campi SOLO DOPO che tutti i controlli sono stati creati
        if self.preventivo_id:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self.carica_valori_con_delay)  # 100ms delay

        # DOPO il caricamento, disabilita solo se necessario
        if self.modalita == 'visualizza':
            QTimer.singleShot(150, self.disabilita_solo_controlli)  # Dopo il caricamento
    
    def create_client_info_section(self, parent_layout):
        """NUOVO: Sezione informazioni cliente"""
        client_group = QGroupBox("Informazioni Cliente")
        client_group.setGraphicsEffect(self.create_shadow_effect())
        
        client_layout = QFormLayout(client_group)
        client_layout.setContentsMargins(25, 28, 25, 25)
        client_layout.setVerticalSpacing(16)
        client_layout.setHorizontalSpacing(16)
        
        # Campi cliente in layout a griglia per sfruttare lo spazio
        client_grid_widget = QWidget()
        client_grid = QGridLayout(client_grid_widget)
        client_grid.setSpacing(16)
        
        # Prima riga: Nome Cliente e Numero Ordine
        client_grid.addWidget(self.create_standard_label("Nome Cliente:"), 0, 0)
        self.edit_nome_cliente = QLineEdit()
        client_grid.addWidget(self.edit_nome_cliente, 0, 1)
        
        client_grid.addWidget(self.create_standard_label("Numero Ordine:"), 0, 2)
        self.edit_numero_ordine = QLineEdit()
        client_grid.addWidget(self.edit_numero_ordine, 0, 3)
        
        # Seconda riga: Codice, Misura e Finitura
        client_grid.addWidget(self.create_standard_label("Codice:"), 1, 0)
        self.edit_codice = QLineEdit()
        client_grid.addWidget(self.edit_codice, 1, 1)

        client_grid.addWidget(self.create_standard_label("Misura:"), 1, 2)
        self.edit_misura = QLineEdit()
        client_grid.addWidget(self.edit_misura, 1, 3)

        client_grid.addWidget(self.create_standard_label("Finitura:"), 1, 4)
        self.edit_finitura = QLineEdit()
        client_grid.addWidget(self.edit_finitura, 1, 5)

        # Terza riga: Descrizione (LineEdit semplice con limite caratteri)
        client_grid.addWidget(self.create_standard_label("Descrizione:"), 2, 0)
        self.edit_descrizione = QLineEdit()
        self.edit_descrizione.setMaxLength(100)  # Limite a 100 caratteri
        client_grid.addWidget(self.edit_descrizione, 2, 1, 1, 5)  # Span su 5 colonne
        
        client_layout.addRow(client_grid_widget)
        
        # Carica i dati se esistenti
        if hasattr(self, 'nome_cliente_data'):
            self.edit_nome_cliente.setText(self.nome_cliente_data)
            self.edit_numero_ordine.setText(self.numero_ordine_data)
            self.edit_descrizione.setText(self.descrizione_data)
            self.edit_codice.setText(self.codice_data)
            if hasattr(self, 'misura_data'):
                self.edit_misura.setText(self.misura_data)
            if hasattr(self, 'finitura_data'):
                self.edit_finitura.setText(self.finitura_data)

        parent_layout.addWidget(client_group)
    
    def disabilita_solo_controlli(self):
        """Disabilita solo i controlli senza ricaricare i valori (per modalità visualizzazione)"""
        # Disabilita i campi cliente
        self.edit_nome_cliente.setEnabled(False)
        self.edit_numero_ordine.setEnabled(False)
        self.edit_descrizione.setEnabled(False)
        self.edit_codice.setEnabled(False)
        self.edit_misura.setEnabled(False)
        self.edit_finitura.setEnabled(False)

        # Disabilita tutti i SpinBox
        self.edit_minuti_taglio.setEnabled(False)
        self.edit_minuti_avvolgimento.setEnabled(False)
        self.edit_minuti_pulizia.setEnabled(False)
        self.edit_minuti_rettifica.setEnabled(False)
        self.edit_minuti_imballaggio.setEnabled(False)
        self.edit_costi_accessori.setEnabled(False)
        self.edit_prezzo_cliente.setEnabled(False)
        
        # Disabilita pulsanti di modifica
        if hasattr(self, 'btn_aggiungi_materiale'):
            self.btn_aggiungi_materiale.setEnabled(False)
    
    def create_shadow_effect(self, blur=10, opacity=12):
        """Effetto ombra standardizzato"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setColor(QColor(0, 0, 0, opacity))
        shadow.setOffset(0, 2)
        return shadow
    
    def create_header(self, parent_layout):
        """Header unificato - DINAMICO per modalità"""
        if self.modalita == 'visualizza':
            title_text = f"Visualizzazione Preventivo #{self.preventivo_id:03d}"
        elif self.modalita == 'revisione':
            title_text = f"Revisione Preventivo #{self.preventivo_originale_id:03d}"
        elif self.modalita == 'modifica':
            title_text = f"Modifica Preventivo #{self.preventivo_id:03d}"
        else:
            title_text = "Calcolo Preventivo"
            
        title_label = QLabel(title_text)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 700;
                color: #2d3748;
                padding: 0;
            }
        """)
        parent_layout.addWidget(title_label)
    
    def create_left_column(self, parent_layout):
        """Colonna materiali - stile unificato e responsive"""
        column_widget = QWidget()
        column_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(column_widget)
        layout.setSpacing(20)
        
        # Sezione materiali
        materiali_group = QGroupBox("Materiali")
        materiali_group.setGraphicsEffect(self.create_shadow_effect())
        
        materiali_layout = QVBoxLayout(materiali_group)
        materiali_layout.setContentsMargins(25, 28, 25, 25)
        materiali_layout.setSpacing(16)
        
        # Info costo materiali
        self.create_cost_info_card(materiali_layout)
        
        # Pulsanti materiali
        self.create_material_buttons(materiali_layout)
        
        layout.addWidget(materiali_group)
        layout.addStretch()
        
        parent_layout.addWidget(column_widget)
    
    def create_middle_column(self, parent_layout):
        """Colonna tempi - stile unificato e responsive"""
        column_widget = QWidget()
        column_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(column_widget)
        layout.setSpacing(20)
        
        # Sezione tempi
        tempi_group = QGroupBox("Tempi di Lavorazione")
        tempi_group.setGraphicsEffect(self.create_shadow_effect())
        
        tempi_layout = QVBoxLayout(tempi_group)
        tempi_layout.setContentsMargins(25, 28, 25, 25)
        tempi_layout.setSpacing(16)
        
        # Form tempi
        self.create_time_form(tempi_layout)
        
        # Totale mano d'opera
        self.create_total_time_card(tempi_layout)
        
        layout.addWidget(tempi_group)
        layout.addStretch()
        
        parent_layout.addWidget(column_widget)
    
    def create_right_column(self, parent_layout):
        """Colonna costi e totali - stile unificato e responsive"""
        column_widget = QWidget()
        column_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(column_widget)
        layout.setSpacing(20)
        
        # Sezione costi accessori
        costi_group = QGroupBox("Costi Accessori")
        costi_group.setGraphicsEffect(self.create_shadow_effect())
        
        costi_layout = QVBoxLayout(costi_group)
        costi_layout.setContentsMargins(25, 28, 25, 25)
        costi_layout.setSpacing(16)
        
        self.create_accessory_costs_form(costi_layout)
        
        layout.addWidget(costi_group)
        
        # Sezione totali
        totali_group = QGroupBox("Riepilogo Finale")
        totali_group.setGraphicsEffect(self.create_shadow_effect())
        
        totali_layout = QVBoxLayout(totali_group)
        totali_layout.setContentsMargins(25, 28, 25, 25)
        totali_layout.setSpacing(16)
        
        self.create_totals_summary(totali_layout)
        
        layout.addWidget(totali_group)
        layout.addStretch()
        
        parent_layout.addWidget(column_widget)
    
    def create_cost_info_card(self, parent_layout):
        """Card info costo materiali"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 20px;
                margin: 2px 0px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        
        # Costo totale
        self.lbl_costo_totale_materiali = QLabel("€ 0,00")
        self.lbl_costo_totale_materiali.setStyleSheet("""
            QLabel {
                color: #2d3748;
                font-size: 20px;
                font-weight: 700;
                font-family: system-ui, -apple-system, sans-serif;
            }
        """)
        
        desc_label = QLabel("Costo Totale Materiali")
        desc_label.setStyleSheet("""
            QLabel {
                color: #4a5568;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        
        # Info materiali
        self.lbl_num_materiali = QLabel("Nessun materiale inserito")
        self.lbl_num_materiali.setStyleSheet("""
            QLabel {
                color: #718096;
                font-size: 13px;
                font-weight: 500;
            }
        """)
        
        layout.addWidget(self.lbl_costo_totale_materiali)
        layout.addWidget(desc_label)
        layout.addWidget(self.lbl_num_materiali)
        
        parent_layout.addWidget(container)
    
    def create_material_buttons(self, parent_layout):
        """Pulsanti materiali standardizzati - ADATTATO per modalità"""
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(12)
        
        if self.modalita != 'visualizza':
            # Aggiungi materiale
            self.btn_aggiungi_materiale = QPushButton("Aggiungi Materiale")
            self.btn_aggiungi_materiale.setStyleSheet("""
                QPushButton {
                    background-color: #4a5568;
                    color: #ffffff;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #2d3748;
                }
            """)
            self.btn_aggiungi_materiale.clicked.connect(self.aggiungi_materiale)
            
            # Visualizza materiali
            self.btn_visualizza_materiali = QPushButton("Visualizza e Modifica")
            self.btn_visualizza_materiali.setStyleSheet("""
                QPushButton {
                    background-color: #f7fafc;
                    color: #4a5568;
                    border: 1px solid #e2e8f0;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #edf2f7;
                }
                QPushButton:disabled {
                    background-color: #f7fafc;
                    color: #a0aec0;
                    border-color: #e2e8f0;
                }
            """)
            self.btn_visualizza_materiali.clicked.connect(self.visualizza_materiali)
            self.btn_visualizza_materiali.setEnabled(False)
            
            buttons_layout.addWidget(self.btn_aggiungi_materiale)
            buttons_layout.addWidget(self.btn_visualizza_materiali)
        else:
            # Solo visualizzazione materiali
            self.btn_visualizza_materiali = QPushButton("Visualizza Materiali")
            self.btn_visualizza_materiali.setStyleSheet("""
                QPushButton {
                    background-color: #f7fafc;
                    color: #4a5568;
                    border: 1px solid #e2e8f0;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #edf2f7;
                }
            """)
            self.btn_visualizza_materiali.clicked.connect(self.visualizza_materiali)
            buttons_layout.addWidget(self.btn_visualizza_materiali)
        
        parent_layout.addLayout(buttons_layout)
    
    def create_time_form(self, parent_layout):
        """Form tempi standardizzato"""
        # Layout a griglia per i tempi
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)
        grid_layout.setVerticalSpacing(16)
        
        # Campi tempi
        self.edit_minuti_taglio = self.create_standard_spinbox("min")
        self.edit_minuti_avvolgimento = self.create_standard_spinbox("min")
        self.edit_minuti_pulizia = self.create_standard_spinbox("min")
        self.edit_minuti_rettifica = self.create_standard_spinbox("min")
        self.edit_minuti_imballaggio = self.create_standard_spinbox("min")
        
        # Aggiunta alla griglia
        grid_layout.addWidget(self.create_standard_label("Taglio:"), 0, 0)
        grid_layout.addWidget(self.edit_minuti_taglio, 0, 1)
        grid_layout.addWidget(self.create_standard_label("Avvolgimento:"), 1, 0)
        grid_layout.addWidget(self.edit_minuti_avvolgimento, 1, 1)
        grid_layout.addWidget(self.create_standard_label("Pulizia:"), 2, 0)
        grid_layout.addWidget(self.edit_minuti_pulizia, 2, 1)
        grid_layout.addWidget(self.create_standard_label("Rettifica:"), 3, 0)
        grid_layout.addWidget(self.edit_minuti_rettifica, 3, 1)
        grid_layout.addWidget(self.create_standard_label("Imballaggio:"), 4, 0)
        grid_layout.addWidget(self.edit_minuti_imballaggio, 4, 1)
        
        parent_layout.addLayout(grid_layout)
    
    def create_total_time_card(self, parent_layout):
        """Card totale mano d'opera"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #f0fff4;
                border: 1px solid #68d391;
                border-radius: 8px;
                padding: 16px;
                margin: 4px 0px;
            }
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("Totale Mano d'Opera:")
        title_label.setStyleSheet("""
            QLabel {
                color: #2d3748;
                font-size: 14px;
                font-weight: 600;
            }
        """)
        
        self.lbl_tot_mano_opera = QLabel("0,00 min")
        self.lbl_tot_mano_opera.setStyleSheet("""
            QLabel {
                color: #2d3748;
                font-size: 16px;
                font-weight: 700;
                font-family: system-ui, -apple-system, sans-serif;
            }
        """)
        
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(self.lbl_tot_mano_opera)
        
        parent_layout.addWidget(container)
    
    def create_accessory_costs_form(self, parent_layout):
        """Form costi accessori"""
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(16)
        form_layout.setHorizontalSpacing(16)
        
        self.edit_costi_accessori = self.create_standard_spinbox("€")
        form_layout.addRow(self.create_standard_label("Costi Accessori:"), self.edit_costi_accessori)
        
        parent_layout.addLayout(form_layout)
    
    def create_totals_summary(self, parent_layout):
        """Riepilogo totali"""
        # Totali intermedi
        self.create_summary_row("Subtotale:", "lbl_subtotale", "€ 0,00", parent_layout)
        self.create_summary_row("Maggiorazione 25%:", "lbl_maggiorazione_25", "€ 0,00", parent_layout)
        
        # Preventivo finale evidenziato
        final_container = QFrame()
        final_container.setStyleSheet("""
            QFrame {
                background-color: #f0fff4;
                border: 2px solid #68d391;
                border-radius: 8px;
                margin: 8px 0px;
            }
        """)
        final_container.setMinimumHeight(50)

        final_layout = QHBoxLayout(final_container)
        final_layout.setContentsMargins(16, 12, 16, 12)
        
        final_title = QLabel("Preventivo Finale:")
        final_title.setStyleSheet("""
            QLabel {
                color: #2d3748;
                font-size: 16px;
                font-weight: 700;
            }
        """)
        
        self.lbl_preventivo_finale = QLabel("€ 0,00")
        self.lbl_preventivo_finale.setStyleSheet("""
            QLabel {
                color: #2d3748;
                font-size: 18px;
                font-weight: 800;
                font-family: system-ui, -apple-system, sans-serif;
            }
        """)
        
        final_layout.addWidget(final_title)
        final_layout.addStretch()
        final_layout.addWidget(self.lbl_preventivo_finale)
        
        parent_layout.addWidget(final_container)
        
        # Prezzo cliente
        client_form = QFormLayout()
        client_form.setVerticalSpacing(16)
        client_form.setHorizontalSpacing(16)
        
        self.edit_prezzo_cliente = self.create_standard_spinbox("€")
        client_form.addRow(self.create_standard_label("Prezzo Cliente:"), self.edit_prezzo_cliente)
        
        parent_layout.addLayout(client_form)
    
    def create_summary_row(self, title, attr_name, default_value, parent_layout):
        """Riga riepilogo standardizzata"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                padding: 8px 0px;
                margin: 2px 0px;
            }
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #4a5568;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        
        value_label = QLabel(default_value)
        value_label.setStyleSheet("""
            QLabel {
                color: #2d3748;
                font-size: 15px;
                font-weight: 600;
                font-family: system-ui, -apple-system, sans-serif;
            }
        """)
        
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(value_label)
        
        setattr(self, attr_name, value_label)
        parent_layout.addWidget(container)
    
    def create_standard_spinbox(self, suffix="€"):
        """SpinBox standardizzato"""
        spinbox = QDoubleSpinBox()
        spinbox.setMaximum(999999.99)
        spinbox.setDecimals(2)
        if suffix:
            spinbox.setSuffix(f" {suffix}")
        spinbox.setMinimumHeight(36)
        spinbox.valueChanged.connect(self.aggiorna_totali)
        return spinbox
    
    def create_standard_label(self, text):
        """Label standardizzata"""
        label = QLabel(text)
        label.setStyleSheet("""
            QLabel {
                color: #4a5568;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        return label
    
    def create_footer(self, parent_layout):
        """Footer standardizzato - ADATTATO per modalità"""
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        if self.modalita == 'visualizza':
            # Solo pulsante Chiudi
            btn_chiudi = QPushButton("Chiudi")
            btn_chiudi.setStyleSheet("""
                QPushButton {
                    background-color: #f7fafc;
                    color: #4a5568;
                    border: 1px solid #e2e8f0;
                    min-height: 32px;
                    max-width: 120px;
                }
                QPushButton:hover {
                    background-color: #edf2f7;
                }
            """)
            btn_chiudi.clicked.connect(self.close)
            footer_layout.addWidget(btn_chiudi)
        else:
            # Annulla
            self.btn_annulla = QPushButton("Annulla")
            self.btn_annulla.setStyleSheet("""
                QPushButton {
                    background-color: #f7fafc;
                    color: #4a5568;
                    border: 1px solid #e2e8f0;
                    min-height: 32px;
                    max-width: 120px;
                }
                QPushButton:hover {
                    background-color: #edf2f7;
                }
            """)
            self.btn_annulla.clicked.connect(self.close)
            
            # Salva/Salva Revisione
            if self.modalita == 'revisione':
                btn_text = "Salva Revisione"
                btn_method = self.salva_revisione
            else:
                btn_text = "Salva Preventivo"
                btn_method = self.salva_preventivo
                
            self.btn_salva_preventivo = QPushButton(btn_text)
            self.btn_salva_preventivo.setStyleSheet("""
                QPushButton {
                    background-color: #4a5568;
                    color: #ffffff;
                    min-height: 32px;
                    max-width: 160px;
                }
                QPushButton:hover {
                    background-color: #2d3748;
                }
            """)
            self.btn_salva_preventivo.clicked.connect(btn_method)
            
            footer_layout.addWidget(self.btn_annulla)
            footer_layout.addSpacing(12)
            footer_layout.addWidget(self.btn_salva_preventivo)
        
        parent_layout.addLayout(footer_layout)
    
    # =================== METODI FUNZIONALI ===================
    
    def get_dati_cliente(self):
        """Raccoglie i dati cliente dai campi"""
        return {
            'nome_cliente': self.edit_nome_cliente.text().strip(),
            'numero_ordine': self.edit_numero_ordine.text().strip(),
            'descrizione': self.edit_descrizione.text().strip(),
            'codice': self.edit_codice.text().strip(),
            'misura': self.edit_misura.text().strip(),
            'finitura': self.edit_finitura.text().strip()
        }
    
    def carica_valori_con_delay(self):
        """Carica i valori con delay per assicurarsi che l'interfaccia sia pronta"""
        # Forza elaborazione eventi
        QApplication.processEvents()
        
        # Carica dati cliente
        if hasattr(self, 'nome_cliente_data'):
            self.edit_nome_cliente.setText(self.nome_cliente_data or "")
            self.edit_numero_ordine.setText(self.numero_ordine_data or "")
            self.edit_descrizione.setText(self.descrizione_data or "")
            self.edit_codice.setText(self.codice_data or "")
            if hasattr(self, 'misura_data'):
                self.edit_misura.setText(self.misura_data or "")
            if hasattr(self, 'finitura_data'):
                self.edit_finitura.setText(self.finitura_data or "")

        # Imposta valori mano d'opera
        try:
            # Blocca segnali
            self.edit_minuti_taglio.blockSignals(True)
            self.edit_minuti_avvolgimento.blockSignals(True)
            self.edit_minuti_pulizia.blockSignals(True)
            self.edit_minuti_rettifica.blockSignals(True)
            self.edit_minuti_imballaggio.blockSignals(True)
            self.edit_costi_accessori.blockSignals(True)
            self.edit_prezzo_cliente.blockSignals(True)
            
            # Imposta valori
            self.edit_minuti_taglio.setValue(float(self.preventivo.minuti_taglio or 0))
            self.edit_minuti_avvolgimento.setValue(float(self.preventivo.minuti_avvolgimento or 0))
            self.edit_minuti_pulizia.setValue(float(self.preventivo.minuti_pulizia or 0))
            self.edit_minuti_rettifica.setValue(float(self.preventivo.minuti_rettifica or 0))
            self.edit_minuti_imballaggio.setValue(float(self.preventivo.minuti_imballaggio or 0))
            self.edit_costi_accessori.setValue(float(self.preventivo.costi_accessori or 0))
            self.edit_prezzo_cliente.setValue(float(self.preventivo.prezzo_cliente or 0))
            
            # Sblocca segnali
            self.edit_minuti_taglio.blockSignals(False)
            self.edit_minuti_avvolgimento.blockSignals(False)
            self.edit_minuti_pulizia.blockSignals(False)
            self.edit_minuti_rettifica.blockSignals(False)
            self.edit_minuti_imballaggio.blockSignals(False)
            self.edit_costi_accessori.blockSignals(False)
            self.edit_prezzo_cliente.blockSignals(False)
            
            # Aggiorna interfaccia
            self.aggiorna_materiali_info()
            self.aggiorna_totali()
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nel caricamento valori: {str(e)}")
    
    def salva_preventivo(self):
        """Salva preventivo"""
        if not self.preventivo.materiali_calcolati:
            QMessageBox.warning(self, "Attenzione", 
                              "Aggiungi almeno un materiale prima di salvare il preventivo.")
            return
        
        # Aggiorna valori dall'interfaccia
        self.preventivo.prezzo_cliente = self.edit_prezzo_cliente.value()
        self.preventivo.costi_accessori = self.edit_costi_accessori.value()
        self.preventivo.minuti_taglio = self.edit_minuti_taglio.value()
        self.preventivo.minuti_avvolgimento = self.edit_minuti_avvolgimento.value()
        self.preventivo.minuti_pulizia = self.edit_minuti_pulizia.value()
        self.preventivo.minuti_rettifica = self.edit_minuti_rettifica.value()
        self.preventivo.minuti_imballaggio = self.edit_minuti_imballaggio.value()
        
        # Ricalcola totali
        self.preventivo.ricalcola_tutto()
        
        try:
            # Unisci dati preventivo con dati cliente
            preventivo_data = self.preventivo.to_dict()
            preventivo_data.update(self.get_dati_cliente())
            
            # Se modifica preventivo esistente
            if hasattr(self, 'preventivo_id') and self.preventivo_id and self.modalita == 'modifica':
                success = self.db_manager.update_preventivo(self.preventivo_id, preventivo_data)
                if success:
                    QMessageBox.information(self, "Successo!", 
                                          f"Preventivo #{self.preventivo_id:03d} modificato con successo!")
                    self.operazione_completata = True
                    self.preventivo_salvato.emit()
                    self.close()
                else:
                    QMessageBox.critical(self, "Errore", "Errore durante la modifica del preventivo.")
            else:
                # Crea nuovo preventivo
                preventivo_id = self.db_manager.save_preventivo(preventivo_data)
                QMessageBox.information(self, "Successo!", 
                                      f"Preventivo salvato con successo\n\nID: #{preventivo_id:03d}")
                self.operazione_completata = True
                self.preventivo_salvato.emit()
                self.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio:\n{str(e)}")
    
    def salva_revisione(self):
        """Salva revisione"""
        if not self.preventivo.materiali_calcolati:
            QMessageBox.warning(self, "Attenzione", "Aggiungi almeno un materiale prima di salvare.")
            return
        
        # Aggiorna valori dall'interfaccia
        self.preventivo.prezzo_cliente = self.edit_prezzo_cliente.value()
        self.preventivo.costi_accessori = self.edit_costi_accessori.value()
        self.preventivo.minuti_taglio = self.edit_minuti_taglio.value()
        self.preventivo.minuti_avvolgimento = self.edit_minuti_avvolgimento.value()
        self.preventivo.minuti_pulizia = self.edit_minuti_pulizia.value()
        self.preventivo.minuti_rettifica = self.edit_minuti_rettifica.value()
        self.preventivo.minuti_imballaggio = self.edit_minuti_imballaggio.value()
        
        # Ricalcola totali
        self.preventivo.ricalcola_tutto()
        
        try:
            # Unisci dati preventivo con dati cliente
            preventivo_data = self.preventivo.to_dict()
            preventivo_data.update(self.get_dati_cliente())
            
            revisione_id = self.db_manager.add_revisione_preventivo(
                self.preventivo_originale_id,
                preventivo_data,
                self.note_revisione
            )
            if revisione_id:
                QMessageBox.information(self, "Revisione Salvata", 
                                      f"Revisione salvata con successo!\nID: #{revisione_id:03d}")
                self.operazione_completata = True
                self.preventivo_salvato.emit()
                self.close()
            else:
                QMessageBox.critical(self, "Errore", "Errore durante il salvataggio della revisione.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio:\n{str(e)}")
    
    def aggiungi_materiale(self):
        """Aggiungi nuovo materiale"""
        if len(self.preventivo.materiali_calcolati) >= 30:
            QMessageBox.warning(self, "Limite Raggiunto",
                              "Hai raggiunto il limite massimo di 30 materiali.")
            return
        
        diametro_iniziale = 0.0
        if self.preventivo.materiali_calcolati:
            ultimo_materiale = self.preventivo.materiali_calcolati[-1]
            diametro_iniziale = ultimo_materiale.diametro_finale
        
        materiale_window = MaterialeWindow(
            self.db_manager, 
            diametro_iniziale=diametro_iniziale,
            parent=self
        )
        materiale_window.materiale_confermato.connect(self.materiale_aggiunto)
        materiale_window.show()
        self.materiale_windows.append(materiale_window)
    
    def materiale_aggiunto(self, materiale_calcolato, indice=None):
        """Gestisce aggiunta/modifica materiale"""
        if indice is not None:
            self.materiale_modificato(materiale_calcolato, indice)
        else:
            if self.preventivo.aggiungi_materiale(materiale_calcolato):
                self.aggiorna_materiali_info()
                self.aggiorna_totali()
            else:
                QMessageBox.critical(self, "Errore", "Impossibile aggiungere il materiale.")
    
    def visualizza_materiali(self):
        """Visualizza lista materiali"""
        if not self.preventivo.materiali_calcolati:
            QMessageBox.information(self, "Info", "Nessun materiale inserito.")
            return

        self._dialog_materiali = QDialog(self)
        self._dialog_materiali.setWindowTitle("Materiali Inseriti")
        self._dialog_materiali.setGeometry(300, 300, 700, 550)

        layout = QVBoxLayout(self._dialog_materiali)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        title_label = QLabel("Materiali Inseriti")
        title_label.setStyleSheet("font-size: 20px; font-weight: 700; color: #2d3748;")
        layout.addWidget(title_label)

        info_text = "Dettagli dei materiali utilizzati nel preventivo" if self.modalita == 'visualizza' else "Seleziona uno o più materiali per modificarli o eliminarli"
        info_label = QLabel(info_text)
        info_label.setStyleSheet("font-size: 14px; color: #718096;")
        layout.addWidget(info_label)

        # Scroll area con checkbox per ogni materiale
        from PyQt5.QtWidgets import QCheckBox, QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #e2e8f0; border-radius: 8px; }")
        scroll_widget = QWidget()
        self._materiali_checks_layout = QVBoxLayout(scroll_widget)
        self._materiali_checks_layout.setContentsMargins(10, 10, 10, 10)
        self._materiali_checks_layout.setSpacing(6)
        scroll.setWidget(scroll_widget)

        # Conteggio selezione (creato prima di _aggiorna_lista)
        self._lbl_selezione = QLabel("")
        self._lbl_selezione.setStyleSheet("font-size: 12px; color: #718096;")

        self._checkbox_list = []
        self._aggiorna_lista_materiali_dialog()

        layout.addWidget(scroll)

        # Barra selezione
        check_bar = QHBoxLayout()
        check_bar.addWidget(self._lbl_selezione)
        check_bar.addStretch()

        if self.modalita != 'visualizza':
            btn_sel_tutti = QPushButton("Seleziona Tutti")
            btn_sel_tutti.setStyleSheet("font-size: 12px; padding: 4px 10px;")
            btn_sel_tutti.clicked.connect(lambda: self._toggle_tutti_checkbox(True))
            btn_desel_tutti = QPushButton("Deseleziona Tutti")
            btn_desel_tutti.setStyleSheet("font-size: 12px; padding: 4px 10px;")
            btn_desel_tutti.clicked.connect(lambda: self._toggle_tutti_checkbox(False))
            check_bar.addWidget(btn_sel_tutti)
            check_bar.addWidget(btn_desel_tutti)

        layout.addLayout(check_bar)

        # Pulsanti
        buttons_layout = QHBoxLayout()

        if self.modalita != 'visualizza':
            btn_modifica = QPushButton("Modifica")
            btn_modifica.clicked.connect(self.modifica_materiale_selezionato)

            btn_elimina = QPushButton("Elimina Selezionati")
            btn_elimina.setStyleSheet("""
                QPushButton {
                    background-color: #e53e3e;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #c53030;
                }
            """)
            btn_elimina.clicked.connect(self.elimina_materiali_selezionati)

            buttons_layout.addWidget(btn_modifica)
            buttons_layout.addWidget(btn_elimina)

        btn_chiudi = QPushButton("Chiudi")
        btn_chiudi.clicked.connect(self._dialog_materiali.accept)

        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_chiudi)

        layout.addLayout(buttons_layout)
        self._dialog_materiali.exec_()

    def _aggiorna_lista_materiali_dialog(self):
        """Aggiorna le checkbox materiali nel dialog aperto"""
        from PyQt5.QtWidgets import QCheckBox
        # Rimuovi checkbox esistenti
        for cb in self._checkbox_list:
            cb.setParent(None)
        self._checkbox_list.clear()

        for i, materiale in enumerate(self.preventivo.materiali_calcolati):
            testo = (f"#{i+1} - {materiale.materiale_nome}  |  "
                    f"Ø {materiale.diametro:.1f}→{materiale.diametro_finale:.1f}mm  |  "
                    f"L: {materiale.lunghezza:.0f}mm  |  G: {materiale.giri}  |  "
                    f"€{materiale.maggiorazione:.2f}")
            cb = QCheckBox(testo)
            cb.setStyleSheet("""
                QCheckBox {
                    font-size: 13px;
                    padding: 6px 4px;
                    color: #2d3748;
                }
                QCheckBox:hover {
                    background-color: #f7fafc;
                    border-radius: 4px;
                }
            """)
            cb.setProperty("indice", i)
            cb.stateChanged.connect(self._aggiorna_conteggio_selezione)
            self._materiali_checks_layout.addWidget(cb)
            self._checkbox_list.append(cb)

        self._aggiorna_conteggio_selezione()

    def _get_checked_indices(self):
        """Ritorna lista indici dei materiali con checkbox flaggata"""
        return [cb.property("indice") for cb in self._checkbox_list if cb.isChecked()]

    def _toggle_tutti_checkbox(self, stato):
        """Seleziona o deseleziona tutte le checkbox"""
        for cb in self._checkbox_list:
            cb.setChecked(stato)

    def _aggiorna_conteggio_selezione(self):
        """Aggiorna il label con il numero di materiali selezionati"""
        n = len(self._get_checked_indices())
        if n == 0:
            self._lbl_selezione.setText("")
        elif n == 1:
            self._lbl_selezione.setText("1 materiale selezionato")
        else:
            self._lbl_selezione.setText(f"{n} materiali selezionati")

    def modifica_materiale_selezionato(self):
        """Modifica materiale selezionato (singolo)"""
        checked = self._get_checked_indices()
        if not checked:
            QMessageBox.warning(self, "Attenzione", "Seleziona un materiale da modificare.")
            return
        if len(checked) > 1:
            QMessageBox.warning(self, "Attenzione", "Seleziona un solo materiale per la modifica.")
            return

        indice = checked[0]
        materiale_da_modificare = self.preventivo.materiali_calcolati[indice]
        self.apri_finestra_modifica_materiale(indice, materiale_da_modificare)
        self._aggiorna_lista_materiali_dialog()

    def elimina_materiali_selezionati(self):
        """Elimina uno o più materiali flaggati"""
        checked = self._get_checked_indices()
        if not checked:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno un materiale da eliminare.")
            return

        n = len(checked)
        if n == 1:
            nome = self.preventivo.materiali_calcolati[checked[0]].materiale_nome
            msg = f"Eliminare il materiale '{nome}'?"
        else:
            msg = f"Eliminare {n} materiali selezionati?"

        risposta = QMessageBox.question(
            self, "Conferma Eliminazione", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if risposta == QMessageBox.Yes:
            # Elimina dal fondo per non spostare gli indici
            primo_eliminato = min(checked)
            for indice in sorted(checked, reverse=True):
                self.preventivo.rimuovi_materiale(indice)

            if self.preventivo.materiali_calcolati:
                if primo_eliminato == 0:
                    # Se ho eliminato il primo, il nuovo primo parte da diametro 0
                    self.preventivo.materiali_calcolati[0].diametro = 0.0
                    self.preventivo.materiali_calcolati[0].ricalcola_tutto()
                    self.ricalcola_diametri_successivi(0)
                else:
                    # Ricalcola dalla posizione del primo eliminato in poi
                    self.ricalcola_diametri_successivi(primo_eliminato - 1)
                self.preventivo.ricalcola_costo_totale_materiali()

            self.aggiorna_materiali_info()
            self.aggiorna_totali()
            self._aggiorna_lista_materiali_dialog()

            if not self.preventivo.materiali_calcolati:
                self._dialog_materiali.accept()
    
    def apri_finestra_modifica_materiale(self, indice, materiale_esistente):
        """Apri finestra modifica materiale"""
        diametro_iniziale = 0.0
        if indice > 0:
            materiale_precedente = self.preventivo.materiali_calcolati[indice - 1]
            diametro_iniziale = materiale_precedente.diametro_finale
        
        materiale_window = MaterialeWindow(
            self.db_manager, 
            diametro_iniziale=diametro_iniziale,
            materiale_esistente=materiale_esistente,
            indice_modifica=indice,
            parent=self
        )
        materiale_window.materiale_confermato.connect(self.materiale_aggiunto)
        materiale_window.show()
        self.materiale_windows.append(materiale_window)
    
    def materiale_modificato(self, materiale_calcolato, indice):
        """Gestisce modifica materiale"""
        self.preventivo.materiali_calcolati[indice] = materiale_calcolato
        self.ricalcola_diametri_successivi(indice)
        self.preventivo.ricalcola_costo_totale_materiali()
        self.aggiorna_materiali_info()
        self.aggiorna_totali()
        self.repaint()
    
    def ricalcola_diametri_successivi(self, indice_modificato):
        """Ricalcola diametri successivi"""
        for i in range(indice_modificato + 1, len(self.preventivo.materiali_calcolati)):
            materiale_precedente = self.preventivo.materiali_calcolati[i - 1]
            materiale_corrente = self.preventivo.materiali_calcolati[i]
            materiale_corrente.diametro = materiale_precedente.diametro_finale
            materiale_corrente.ricalcola_tutto()
    
    def aggiorna_materiali_info(self):
        """Aggiorna informazioni materiali"""
        num_materiali = len(self.preventivo.materiali_calcolati)
        
        if num_materiali == 0:
            self.lbl_num_materiali.setText("Nessun materiale inserito")
        else:
            self.lbl_num_materiali.setText(f"{num_materiali}/30 materiali inseriti")
        
        # Gestione pulsanti
        if hasattr(self, 'btn_aggiungi_materiale'):
            self.btn_aggiungi_materiale.setEnabled(num_materiali < 30 and self.modalita != 'visualizza')
        if hasattr(self, 'btn_visualizza_materiali'):
            self.btn_visualizza_materiali.setEnabled(num_materiali > 0)
        
        costo_totale = self.preventivo.costo_totale_materiali
        self.lbl_costo_totale_materiali.setText(f"€ {costo_totale:,.2f}")
    
    def aggiorna_totali(self):
        """Aggiorna totali preventivo"""
        self.preventivo.costi_accessori = self.edit_costi_accessori.value()
        self.preventivo.minuti_taglio = self.edit_minuti_taglio.value()
        self.preventivo.minuti_avvolgimento = self.edit_minuti_avvolgimento.value()
        self.preventivo.minuti_pulizia = self.edit_minuti_pulizia.value()
        self.preventivo.minuti_rettifica = self.edit_minuti_rettifica.value()
        self.preventivo.minuti_imballaggio = self.edit_minuti_imballaggio.value()
        
        self.preventivo.ricalcola_tutto()
        
        # Aggiorna interfaccia
        self.lbl_tot_mano_opera.setText(f"{self.preventivo.tot_mano_opera:.2f} min")
        self.lbl_subtotale.setText(f"€ {self.preventivo.subtotale:,.2f}")
        self.lbl_maggiorazione_25.setText(f"€ {self.preventivo.maggiorazione_25:,.2f}")
        self.lbl_preventivo_finale.setText(f"€ {self.preventivo.preventivo_finale:,.2f}")
        
        # Aggiorna prezzo cliente se vuoto
        if self.modalita != 'visualizza' and self.edit_prezzo_cliente.value() == 0:
            self.edit_prezzo_cliente.setValue(self.preventivo.preventivo_finale)
    
    def aggiorna_prezzi_materiali(self):
        """Aggiorna prezzi materiali dal database"""
        materiali_modificati = []
        
        for materiale_calcolato in self.preventivo.materiali_calcolati:
            materiale_db = self.db_manager.get_materiale_by_nome(materiale_calcolato.materiale_nome)
            if materiale_db:
                nuovo_prezzo = materiale_db[3]
                prezzo_precedente = materiale_calcolato.costo_materiale
                
                materiale_calcolato.costo_materiale = nuovo_prezzo
                materiale_calcolato.ricalcola_tutto()
                
                if abs(prezzo_precedente - nuovo_prezzo) > 0.01:
                    materiali_modificati.append(f"{materiale_calcolato.materiale_nome}: €{prezzo_precedente:.2f} → €{nuovo_prezzo:.2f}")
        
        # Aggiorna totali
        self.preventivo.ricalcola_costo_totale_materiali()
        self.aggiorna_materiali_info()
        self.aggiorna_totali()
        
        # Mostra messaggio se ci sono stati aggiornamenti
        if materiali_modificati:
            messaggio = "Prezzi aggiornati:\n\n" + "\n".join(materiali_modificati)
            QMessageBox.information(self, "Prezzi Aggiornati", messaggio)
    
    def closeEvent(self, event):
        """Gestisce chiusura finestra"""
        for window in self.materiale_windows:
            if window.isVisible():
                window.close()
        
        # Non mostrare popup se operazione completata o in modalità visualizzazione
        if self.operazione_completata or self.modalita == 'visualizza':
            event.accept()
            return
        
        # Controllo modifiche non salvate
        if self.modalita in ['nuovo', 'modifica', 'revisione']:
            dati_cliente = self.get_dati_cliente()
            dati_modificati = any(dati_cliente.values())
            
            if (self.preventivo.materiali_calcolati or 
                self.edit_costi_accessori.value() > 0 or
                self.edit_minuti_taglio.value() > 0 or
                self.edit_minuti_avvolgimento.value() > 0 or
                self.edit_minuti_pulizia.value() > 0 or
                self.edit_minuti_rettifica.value() > 0 or
                self.edit_minuti_imballaggio.value() > 0 or
                dati_modificati):
                
                risposta = QMessageBox.question(self, "Conferma Chiusura",
                                              "Ci sono dati non salvati. Vuoi chiudere comunque?",
                                              QMessageBox.Yes | QMessageBox.No)
                if risposta == QMessageBox.No:
                    event.ignore()
                    return
        
        event.accept()