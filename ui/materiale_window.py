"""
MaterialeWindow - Interfaccia di calcolo materiali per preventivi

Version: 2.1.1
Last Updated: 9/19/2025
Author: Antonio VB & Cla.ass

CHANGELOG:
v2.1.1 (9/19/2025):
- FIXED: Errore "too many values to unpack" nel metodo materiale_selezionato()
- FIXED: Import QMessageBox mancante causava AttributeError
- MAINTAINED: Design originale identico, solo correzioni bug

v2.1.0 (2024-12-19):
- FIXED: Risolto bordo tagliato Maggiorazione Finale (margin: 8px→2px era la causa)
- CHANGED: Font uniformati a system-ui per tutti i valori (rimosso monospace)
- CHANGED: "Spessore" rinominato in "Spessore Tela" per maggiore chiarezza
- CHANGED: Campo "Lunghezza Utilizzata" spostato nei Parametri come "Metri"
- CHANGED: "Override Sviluppo" rinominato in "Sviluppo Manuale"
- CHANGED: Labels allineate a sinistra per layout più naturale
- ADDED: Nota "* I valori in grassetto non sono editabili" nei Parametri
- REMOVED: Testo "(automatico)" dal Sviluppo Manuale per design più pulito
"""

from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QWidget, QLabel, QLineEdit, QFormLayout, QMessageBox,
                             QComboBox, QGroupBox, QSpinBox, QDoubleSpinBox, QFrame,
                             QSizePolicy, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from models.materiale import MaterialeCalcolato

class MaterialeWindow(QMainWindow):
    materiale_confermato = pyqtSignal(MaterialeCalcolato, object)
    
    def __init__(self, db_manager, diametro_iniziale=0.0, materiale_esistente=None, indice_modifica=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.diametro_iniziale = diametro_iniziale
        self.materiale_esistente = materiale_esistente
        self.indice_modifica = indice_modifica
        self.materiale_calcolato = MaterialeCalcolato()
        self.materiali_disponibili = []
        
        # Inizializza flag arrotondamento
        self.arrotondamento_modificato_manualmente = False
        
        if materiale_esistente:
            self.materiale_calcolato = self.copia_materiale(materiale_esistente)
        
        self.init_ui()
        self.carica_materiali()
        
        if materiale_esistente:
            self.carica_dati_esistenti()
        elif diametro_iniziale > 0:
            self.edit_diametro.setValue(diametro_iniziale)
            self.materiale_calcolato.diametro = diametro_iniziale
    
    def init_ui(self):
        """Design system unificato per tutti gli elementi"""
        self.setWindowTitle("Calcolo Materiale")
        
        # Dimensioni originali
        self.setMinimumSize(1200, 750)
        self.setMaximumSize(1200, 750)
        self.resize(1200, 750)
        
        # Sistema di design unificato (IDENTICO ALL'ORIGINALE)
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
            QDoubleSpinBox, QSpinBox, QComboBox {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 14px;
                background-color: #ffffff;
                color: #2d3748;
                min-height: 16px;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #718096;
                outline: none;
            }
            QDoubleSpinBox:hover, QSpinBox:hover, QComboBox:hover {
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
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Layout principale con proporzioni fisse
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(20)
        
        # Header
        self.create_header(main_layout)
        
        # Contenuto principale - layout orizzontale bilanciato
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)
        
        self.create_input_section(content_layout)
        self.create_results_section(content_layout)
        
        main_layout.addLayout(content_layout, 1)
        
        # Footer
        self.create_footer(main_layout)
    
    def create_shadow_effect(self, blur=10, opacity=12):
        """Effetto ombra standardizzato"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setColor(QColor(0, 0, 0, opacity))
        shadow.setOffset(0, 2)
        return shadow
    
    def create_header(self, parent_layout):
        """Header unificato"""
        title_text = "Calcolo Materiale"
        if self.materiale_esistente:
            title_text = "Modifica Materiale"
        
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
    
    def create_input_section(self, parent_layout):
        """Sezione input con design unificato"""
        input_group = QGroupBox("Parametri")
        input_group.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        input_group.setFixedWidth(450)
        input_group.setGraphicsEffect(self.create_shadow_effect())
        
        layout = QVBoxLayout(input_group)
        layout.setContentsMargins(25, 28, 25, 25)
        layout.setSpacing(18)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(16)
        form_layout.setHorizontalSpacing(16)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Input fields standardizzati
        self.edit_diametro = self.create_standard_input(suffix=" mm")
        form_layout.addRow(self.create_standard_label("Diametro"), self.edit_diametro)
        
        self.edit_lunghezza = self.create_standard_input(suffix=" mm", decimals=0, default_value=1000)
        form_layout.addRow(self.create_standard_label("Lunghezza"), self.edit_lunghezza)
        
        # Campo Metri sotto Lunghezza
        self.create_metri_field(form_layout)
        
        self.combo_materiale = QComboBox()
        self.combo_materiale.currentIndexChanged.connect(self.materiale_selezionato)
        form_layout.addRow(self.create_standard_label("Materiale"), self.combo_materiale)
        
        self.edit_giri = QSpinBox()
        self.edit_giri.setMaximum(9999)
        self.edit_giri.setValue(1)
        self.edit_giri.valueChanged.connect(self.ricalcola_tutto)
        form_layout.addRow(self.create_standard_label("Giri"), self.edit_giri)
        
        layout.addLayout(form_layout)
        
        # Nota per i campi non editabili
        note_label = QLabel("* I valori in grassetto non sono editabili")
        note_label.setStyleSheet("""
            QLabel {
                color: #718096;
                font-size: 12px;
                font-style: italic;
                padding: 8px 0 0 0;
            }
        """)
        layout.addWidget(note_label)
        
        layout.addStretch()
        
        parent_layout.addWidget(input_group)
    
    def create_metri_field(self, form_layout):
        """Campo metri sotto lunghezza - stile unificato"""
        self.lbl_lunghezza_utilizzata = QLabel("0.000000 m")
        self.lbl_lunghezza_utilizzata.setStyleSheet("""
            QLabel {
                color: #4a5568;
                font-size: 14px;
                font-weight: 600;
                font-family: system-ui, -apple-system, sans-serif;
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 10px 14px;
                min-height: 16px;
            }
        """)
        form_layout.addRow(self.create_standard_label("Metri"), self.lbl_lunghezza_utilizzata)
    
    def create_results_section(self, parent_layout):
        """Sezione risultati con design unificato"""
        results_group = QGroupBox("Risultati")
        results_group.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        results_group.setFixedWidth(450)
        results_group.setGraphicsEffect(self.create_shadow_effect())
        
        layout = QVBoxLayout(results_group)
        layout.setContentsMargins(25, 28, 25, 25)
        layout.setSpacing(12)
        
        # Tutti i risultati con design identico
        self.create_standard_result("Spessore Tela", "lbl_spessore", "0.00 mm", layout)
        self.create_standard_result("Diametro Finale", "lbl_diametro_finale", "0.00 mm", layout, important=True)
        self.create_standard_result("Sviluppo", "lbl_sviluppo", "0.00", layout, important=True)
        
        # Sviluppo manuale section
        self.create_override_section(layout)
        
        self.create_standard_result("Costo Materiale", "lbl_costo_materiale", "€0.00", layout)
        self.create_standard_result("Costo Totale", "lbl_costo_totale", "€0.00", layout)
        
        # Maggiorazione finale
        self.create_final_result(layout)
        
        layout.addStretch()
        
        parent_layout.addWidget(results_group)
    
    def create_standard_input(self, suffix="", decimals=2, default_value=0):
        """Input standardizzato per tutto il form"""
        field = QDoubleSpinBox()
        field.setMaximum(999999.99)
        field.setDecimals(decimals)
        if suffix:
            field.setSuffix(suffix)
        if default_value:
            field.setValue(default_value)
        field.valueChanged.connect(self.ricalcola_tutto)
        field.setMinimumHeight(36)
        return field
    
    def create_standard_label(self, text):
        """Label standardizzata per tutto il form"""
        label = QLabel(text)
        label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #4a5568;
                min-width: 80px;
            }
        """)
        return label
    
    def create_standard_result(self, title, attr_name, default_value, parent_layout, important=False):
        """Risultato standardizzato - stile identico ai Parametri"""
        container = QFrame()
        container.setFixedHeight(48)
        
        # Sfondo uniforme senza bordi per il contenitore
        container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 2px 0px;
            }
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(16)
        
        # Label senza bordi - stile identico ai Parametri
        title_label = QLabel(f"{title}:")
        title_label.setStyleSheet("""
            QLabel {
                color: #4a5568;
                font-size: 14px;
                font-weight: 500;
                min-width: 120px;
                background-color: transparent;
                border: none;
            }
        """)
        title_label.setFixedHeight(36)
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Valore con bordi - stile identico agli input
        value_label = QLabel(default_value)
        if important:
            value_label.setStyleSheet("""
                QLabel {
                    color: #2d3748;
                    font-size: 14px;
                    font-weight: 600;
                    font-family: system-ui, -apple-system, sans-serif;
                    background-color: #f7fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 10px 14px;
                    min-height: 16px;
                }
            """)
        else:
            value_label.setStyleSheet("""
                QLabel {
                    color: #4a5568;
                    font-size: 14px;
                    font-weight: 600;
                    font-family: system-ui, -apple-system, sans-serif;
                    background-color: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 10px 14px;
                    min-height: 16px;
                }
            """)
        
        value_label.setFixedHeight(36)
        value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        setattr(self, attr_name, value_label)
        parent_layout.addWidget(container)
    
    def create_override_section(self, parent_layout):
        """Sviluppo manuale section - stile unificato ai Parametri"""
        container = QFrame()
        container.setFixedHeight(48)
        container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 6px 0px;
            }
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(16)
        
        # Label senza bordi - stile identico
        title_label = QLabel("Sviluppo Manuale:")
        title_label.setStyleSheet("""
            QLabel {
                color: #4a5568;
                font-size: 14px;
                font-weight: 500;
                min-width: 120px;
                background-color: transparent;
                border: none;
            }
        """)
        title_label.setFixedHeight(36)
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Container per input senza status - allineato come gli altri
        input_container = QWidget()
        input_container.setFixedHeight(36)
        
        # Input con stile standard e larghezza completa come gli altri campi
        self.edit_arrotondamento = QDoubleSpinBox()
        self.edit_arrotondamento.setMaximum(999999.99)
        self.edit_arrotondamento.setDecimals(2)
        self.edit_arrotondamento.setFixedHeight(36)
        self.edit_arrotondamento.valueChanged.connect(self.arrotondamento_modificato)
        self.edit_arrotondamento.setStyleSheet("""
            QDoubleSpinBox {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 14px;
                background-color: #ffffff;
                color: #2d3748;
                min-height: 16px;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QDoubleSpinBox:focus {
                border-color: #718096;
                outline: none;
            }
            QDoubleSpinBox:hover {
                border-color: #a0aec0;
            }
        """)
        
        # Status nascosto per logica interna
        self.lbl_arrotondamento_status = QLabel("")
        self.lbl_arrotondamento_status.hide()
        
        # Layout singolo per l'input
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.addWidget(self.edit_arrotondamento)
        
        layout.addWidget(title_label)
        layout.addWidget(input_container)
        
        parent_layout.addWidget(container)
    
    def create_final_result(self, parent_layout):
        """Maggiorazione finale - ricreata identica agli altri campi"""
        container = QFrame()
        container.setFixedHeight(48)
        
        # Stesso stile container degli altri
        container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 2px 0px;
            }
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(16)
        
        # Label identica agli altri
        title_label = QLabel("Maggiorazione Finale:")
        title_label.setStyleSheet("""
            QLabel {
                color: #4a5568;
                font-size: 14px;
                font-weight: 500;
                min-width: 120px;
                background-color: transparent;
                border: none;
            }
        """)
        title_label.setFixedHeight(36)
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Valore identico agli altri MA con sfondo verde
        self.lbl_maggiorazione = QLabel("€0.00")
        self.lbl_maggiorazione.setStyleSheet("""
            QLabel {
                color: #2d3748;
                font-size: 14px;
                font-weight: 600;
                font-family: system-ui, -apple-system, sans-serif;
                background-color: #f0fff4;
                border: 1px solid #68d391;
                border-radius: 6px;
                padding: 10px 14px;
                min-height: 16px;
            }
        """)
        self.lbl_maggiorazione.setFixedHeight(36)
        self.lbl_maggiorazione.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(self.lbl_maggiorazione)
        
        parent_layout.addWidget(container)
    
    def create_footer(self, parent_layout):
        """Footer standardizzato"""
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        self.btn_annulla = QPushButton("Annulla")
        self.btn_annulla.setFixedHeight(40)
        self.btn_annulla.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
        """)
        self.btn_annulla.clicked.connect(self.close)
        
        confirm_text = "Aggiorna" if self.materiale_esistente else "Conferma"
        self.btn_concludi = QPushButton(confirm_text)
        self.btn_concludi.setFixedHeight(40)
        self.btn_concludi.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
        """)
        self.btn_concludi.clicked.connect(self.concludi_operazione)
        
        footer_layout.addWidget(self.btn_annulla)
        footer_layout.addSpacing(12)
        footer_layout.addWidget(self.btn_concludi)
        
        parent_layout.addLayout(footer_layout)
    
    def arrotondamento_modificato(self):
        """Gestisce la modifica del campo arrotondamento"""
        valore = self.edit_arrotondamento.value()
        
        if valore != 0:
            self.arrotondamento_modificato_manualmente = True
            self.lbl_arrotondamento_status.setText("(personalizzato)")
            self.lbl_arrotondamento_status.setStyleSheet("""
                QLabel {
                    color: #e53e3e;
                    font-size: 11px;
                    font-style: italic;
                    font-weight: 600;
                }
            """)
        else:
            self.arrotondamento_modificato_manualmente = False
            self.lbl_arrotondamento_status.setText("(automatico)")
            self.lbl_arrotondamento_status.setStyleSheet("""
                QLabel {
                    color: #a0aec0;
                    font-size: 11px;
                    font-style: italic;
                }
            """)
        
        self.ricalcola_tutto()
    
    def copia_materiale(self, materiale_originale):
        """Copia un materiale esistente"""
        nuovo_materiale = MaterialeCalcolato()
        nuovo_materiale.diametro = materiale_originale.diametro
        nuovo_materiale.lunghezza = materiale_originale.lunghezza
        nuovo_materiale.materiale_id = materiale_originale.materiale_id
        nuovo_materiale.materiale_nome = materiale_originale.materiale_nome
        nuovo_materiale.giri = materiale_originale.giri
        nuovo_materiale.spessore = materiale_originale.spessore
        nuovo_materiale.arrotondamento_manuale = materiale_originale.arrotondamento_manuale
        nuovo_materiale.costo_materiale = materiale_originale.costo_materiale
        nuovo_materiale.ricalcola_tutto()
        return nuovo_materiale
    
    def carica_materiali(self):
        """Carica la lista dei materiali disponibili"""
        self.combo_materiale.clear()
        self.combo_materiale.addItem("Seleziona un materiale...", None)
        
        try:
            self.materiali_disponibili = self.db_manager.get_all_materiali()
            for materiale in self.materiali_disponibili:
                id_mat, nome, spessore, prezzo = materiale
                text = f"{nome} - {spessore}mm - €{prezzo:.2f}/m"
                self.combo_materiale.addItem(text, id_mat)
        except Exception as e:
            QMessageBox.error(self, "Errore", f"Errore nel caricamento materiali: {str(e)}")
    
    def materiale_selezionato(self):
        """CORRETTO: Gestisce la selezione di un materiale"""
        materiale_id = self.combo_materiale.currentData()
        if materiale_id is None:
            return
        
        try:
            materiale_info = self.db_manager.get_materiale_by_id(materiale_id)
            if materiale_info:
                # CORREZIONE: Il metodo restituisce (id, nome, spessore, prezzo)
                id_materiale, nome, spessore, prezzo = materiale_info
                
                self.materiale_calcolato.materiale_id = materiale_id
                self.materiale_calcolato.materiale_nome = nome
                self.materiale_calcolato.spessore = spessore
                self.materiale_calcolato.costo_materiale = prezzo
                
                self.ricalcola_tutto()
        except Exception as e:
            QMessageBox.error(self, "Errore", f"Errore nella selezione materiale: {str(e)}")
    
    def ricalcola_tutto(self):
        """Ricalcola tutti i valori con logica arrotondamento"""
        if not hasattr(self, 'edit_giri') or not hasattr(self, 'lbl_spessore'):
            return
            
        self.materiale_calcolato.diametro = self.edit_diametro.value()
        self.materiale_calcolato.lunghezza = self.edit_lunghezza.value()
        self.materiale_calcolato.giri = self.edit_giri.value()
        self.materiale_calcolato.arrotondamento_manuale = self.edit_arrotondamento.value()
        
        self.materiale_calcolato.ricalcola_tutto()
        self.aggiorna_display()
    
    def aggiorna_display(self):
        """Aggiorna tutti i valori mostrati nell'interfaccia"""
        try:
            if hasattr(self, 'lbl_spessore'):
                self.lbl_spessore.setText(f"{self.materiale_calcolato.spessore:.2f} mm")
            if hasattr(self, 'lbl_diametro_finale'):
                self.lbl_diametro_finale.setText(f"{self.materiale_calcolato.diametro_finale:.2f} mm")
            if hasattr(self, 'lbl_sviluppo'):
                self.lbl_sviluppo.setText(f"{self.materiale_calcolato.sviluppo:.2f}")
            if hasattr(self, 'lbl_costo_materiale'):
                self.lbl_costo_materiale.setText(f"€{self.materiale_calcolato.costo_materiale:.2f}")
            if hasattr(self, 'lbl_lunghezza_utilizzata'):
                self.lbl_lunghezza_utilizzata.setText(f"{self.materiale_calcolato.lunghezza_utilizzata:.6f} m")
            if hasattr(self, 'lbl_costo_totale'):
                self.lbl_costo_totale.setText(f"€{self.materiale_calcolato.costo_totale:.2f}")
            if hasattr(self, 'lbl_maggiorazione'):
                self.lbl_maggiorazione.setText(f"€{self.materiale_calcolato.maggiorazione:.2f}")
        except Exception as e:
            pass
    
    def carica_dati_esistenti(self):
        """Carica i dati di un materiale esistente per la modifica"""
        if not self.materiale_esistente:
            return
        
        self.edit_diametro.setValue(self.materiale_esistente.diametro)
        self.edit_lunghezza.setValue(self.materiale_esistente.lunghezza)
        self.edit_giri.setValue(self.materiale_esistente.giri)
        
        if hasattr(self.materiale_esistente, 'arrotondamento_manuale') and self.materiale_esistente.arrotondamento_manuale != 0:
            self.edit_arrotondamento.setValue(self.materiale_esistente.arrotondamento_manuale)
            self.arrotondamento_modificato_manualmente = True
        
        if self.materiale_esistente.materiale_id:
            for i in range(self.combo_materiale.count()):
                if self.combo_materiale.itemData(i) == self.materiale_esistente.materiale_id:
                    self.combo_materiale.setCurrentIndex(i)
                    break
        
        self.aggiorna_display()
    
    def concludi_operazione(self):
        """Valida e conferma il materiale con controllo arrotondamento"""
        if self.materiale_calcolato.materiale_id is None:
            QMessageBox.warning(self, "Attenzione", "Seleziona un materiale.")
            return
        
        if self.materiale_calcolato.diametro <= 0:
            return
        
        if self.materiale_calcolato.lunghezza <= 0:
            QMessageBox.warning(self, "Attenzione", "Inserisci una lunghezza valida.")
            return
        
        if self.materiale_calcolato.giri <= 0:
            QMessageBox.warning(self, "Attenzione", "Inserisci un numero di giri valido.")
            return
        
        # Controllo arrotondamento personalizzato
        if self.arrotondamento_modificato_manualmente and self.edit_arrotondamento.value() != 0:
            reply = QMessageBox.question(
                self, 
                "Sviluppo Personalizzato", 
                f"Hai impostato un valore di sviluppo personalizzato ({self.edit_arrotondamento.value():.2f}) "
                f"che sovrascriverà il valore calcolato automaticamente ({self.materiale_calcolato.sviluppo:.2f}).\n\n"
                "Vuoi procedere con questo valore personalizzato?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        # Aggiorna il valore di sviluppo effettivo prima di emettere
        if self.arrotondamento_modificato_manualmente and self.edit_arrotondamento.value() != 0:
            self.materiale_calcolato.sviluppo = self.edit_arrotondamento.value()
        
        self.materiale_confermato.emit(self.materiale_calcolato, self.indice_modifica)
        self.close()
    
    def closeEvent(self, event):
        """Gestisce la chiusura della finestra"""
        if hasattr(self.parent(), 'materiale_windows'):
            try:
                self.parent().materiale_windows.remove(self)
            except ValueError:
                pass
        event.accept()