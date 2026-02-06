#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
ConfrontoPreventiviWindow - Finestra per confrontare due preventivi
Uso riservato esclusivamente a RCS

Version: 1.0.0
Last Updated: 04/02/2025
Author: Sviluppatore PyQt5 + Claude
"""

from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
                             QWidget, QLabel, QFrame, QScrollArea, QComboBox,
                             QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
                             QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

class ConfrontoPreventiviWindow(QMainWindow):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.preventivo1_id = None
        self.preventivo1_data = None
        self.preventivo2_id = None
        self.preventivo2_data = None
        self.fase_corrente = 1  # 1 = selezione primo, 2 = selezione secondo, 3 = confronto

        self.init_ui()

    def init_ui(self):
        """Inizializza l'interfaccia utente"""
        self.setWindowTitle("RCS - Confronto Preventivi")
        self.setMinimumSize(1400, 800)

        # Widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)

        # Titolo
        title_label = QLabel("Confronto Preventivi")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_label.setStyleSheet("color: #2d3748; border: none; padding: 0;")
        header_layout.addWidget(title_label)

        # Sottotitolo (cambia in base alla fase)
        self.subtitle_label = QLabel("Seleziona il primo preventivo da confrontare")
        self.subtitle_label.setFont(QFont("Segoe UI", 12))
        self.subtitle_label.setStyleSheet("color: #4a5568; border: none; padding: 0;")
        header_layout.addWidget(self.subtitle_label)

        main_layout.addWidget(header_frame)

        # Container per contenuto dinamico
        self.content_container = QFrame()
        self.content_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(15)

        main_layout.addWidget(self.content_container, 1)

        # Pulsante chiudi
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_chiudi = QPushButton("Chiudi")
        btn_chiudi.setMinimumSize(120, 40)
        btn_chiudi.setStyleSheet("""
            QPushButton {
                background-color: #e2e8f0;
                color: #2d3748;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cbd5e0;
            }
        """)
        btn_chiudi.clicked.connect(self.close)
        btn_layout.addWidget(btn_chiudi)

        main_layout.addLayout(btn_layout)

        # Mostra la prima fase
        self.mostra_fase_1()

    def pulisci_content(self):
        """Pulisce il contenuto dinamico"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    subitem = item.layout().takeAt(0)
                    if subitem.widget():
                        subitem.widget().deleteLater()

    def mostra_fase_1(self):
        """Mostra interfaccia per selezione primo preventivo"""
        self.fase_corrente = 1
        self.subtitle_label.setText("Seleziona il primo preventivo da confrontare")
        self.crea_interfaccia_selezione(1)

    def mostra_fase_2(self):
        """Mostra interfaccia per selezione secondo preventivo"""
        self.fase_corrente = 2
        self.subtitle_label.setText("Seleziona il secondo preventivo da confrontare")
        self.crea_interfaccia_selezione(2)

    def mostra_fase_3(self):
        """Mostra interfaccia di confronto"""
        self.fase_corrente = 3
        self.subtitle_label.setText("Confronto tra i due preventivi selezionati")
        self.crea_interfaccia_confronto()

    def crea_interfaccia_selezione(self, numero_preventivo):
        """Crea l'interfaccia per selezionare un preventivo"""
        self.pulisci_content()

        # Filtro per cliente
        filtro_layout = QHBoxLayout()

        label_cliente = QLabel("Cliente:")
        label_cliente.setFont(QFont("Segoe UI", 11, QFont.Bold))
        label_cliente.setStyleSheet("color: #2d3748;")
        filtro_layout.addWidget(label_cliente)

        self.combo_clienti = QComboBox()
        self.combo_clienti.setMinimumHeight(36)
        self.combo_clienti.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #cbd5e0;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QComboBox:hover {
                border-color: #4299e1;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        filtro_layout.addWidget(self.combo_clienti, 1)

        filtro_layout.addSpacing(20)

        label_filtro = QLabel("Cerca:")
        label_filtro.setFont(QFont("Segoe UI", 11, QFont.Bold))
        label_filtro.setStyleSheet("color: #2d3748;")
        filtro_layout.addWidget(label_filtro)

        self.input_filtro = QLineEdit()
        self.input_filtro.setPlaceholderText("Cerca in tutti i campi...")
        self.input_filtro.setMinimumHeight(36)
        self.input_filtro.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #cbd5e0;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #4299e1;
            }
        """)
        self.input_filtro.textChanged.connect(self.filtra_preventivi)
        filtro_layout.addWidget(self.input_filtro, 1)

        self.content_layout.addLayout(filtro_layout)

        # Lista preventivi
        self.lista_preventivi = QListWidget()
        self.lista_preventivi.setStyleSheet("""
            QListWidget {
                background-color: #fafbfc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 5px;
            }
            QListWidget::item {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 10px;
                margin: 3px;
            }
            QListWidget::item:hover {
                background-color: #edf2f7;
                border-color: #cbd5e0;
            }
            QListWidget::item:selected {
                background-color: #bee3f8;
                border-color: #4299e1;
                color: #2d3748;
            }
        """)
        self.lista_preventivi.itemDoubleClicked.connect(lambda: self.seleziona_preventivo(numero_preventivo))
        self.content_layout.addWidget(self.lista_preventivi, 1)

        # Label "nessun preventivo trovato" (nascosta di default)
        self.label_nessun_preventivo = QLabel("Nessun preventivo trovato")
        self.label_nessun_preventivo.setAlignment(Qt.AlignCenter)
        self.label_nessun_preventivo.setFont(QFont("Segoe UI", 14))
        self.label_nessun_preventivo.setStyleSheet("color: #718096; padding: 40px;")
        self.label_nessun_preventivo.setVisible(False)
        self.content_layout.addWidget(self.label_nessun_preventivo)

        # Pulsante selezione
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_seleziona = QPushButton("Seleziona Preventivo")
        btn_seleziona.setMinimumSize(180, 40)
        btn_seleziona.setStyleSheet("""
            QPushButton {
                background-color: #4299e1;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3182ce;
            }
            QPushButton:disabled {
                background-color: #cbd5e0;
                color: #a0aec0;
            }
        """)
        btn_seleziona.clicked.connect(lambda: self.seleziona_preventivo(numero_preventivo))
        btn_layout.addWidget(btn_seleziona)

        self.content_layout.addLayout(btn_layout)

        # Carica i clienti
        self.carica_clienti()

    def carica_clienti(self):
        """Carica la lista dei clienti dal database"""
        self.combo_clienti.clear()
        self.combo_clienti.addItem("-- Tutti i clienti --", None)

        try:
            preventivi_raw = self.db_manager.get_all_preventivi()
            clienti = set()
            for prev_tuple in preventivi_raw:
                # prev_tuple è (id, data_creazione, preventivo_finale, prezzo_cliente,
                #               nome_cliente, numero_ordine, descrizione, codice, numero_revisione)
                nome_cliente = prev_tuple[4].strip() if len(prev_tuple) > 4 and prev_tuple[4] else ''
                if nome_cliente:
                    clienti.add(nome_cliente)

            for cliente in sorted(clienti):
                self.combo_clienti.addItem(cliente, cliente)

            self.combo_clienti.currentIndexChanged.connect(self.filtra_preventivi)
            self.filtra_preventivi()
        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Errore nel caricamento clienti: {str(e)}")

    def filtra_preventivi(self):
        """Filtra i preventivi in base al cliente e al testo di ricerca"""
        self.lista_preventivi.clear()

        cliente_selezionato = self.combo_clienti.currentData()
        testo_filtro = self.input_filtro.text().lower().strip()

        try:
            preventivi_raw = self.db_manager.get_all_preventivi()
            preventivi_filtrati = []

            for prev_tuple in preventivi_raw:
                # prev_tuple è (id, data_creazione, preventivo_finale, prezzo_cliente,
                #               nome_cliente, numero_ordine, descrizione, codice, numero_revisione)
                id_prev = prev_tuple[0]
                data_creazione = prev_tuple[1]
                preventivo_finale = prev_tuple[2]
                prezzo_cliente = prev_tuple[3]
                nome_cliente = prev_tuple[4] if len(prev_tuple) > 4 else ''
                numero_ordine = prev_tuple[5] if len(prev_tuple) > 5 else ''
                descrizione = prev_tuple[6] if len(prev_tuple) > 6 else ''
                codice = prev_tuple[7] if len(prev_tuple) > 7 else ''
                numero_revisione = prev_tuple[8] if len(prev_tuple) > 8 else 1

                # Filtro per cliente
                if cliente_selezionato:
                    if nome_cliente.strip() != cliente_selezionato:
                        continue

                # Filtro per testo (cerca in TUTTI i campi)
                if testo_filtro:
                    # Crea una stringa con tutti i valori
                    valori_da_cercare = [
                        str(id_prev),
                        str(data_creazione),
                        str(preventivo_finale),
                        str(prezzo_cliente),
                        str(nome_cliente),
                        str(numero_ordine),
                        str(descrizione),
                        str(codice),
                        str(numero_revisione),
                        "originale" if numero_revisione == 1 else "revisionato",
                        "revisione" if numero_revisione > 1 else ""
                    ]

                    testo_completo = " ".join(valori_da_cercare).lower()

                    if testo_filtro not in testo_completo:
                        continue

                preventivi_filtrati.append(prev_tuple)

            # Mostra/nascondi label "nessun preventivo"
            if len(preventivi_filtrati) == 0:
                self.lista_preventivi.setVisible(False)
                self.label_nessun_preventivo.setVisible(True)
            else:
                self.lista_preventivi.setVisible(True)
                self.label_nessun_preventivo.setVisible(False)

                # Popola la lista
                for prev_tuple in preventivi_filtrati:
                    id_prev = prev_tuple[0]
                    data_creazione = prev_tuple[1]
                    preventivo_finale = prev_tuple[2]
                    nome_cliente = prev_tuple[4] if len(prev_tuple) > 4 else 'N/A'
                    descrizione = prev_tuple[6] if len(prev_tuple) > 6 else 'N/A'
                    numero_revisione = prev_tuple[8] if len(prev_tuple) > 8 else 1

                    tipo_preventivo = "Originale" if numero_revisione == 1 else f"Revisione {numero_revisione}"

                    testo = (f"ID: {id_prev} - "
                            f"{nome_cliente} - "
                            f"{descrizione} - "
                            f"€{preventivo_finale:.2f} - "
                            f"{data_creazione} - "
                            f"{tipo_preventivo}")

                    item = QListWidgetItem(testo)
                    item.setData(Qt.UserRole, id_prev)
                    self.lista_preventivi.addItem(item)

        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Errore nel caricamento preventivi: {str(e)}")

    def seleziona_preventivo(self, numero_preventivo):
        """Seleziona un preventivo e passa alla fase successiva"""
        item_selezionato = self.lista_preventivi.currentItem()
        if not item_selezionato:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo dalla lista")
            return

        preventivo_id = item_selezionato.data(Qt.UserRole)

        try:
            preventivo_data = self.db_manager.get_preventivo_by_id(preventivo_id)

            if numero_preventivo == 1:
                self.preventivo1_id = preventivo_id
                self.preventivo1_data = preventivo_data
                self.mostra_fase_2()
            else:
                self.preventivo2_id = preventivo_id
                self.preventivo2_data = preventivo_data
                self.mostra_fase_3()

        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Errore nel caricamento preventivo: {str(e)}")

    def crea_interfaccia_confronto(self):
        """Crea l'interfaccia di confronto tra i due preventivi"""
        self.pulisci_content()

        # Scroll area per il confronto
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #fafbfc;
            }
        """)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)

        # Intestazione con i nomi dei due preventivi
        header_confronto = QFrame()
        header_confronto.setStyleSheet("""
            QFrame {
                background-color: #edf2f7;
                border: 1px solid #cbd5e0;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        header_layout = QHBoxLayout(header_confronto)

        # Preventivo 1
        prev1_header = QVBoxLayout()
        prev1_title = QLabel("PREVENTIVO 1")
        prev1_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        prev1_title.setStyleSheet("color: #2d3748; border: none;")
        prev1_header.addWidget(prev1_title)

        numero_rev_1 = self.preventivo1_data.get('numero_revisione', 1)
        tipo_prev_1 = "Originale" if numero_rev_1 == 1 else f"Revisionato (Rev. {numero_rev_1})"
        prev1_tipo = QLabel(tipo_prev_1)
        prev1_tipo.setFont(QFont("Segoe UI", 11))
        prev1_tipo.setStyleSheet("color: #4a5568; border: none;")
        prev1_header.addWidget(prev1_tipo)

        prev1_info = QLabel(f"{self.preventivo1_data.get('nome_cliente', 'N/A')} - {self.preventivo1_data.get('descrizione', 'N/A')}")
        prev1_info.setFont(QFont("Segoe UI", 10))
        prev1_info.setStyleSheet("color: #718096; border: none;")
        prev1_header.addWidget(prev1_info)

        header_layout.addLayout(prev1_header, 1)

        # Separatore
        separatore_header = QFrame()
        separatore_header.setFrameShape(QFrame.VLine)
        separatore_header.setFrameShadow(QFrame.Sunken)
        separatore_header.setStyleSheet("background-color: #cbd5e0; border: none;")
        separatore_header.setFixedWidth(2)
        header_layout.addWidget(separatore_header)

        # Preventivo 2
        prev2_header = QVBoxLayout()
        prev2_title = QLabel("PREVENTIVO 2")
        prev2_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        prev2_title.setStyleSheet("color: #2d3748; border: none;")
        prev2_header.addWidget(prev2_title)

        numero_rev_2 = self.preventivo2_data.get('numero_revisione', 1)
        tipo_prev_2 = "Originale" if numero_rev_2 == 1 else f"Revisionato (Rev. {numero_rev_2})"
        prev2_tipo = QLabel(tipo_prev_2)
        prev2_tipo.setFont(QFont("Segoe UI", 11))
        prev2_tipo.setStyleSheet("color: #4a5568; border: none;")
        prev2_header.addWidget(prev2_tipo)

        prev2_info = QLabel(f"{self.preventivo2_data.get('nome_cliente', 'N/A')} - {self.preventivo2_data.get('descrizione', 'N/A')}")
        prev2_info.setFont(QFont("Segoe UI", 10))
        prev2_info.setStyleSheet("color: #718096; border: none;")
        prev2_header.addWidget(prev2_info)

        header_layout.addLayout(prev2_header, 1)

        scroll_layout.addWidget(header_confronto)

        # Sezioni di confronto
        self.crea_sezione_confronto(scroll_layout, "Informazioni Generali", [
            ("ID", "id"),
            ("Data Creazione", "data_creazione"),
            ("Cliente", "nome_cliente"),
            ("Codice", "codice"),
            ("Numero Ordine", "numero_ordine"),
            ("Descrizione", "descrizione"),
            ("Numero Revisione", "numero_revisione")
        ])

        self.crea_sezione_confronto(scroll_layout, "Costi Materiali", [
            ("Costo Totale Materiali", "costo_totale_materiali", True),
            ("Costi Accessori", "costi_accessori", True)
        ])

        self.crea_sezione_confronto(scroll_layout, "Mano d'Opera (minuti)", [
            ("Taglio", "minuti_taglio"),
            ("Avvolgimento", "minuti_avvolgimento"),
            ("Pulizia", "minuti_pulizia"),
            ("Rettifica", "minuti_rettifica"),
            ("Imballaggio", "minuti_imballaggio"),
            ("Totale Mano d'Opera", "tot_mano_opera")
        ])

        self.crea_sezione_confronto(scroll_layout, "Preventivo", [
            ("Subtotale", "subtotale", True),
            ("Maggiorazione 25%", "maggiorazione_25", True),
            ("Preventivo Finale", "preventivo_finale", True),
            ("Prezzo Cliente", "prezzo_cliente", True)
        ])

        # Sezione materiali
        self.crea_sezione_materiali_confronto(scroll_layout)

        scroll.setWidget(scroll_widget)
        self.content_layout.addWidget(scroll, 1)

        # Pulsanti azione
        btn_layout = QHBoxLayout()

        btn_nuovo = QPushButton("Nuovo Confronto")
        btn_nuovo.setMinimumSize(150, 40)
        btn_nuovo.setStyleSheet("""
            QPushButton {
                background-color: #48bb78;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #38a169;
            }
        """)
        btn_nuovo.clicked.connect(self.reset_confronto)
        btn_layout.addWidget(btn_nuovo)

        btn_layout.addStretch()

        self.content_layout.addLayout(btn_layout)

    def crea_sezione_confronto(self, parent_layout, titolo, campi):
        """Crea una sezione di confronto con i campi specificati"""
        sezione_frame = QFrame()
        sezione_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        sezione_layout = QVBoxLayout(sezione_frame)

        # Titolo sezione
        titolo_label = QLabel(titolo)
        titolo_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        titolo_label.setStyleSheet("color: #2d3748; border: none; padding-bottom: 10px;")
        sezione_layout.addWidget(titolo_label)

        # Container per i campi a due colonne
        for nome_campo, chiave_campo, *args in campi:
            is_currency = len(args) > 0 and args[0]

            campo_layout = QHBoxLayout()
            campo_layout.setSpacing(10)

            # Valore preventivo 1
            valore1 = self.preventivo1_data.get(chiave_campo, "N/A")
            campo1 = self.crea_campo_confronto(nome_campo, valore1, self.preventivo1_data, 1, is_currency)
            campo_layout.addWidget(campo1, 1)

            # Separatore
            separatore = QFrame()
            separatore.setFrameShape(QFrame.VLine)
            separatore.setFrameShadow(QFrame.Sunken)
            separatore.setStyleSheet("background-color: #e2e8f0;")
            separatore.setFixedWidth(1)
            campo_layout.addWidget(separatore)

            # Valore preventivo 2
            valore2 = self.preventivo2_data.get(chiave_campo, "N/A")
            campo2 = self.crea_campo_confronto(nome_campo, valore2, self.preventivo2_data, 2, is_currency)
            campo_layout.addWidget(campo2, 1)

            sezione_layout.addLayout(campo_layout)

        parent_layout.addWidget(sezione_frame)

    def crea_campo_confronto(self, nome_campo, valore, preventivo_data, posizione, is_currency=False):
        """Crea un campo di confronto con evidenziazione se diverso"""
        campo_frame = QFrame()
        campo_layout = QVBoxLayout(campo_frame)
        campo_layout.setContentsMargins(10, 10, 10, 10)
        campo_layout.setSpacing(5)

        # Verifica se il campo è diverso tra i due preventivi
        is_different = self.campo_e_diverso(nome_campo, preventivo_data)

        # Applica stile evidenziato se diverso
        if is_different:
            campo_frame.setStyleSheet("""
                QFrame {
                    background-color: #fef5e7;
                    border: 2px solid #f39c12;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
        else:
            campo_frame.setStyleSheet("""
                QFrame {
                    background-color: #f7fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)

        # Label nome campo
        label_nome = QLabel(nome_campo)
        label_nome.setFont(QFont("Segoe UI", 10, QFont.Bold))
        label_nome.setStyleSheet("color: #4a5568; border: none; padding: 0;")
        campo_layout.addWidget(label_nome)

        # Label valore
        if is_currency and isinstance(valore, (int, float)):
            testo_valore = f"€ {valore:.2f}"
        else:
            testo_valore = str(valore)

        label_valore = QLabel(testo_valore)
        label_valore.setFont(QFont("Segoe UI", 12))
        label_valore.setStyleSheet("color: #2d3748; border: none; padding: 0;")
        label_valore.setWordWrap(True)
        campo_layout.addWidget(label_valore)

        return campo_frame

    def campo_e_diverso(self, nome_campo, preventivo_data):
        """Verifica se un campo è diverso tra i due preventivi"""
        # Mappa i nomi dei campi alle chiavi del dizionario
        campo_map = {
            "ID": "id",
            "Data Creazione": "data_creazione",
            "Cliente": "nome_cliente",
            "Codice": "codice",
            "Numero Ordine": "numero_ordine",
            "Descrizione": "descrizione",
            "Numero Revisione": "numero_revisione",
            "Costo Totale Materiali": "costo_totale_materiali",
            "Costi Accessori": "costi_accessori",
            "Taglio": "minuti_taglio",
            "Avvolgimento": "minuti_avvolgimento",
            "Pulizia": "minuti_pulizia",
            "Rettifica": "minuti_rettifica",
            "Imballaggio": "minuti_imballaggio",
            "Totale Mano d'Opera": "tot_mano_opera",
            "Subtotale": "subtotale",
            "Maggiorazione 25%": "maggiorazione_25",
            "Preventivo Finale": "preventivo_finale",
            "Prezzo Cliente": "prezzo_cliente"
        }

        chiave = campo_map.get(nome_campo)
        if not chiave:
            return False

        valore1 = self.preventivo1_data.get(chiave)
        valore2 = self.preventivo2_data.get(chiave)

        # Confronto numerico per float/int
        if isinstance(valore1, (int, float)) and isinstance(valore2, (int, float)):
            return abs(valore1 - valore2) > 0.01

        # Confronto standard per altri tipi
        return valore1 != valore2

    def crea_sezione_materiali_confronto(self, parent_layout):
        """Crea la sezione di confronto dei materiali utilizzati"""
        sezione_frame = QFrame()
        sezione_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        sezione_layout = QVBoxLayout(sezione_frame)

        # Titolo sezione
        titolo_label = QLabel("Materiali Utilizzati")
        titolo_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        titolo_label.setStyleSheet("color: #2d3748; border: none; padding-bottom: 10px;")
        sezione_layout.addWidget(titolo_label)

        # Layout a due colonne per i materiali
        materiali_layout = QHBoxLayout()
        materiali_layout.setSpacing(10)

        # Materiali preventivo 1
        materiali1 = self.preventivo1_data.get('materiali_utilizzati', [])
        materiali2 = self.preventivo2_data.get('materiali_utilizzati', [])
        col1 = self.crea_colonna_materiali(materiali1, materiali2, 1)
        materiali_layout.addWidget(col1, 1)

        # Separatore
        separatore = QFrame()
        separatore.setFrameShape(QFrame.VLine)
        separatore.setFrameShadow(QFrame.Sunken)
        separatore.setStyleSheet("background-color: #e2e8f0;")
        separatore.setFixedWidth(1)
        materiali_layout.addWidget(separatore)

        # Materiali preventivo 2
        col2 = self.crea_colonna_materiali(materiali2, materiali1, 2)
        materiali_layout.addWidget(col2, 1)

        sezione_layout.addLayout(materiali_layout)
        parent_layout.addWidget(sezione_frame)

    def crea_colonna_materiali(self, materiali, materiali_altro_preventivo, numero_preventivo):
        """Crea una colonna con la lista dei materiali, evidenziando le differenze"""
        col_widget = QWidget()
        col_layout = QVBoxLayout(col_widget)
        col_layout.setContentsMargins(0, 0, 0, 0)
        col_layout.setSpacing(10)

        if not materiali or len(materiali) == 0:
            no_materiali = QLabel("Nessun materiale")
            no_materiali.setFont(QFont("Segoe UI", 11))
            no_materiali.setStyleSheet("color: #a0aec0; padding: 20px;")
            no_materiali.setAlignment(Qt.AlignCenter)
            col_layout.addWidget(no_materiali)
        else:
            for i, materiale in enumerate(materiali):
                # Verifica se questo materiale è diverso dall'altro preventivo
                is_different = self.materiale_e_diverso(materiale, materiali_altro_preventivo, i)

                materiale_frame = QFrame()

                # Applica stile evidenziato se diverso
                if is_different:
                    materiale_frame.setStyleSheet("""
                        QFrame {
                            background-color: #fef5e7;
                            border: 2px solid #f39c12;
                            border-radius: 6px;
                            padding: 10px;
                        }
                    """)
                else:
                    materiale_frame.setStyleSheet("""
                        QFrame {
                            background-color: #f7fafc;
                            border: 1px solid #e2e8f0;
                            border-radius: 6px;
                            padding: 10px;
                        }
                    """)

                materiale_layout = QVBoxLayout(materiale_frame)
                materiale_layout.setSpacing(3)

                # Titolo materiale
                titolo_mat = QLabel(f"Materiale {i+1}: {materiale.get('materiale_nome', 'N/A')}")
                titolo_mat.setFont(QFont("Segoe UI", 11, QFont.Bold))
                titolo_mat.setStyleSheet("color: #2d3748; border: none;")
                materiale_layout.addWidget(titolo_mat)

                # Dettagli
                dettagli = [
                    f"Diametro: {materiale.get('diametro', 0)} mm",
                    f"Lunghezza: {materiale.get('lunghezza', 0)} mm",
                    f"Giri: {materiale.get('giri', 0)}",
                    f"Spessore: {materiale.get('spessore', 0)} mm",
                    f"Diametro Finale: {materiale.get('diametro_finale', 0):.2f} mm",
                    f"Sviluppo: {materiale.get('sviluppo', 0):.2f}",
                    f"Lunghezza Utilizzata: {materiale.get('lunghezza_utilizzata', 0):.4f} m²",
                    f"Costo Materiale: € {materiale.get('costo_materiale', 0):.2f}/m²",
                    f"Costo Totale: € {materiale.get('costo_totale', 0):.2f}",
                    f"Maggiorazione: € {materiale.get('maggiorazione', 0):.2f}"
                ]

                for dettaglio in dettagli:
                    label = QLabel(dettaglio)
                    label.setFont(QFont("Segoe UI", 9))
                    label.setStyleSheet("color: #4a5568; border: none;")
                    materiale_layout.addWidget(label)

                col_layout.addWidget(materiale_frame)

        col_layout.addStretch()
        return col_widget

    def materiale_e_diverso(self, materiale, materiali_altro_preventivo, indice):
        """Verifica se un materiale è diverso rispetto all'altro preventivo"""
        # Se l'altro preventivo non ha materiali a questo indice, è diverso
        if not materiali_altro_preventivo or indice >= len(materiali_altro_preventivo):
            return True

        materiale_altro = materiali_altro_preventivo[indice]

        # Campi da confrontare
        campi_da_confrontare = [
            'materiale_nome', 'diametro', 'lunghezza', 'giri', 'spessore',
            'diametro_finale', 'sviluppo', 'lunghezza_utilizzata',
            'costo_materiale', 'costo_totale', 'maggiorazione'
        ]

        for campo in campi_da_confrontare:
            valore1 = materiale.get(campo)
            valore2 = materiale_altro.get(campo)

            # Confronto numerico per float/int
            if isinstance(valore1, (int, float)) and isinstance(valore2, (int, float)):
                if abs(valore1 - valore2) > 0.01:
                    return True
            # Confronto standard per altri tipi
            elif valore1 != valore2:
                return True

        return False

    def reset_confronto(self):
        """Reset per iniziare un nuovo confronto"""
        self.preventivo1_id = None
        self.preventivo1_data = None
        self.preventivo2_id = None
        self.preventivo2_data = None
        self.fase_corrente = 1
        self.mostra_fase_1()
