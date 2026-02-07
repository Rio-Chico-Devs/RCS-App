"""
VisualizzaPreventiviWindow - Interfaccia per visualizzare e gestire i preventivi con design system unificato

Version: 1.0.0
Last Updated: 2026-02-06
Author: Sviluppatore PyQt5

CHANGELOG:
v1.0.0 (2026-02-06):
- CREATED: Nuova finestra dedicata per visualizzare preventivi
- ADDED: Design system unificato con MainWindow e altre finestre
- ADDED: Filtri avanzati (origine, cliente, keyword)
- ADDED: Apertura a schermo intero con controlli finestra
- ADDED: Azioni preventivi (visualizza, modifica, elimina, revisione, confronta, genera documento)
"""

from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
                             QWidget, QLabel, QListWidget, QMessageBox, QListWidgetItem,
                             QGroupBox, QFrame, QGraphicsDropShadowEffect,
                             QLineEdit, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from typing import Optional, Any

class VisualizzaPreventiviWindow(QMainWindow):
    preventivo_modificato = pyqtSignal()  # Signal per notificare modifiche

    def __init__(self, db_manager: Any, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.db_manager = db_manager
        self.parent_window = parent
        self.modalita_visualizzazione = 'preventivi'  # 'preventivi' o 'revisioni'
        self.init_ui()
        self.load_clienti_filtro()
        self.load_preventivi()

    def init_ui(self) -> None:
        """Design system unificato - apertura a schermo intero"""
        self.setWindowTitle("Visualizza Preventivi - Software Aziendale RCS")

        # Apertura massimizzata mantenendo i controlli della finestra
        self.showMaximized()

        # Stile unificato con design system coerente
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
            QLineEdit, QComboBox {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 14px;
                background-color: #ffffff;
                color: #2d3748;
                min-height: 18px;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #718096;
                outline: none;
            }
            QLineEdit:hover, QComboBox:hover {
                border-color: #a0aec0;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #4a5568;
                width: 0;
                height: 0;
                margin-right: 10px;
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

        # Layout principale - margini ridotti per mostrare tutto
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(12)

        # Header
        self.create_header(main_layout)

        # Toggle visualizzazione preventivi/revisioni
        self.create_view_toggle(main_layout)

        # Filtri
        self.create_filters_section(main_layout)

        # Lista preventivi
        self.create_lista_preventivi(main_layout)

        # Pulsanti azioni
        self.create_action_buttons(main_layout)

        # Footer
        self.create_footer(main_layout)

    def create_shadow_effect(self, blur: int = 10, opacity: int = 12) -> QGraphicsDropShadowEffect:
        """Effetto ombra standardizzato"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setColor(QColor(0, 0, 0, opacity))
        shadow.setOffset(0, 2)
        return shadow

    def create_header(self, parent_layout: QVBoxLayout) -> None:
        """Header unificato - compatto"""
        header_container = QFrame()
        header_container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                padding: 5px 0px;
            }
        """)

        header_layout = QVBoxLayout(header_container)
        header_layout.setSpacing(4)

        # Titolo principale
        title_label = QLabel("Visualizza Preventivi")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 700;
                color: #2d3748;
                padding: 0;
            }
        """)

        # Sottotitolo
        subtitle_label = QLabel("Esplora, filtra e gestisci tutti i preventivi salvati")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 400;
                color: #718096;
                padding: 0;
            }
        """)

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)

        parent_layout.addWidget(header_container)

    def create_view_toggle(self, parent_layout: QVBoxLayout) -> None:
        """Toggle per cambiare tra preventivi e revisioni - compatto"""
        toggle_container = QFrame()
        toggle_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        toggle_container.setGraphicsEffect(self.create_shadow_effect())

        toggle_layout = QHBoxLayout(toggle_container)
        toggle_layout.setSpacing(10)

        # Label
        label = QLabel("Visualizza:")
        label.setStyleSheet("""
            QLabel {
                color: #4a5568;
                font-size: 14px;
                font-weight: 600;
            }
        """)

        # Pulsante Preventivi
        self.btn_mostra_preventivi = QPushButton("Preventivi")
        self.btn_mostra_preventivi.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                min-height: 28px;
                min-width: 100px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
        """)
        self.btn_mostra_preventivi.clicked.connect(lambda: self.cambia_visualizzazione('preventivi'))

        # Pulsante Revisioni
        self.btn_mostra_revisioni = QPushButton("Revisioni")
        self.btn_mostra_revisioni.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: 28px;
                min-width: 100px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
        """)
        self.btn_mostra_revisioni.clicked.connect(lambda: self.cambia_visualizzazione('revisioni'))

        toggle_layout.addWidget(label)
        toggle_layout.addWidget(self.btn_mostra_preventivi)
        toggle_layout.addWidget(self.btn_mostra_revisioni)
        toggle_layout.addStretch()

        parent_layout.addWidget(toggle_container)

    def create_filters_section(self, parent_layout: QVBoxLayout) -> None:
        """Sezione filtri per preventivi - inline compatto"""
        filters_container = QFrame()
        filters_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 12px;
            }
        """)
        filters_container.setGraphicsEffect(self.create_shadow_effect())

        # Layout orizzontale per tutti i filtri inline
        filters_layout = QHBoxLayout(filters_container)
        filters_layout.setSpacing(15)

        # Filtro Tipo Preventivo (solo per modalità revisioni)
        self.label_tipo = QLabel("Tipo Preventivo:")
        self.label_tipo.setStyleSheet("QLabel { font-weight: 500; color: #4a5568; }")
        self.filtro_origine = QComboBox()
        self.filtro_origine.addItems(["Tutti", "Originali", "Revisionati", "Modificati"])
        self.filtro_origine.currentIndexChanged.connect(self.load_preventivi)
        self.filtro_origine.setMinimumWidth(140)

        # Nascosto di default (si mostra solo in modalità revisioni)
        self.label_tipo.setVisible(False)
        self.filtro_origine.setVisible(False)

        filters_layout.addWidget(self.label_tipo)
        filters_layout.addWidget(self.filtro_origine)

        # Filtro Cliente
        cliente_label = QLabel("Cliente:")
        cliente_label.setStyleSheet("QLabel { font-weight: 500; color: #4a5568; }")
        self.filtro_cliente = QComboBox()
        self.filtro_cliente.addItem("Tutti i clienti", None)
        self.filtro_cliente.currentIndexChanged.connect(self.load_preventivi)
        self.filtro_cliente.setMinimumWidth(180)

        filters_layout.addWidget(cliente_label)
        filters_layout.addWidget(self.filtro_cliente)

        # Filtro Keyword
        keyword_label = QLabel("Cerca:")
        keyword_label.setStyleSheet("QLabel { font-weight: 500; color: #4a5568; }")
        self.filtro_keyword = QLineEdit()
        self.filtro_keyword.setPlaceholderText("ID, cliente, descrizione, codice, prezzo...")
        self.filtro_keyword.textChanged.connect(self.load_preventivi)

        filters_layout.addWidget(keyword_label)
        filters_layout.addWidget(self.filtro_keyword, 1)  # Stretch per occupare spazio rimanente

        parent_layout.addWidget(filters_container)

    def create_lista_preventivi(self, parent_layout: QVBoxLayout) -> None:
        """Lista preventivi con conteggio - compatta"""
        lista_group = QGroupBox("Preventivi")
        lista_group.setGraphicsEffect(self.create_shadow_effect())

        lista_layout = QVBoxLayout(lista_group)
        lista_layout.setContentsMargins(15, 20, 15, 15)
        lista_layout.setSpacing(8)

        # Lista - altezza ridotta per mostrare i pulsanti
        self.lista_preventivi = QListWidget()
        self.lista_preventivi.setMinimumHeight(180)
        self.lista_preventivi.setMaximumHeight(250)
        self.lista_preventivi.itemDoubleClicked.connect(self.visualizza_preventivo)
        lista_layout.addWidget(self.lista_preventivi)

        # Conteggio
        self.lbl_conteggio = QLabel("0 preventivi caricati")
        self.lbl_conteggio.setStyleSheet("""
            QLabel {
                color: #718096;
                font-size: 13px;
                font-weight: 500;
            }
        """)
        lista_layout.addWidget(self.lbl_conteggio)

        parent_layout.addWidget(lista_group)

    def create_action_buttons(self, parent_layout: QVBoxLayout) -> None:
        """Pulsanti azioni preventivi - compatti"""
        buttons_container = QFrame()
        buttons_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        buttons_container.setGraphicsEffect(self.create_shadow_effect())

        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setSpacing(8)

        # Prima riga
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        # Visualizza
        self.btn_visualizza = QPushButton("Visualizza Dettagli")
        self.btn_visualizza.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                min-height: 32px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
        """)
        self.btn_visualizza.clicked.connect(self.visualizza_preventivo)

        # Modifica
        self.btn_modifica = QPushButton("Modifica")
        self.btn_modifica.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                min-height: 32px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
        """)
        self.btn_modifica.clicked.connect(self.modifica_preventivo)

        # Crea Revisione
        self.btn_revisione = QPushButton("Crea Revisione")
        self.btn_revisione.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                min-height: 32px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
        """)
        self.btn_revisione.clicked.connect(self.crea_revisione)

        row1.addWidget(self.btn_visualizza)
        row1.addWidget(self.btn_modifica)
        row1.addWidget(self.btn_revisione)

        # Seconda riga
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        # Confronta
        self.btn_confronta = QPushButton("Confronta Preventivi")
        self.btn_confronta.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: 32px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
        """)
        self.btn_confronta.clicked.connect(self.confronta_preventivi)

        # Genera Documento
        self.btn_genera = QPushButton("Genera Documento")
        self.btn_genera.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: 32px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
        """)
        self.btn_genera.clicked.connect(self.genera_documento)

        # Elimina
        self.btn_elimina = QPushButton("Elimina")
        self.btn_elimina.setStyleSheet("""
            QPushButton {
                background-color: #e53e3e;
                color: #ffffff;
                min-height: 32px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #c53030;
            }
        """)
        self.btn_elimina.clicked.connect(self.elimina_preventivo)

        row2.addWidget(self.btn_confronta)
        row2.addWidget(self.btn_genera)
        row2.addWidget(self.btn_elimina)

        buttons_layout.addLayout(row1)
        buttons_layout.addLayout(row2)

        parent_layout.addWidget(buttons_container)

    def create_footer(self, parent_layout: QVBoxLayout) -> None:
        """Footer con pulsante chiudi - compatto"""
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        # Chiudi finestra
        btn_chiudi = QPushButton("Chiudi")
        btn_chiudi.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: 32px;
                min-width: 120px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
        """)
        btn_chiudi.clicked.connect(lambda: self.close())

        footer_layout.addWidget(btn_chiudi)
        parent_layout.addLayout(footer_layout)

    # =============================================================================
    # METODI FUNZIONALI
    # =============================================================================

    def load_clienti_filtro(self) -> None:
        """Carica la lista dei clienti nel filtro"""
        self.filtro_cliente.clear()
        self.filtro_cliente.addItem("Tutti i clienti", None)

        try:
            preventivi = self.db_manager.get_all_preventivi()
            clienti = set()
            for prev in preventivi:
                if len(prev) >= 5:
                    nome_cliente = prev[4].strip() if prev[4] else ''
                    if nome_cliente:
                        clienti.add(nome_cliente)

            for cliente in sorted(clienti):
                self.filtro_cliente.addItem(cliente, cliente)
        except Exception as e:
            print(f"Errore nel caricamento clienti filtro: {str(e)}")

    def load_preventivi(self) -> None:
        """Carica preventivi in base alla modalità e ai filtri attivi"""
        self.lista_preventivi.clear()

        # Ottieni i valori dei filtri
        filtro_origine_text = self.filtro_origine.currentText()
        filtro_cliente_data = self.filtro_cliente.currentData()
        filtro_keyword_text = self.filtro_keyword.text().lower().strip()

        if self.modalita_visualizzazione == 'preventivi':
            # Mostra solo preventivi (ultima revisione di ogni gruppo)
            preventivi = self.db_manager.get_all_preventivi_latest()
        else:
            # Mostra solo le revisioni (numero_revisione > 1)
            preventivi = self.db_manager.get_all_preventivi()
            preventivi_filtrati = []
            for prev in preventivi:
                if len(prev) >= 9:
                    numero_revisione = prev[8] if len(prev) > 8 else 1
                    if numero_revisione > 1:
                        preventivi_filtrati.append(prev)
            preventivi = preventivi_filtrati

        count = 0
        for preventivo in preventivi:
            # Formato: id, data_creazione, preventivo_finale, prezzo_cliente,
            # nome_cliente, numero_ordine, descrizione, codice, numero_revisione
            if len(preventivo) >= 9:
                id_prev, data_creazione, preventivo_finale, prezzo_cliente, nome_cliente, numero_ordine, descrizione, codice, numero_revisione = preventivo[:9]
            else:
                id_prev, data_creazione, preventivo_finale, prezzo_cliente = preventivo[:4]
                nome_cliente, numero_ordine, descrizione, codice, numero_revisione = "", "", "", "", 1

            # APPLICA FILTRO ORIGINE
            if filtro_origine_text == "Originali" and numero_revisione != 1:
                continue
            elif filtro_origine_text == "Revisionati" and numero_revisione == 1:
                continue
            elif filtro_origine_text == "Modificati" and numero_revisione == 1:
                continue

            # APPLICA FILTRO CLIENTE
            if filtro_cliente_data and nome_cliente.strip() != filtro_cliente_data:
                continue

            # APPLICA FILTRO KEYWORD
            if filtro_keyword_text:
                campi_ricerca = [
                    str(id_prev), str(data_creazione), str(preventivo_finale),
                    str(prezzo_cliente), str(nome_cliente), str(numero_ordine),
                    str(descrizione), str(codice), str(numero_revisione)
                ]
                testo_completo = " ".join(campi_ricerca).lower()
                if filtro_keyword_text not in testo_completo:
                    continue

            # Formatta la data
            data_formattata = data_creazione.split('T')[0] if 'T' in data_creazione else data_creazione

            # Formatta il testo
            if self.modalita_visualizzazione == 'revisioni':
                prefisso_tipo = "Revisione"
            else:
                if numero_revisione == 1:
                    prefisso_tipo = "Originale"
                else:
                    prefisso_tipo = "Revisionato"

            cliente_info = nome_cliente if nome_cliente else "Cliente non specificato"
            ordine_info = f" | {numero_ordine}" if numero_ordine else ""

            testo = f"#{id_prev:03d} [{prefisso_tipo}] - {data_formattata} - {cliente_info}{ordine_info}"
            testo += f"\nPreventivo: EUR {preventivo_finale:,.2f} | Cliente: EUR {prezzo_cliente:,.2f}"
            if descrizione:
                testo += f"\nDescrizione: {descrizione[:60]}{'...' if len(descrizione) > 60 else ''}"

            item = QListWidgetItem(testo)
            item.setData(Qt.UserRole, id_prev)
            self.lista_preventivi.addItem(item)
            count += 1

        # Aggiorna conteggio
        self.lbl_conteggio.setText(f"{count} preventivi visualizzati")

    def cambia_visualizzazione(self, modalita: str) -> None:
        """Cambia tra visualizzazione Preventivi e Revisioni"""
        self.modalita_visualizzazione = modalita

        # Mostra/nascondi filtro Tipo Preventivo in base alla modalità
        if modalita == 'preventivi':
            # Nascondi filtro tipo (non ha senso per preventivi che mostrano solo ultime versioni)
            self.label_tipo.setVisible(False)
            self.filtro_origine.setVisible(False)
        else:
            # Mostra filtro tipo per revisioni
            self.label_tipo.setVisible(True)
            self.filtro_origine.setVisible(True)

        # Aggiorna stili pulsanti
        if modalita == 'preventivi':
            self.btn_mostra_preventivi.setStyleSheet("""
                QPushButton {
                    background-color: #4a5568;
                    color: #ffffff;
                    min-height: 28px;
                    min-width: 100px;
                    padding: 6px 16px;
                }
                QPushButton:hover {
                    background-color: #2d3748;
                }
            """)
            self.btn_mostra_revisioni.setStyleSheet("""
                QPushButton {
                    background-color: #f7fafc;
                    color: #4a5568;
                    border: 1px solid #e2e8f0;
                    min-height: 28px;
                    min-width: 100px;
                    padding: 6px 16px;
                }
                QPushButton:hover {
                    background-color: #edf2f7;
                }
            """)
        else:
            self.btn_mostra_revisioni.setStyleSheet("""
                QPushButton {
                    background-color: #4a5568;
                    color: #ffffff;
                    min-height: 28px;
                    min-width: 100px;
                    padding: 6px 16px;
                }
                QPushButton:hover {
                    background-color: #2d3748;
                }
            """)
            self.btn_mostra_preventivi.setStyleSheet("""
                QPushButton {
                    background-color: #f7fafc;
                    color: #4a5568;
                    border: 1px solid #e2e8f0;
                    min-height: 28px;
                    min-width: 100px;
                    padding: 6px 16px;
                }
                QPushButton:hover {
                    background-color: #edf2f7;
                }
            """)

        # Ricarica lista
        self.load_preventivi()

    def visualizza_preventivo(self) -> None:
        """Visualizza i dettagli del preventivo selezionato"""
        current_item = self.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo da visualizzare.")
            return

        preventivo_id = current_item.data(Qt.UserRole)

        # Importa qui per evitare circular import
        from ui.preventivo_window import PreventivoWindow

        preventivo_window = PreventivoWindow(
            self.db_manager,
            self,
            preventivo_id=preventivo_id,
            modalita='visualizza'
        )
        preventivo_window.preventivo_salvato.connect(self.on_preventivo_modificato)
        preventivo_window.show()

    def modifica_preventivo(self) -> None:
        """Apre un preventivo per la modifica DIRETTA"""
        current_item = self.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo da modificare.")
            return

        preventivo_id = current_item.data(Qt.UserRole)

        from ui.preventivo_window import PreventivoWindow

        preventivo_window = PreventivoWindow(
            self.db_manager,
            self,
            preventivo_id=preventivo_id,
            modalita='modifica'
        )
        preventivo_window.preventivo_salvato.connect(self.on_preventivo_modificato)
        preventivo_window.show()

    def crea_revisione(self) -> None:
        """Crea una revisione di un preventivo esistente"""
        current_item = self.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo per creare una revisione.")
            return

        preventivo_id = current_item.data(Qt.UserRole)

        # Dialog per note revisione
        from ui.main_window_business_logic import MainWindowBusinessLogic
        note_revisione = MainWindowBusinessLogic.richiedi_note_revisione(self)
        if note_revisione is None:
            return

        from ui.preventivo_window import PreventivoWindow

        preventivo_window = PreventivoWindow(
            self.db_manager,
            self,
            preventivo_id=preventivo_id,
            modalita='revisione',
            note_revisione=note_revisione
        )
        preventivo_window.preventivo_salvato.connect(self.on_preventivo_modificato)
        preventivo_window.show()

    def confronta_preventivi(self) -> None:
        """Apre la finestra confronto preventivi"""
        from ui.confronto_preventivi_window import ConfrontoPreventiviWindow

        confronto_window = ConfrontoPreventiviWindow(self.db_manager, self)
        confronto_window.show()

    def genera_documento(self) -> None:
        """Genera documento dal preventivo selezionato"""
        current_item = self.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo dalla lista per generare il documento.")
            return

        # Usa la stessa logica di MainWindowBusinessLogic
        from ui.main_window_business_logic import MainWindowBusinessLogic

        # Crea un oggetto temporaneo con gli attributi necessari
        class TempWindow:
            def __init__(self, db_manager, lista_preventivi):
                self.db_manager = db_manager
                self.lista_preventivi = lista_preventivi

        temp_window = TempWindow(self.db_manager, self.lista_preventivi)
        MainWindowBusinessLogic.genera_documento_preventivo(temp_window)

    def elimina_preventivo(self) -> None:
        """Elimina il preventivo selezionato"""
        current_item = self.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un preventivo da eliminare.")
            return

        # Dialog di conferma
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Conferma Eliminazione")
        dialog.setText("Sei sicuro di voler eliminare questo preventivo?\n\nQuesta azione eliminerà anche tutte le sue revisioni e non può essere annullata.")
        dialog.setIcon(QMessageBox.Question)
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)

        risposta = dialog.exec_()

        if risposta == QMessageBox.Yes:
            preventivo_id = current_item.data(Qt.UserRole)

            if self.db_manager.delete_preventivo_e_revisioni(preventivo_id):
                QMessageBox.information(self, "Successo",
                                      "Preventivo e tutte le sue revisioni sono stati eliminati con successo.")
                self.load_preventivi()
                self.preventivo_modificato.emit()
            else:
                QMessageBox.error(self, "Errore",
                                "Errore durante l'eliminazione del preventivo.")

    def on_preventivo_modificato(self) -> None:
        """Callback quando un preventivo viene modificato"""
        self.load_preventivi()
        self.load_clienti_filtro()  # Ricarica anche i clienti nel caso ne sia stato aggiunto uno nuovo
        self.preventivo_modificato.emit()
