#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Materiale UI Components - Componenti dell'interfaccia utente per MaterialeWindow
Uso riservato esclusivamente a RCS

Version: 1.0.0
Last Updated: 23/09/2025
Author: Antonio VB + Claude
"""

from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLabel,
                             QLineEdit, QFormLayout, QGroupBox, QDoubleSpinBox, QFrame,
                             QGridLayout, QGraphicsDropShadowEffect, QComboBox, QSpinBox,
                             QSizePolicy, QScrollArea, QApplication, QDesktopWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from ui.tela_preview_widget import TelaPreviewWidget


class NoScrollSpinBox(QSpinBox):
    """QSpinBox che ignora la rotella del mouse"""
    def wheelEvent(self, event):
        event.ignore()


class NoScrollDoubleSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox che ignora la rotella del mouse"""
    def wheelEvent(self, event):
        event.ignore()

class MaterialeUIComponents:
    """Classe per creare componenti UI standardizzati per MaterialeWindow"""
    
    @staticmethod
    def create_shadow_effect(blur=10, opacity=12):
        """Effetto ombra standardizzato"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setColor(QColor(0, 0, 0, opacity))
        shadow.setOffset(0, 2)
        return shadow
    
    @staticmethod
    def init_ui(window_instance):
        """Inizializza l'interfaccia utente completa"""
        window_instance.setWindowTitle("Calcolo Materiale")
        if window_instance.materiale_esistente:
            window_instance.setWindowTitle("Modifica Materiale")
        
        # Schermo intero
        window_instance.showMaximized()
        
        # Sistema di design unificato (IDENTICO ALL'ORIGINALE)
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
        window_instance.setCentralWidget(main_widget)
        
        # Layout principale con proporzioni fisse
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(20)
        
        # Header
        MaterialeUIComponents.create_header(window_instance, main_layout)
        
        # Contenuto principale - layout orizzontale: Input | Risultati | Anteprima
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        MaterialeUIComponents.create_input_section(window_instance, content_layout)
        MaterialeUIComponents.create_results_section(window_instance, content_layout)
        MaterialeUIComponents.create_preview_section(window_instance, content_layout)

        main_layout.addLayout(content_layout, 1)
        
        # Footer
        MaterialeUIComponents.create_footer(window_instance, main_layout)
    
    @staticmethod
    def create_header(window_instance, parent_layout):
        """Header unificato"""
        title_text = "Calcolo Materiale"
        if window_instance.materiale_esistente:
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
    
    @staticmethod
    def create_input_section(window_instance, parent_layout):
        """Sezione input con design unificato"""
        input_group = QGroupBox("Parametri")
        input_group.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        input_group.setFixedWidth(450)
        input_group.setGraphicsEffect(MaterialeUIComponents.create_shadow_effect())

        layout = QVBoxLayout(input_group)
        layout.setContentsMargins(25, 28, 25, 25)
        layout.setSpacing(18)

        # Form layout principale
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(16)
        form_layout.setHorizontalSpacing(16)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # === CAMPI CILINDRICA (diametro + lunghezza) - visibili in modalità cilindrica ===
        window_instance.cilindrico_widget = QWidget()
        cilindrico_layout = QFormLayout(window_instance.cilindrico_widget)
        cilindrico_layout.setVerticalSpacing(16)
        cilindrico_layout.setHorizontalSpacing(16)
        cilindrico_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        cilindrico_layout.setContentsMargins(0, 0, 0, 0)

        window_instance.edit_diametro = MaterialeUIComponents.create_standard_input("mm", window_instance.on_parametro_changed)
        cilindrico_layout.addRow(MaterialeUIComponents.create_standard_label("Diametro"), window_instance.edit_diametro)

        window_instance.edit_lunghezza = MaterialeUIComponents.create_standard_input("mm", window_instance.on_parametro_changed, decimals=0, default_value=1000)
        cilindrico_layout.addRow(MaterialeUIComponents.create_standard_label("Lunghezza"), window_instance.edit_lunghezza)

        layout.addWidget(window_instance.cilindrico_widget)

        # === SEZIONI CONICHE - visibile solo in modalità conica ===
        window_instance.conica_widget = QWidget()
        conica_layout = QVBoxLayout(window_instance.conica_widget)
        conica_layout.setContentsMargins(0, 0, 0, 0)
        conica_layout.setSpacing(6)

        # Header sezioni + pulsanti
        sezioni_header = QHBoxLayout()
        lbl_sezioni = QLabel("Sezioni coniche:")
        lbl_sezioni.setStyleSheet("font-size: 13px; font-weight: 600; color: #4a5568;")
        sezioni_header.addWidget(lbl_sezioni)
        sezioni_header.addStretch()

        window_instance.btn_aggiungi_sezione = QPushButton("+")
        window_instance.btn_aggiungi_sezione.setFixedSize(30, 30)
        window_instance.btn_aggiungi_sezione.setStyleSheet("""
            QPushButton { background-color: #48bb78; color: white; font-size: 16px; font-weight: 700; border-radius: 4px; padding: 0; }
            QPushButton:hover { background-color: #38a169; }
        """)
        window_instance.btn_aggiungi_sezione.clicked.connect(window_instance.aggiungi_sezione_conica)

        window_instance.btn_rimuovi_sezione = QPushButton("-")
        window_instance.btn_rimuovi_sezione.setFixedSize(30, 30)
        window_instance.btn_rimuovi_sezione.setStyleSheet("""
            QPushButton { background-color: #e53e3e; color: white; font-size: 16px; font-weight: 700; border-radius: 4px; padding: 0; }
            QPushButton:hover { background-color: #c53030; }
        """)
        window_instance.btn_rimuovi_sezione.clicked.connect(window_instance.rimuovi_sezione_conica)

        sezioni_header.addWidget(window_instance.btn_aggiungi_sezione)
        sezioni_header.addWidget(window_instance.btn_rimuovi_sezione)
        conica_layout.addLayout(sezioni_header)

        # Header colonne
        col_header = QHBoxLayout()
        col_header.setSpacing(4)
        for txt in ["#", "Lungh. (mm)", "Ø Inizio", "Ø Fine"]:
            lbl = QLabel(txt)
            lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #718096;")
            lbl.setAlignment(Qt.AlignCenter)
            if txt == "#":
                lbl.setFixedWidth(20)
            col_header.addWidget(lbl)
        conica_layout.addLayout(col_header)

        # Scroll area per le righe sezioni
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setMaximumHeight(200)

        window_instance.sezioni_container = QWidget()
        window_instance.sezioni_layout = QVBoxLayout(window_instance.sezioni_container)
        window_instance.sezioni_layout.setContentsMargins(0, 0, 0, 0)
        window_instance.sezioni_layout.setSpacing(4)
        window_instance.sezioni_layout.addStretch()
        scroll.setWidget(window_instance.sezioni_container)

        conica_layout.addWidget(scroll)

        # Lista per tenere traccia dei widget delle sezioni
        window_instance.sezioni_widgets = []

        window_instance.conica_widget.hide()
        layout.addWidget(window_instance.conica_widget)

        # Campo Metri sotto Lunghezza
        MaterialeUIComponents.create_metri_field(window_instance, form_layout)

        # Materiale combo
        window_instance.combo_materiale = QComboBox()
        window_instance.combo_materiale.currentIndexChanged.connect(window_instance.on_materiale_changed)
        form_layout.addRow(MaterialeUIComponents.create_standard_label("Materiale"), window_instance.combo_materiale)

        # Giri
        window_instance.edit_giri = NoScrollSpinBox()
        window_instance.edit_giri.setMaximum(9999)
        window_instance.edit_giri.setValue(1)
        window_instance.edit_giri.valueChanged.connect(window_instance.on_parametro_changed)
        form_layout.addRow(MaterialeUIComponents.create_standard_label("Giri"), window_instance.edit_giri)

        layout.addLayout(form_layout)

        # Toggle Conica
        window_instance.btn_conica = QPushButton("Conica")
        window_instance.btn_conica.setCheckable(True)
        window_instance.btn_conica.setFixedHeight(36)
        window_instance.btn_conica.setStyleSheet("""
            QPushButton { background-color: #edf2f7; color: #4a5568; border: 1px solid #e2e8f0; font-size: 13px; font-weight: 600; }
            QPushButton:hover { background-color: #e2e8f0; }
            QPushButton:checked { background-color: #4299e1; color: white; border: 1px solid #3182ce; }
        """)
        window_instance.btn_conica.clicked.connect(window_instance.toggle_conica)
        layout.addWidget(window_instance.btn_conica)

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
    
    @staticmethod
    def create_standard_input(suffix="", callback=None, decimals=2, default_value=0):
        """Input standardizzato per tutto il form"""
        field = NoScrollDoubleSpinBox()
        field.setMaximum(999999.99)
        field.setDecimals(decimals)
        if suffix:
            field.setSuffix(f" {suffix}")
        if default_value:
            field.setValue(default_value)
        if callback:
            field.valueChanged.connect(callback)
        field.setMinimumHeight(36)
        return field
    
    @staticmethod
    def create_standard_label(text):
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
    
    @staticmethod
    def create_metri_field(window_instance, form_layout):
        """Campo metri sotto lunghezza - stile unificato"""
        window_instance.lbl_lunghezza_utilizzata = QLabel("0.000000 m")
        window_instance.lbl_lunghezza_utilizzata.setStyleSheet("""
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
        form_layout.addRow(MaterialeUIComponents.create_standard_label("Metri"), window_instance.lbl_lunghezza_utilizzata)
    
    @staticmethod
    def create_results_section(window_instance, parent_layout):
        """Sezione risultati con design unificato"""
        results_group = QGroupBox("Risultati")
        results_group.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        results_group.setFixedWidth(450)
        results_group.setGraphicsEffect(MaterialeUIComponents.create_shadow_effect())
        
        layout = QVBoxLayout(results_group)
        layout.setContentsMargins(25, 28, 25, 25)
        layout.setSpacing(12)
        
        # Tutti i risultati con design identico
        MaterialeUIComponents.create_standard_result(window_instance, "Spessore Tela", "lbl_spessore", "0.00 mm", layout)
        MaterialeUIComponents.create_standard_result(window_instance, "Diametro Finale", "lbl_diametro_finale", "0.00 mm", layout, important=True)
        MaterialeUIComponents.create_standard_result(window_instance, "Sviluppo", "lbl_sviluppo", "0.00", layout, important=True)
        
        # Sviluppo manuale section - FIX: callback specifico per sviluppo
        MaterialeUIComponents.create_override_section(window_instance, layout)
        
        MaterialeUIComponents.create_standard_result(window_instance, "Costo Materiale", "lbl_costo_materiale", "€0.00", layout)
        MaterialeUIComponents.create_standard_result(window_instance, "Costo Totale", "lbl_costo_totale", "€0.00", layout)
        
        # Maggiorazione finale
        MaterialeUIComponents.create_final_result(window_instance, layout)
        
        layout.addStretch()
        
        parent_layout.addWidget(results_group)
    
    @staticmethod
    def create_standard_result(window_instance, title, attr_name, default_value, parent_layout, important=False):
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
        
        setattr(window_instance, attr_name, value_label)
        parent_layout.addWidget(container)
    
    @staticmethod
    def create_override_section(window_instance, parent_layout):
        """Sviluppo manuale section - FIX: callback specifico per sviluppo"""
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
        
        # FIX: Input con callback specifico per sviluppo manuale
        window_instance.edit_arrotondamento = NoScrollDoubleSpinBox()
        window_instance.edit_arrotondamento.setMaximum(999999.99)
        window_instance.edit_arrotondamento.setDecimals(2)
        window_instance.edit_arrotondamento.setFixedHeight(36)
        window_instance.edit_arrotondamento.valueChanged.connect(window_instance.on_sviluppo_manuale_changed)
        window_instance.edit_arrotondamento.setStyleSheet("""
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
        window_instance.lbl_arrotondamento_status = QLabel("")
        window_instance.lbl_arrotondamento_status.hide()
        
        # Layout singolo per l'input
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.addWidget(window_instance.edit_arrotondamento)
        
        layout.addWidget(title_label)
        layout.addWidget(input_container)
        
        parent_layout.addWidget(container)
    
    @staticmethod
    def create_final_result(window_instance, parent_layout):
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
        window_instance.lbl_maggiorazione = QLabel("€0.00")
        window_instance.lbl_maggiorazione.setStyleSheet("""
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
        window_instance.lbl_maggiorazione.setFixedHeight(36)
        window_instance.lbl_maggiorazione.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(window_instance.lbl_maggiorazione)
        
        parent_layout.addWidget(container)
    
    @staticmethod
    def create_preview_section(window_instance, parent_layout):
        """Sezione anteprima CAD della tela tagliata"""
        preview_group = QGroupBox("Anteprima Tela")
        preview_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        preview_group.setGraphicsEffect(MaterialeUIComponents.create_shadow_effect())

        layout = QVBoxLayout(preview_group)
        layout.setContentsMargins(15, 28, 15, 15)
        layout.setSpacing(8)

        # Barra pulsanti trasformazione
        btn_style = """
            QPushButton {
                background-color: #edf2f7;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                font-size: 16px;
                padding: 0;
            }
            QPushButton:hover { background-color: #e2e8f0; }
            QPushButton:pressed { background-color: #cbd5e0; }
        """
        transform_layout = QHBoxLayout()
        transform_layout.setSpacing(6)
        transform_layout.addStretch()

        btn_rotate_left = QPushButton("↺")
        btn_rotate_left.setToolTip("Ruota a sinistra (90°)")
        btn_rotate_left.setFixedSize(32, 32)
        btn_rotate_left.setStyleSheet(btn_style)
        transform_layout.addWidget(btn_rotate_left)

        btn_rotate_right = QPushButton("↻")
        btn_rotate_right.setToolTip("Ruota a destra (90°)")
        btn_rotate_right.setFixedSize(32, 32)
        btn_rotate_right.setStyleSheet(btn_style)
        transform_layout.addWidget(btn_rotate_right)

        btn_flip_h = QPushButton("↔")
        btn_flip_h.setToolTip("Capovolgi orizzontalmente")
        btn_flip_h.setFixedSize(32, 32)
        btn_flip_h.setStyleSheet(btn_style)
        transform_layout.addWidget(btn_flip_h)

        btn_flip_v = QPushButton("↕")
        btn_flip_v.setToolTip("Capovolgi verticalmente")
        btn_flip_v.setFixedSize(32, 32)
        btn_flip_v.setStyleSheet(btn_style)
        transform_layout.addWidget(btn_flip_v)

        layout.addLayout(transform_layout)

        # Widget di anteprima CAD
        window_instance.tela_preview = TelaPreviewWidget()

        btn_rotate_left.clicked.connect(window_instance.tela_preview.rotate_left)
        btn_rotate_right.clicked.connect(window_instance.tela_preview.rotate_right)
        btn_flip_h.clicked.connect(window_instance.tela_preview.flip_horizontal)
        btn_flip_v.clicked.connect(window_instance.tela_preview.flip_vertical)

        layout.addWidget(window_instance.tela_preview, 1)

        parent_layout.addWidget(preview_group, 1)  # stretch=1 per prendere spazio rimanente

    @staticmethod
    def create_footer(window_instance, parent_layout):
        """Footer standardizzato"""
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        window_instance.btn_annulla = QPushButton("Annulla")
        window_instance.btn_annulla.setFixedHeight(40)
        window_instance.btn_annulla.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
        """)
        window_instance.btn_annulla.clicked.connect(window_instance.close)
        
        confirm_text = "Aggiorna" if window_instance.materiale_esistente else "Conferma"
        window_instance.btn_concludi = QPushButton(confirm_text)
        window_instance.btn_concludi.setFixedHeight(40)
        window_instance.btn_concludi.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
        """)
        window_instance.btn_concludi.clicked.connect(window_instance.concludi_operazione)
        
        footer_layout.addWidget(window_instance.btn_annulla)
        footer_layout.addSpacing(12)
        footer_layout.addWidget(window_instance.btn_concludi)
        
        parent_layout.addLayout(footer_layout)
    
    @staticmethod
    def aggiorna_display(window_instance):
        """Aggiorna tutti i valori mostrati nell'interfaccia"""
        try:
            if hasattr(window_instance, 'lbl_spessore'):
                window_instance.lbl_spessore.setText(f"{window_instance.materiale_calcolato.spessore:.2f} mm")
            if hasattr(window_instance, 'lbl_diametro_finale'):
                window_instance.lbl_diametro_finale.setText(f"{window_instance.materiale_calcolato.diametro_finale:.2f} mm")
            if hasattr(window_instance, 'lbl_sviluppo'):
                window_instance.lbl_sviluppo.setText(f"{window_instance.materiale_calcolato.sviluppo:.2f}")
            if hasattr(window_instance, 'lbl_costo_materiale'):
                window_instance.lbl_costo_materiale.setText(f"€{window_instance.materiale_calcolato.costo_materiale:.2f}")
            if hasattr(window_instance, 'lbl_lunghezza_utilizzata'):
                window_instance.lbl_lunghezza_utilizzata.setText(f"{window_instance.materiale_calcolato.lunghezza_utilizzata:.6f} m")
            if hasattr(window_instance, 'lbl_costo_totale'):
                window_instance.lbl_costo_totale.setText(f"€{window_instance.materiale_calcolato.costo_totale:.2f}")
            if hasattr(window_instance, 'lbl_maggiorazione'):
                window_instance.lbl_maggiorazione.setText(f"€{window_instance.materiale_calcolato.maggiorazione:.2f}")
        except Exception as e:
            pass