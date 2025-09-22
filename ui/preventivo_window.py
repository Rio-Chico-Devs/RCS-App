"""
PreventivoWindow - Interfaccia calcolo preventivi con design unificato - VERSIONE SCHERMO INTERO + REVISIONI

Version: 2.2.0
Last Updated: 9/19/2025
Author: Antonio VB

CHANGELOG:
v2.2.0 (9/19/2025):
- ADDED: Sistema revisioni completo (modalità nuovo/visualizza/revisione)
- ADDED: Caricamento preventivi esistenti con compatibilità stratifica/sviluppo
- ADDED: Metodi salva_revisione() e supporto note revisione
- MAINTAINED: Design system originale identico (nessuna modifica grafica)
- MAINTAINED: Tutti i metodi e funzionalità originali

v2.1.0 (9/19/2025):
- ADDED: Apertura automatica a schermo intero con showMaximized()
- CHANGED: Layout responsive per sfruttare tutto lo spazio disponibile
- CHANGED: Colonne espandibili invece di larghezza fissa
- IMPROVED: Migliore utilizzo dello schermo su monitor grandi
"""

from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QWidget, QLabel, QLineEdit, QFormLayout, QMessageBox,
                             QScrollArea, QGroupBox, QSpinBox, QDoubleSpinBox,
                             QDialog, QListWidget, QListWidgetItem, QGridLayout, QFrame,
                             QSizePolicy, QApplication, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QDoubleValidator, QColor
from models.preventivo import Preventivo
from models.materiale import MaterialeCalcolato
from ui.materiale_window import MaterialeWindow
import json

class PreventivoWindow(QMainWindow):
    preventivo_salvato = pyqtSignal()
    
    def __init__(self, db_manager, parent=None, preventivo_id=None, modalita='nuovo', note_revisione=""):
        super().__init__(parent)
        self.db_manager = db_manager
        
        # NUOVO: Parametri per sistema revisioni
        self.preventivo_id = preventivo_id
        self.modalita = modalita  # 'nuovo', 'visualizza', 'revisione'
        self.note_revisione = note_revisione
        self.preventivo_originale_id = None
        
        self.preventivo = Preventivo()
        self.materiale_windows = []
        
        # NUOVO: Se stiamo caricando un preventivo esistente
        if preventivo_id:
            self.carica_preventivo_esistente()
        
        self.init_ui()
        self.aggiorna_totali()
    
    def carica_preventivo_esistente(self):
        """NUOVO: Carica un preventivo esistente dal database"""
        preventivo_data = self.db_manager.get_preventivo_by_id(self.preventivo_id)
        if not preventivo_data:
            QMessageBox.error(self, "Errore", "Preventivo non trovato nel database.")
            return
            
        # Carica i dati del preventivo
        self.preventivo.costi_accessori = preventivo_data.get('costi_accessori', 0.0)
        self.preventivo.minuti_taglio = preventivo_data.get('minuti_taglio', 0.0)
        self.preventivo.minuti_avvolgimento = preventivo_data.get('minuti_avvolgimento', 0.0)
        self.preventivo.minuti_pulizia = preventivo_data.get('minuti_pulizia', 0.0)
        self.preventivo.minuti_rettifica = preventivo_data.get('minuti_rettifica', 0.0)
        self.preventivo.minuti_imballaggio = preventivo_data.get('minuti_imballaggio', 0.0)
        self.preventivo.prezzo_cliente = preventivo_data.get('prezzo_cliente', 0.0)
        
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
        
        # Ricalcola tutto
        self.preventivo.ricalcola_tutto()
    
    def init_ui(self):
        """Design system unificato con MaterialeWindow - VERSIONE SCHERMO INTERO + titoli dinamici"""
        # NUOVO: Titolo dinamico basato sulla modalità
        if self.modalita == 'visualizza':
            title = f"Visualizzazione Preventivo #{self.preventivo_id:03d}"
        elif self.modalita == 'revisione':
            title = f"Revisione Preventivo #{self.preventivo_originale_id:03d}"
        else:
            title = "Calcolo Preventivo"
            
        self.setWindowTitle(title)
        
        # MODIFICA: Apertura a schermo intero invece di dimensioni fisse
        self.showMaximized()  # Apre la finestra massimizzata
        
        # Stile unificato con MaterialeWindow (IDENTICO ALL'ORIGINALE)
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
            QDoubleSpinBox, QSpinBox {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 14px;
                background-color: #ffffff;
                color: #2d3748;
                min-height: 18px;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QDoubleSpinBox:focus, QSpinBox:focus {
                border-color: #718096;
                outline: none;
            }
            QDoubleSpinBox:hover, QSpinBox:hover {
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
        
        # Contenuto principale - layout responsive a tre colonne
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)
        
        self.create_left_column(content_layout)   # Materiali
        self.create_middle_column(content_layout) # Tempi
        self.create_right_column(content_layout)  # Costi e Totali
        
        main_layout.addLayout(content_layout, 1)
        
        # Footer
        self.create_footer(main_layout)
        
        # NUOVO: Disabilita campi se in modalità visualizzazione
        if self.modalita == 'visualizza':
            self.disabilita_modifiche()
    
    def disabilita_modifiche(self):
        """NUOVO: Disabilita tutti i campi di input in modalità visualizzazione"""
        # Disabilita tutti i SpinBox
        self.edit_minuti_taglio.setEnabled(False)
        self.edit_minuti_avvolgimento.setEnabled(False)
        self.edit_minuti_pulizia.setEnabled(False)
        self.edit_minuti_rettifica.setEnabled(False)
        self.edit_minuti_imballaggio.setEnabled(False)
        self.edit_costi_accessori.setEnabled(False)
        self.edit_prezzo_cliente.setEnabled(False)
        
        # Disabilita pulsanti di modifica
        self.btn_aggiungi_materiale.setEnabled(False)
        
        # Aggiorna i valori dai dati caricati
        self.edit_costi_accessori.setValue(self.preventivo.costi_accessori)
        self.edit_minuti_taglio.setValue(self.preventivo.minuti_taglio)
        self.edit_minuti_avvolgimento.setValue(self.preventivo.minuti_avvolgimento)
        self.edit_minuti_pulizia.setValue(self.preventivo.minuti_pulizia)
        self.edit_minuti_rettifica.setValue(self.preventivo.minuti_rettifica)
        self.edit_minuti_imballaggio.setValue(self.preventivo.minuti_imballaggio)
        self.edit_prezzo_cliente.setValue(self.preventivo.prezzo_cliente)
        
        # Aggiorna le informazioni sui materiali
        self.aggiorna_materiali_info()
    
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
        """Colonna materiali - stile unificato e responsive (IDENTICA ALL'ORIGINALE)"""
        column_widget = QWidget()
        # MODIFICA: Colonna espandibile per sfruttare lo spazio disponibile
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
        """Colonna tempi - stile unificato e responsive (IDENTICA ALL'ORIGINALE)"""
        column_widget = QWidget()
        # MODIFICA: Colonna espandibile per sfruttare lo spazio disponibile
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
        """Colonna costi e totali - stile unificato e responsive (IDENTICA ALL'ORIGINALE)"""
        column_widget = QWidget()
        # MODIFICA: Colonna espandibile per sfruttare lo spazio disponibile
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
        """Card info costo materiali (IDENTICA ALL'ORIGINALE)"""
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
        
        # MODIFICA: Pulsanti diversi per modalità visualizzazione
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
        """Form tempi standardizzato (IDENTICO ALL'ORIGINALE)"""
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
        """Card totale mano d'opera (IDENTICA ALL'ORIGINALE)"""
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
        """Form costi accessori (IDENTICO ALL'ORIGINALE)"""
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(16)
        form_layout.setHorizontalSpacing(16)
        
        self.edit_costi_accessori = self.create_standard_spinbox("€")
        form_layout.addRow(self.create_standard_label("Costi Accessori:"), self.edit_costi_accessori)
        
        parent_layout.addLayout(form_layout)
    
    def create_totals_summary(self, parent_layout):
        """Riepilogo totali (IDENTICO ALL'ORIGINALE)"""
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
                padding: 16px;
                margin: 8px 0px;
            }
        """)
        
        final_layout = QHBoxLayout(final_container)
        final_layout.setContentsMargins(0, 0, 0, 0)
        
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
        """Riga riepilogo standardizzata (IDENTICA ALL'ORIGINALE)"""
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
        """SpinBox standardizzato (IDENTICO ALL'ORIGINALE)"""
        spinbox = QDoubleSpinBox()
        spinbox.setMaximum(999999.99)
        spinbox.setDecimals(2)
        if suffix:
            spinbox.setSuffix(f" {suffix}")
        spinbox.setMinimumHeight(36)
        spinbox.valueChanged.connect(self.aggiorna_totali)
        return spinbox
    
    def create_standard_label(self, text):
        """Label standardizzata (IDENTICA ALL'ORIGINALE)"""
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
        
        # NUOVO: Pulsanti diversi per modalità
        if self.modalita == 'visualizza':
            # Solo pulsante Chiudi
            btn_chiudi = QPushButton("Chiudi")
            btn_chiudi.setStyleSheet("""
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
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #edf2f7;
                }
            """)
            self.btn_annulla.clicked.connect(self.close)
            
            # NUOVO: Salva/Salva Revisione
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
                    min-height: 40px;
                    min-width: 160px;
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
    
    # =================== METODI FUNZIONALI (ORIGINALI + REVISIONI) ===================
    
    def aggiungi_materiale(self):
        """Metodo originale IDENTICO"""
        if len(self.preventivo.materiali_calcolati) >= 10:
            QMessageBox.warning(self, "Limite Raggiunto", 
                              "Hai raggiunto il limite massimo di 10 materiali.")
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
        """Metodo originale IDENTICO"""
        print(f"DEBUG: materiale_aggiunto chiamato con indice={indice}")
        
        if indice is not None:
            print(f"DEBUG: Modificando materiale esistente all'indice {indice}")
            print(f"DEBUG: Nuovo costo materiale: €{materiale_calcolato.maggiorazione:.2f}")
            self.materiale_modificato(materiale_calcolato, indice)
        else:
            print(f"DEBUG: Aggiungendo nuovo materiale")
            if self.preventivo.aggiungi_materiale(materiale_calcolato):
                self.aggiorna_materiali_info()
                self.aggiorna_totali()
            else:
                QMessageBox.error(self, "Errore", "Impossibile aggiungere il materiale.")
    
    def visualizza_materiali(self):
        """Metodo originale ADATTATO per modalità visualizzazione"""
        if not self.preventivo.materiali_calcolati:
            QMessageBox.information(self, "Info", "Nessun materiale inserito.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Materiali Inseriti")
        dialog.setGeometry(300, 300, 700, 550)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #fafbfc;
            }
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                font-size: 14px;
                padding: 12px;
            }
            QListWidget::item {
                border-radius: 6px;
                padding: 12px;
                margin: 2px;
                border-bottom: 1px solid #f7fafc;
            }
            QListWidget::item:hover {
                background-color: #f7fafc;
            }
            QListWidget::item:selected {
                background-color: #edf2f7;
                color: #2d3748;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        title_label = QLabel("Materiali Inseriti")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 700;
                color: #2d3748;
            }
        """)
        layout.addWidget(title_label)
        
        # MODIFICA: Testo diverso per modalità visualizzazione
        if self.modalita == 'visualizza':
            info_text = "Dettagli dei materiali utilizzati nel preventivo"
        else:
            info_text = "Seleziona un materiale per modificarlo o eliminarlo"
            
        info_label = QLabel(info_text)
        info_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #718096;
            }
        """)
        layout.addWidget(info_label)
        
        lista_materiali = QListWidget()
        for i, materiale in enumerate(self.preventivo.materiali_calcolati):
            testo = (f"#{i+1} - {materiale.materiale_nome}\n"
                    f"Ø Iniziale → Ø Finale: {materiale.diametro:.1f}mm → {materiale.diametro_finale:.1f}mm  "
                    f"Lunghezza: {materiale.lunghezza:.0f}mm  Numero Giri: {materiale.giri} \n"
                    f"Costo Singolo Materiale: €{materiale.maggiorazione:.2f}")
            
            item = QListWidgetItem(testo)
            item.setData(Qt.UserRole, i)
            lista_materiali.addItem(item)
        
        # MODIFICA: Disabilita doppio clic se in modalità visualizzazione
        if self.modalita != 'visualizza':
            lista_materiali.itemDoubleClicked.connect(lambda item: self.modifica_materiale_selezionato(dialog, lista_materiali))
        layout.addWidget(lista_materiali)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        # MODIFICA: Pulsanti solo se non in modalità visualizzazione
        if self.modalita != 'visualizza':
            btn_modifica = QPushButton("Modifica")
            btn_modifica.setStyleSheet("""
                QPushButton {
                    background-color: #4a5568;
                    color: #ffffff;
                    min-height: 36px;
                }
                QPushButton:hover {
                    background-color: #2d3748;
                }
            """)
            btn_modifica.clicked.connect(lambda: self.modifica_materiale_selezionato(dialog, lista_materiali))
            
            btn_elimina = QPushButton("Elimina")
            btn_elimina.setStyleSheet("""
                QPushButton {
                    background-color: #e53e3e;
                    color: #ffffff;
                    min-height: 36px;
                }
                QPushButton:hover {
                    background-color: #c53030;
                }
            """)
            btn_elimina.clicked.connect(lambda: self.elimina_materiale_selezionato(dialog, lista_materiali))
            
            buttons_layout.addWidget(btn_modifica)
            buttons_layout.addWidget(btn_elimina)
        
        btn_chiudi = QPushButton("Chiudi")
        btn_chiudi.setStyleSheet("""
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
        btn_chiudi.clicked.connect(dialog.accept)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_chiudi)
        
        layout.addLayout(buttons_layout)
        dialog.exec_()
    
    def modifica_materiale_selezionato(self, dialog, lista_materiali):
        """Metodo originale IDENTICO"""
        current_item = lista_materiali.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un materiale da modificare.")
            return
        
        indice = current_item.data(Qt.UserRole)
        materiale_da_modificare = self.preventivo.materiali_calcolati[indice]
        dialog.accept()
        self.apri_finestra_modifica_materiale(indice, materiale_da_modificare)
    
    def elimina_materiale_selezionato(self, dialog, lista_materiali):
        """Metodo originale IDENTICO"""
        current_item = lista_materiali.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un materiale da eliminare.")
            return
        
        indice = current_item.data(Qt.UserRole)
        materiale = self.preventivo.materiali_calcolati[indice]
        
        risposta = QMessageBox.question(
            self, "Conferma Eliminazione",
            f"Eliminare il materiale '{materiale.materiale_nome}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if risposta == QMessageBox.Yes:
            if self.preventivo.rimuovi_materiale(indice):
                self.ricalcola_diametri_successivi(indice - 1)
                self.aggiorna_materiali_info()
                self.aggiorna_totali()
                dialog.accept()
    
    def apri_finestra_modifica_materiale(self, indice, materiale_esistente):
        """Metodo originale IDENTICO"""
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
        """Metodo originale IDENTICO"""
        self.preventivo.materiali_calcolati[indice] = materiale_calcolato
        self.ricalcola_diametri_successivi(indice)
        
        # IMPORTANTE: Forza il ricalcolo del costo totale materiali
        self.preventivo.ricalcola_costo_totale_materiali()
        
        self.aggiorna_materiali_info()
        self.aggiorna_totali()
        
        # Forza un refresh immediato dell'interfaccia
        self.repaint()
    
    def ricalcola_diametri_successivi(self, indice_modificato):
        """Metodo originale IDENTICO"""
        for i in range(indice_modificato + 1, len(self.preventivo.materiali_calcolati)):
            materiale_precedente = self.preventivo.materiali_calcolati[i - 1]
            materiale_corrente = self.preventivo.materiali_calcolati[i]
            materiale_corrente.diametro = materiale_precedente.diametro_finale
            materiale_corrente.ricalcola_tutto()
    
    def aggiorna_materiali_info(self):
        """Metodo originale IDENTICO"""
        num_materiali = len(self.preventivo.materiali_calcolati)
        
        if num_materiali == 0:
            self.lbl_num_materiali.setText("Nessun materiale inserito")
        else:
            self.lbl_num_materiali.setText(f"{num_materiali}/10 materiali inseriti")
        
        # MODIFICA: Gestione pulsanti per modalità
        if hasattr(self, 'btn_aggiungi_materiale'):
            self.btn_aggiungi_materiale.setEnabled(num_materiali < 10 and self.modalita != 'visualizza')
        if hasattr(self, 'btn_visualizza_materiali'):
            self.btn_visualizza_materiali.setEnabled(num_materiali > 0)
        
        costo_totale = self.preventivo.costo_totale_materiali
        print(f"DEBUG aggiorna_materiali_info: Costo totale calcolato: €{costo_totale:.2f}")
        
        # Debug: mostra i costi individuali
        for i, mat in enumerate(self.preventivo.materiali_calcolati):
            print(f"  Materiale {i+1}: {mat.materiale_nome} = €{mat.maggiorazione:.2f}")
        
        self.lbl_costo_totale_materiali.setText(f"€ {costo_totale:,.2f}")
    
    def aggiorna_totali(self):
        """Metodo originale IDENTICO"""
        self.preventivo.costi_accessori = self.edit_costi_accessori.value()
        self.preventivo.minuti_taglio = self.edit_minuti_taglio.value()
        self.preventivo.minuti_avvolgimento = self.edit_minuti_avvolgimento.value()
        self.preventivo.minuti_pulizia = self.edit_minuti_pulizia.value()
        self.preventivo.minuti_rettifica = self.edit_minuti_rettifica.value()
        self.preventivo.minuti_imballaggio = self.edit_minuti_imballaggio.value()
        
        self.preventivo.ricalcola_tutto()
        
        # Formatazione con separatori migliaia
        self.lbl_tot_mano_opera.setText(f"{self.preventivo.tot_mano_opera:.2f} min")
        self.lbl_subtotale.setText(f"€ {self.preventivo.subtotale:,.2f}")
        self.lbl_maggiorazione_25.setText(f"€ {self.preventivo.maggiorazione_25:,.2f}")
        self.lbl_preventivo_finale.setText(f"€ {self.preventivo.preventivo_finale:,.2f}")
        
        # MODIFICA: Solo se non in modalità visualizzazione
        if self.modalita != 'visualizza' and self.edit_prezzo_cliente.value() == 0:
            self.edit_prezzo_cliente.setValue(self.preventivo.preventivo_finale)
    
    def aggiorna_prezzi_materiali(self):
        """NUOVO: Aggiorna i prezzi dei materiali già inseriti nel preventivo"""
        materiali_aggiornati = False
        materiali_modificati = []
        
        for materiale_calcolato in self.preventivo.materiali_calcolati:
            # Recupera il prezzo aggiornato dal database
            materiale_db = self.db_manager.get_materiale_by_nome(materiale_calcolato.materiale_nome)
            if materiale_db:
                # materiale_db = (id, nome, spessore, prezzo)
                nuovo_prezzo = materiale_db[3]
                prezzo_precedente = materiale_calcolato.prezzo if hasattr(materiale_calcolato, 'prezzo') else materiale_calcolato.costo_materiale
                
                # Debug: stampa i prezzi per verificare
                print(f"Materiale {materiale_calcolato.materiale_nome}: Prezzo precedente: {prezzo_precedente}, Nuovo prezzo: {nuovo_prezzo}")
                
                # Aggiorna sempre il prezzo e ricalcola
                materiale_calcolato.costo_materiale = nuovo_prezzo
                if hasattr(materiale_calcolato, 'prezzo'):
                    materiale_calcolato.prezzo = nuovo_prezzo
                materiale_calcolato.ricalcola_tutto()
                
                if abs(prezzo_precedente - nuovo_prezzo) > 0.01:  # Controllo con tolleranza
                    materiali_modificati.append(f"{materiale_calcolato.materiale_nome}: €{prezzo_precedente:.2f} → €{nuovo_prezzo:.2f}")
                    materiali_aggiornati = True
        
        # Forza sempre l'aggiornamento dei totali
        self.preventivo.ricalcola_costo_totale_materiali()
        self.aggiorna_materiali_info()
        self.aggiorna_totali()
        
        # Mostra messaggio solo se ci sono stati cambiamenti effettivi
        if materiali_aggiornati and materiali_modificati:
            messaggio = "Prezzi aggiornati:\n\n" + "\n".join(materiali_modificati)
            QMessageBox.information(self, "Prezzi Aggiornati", messaggio)
    
    def salva_preventivo(self):
        """Metodo originale IDENTICO"""
        if not self.preventivo.materiali_calcolati:
            QMessageBox.warning(self, "Attenzione", 
                              "Aggiungi almeno un materiale prima di salvare il preventivo.")
            return
        
        self.preventivo.prezzo_cliente = self.edit_prezzo_cliente.value()
        
        try:
            preventivo_id = self.db_manager.save_preventivo(self.preventivo.to_dict())
            
            QMessageBox.information(self, "Successo!", 
                                  f"Preventivo salvato con successo\n\nID: {preventivo_id}")
            
            self.preventivo_salvato.emit()
            self.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", 
                               f"Errore durante il salvataggio:\n{str(e)}")
    
    def salva_revisione(self):
        """NUOVO: Salva una revisione del preventivo esistente"""
        if not self.preventivo.materiali_calcolati:
            QMessageBox.warning(self, "Attenzione", 
                              "Aggiungi almeno un materiale prima di salvare.")
            return
        
        # Aggiorna il prezzo cliente
        self.preventivo.prezzo_cliente = self.edit_prezzo_cliente.value()
        
        try:
            revisione_id = self.db_manager.add_revisione_preventivo(
                self.preventivo_originale_id,
                self.preventivo.to_dict(),
                self.note_revisione
            )
            if revisione_id:
                QMessageBox.information(self, "Revisione Salvata", 
                                      f"Revisione salvata con successo!\nID: #{revisione_id:03d}")
                self.preventivo_salvato.emit()
                self.close()
            else:
                QMessageBox.error(self, "Errore", "Errore durante il salvataggio della revisione.")
        except Exception as e:
            QMessageBox.error(self, "Errore", f"Errore durante il salvataggio:\n{str(e)}")
    
    def closeEvent(self, event):
        """Gestisce la chiusura della finestra - AGGIORNATO con controllo modalità"""
        for window in self.materiale_windows:
            if window.isVisible():
                window.close()
        
        # NUOVO: Controllo modifiche non salvate solo se non in modalità visualizzazione
        if self.modalita != 'visualizza':
            if (self.preventivo.materiali_calcolati or 
                self.edit_costi_accessori.value() > 0 or
                self.edit_minuti_taglio.value() > 0 or
                self.edit_minuti_avvolgimento.value() > 0 or
                self.edit_minuti_pulizia.value() > 0 or
                self.edit_minuti_rettifica.value() > 0 or
                self.edit_minuti_imballaggio.value() > 0):
                
                risposta = QMessageBox.question(self, "Conferma Chiusura",
                                              "Ci sono dati non salvati. Vuoi chiudere comunque?",
                                              QMessageBox.Yes | QMessageBox.No)
                if risposta == QMessageBox.No:
                    event.ignore()
                    return
        
        event.accept()
        
    