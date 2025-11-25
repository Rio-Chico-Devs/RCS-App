#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Preventivo UI Components - Componenti dell'interfaccia utente per preventivi COMPLETO
Uso riservato esclusivamente a RCS

Version: 1.0.0
Last Updated: 23/09/2025
Author: Antonio VB + Claude
"""

from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLabel, 
                             QLineEdit, QFormLayout, QGroupBox, QDoubleSpinBox, QFrame,
                             QGridLayout, QGraphicsDropShadowEffect, QScrollArea, QListWidget,
                             QListWidgetItem, QSizePolicy, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

class PreventivoUIComponents:
    """Classe per creare componenti UI standardizzati"""
    
    @staticmethod
    def create_shadow_effect(blur=10, opacity=12):
        """Effetto ombra standardizzato"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setColor(QColor(0, 0, 0, opacity))
        shadow.setOffset(0, 2)
        return shadow
    
    @staticmethod
    def create_standard_label(text):
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
    
    @staticmethod
    def create_standard_spinbox(suffix="€", callback=None):
        """SpinBox standardizzato"""
        spinbox = QDoubleSpinBox()
        spinbox.setMaximum(999999.99)
        spinbox.setDecimals(2)
        if suffix:
            spinbox.setSuffix(f" {suffix}")
        spinbox.setMinimumHeight(36)
        if callback:
            spinbox.valueChanged.connect(callback)
        return spinbox
    
    @staticmethod
    def init_ui(window_instance):
        """Inizializza l'interfaccia utente completa"""
        window_instance.setWindowTitle("RCS - Calcolo Preventivi")
        window_instance.setGeometry(100, 100, 1000, 800)
        
        # Widget principale con scroll
        main_widget = QWidget()
        window_instance.setCentralWidget(main_widget)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        scroll_layout.setContentsMargins(30, 30, 30, 30)
        
        # Componenti principali
        PreventivoUIComponents.create_header(window_instance, scroll_layout)
        PreventivoUIComponents.create_dati_cliente_section(window_instance, scroll_layout)
        PreventivoUIComponents.create_materiali_section(window_instance, scroll_layout)
        PreventivoUIComponents.create_costi_section(window_instance, scroll_layout)
        PreventivoUIComponents.create_footer(window_instance, scroll_layout, None)
        
        scroll_area.setWidget(scroll_content)
        
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
        # Stili globali
        window_instance.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QGroupBox {
                font-size: 16px;
                font-weight: 600;
                color: #2d3748;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px 0 8px;
                background-color: #ffffff;
            }
            QLineEdit, QDoubleSpinBox {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
                min-height: 20px;
                background-color: #ffffff;
            }
            QLineEdit:focus, QDoubleSpinBox:focus {
                border-color: #4a5568;
                background-color: #f7fafc;
            }
            QPushButton {
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                padding: 8px 16px;
            }
        """)
    
    @staticmethod
    def create_header(window_instance, parent_layout):
        """Crea header con titolo dinamico"""
        if window_instance.modalita == 'visualizza':
            title_text = f"Visualizzazione Preventivo #{window_instance.preventivo_id:03d}"
        elif window_instance.modalita == 'revisione':
            title_text = f"Revisione Preventivo #{window_instance.preventivo_originale_id:03d}"
        elif window_instance.modalita == 'modifica':
            title_text = f"Modifica Preventivo #{window_instance.preventivo_id:03d}"
        else:
            title_text = "Calcolo Preventivo"
            
        title_label = QLabel(title_text)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 700;
                color: #2d3748;
                padding: 0 0 20px 0;
            }
        """)
        parent_layout.addWidget(title_label)
    
    @staticmethod
    def create_dati_cliente_section(window_instance, parent_layout):
        """Crea sezione informazioni cliente"""
        client_group = QGroupBox("Informazioni Cliente")
        client_group.setGraphicsEffect(PreventivoUIComponents.create_shadow_effect())
        
        client_layout = QFormLayout(client_group)
        client_layout.setContentsMargins(25, 28, 25, 25)
        client_layout.setVerticalSpacing(16)
        client_layout.setHorizontalSpacing(16)
        
        # Campi cliente in layout a griglia
        client_grid_widget = QWidget()
        client_grid = QGridLayout(client_grid_widget)
        client_grid.setSpacing(16)
        
        # Prima riga: Nome Cliente e Numero Ordine
        client_grid.addWidget(PreventivoUIComponents.create_standard_label("Nome Cliente:"), 0, 0)
        window_instance.edit_nome_cliente = QLineEdit()
        client_grid.addWidget(window_instance.edit_nome_cliente, 0, 1)
        
        client_grid.addWidget(PreventivoUIComponents.create_standard_label("Numero Ordine:"), 0, 2)
        window_instance.edit_numero_ordine = QLineEdit()
        client_grid.addWidget(window_instance.edit_numero_ordine, 0, 3)
        
        # Seconda riga: Codice
        client_grid.addWidget(PreventivoUIComponents.create_standard_label("Codice:"), 1, 0)
        window_instance.edit_codice = QLineEdit()
        client_grid.addWidget(window_instance.edit_codice, 1, 1)
        
        # Terza riga: Descrizione
        client_grid.addWidget(PreventivoUIComponents.create_standard_label("Descrizione:"), 2, 0)
        window_instance.edit_descrizione = QLineEdit()
        window_instance.edit_descrizione.setMaxLength(100)
        client_grid.addWidget(window_instance.edit_descrizione, 2, 1, 1, 3)
        
        client_layout.addRow(client_grid_widget)
        
        # Disabilita i campi se in modalità visualizza
        if window_instance.modalita == 'visualizza':
            window_instance.edit_nome_cliente.setReadOnly(True)
            window_instance.edit_numero_ordine.setReadOnly(True)
            window_instance.edit_codice.setReadOnly(True)
            window_instance.edit_descrizione.setReadOnly(True)
        
        parent_layout.addWidget(client_group)
    
    @staticmethod
    def create_materiali_section(window_instance, parent_layout):
        """Crea sezione gestione materiali"""
        materiali_group = QGroupBox("Gestione Materiali")
        materiali_group.setGraphicsEffect(PreventivoUIComponents.create_shadow_effect())
        
        materiali_layout = QVBoxLayout(materiali_group)
        materiali_layout.setContentsMargins(25, 28, 25, 25)
        materiali_layout.setSpacing(16)
        
        # Pulsante aggiungi materiale
        if window_instance.modalita != 'visualizza':
            btn_aggiungi_materiale = QPushButton("Aggiungi Materiale")
            btn_aggiungi_materiale.setStyleSheet("""
                QPushButton {
                    background-color: #4a5568;
                    color: #ffffff;
                    font-size: 14px;
                    min-height: 36px;
                    max-width: 180px;
                }
                QPushButton:hover {
                    background-color: #2d3748;
                }
            """)
            btn_aggiungi_materiale.clicked.connect(window_instance.aggiungi_materiale)
            materiali_layout.addWidget(btn_aggiungi_materiale)
        
        # Lista materiali
        window_instance.lista_materiali = QListWidget()
        window_instance.lista_materiali.setMaximumHeight(300)
        window_instance.lista_materiali.setStyleSheet("""
            QListWidget {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background-color: #f7fafc;
                alternate-background-color: #ffffff;
            }
            QListWidget::item {
                border-bottom: 1px solid #e2e8f0;
                padding: 12px;
                background-color: #ffffff;
                margin: 2px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #edf2f7;
                border-color: #4a5568;
            }
        """)
        materiali_layout.addWidget(window_instance.lista_materiali)
        
        # Info costo materiali
        PreventivoUIComponents.create_cost_info_card(window_instance, materiali_layout)
        
        parent_layout.addWidget(materiali_group)
    
    @staticmethod
    def create_costi_section(window_instance, parent_layout):
        """Crea sezione costi e totali"""
        costi_group = QGroupBox("Costi e Tempi")
        costi_group.setGraphicsEffect(PreventivoUIComponents.create_shadow_effect())
        
        costi_layout = QVBoxLayout(costi_group)
        costi_layout.setContentsMargins(25, 28, 25, 25)
        costi_layout.setSpacing(20)
        
        # Layout orizzontale per due colonne
        columns_layout = QHBoxLayout()
        
        # Colonna sinistra - Tempi
        tempi_widget = QWidget()
        tempi_layout = QVBoxLayout(tempi_widget)
        tempi_layout.addWidget(PreventivoUIComponents.create_standard_label("Tempi di Lavorazione"))
        
        PreventivoUIComponents.create_time_form(window_instance, tempi_layout)
        columns_layout.addWidget(tempi_widget)
        
        # Separatore
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        columns_layout.addWidget(separator)
        
        # Colonna destra - Costi
        costi_widget = QWidget()
        costi_layout_inner = QVBoxLayout(costi_widget)
        costi_layout_inner.addWidget(PreventivoUIComponents.create_standard_label("Costi Aggiuntivi"))
        
        costi_grid = QGridLayout()
        costi_grid.setSpacing(12)
        
        # Costo orario e costi accessori
        window_instance.edit_costo_orario = PreventivoUIComponents.create_standard_spinbox("€/h", window_instance.on_mano_opera_changed)
        window_instance.edit_costo_orario.setValue(25.00)
        
        window_instance.edit_costi_accessori = PreventivoUIComponents.create_standard_spinbox("€", window_instance.on_costi_accessori_changed)
        
        costi_grid.addWidget(PreventivoUIComponents.create_standard_label("Costo Orario:"), 0, 0)
        costi_grid.addWidget(window_instance.edit_costo_orario, 0, 1)
        costi_grid.addWidget(PreventivoUIComponents.create_standard_label("Costi Accessori:"), 1, 0)
        costi_grid.addWidget(window_instance.edit_costi_accessori, 1, 1)
        
        costi_layout_inner.addLayout(costi_grid)
        columns_layout.addWidget(costi_widget)
        
        costi_layout.addLayout(columns_layout)
        
        # Disabilita controlli se in modalità visualizza
        if window_instance.modalita == 'visualizza':
            for widget_name in ['edit_minuti_taglio', 'edit_minuti_avvolgimento', 'edit_minuti_pulizia', 
                               'edit_minuti_rettifica', 'edit_minuti_imballaggio', 'edit_costo_orario', 'edit_costi_accessori']:
                if hasattr(window_instance, widget_name):
                    getattr(window_instance, widget_name).setReadOnly(True)
        
        # Sezione riepilogo totali
        PreventivoUIComponents.create_totals_summary(window_instance, costi_layout)
        
        parent_layout.addWidget(costi_group)
    
    @staticmethod
    def create_cost_info_card(window_instance, parent_layout):
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
        window_instance.lbl_costo_totale_materiali = QLabel("EUR 0,00")
        window_instance.lbl_costo_totale_materiali.setStyleSheet("""
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
        window_instance.lbl_num_materiali = QLabel("Nessun materiale inserito")
        window_instance.lbl_num_materiali.setStyleSheet("""
            QLabel {
                color: #718096;
                font-size: 13px;
                font-weight: 500;
            }
        """)
        
        layout.addWidget(window_instance.lbl_costo_totale_materiali)
        layout.addWidget(desc_label)
        layout.addWidget(window_instance.lbl_num_materiali)
        
        parent_layout.addWidget(container)
    
    @staticmethod
    def create_time_form(window_instance, parent_layout):
        """Form tempi standardizzato"""
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)
        grid_layout.setVerticalSpacing(16)
        
        # Campi tempi
        window_instance.edit_minuti_taglio = PreventivoUIComponents.create_standard_spinbox("min", window_instance.aggiorna_totali)
        window_instance.edit_minuti_avvolgimento = PreventivoUIComponents.create_standard_spinbox("min", window_instance.aggiorna_totali)
        window_instance.edit_minuti_pulizia = PreventivoUIComponents.create_standard_spinbox("min", window_instance.aggiorna_totali)
        window_instance.edit_minuti_rettifica = PreventivoUIComponents.create_standard_spinbox("min", window_instance.aggiorna_totali)
        window_instance.edit_minuti_imballaggio = PreventivoUIComponents.create_standard_spinbox("min", window_instance.aggiorna_totali)
        
        # Aggiunta alla griglia
        grid_layout.addWidget(PreventivoUIComponents.create_standard_label("Taglio:"), 0, 0)
        grid_layout.addWidget(window_instance.edit_minuti_taglio, 0, 1)
        grid_layout.addWidget(PreventivoUIComponents.create_standard_label("Avvolgimento:"), 1, 0)
        grid_layout.addWidget(window_instance.edit_minuti_avvolgimento, 1, 1)
        grid_layout.addWidget(PreventivoUIComponents.create_standard_label("Pulizia:"), 2, 0)
        grid_layout.addWidget(window_instance.edit_minuti_pulizia, 2, 1)
        grid_layout.addWidget(PreventivoUIComponents.create_standard_label("Rettifica:"), 3, 0)
        grid_layout.addWidget(window_instance.edit_minuti_rettifica, 3, 1)
        grid_layout.addWidget(PreventivoUIComponents.create_standard_label("Imballaggio:"), 4, 0)
        grid_layout.addWidget(window_instance.edit_minuti_imballaggio, 4, 1)
        
        parent_layout.addLayout(grid_layout)
    
    @staticmethod
    def create_totals_summary(window_instance, parent_layout):
        """Crea sezione riepilogo totali"""
        totali_frame = QFrame()
        totali_frame.setStyleSheet("""
            QFrame {
                background-color: #2d3748;
                border-radius: 8px;
                padding: 20px;
                margin-top: 16px;
            }
        """)
        
        totali_layout = QGridLayout(totali_frame)
        totali_layout.setSpacing(12)
        
        # Labels per totali
        labels_style = """
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
            }
        """
        values_style = """
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: 700;
                text-align: right;
            }
        """
        
        # Costo Materiali
        lbl_materiali = QLabel("Costo Materiali:")
        lbl_materiali.setStyleSheet(labels_style)
        window_instance.lbl_totale_materiali = QLabel("EUR 0,00")
        window_instance.lbl_totale_materiali.setStyleSheet(values_style)
        window_instance.lbl_totale_materiali.setAlignment(Qt.AlignRight)
        
        # Mano d'Opera
        lbl_manodopera = QLabel("Mano d'Opera:")
        lbl_manodopera.setStyleSheet(labels_style)
        window_instance.lbl_totale_manodopera = QLabel("EUR 0,00")
        window_instance.lbl_totale_manodopera.setStyleSheet(values_style)
        window_instance.lbl_totale_manodopera.setAlignment(Qt.AlignRight)
        
        # Costi Accessori
        lbl_accessori = QLabel("Costi Accessori:")
        lbl_accessori.setStyleSheet(labels_style)
        window_instance.lbl_totale_accessori = QLabel("EUR 0,00")
        window_instance.lbl_totale_accessori.setStyleSheet(values_style)
        window_instance.lbl_totale_accessori.setAlignment(Qt.AlignRight)
        
        # Totale Finale
        lbl_finale = QLabel("TOTALE PREVENTIVO:")
        lbl_finale.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
            }
        """)
        window_instance.lbl_totale_finale = QLabel("EUR 0,00")
        window_instance.lbl_totale_finale.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 20px;
                font-weight: 700;
                text-align: right;
            }
        """)
        window_instance.lbl_totale_finale.setAlignment(Qt.AlignRight)
        
        # Aggiunta al layout
        totali_layout.addWidget(lbl_materiali, 0, 0)
        totali_layout.addWidget(window_instance.lbl_totale_materiali, 0, 1)
        totali_layout.addWidget(lbl_manodopera, 1, 0)
        totali_layout.addWidget(window_instance.lbl_totale_manodopera, 1, 1)
        totali_layout.addWidget(lbl_accessori, 2, 0)
        totali_layout.addWidget(window_instance.lbl_totale_accessori, 2, 1)
        
        # Linea separatrice
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("QFrame { color: #4a5568; }")
        totali_layout.addWidget(separator, 3, 0, 1, 2)
        
        totali_layout.addWidget(lbl_finale, 4, 0)
        totali_layout.addWidget(window_instance.lbl_totale_finale, 4, 1)
        
        parent_layout.addWidget(totali_frame)
    
    @staticmethod
    def create_footer(window_instance, parent_layout, existing_layout=None):
        """Footer standardizzato per tutte le modalità"""
        if existing_layout:
            footer_layout = existing_layout
        else:
            footer_layout = QHBoxLayout()
        
        footer_layout.addStretch()
        
        if window_instance.modalita == 'visualizza':
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
            btn_chiudi.clicked.connect(window_instance.close)
            footer_layout.addWidget(btn_chiudi)
        else:
            # Annulla
            btn_annulla = QPushButton("Annulla")
            btn_annulla.setStyleSheet("""
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
            btn_annulla.clicked.connect(window_instance.close)
            
            # Salva/Salva Revisione
            if window_instance.modalita == 'revisione':
                btn_text = "Salva Revisione"
                btn_method = window_instance.salva_preventivo  # In modalità revisione usa lo stesso metodo
            else:
                btn_text = "Salva Preventivo"
                btn_method = window_instance.salva_preventivo
                
            btn_salva = QPushButton(btn_text)
            btn_salva.setStyleSheet("""
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
            btn_salva.clicked.connect(btn_method)
            
            footer_layout.addWidget(btn_annulla)
            footer_layout.addSpacing(12)
            footer_layout.addWidget(btn_salva)
        
        if not existing_layout:
            parent_layout.addLayout(footer_layout)
    
    @staticmethod
    def aggiorna_materiali_info(window_instance):
        """Aggiorna informazioni materiali nella lista"""
        window_instance.lista_materiali.clear()
        
        if not window_instance.preventivo.materiali_calcolati:
            window_instance.lbl_num_materiali.setText("Nessun materiale inserito")
            return
        
        for i, materiale in enumerate(window_instance.preventivo.materiali_calcolati):
            # Crea testo per item lista
            item_text = f"Materiale {i+1}: {materiale.nome} - Diametro: {materiale.diametro_interno:.1f}→{materiale.diametro_finale:.1f}mm - Costo: EUR {materiale.costo_totale:.2f}"
            
            # Crea item
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, i)
            
            # Aggiunge pulsanti se non in modalità visualizza
            if window_instance.modalita != 'visualizza':
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(0, 0, 0, 0)
                
                # Label del materiale
                label = QLabel(item_text)
                label.setStyleSheet("color: #2d3748; font-size: 13px;")
                layout.addWidget(label)
                layout.addStretch()
                
                # Pulsante Modifica
                btn_modifica = QPushButton("Modifica")
                btn_modifica.setMaximumWidth(80)
                btn_modifica.setStyleSheet("""
                    QPushButton {
                        background-color: #4a5568;
                        color: white;
                        border: none;
                        padding: 4px 8px;
                        min-height: 24px;
                    }
                    QPushButton:hover {
                        background-color: #2d3748;
                    }
                """)
                btn_modifica.clicked.connect(lambda checked, idx=i: window_instance.modifica_materiale(idx))
                layout.addWidget(btn_modifica)
                
                # Pulsante Elimina
                btn_elimina = QPushButton("Elimina")
                btn_elimina.setMaximumWidth(80)
                btn_elimina.setStyleSheet("""
                    QPushButton {
                        background-color: #e53e3e;
                        color: white;
                        border: none;
                        padding: 4px 8px;
                        min-height: 24px;
                    }
                    QPushButton:hover {
                        background-color: #c53030;
                    }
                """)
                btn_elimina.clicked.connect(lambda checked, idx=i: window_instance.elimina_materiale(idx))
                layout.addWidget(btn_elimina)
                
                # Imposta widget custom
                item.setSizeHint(widget.sizeHint())
                window_instance.lista_materiali.addItem(item)
                window_instance.lista_materiali.setItemWidget(item, widget)
            else:
                # In modalità visualizza, solo il testo
                window_instance.lista_materiali.addItem(item)
        
        # Aggiorna contatore
        num_materiali = len(window_instance.preventivo.materiali_calcolati)
        window_instance.lbl_num_materiali.setText(f"{num_materiali} materiale{'i' if num_materiali != 1 else ''} inserit{'i' if num_materiali != 1 else 'o'}")
    
    @staticmethod
    def aggiorna_interface_totali(window_instance):
        """Aggiorna interfaccia totali"""
        # Costo materiali
        costo_materiali = window_instance.preventivo.costo_totale_materiali
        window_instance.lbl_costo_totale_materiali.setText(f"EUR {costo_materiali:.2f}")
        
        # Controlla se esistono le label del riepilogo totali prima di aggiornarle
        if hasattr(window_instance, 'lbl_totale_materiali'):
            window_instance.lbl_totale_materiali.setText(f"EUR {costo_materiali:.2f}")
        
        # Mano d'opera
        if hasattr(window_instance, 'lbl_totale_manodopera'):
            costo_manodopera = window_instance.preventivo.costo_totale_manodopera
            window_instance.lbl_totale_manodopera.setText(f"EUR {costo_manodopera:.2f}")
        
        # Costi accessori
        if hasattr(window_instance, 'lbl_totale_accessori'):
            costi_accessori = window_instance.preventivo.costi_accessori
            window_instance.lbl_totale_accessori.setText(f"EUR {costi_accessori:.2f}")
        
        # Totale finale
        if hasattr(window_instance, 'lbl_totale_finale'):
            totale_finale = window_instance.preventivo.costo_totale_finale
            window_instance.lbl_totale_finale.setText(f"EUR {totale_finale:.2f}")
    
    @staticmethod
    def set_dati_cliente(window_instance, nome_cliente, numero_ordine, descrizione, codice):
        """Imposta dati cliente nei controlli"""
        if hasattr(window_instance, 'edit_nome_cliente'):
            window_instance.edit_nome_cliente.setText(nome_cliente or "")
        if hasattr(window_instance, 'edit_numero_ordine'):
            window_instance.edit_numero_ordine.setText(numero_ordine or "")
        if hasattr(window_instance, 'edit_descrizione'):
            window_instance.edit_descrizione.setText(descrizione or "")
        if hasattr(window_instance, 'edit_codice'):
            window_instance.edit_codice.setText(codice or "")