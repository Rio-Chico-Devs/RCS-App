"""
GestioneMaterialiWindow - Interfaccia per gestire i materiali con design system unificato

Version: 1.0.0
Last Updated: 2024-12-19
Author: Sviluppatore PyQt5

CHANGELOG:
v1.0.0 (2024-12-19):
- CREATED: Nuova finestra per gestire materiali esistenti
- ADDED: Design system unificato con MainWindow e PreventivoWindow
- ADDED: Funzionalità di modifica, aggiunta ed eliminazione materiali
- ADDED: Apertura a schermo intero con controlli finestra
- ADDED: Lista materiali con ricerca e filtro
- ADDED: Form di modifica con validazione dati
"""

from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QWidget, QLabel, QListWidget, QMessageBox, QListWidgetItem,
                             QGroupBox, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
                             QLineEdit, QDoubleSpinBox, QFormLayout, QDialog, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

class GestioneMaterialiWindow(QMainWindow):
    materiali_modificati = pyqtSignal()  # Signal per notificare modifiche
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.init_ui()
        self.carica_materiali()
    
    def init_ui(self):
        """Design system unificato - apertura a schermo intero"""
        self.setWindowTitle("Gestione Materiali - Software Aziendale RCS")
        
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
            QLineEdit, QDoubleSpinBox {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 14px;
                background-color: #ffffff;
                color: #2d3748;
                min-height: 18px;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QLineEdit:focus, QDoubleSpinBox:focus {
                border-color: #718096;
                outline: none;
            }
            QLineEdit:hover, QDoubleSpinBox:hover {
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
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(30)
        
        # Header
        self.create_header(main_layout)
        
        # Contenuto principale - layout a due colonne
        content_layout = QHBoxLayout()
        content_layout.setSpacing(40)
        
        # Colonna lista materiali
        self.create_lista_materiali_column(content_layout)
        
        # Colonna form modifica
        self.create_form_column(content_layout)
        
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
        header_container = QFrame()
        header_container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                padding: 20px 0px;
            }
        """)
        
        header_layout = QVBoxLayout(header_container)
        header_layout.setSpacing(8)
        
        # Titolo principale
        title_label = QLabel("Gestione Materiali")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: 700;
                color: #2d3748;
                padding: 0;
            }
        """)
        
        # Sottotitolo
        subtitle_label = QLabel("Modifica, aggiungi ed elimina materiali dal database")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 400;
                color: #718096;
                padding: 0;
            }
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        parent_layout.addWidget(header_container)
    
    def create_lista_materiali_column(self, parent_layout):
        """Colonna lista materiali"""
        column_widget = QWidget()
        column_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(column_widget)
        layout.setSpacing(20)
        
        # Sezione lista materiali
        lista_group = QGroupBox("Materiali Disponibili")
        lista_group.setGraphicsEffect(self.create_shadow_effect())
        
        lista_layout = QVBoxLayout(lista_group)
        lista_layout.setContentsMargins(30, 35, 30, 30)
        lista_layout.setSpacing(16)
        
        # Barra di ricerca
        self.create_search_bar(lista_layout)
        
        # Lista materiali
        self.lista_materiali = QListWidget()
        self.lista_materiali.setMinimumHeight(400)
        self.lista_materiali.itemSelectionChanged.connect(self.on_materiale_selezionato)
        lista_layout.addWidget(self.lista_materiali)
        
        # Info conteggio
        self.lbl_conteggio = QLabel("0 materiali caricati")
        self.lbl_conteggio.setStyleSheet("""
            QLabel {
                color: #718096;
                font-size: 13px;
                font-weight: 500;
            }
        """)
        lista_layout.addWidget(self.lbl_conteggio)
        
        # Pulsanti lista
        self.create_lista_buttons(lista_layout)
        
        layout.addWidget(lista_group)
        parent_layout.addWidget(column_widget)
    
    def create_search_bar(self, parent_layout):
        """Barra di ricerca materiali"""
        search_container = QFrame()
        search_container.setStyleSheet("""
            QFrame {
                background-color: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                margin: 2px 0px;
            }
        """)
        
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        search_label = QLabel("Cerca:")
        search_label.setStyleSheet("""
            QLabel {
                color: #4a5568;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Inserisci nome materiale...")
        self.search_edit.textChanged.connect(self.filtra_materiali)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        
        parent_layout.addWidget(search_container)
    
    def create_lista_buttons(self, parent_layout):
        """Pulsanti per la lista materiali"""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        # Nuovo materiale
        self.btn_nuovo_materiale = QPushButton("Nuovo Materiale")
        self.btn_nuovo_materiale.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
        """)
        self.btn_nuovo_materiale.clicked.connect(self.nuovo_materiale)
        
        # Aggiorna lista
        self.btn_aggiorna_lista = QPushButton("Aggiorna Lista")
        self.btn_aggiorna_lista.setStyleSheet("""
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
        self.btn_aggiorna_lista.clicked.connect(self.carica_materiali)
        
        buttons_layout.addWidget(self.btn_nuovo_materiale)
        buttons_layout.addWidget(self.btn_aggiorna_lista)
        buttons_layout.addStretch()
        
        parent_layout.addLayout(buttons_layout)
    
    def create_form_column(self, parent_layout):
        """Colonna form di modifica"""
        column_widget = QWidget()
        column_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(column_widget)
        layout.setSpacing(20)
        
        # Sezione form
        form_group = QGroupBox("Dettagli Materiale")
        form_group.setGraphicsEffect(self.create_shadow_effect())
        
        form_layout = QVBoxLayout(form_group)
        form_layout.setContentsMargins(30, 35, 30, 30)
        form_layout.setSpacing(20)
        
        # Info selezione
        self.create_selection_info(form_layout)
        
        # Form fields
        self.create_form_fields(form_layout)
        
        # Pulsanti form
        self.create_form_buttons(form_layout)
        
        layout.addWidget(form_group)
        layout.addStretch()
        
        parent_layout.addWidget(column_widget)
    
    def create_selection_info(self, parent_layout):
        """Informazioni selezione corrente"""
        self.info_container = QFrame()
        self.info_container.setStyleSheet("""
            QFrame {
                background-color: #f0fff4;
                border: 1px solid #68d391;
                border-radius: 8px;
                padding: 16px;
                margin: 2px 0px;
            }
        """)
        
        info_layout = QVBoxLayout(self.info_container)
        info_layout.setSpacing(4)
        
        self.lbl_selezione = QLabel("Seleziona un materiale per modificarlo")
        self.lbl_selezione.setStyleSheet("""
            QLabel {
                color: #2d3748;
                font-size: 14px;
                font-weight: 600;
            }
        """)
        
        self.lbl_info_materiale = QLabel("")
        self.lbl_info_materiale.setStyleSheet("""
            QLabel {
                color: #4a5568;
                font-size: 13px;
                font-weight: 500;
            }
        """)
        
        info_layout.addWidget(self.lbl_selezione)
        info_layout.addWidget(self.lbl_info_materiale)
        
        parent_layout.addWidget(self.info_container)
    
    def create_form_fields(self, parent_layout):
        """Campi del form"""
        form_fields = QFormLayout()
        form_fields.setVerticalSpacing(16)
        form_fields.setHorizontalSpacing(16)

        # Nome materiale
        self.edit_nome = QLineEdit()
        self.edit_nome.setPlaceholderText("es. HS300")

        # Spessore
        self.edit_spessore = QDoubleSpinBox()
        self.edit_spessore.setDecimals(2)
        self.edit_spessore.setMaximum(999.99)
        self.edit_spessore.setSuffix(" mm")
        self.edit_spessore.setMinimumHeight(36)

        # Prezzo (preventivo)
        self.edit_prezzo = QDoubleSpinBox()
        self.edit_prezzo.setDecimals(2)
        self.edit_prezzo.setMaximum(9999.99)
        self.edit_prezzo.setSuffix(" €")
        self.edit_prezzo.setMinimumHeight(36)

        # Fornitore
        self.edit_fornitore = QLineEdit()
        self.edit_fornitore.setPlaceholderText("es. Toray, Hexcel...")

        # Prezzo Fornitore
        self.edit_prezzo_fornitore = QDoubleSpinBox()
        self.edit_prezzo_fornitore.setDecimals(2)
        self.edit_prezzo_fornitore.setMaximum(9999.99)
        self.edit_prezzo_fornitore.setSuffix(" €/m²")
        self.edit_prezzo_fornitore.setMinimumHeight(36)

        # Capacità Magazzino (m²)
        self.edit_capacita_magazzino = QDoubleSpinBox()
        self.edit_capacita_magazzino.setDecimals(2)
        self.edit_capacita_magazzino.setMaximum(99999.99)
        self.edit_capacita_magazzino.setSuffix(" m²")
        self.edit_capacita_magazzino.setMinimumHeight(36)

        # Giacenza (m²)
        self.edit_giacenza = QDoubleSpinBox()
        self.edit_giacenza.setDecimals(2)
        self.edit_giacenza.setMaximum(99999.99)
        self.edit_giacenza.setSuffix(" m²")
        self.edit_giacenza.setMinimumHeight(36)

        # Aggiunta campi
        form_fields.addRow(self.create_standard_label("Nome Materiale:"), self.edit_nome)
        form_fields.addRow(self.create_standard_label("Spessore:"), self.edit_spessore)
        form_fields.addRow(self.create_standard_label("Prezzo (Preventivo):"), self.edit_prezzo)
        form_fields.addRow(self.create_standard_label("Fornitore:"), self.edit_fornitore)
        form_fields.addRow(self.create_standard_label("Prezzo Fornitore:"), self.edit_prezzo_fornitore)
        form_fields.addRow(self.create_standard_label("Capacità Magazzino:"), self.edit_capacita_magazzino)
        form_fields.addRow(self.create_standard_label("Giacenza:"), self.edit_giacenza)

        parent_layout.addLayout(form_fields)

        # Inizialmente disabilita i campi
        self.abilita_form(False)
    
    def create_form_buttons(self, parent_layout):
        """Pulsanti del form"""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        # Salva modifiche
        self.btn_salva = QPushButton("Salva Modifiche")
        self.btn_salva.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
            QPushButton:disabled {
                background-color: #a0aec0;
                color: #ffffff;
            }
        """)
        self.btn_salva.clicked.connect(self.salva_materiale)
        
        # Elimina materiale
        self.btn_elimina = QPushButton("Elimina Materiale")
        self.btn_elimina.setStyleSheet("""
            QPushButton {
                background-color: #e53e3e;
                color: #ffffff;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #c53030;
            }
            QPushButton:disabled {
                background-color: #a0aec0;
                color: #ffffff;
            }
        """)
        self.btn_elimina.clicked.connect(self.elimina_materiale)
        
        # Reset form
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setStyleSheet("""
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
        self.btn_reset.clicked.connect(self.reset_form)
        
        buttons_layout.addWidget(self.btn_salva)
        buttons_layout.addWidget(self.btn_elimina)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_reset)
        
        parent_layout.addLayout(buttons_layout)
        
        # Inizialmente disabilita i pulsanti
        self.abilita_pulsanti_form(False)
    
    def create_footer(self, parent_layout):
        """Footer con pulsante chiudi"""
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        # Chiudi finestra
        btn_chiudi = QPushButton("Chiudi Gestione Materiali")
        btn_chiudi.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                min-height: 40px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
        """)
        btn_chiudi.clicked.connect(self.close)
        
        footer_layout.addWidget(btn_chiudi)
        parent_layout.addLayout(footer_layout)
    
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
    
    # Metodi funzionali
    def carica_materiali(self):
        """Carica tutti i materiali dal database"""
        self.lista_materiali.clear()
        self.materiali_data = self.db_manager.get_all_materiali()
        
        for materiale in self.materiali_data:
            id_mat, nome, spessore, prezzo = materiale[:4]
            fornitore = materiale[4] if len(materiale) > 4 else ""
            testo = f"{nome} • {spessore}mm • €{prezzo:.2f}"
            if fornitore:
                testo += f" • {fornitore}"
            
            item = QListWidgetItem(testo)
            item.setData(Qt.UserRole, materiale)  # Salva tutti i dati del materiale
            self.lista_materiali.addItem(item)
        
        self.aggiorna_conteggio()
        self.filtra_materiali()  # Applica eventuale filtro esistente
    
    def aggiorna_conteggio(self):
        """Aggiorna il conteggio dei materiali"""
        count = self.lista_materiali.count()
        self.lbl_conteggio.setText(f"{count} materiali caricati")
    
    def filtra_materiali(self):
        """Filtra i materiali in base alla ricerca"""
        search_text = self.search_edit.text().lower()
        
        for i in range(self.lista_materiali.count()):
            item = self.lista_materiali.item(i)
            materiale_data = item.data(Qt.UserRole)
            nome = materiale_data[1].lower()  # Nome materiale
            
            # Mostra/nascondi in base alla ricerca
            item.setHidden(search_text not in nome)
    
    def on_materiale_selezionato(self):
        """Gestisce la selezione di un materiale"""
        current_item = self.lista_materiali.currentItem()
        if not current_item:
            self.abilita_form(False)
            self.abilita_pulsanti_form(False)
            self.lbl_selezione.setText("Seleziona un materiale per modificarlo")
            self.lbl_info_materiale.setText("")
            return
        
        # Ottieni i dati del materiale selezionato
        materiale_data = current_item.data(Qt.UserRole)
        self.materiale_corrente = materiale_data
        id_mat, nome, spessore, prezzo = materiale_data[:4]
        fornitore = materiale_data[4] if len(materiale_data) > 4 else ""
        prezzo_fornitore = materiale_data[5] if len(materiale_data) > 5 else 0.0
        capacita_magazzino = materiale_data[6] if len(materiale_data) > 6 else 0.0
        giacenza = materiale_data[7] if len(materiale_data) > 7 else 0.0

        # Aggiorna le informazioni
        self.lbl_selezione.setText(f"Materiale selezionato: {nome}")
        self.lbl_info_materiale.setText(f"ID: {id_mat} • Creato nel database")

        # Popola il form
        self.edit_nome.setText(nome)
        self.edit_spessore.setValue(spessore)
        self.edit_prezzo.setValue(prezzo)
        self.edit_fornitore.setText(fornitore)
        self.edit_prezzo_fornitore.setValue(prezzo_fornitore)
        self.edit_capacita_magazzino.setValue(capacita_magazzino)
        self.edit_giacenza.setValue(giacenza)
        
        # Abilita form e pulsanti
        self.abilita_form(True)
        self.abilita_pulsanti_form(True)
    
    def abilita_form(self, enabled):
        """Abilita/disabilita i campi del form"""
        self.edit_nome.setEnabled(enabled)
        self.edit_spessore.setEnabled(enabled)
        self.edit_prezzo.setEnabled(enabled)
        self.edit_fornitore.setEnabled(enabled)
        self.edit_prezzo_fornitore.setEnabled(enabled)
        self.edit_capacita_magazzino.setEnabled(enabled)
        self.edit_giacenza.setEnabled(enabled)
    
    def abilita_pulsanti_form(self, enabled):
        """Abilita/disabilita i pulsanti del form"""
        self.btn_salva.setEnabled(enabled)
        self.btn_elimina.setEnabled(enabled)
    
    def reset_form(self):
        """Reset del form ai valori originali"""
        if hasattr(self, 'materiale_corrente'):
            self.on_materiale_selezionato()
        else:
            self.edit_nome.clear()
            self.edit_spessore.setValue(0.0)
            self.edit_prezzo.setValue(0.0)
            self.edit_fornitore.clear()
            self.edit_prezzo_fornitore.setValue(0.0)
            self.edit_capacita_magazzino.setValue(0.0)
            self.edit_giacenza.setValue(0.0)
    
    def nuovo_materiale(self):
        """Apre dialog per creare un nuovo materiale"""
        dialog = NuovoMaterialeDialog(self.db_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            self.carica_materiali()
            QMessageBox.information(self, "Successo", "Nuovo materiale aggiunto con successo!")
    
    def salva_materiale(self):
        """Salva le modifiche al materiale corrente"""
        if not hasattr(self, 'materiale_corrente'):
            return
        
        # Validazione dati
        nome = self.edit_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Errore", "Il nome del materiale è obbligatorio.")
            return
        
        spessore = self.edit_spessore.value()
        if spessore <= 0:
            QMessageBox.warning(self, "Errore", "Lo spessore deve essere maggiore di 0.")
            return
        
        prezzo = self.edit_prezzo.value()
        if prezzo <= 0:
            QMessageBox.warning(self, "Errore", "Il prezzo deve essere maggiore di 0.")
            return
        
        # Conferma modifiche
        id_materiale = self.materiale_corrente[0]
        risposta = QMessageBox.question(
            self, "Conferma Modifiche",
            f"Salvare le modifiche al materiale '{nome}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if risposta == QMessageBox.Yes:
            try:
                fornitore = self.edit_fornitore.text().strip()
                prezzo_fornitore = self.edit_prezzo_fornitore.value()
                capacita_magazzino = self.edit_capacita_magazzino.value()
                giacenza = self.edit_giacenza.value()
                success = self.db_manager.update_materiale(
                    id_materiale, nome, spessore, prezzo,
                    fornitore, prezzo_fornitore, capacita_magazzino, giacenza
                )
                if success:
                    QMessageBox.information(self, "Successo", "Materiale aggiornato con successo!")
                    self.carica_materiali()
                    self.materiali_modificati.emit()  # Notifica le modifiche
                else:
                    QMessageBox.critical(self, "Errore", "Nome materiale già esistente o errore nel database.")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio:\n{str(e)}")
    
    def elimina_materiale(self):
        """Elimina il materiale corrente"""
        if not hasattr(self, 'materiale_corrente'):
            return
        
        nome_materiale = self.materiale_corrente[1]
        
        # Conferma eliminazione
        risposta = QMessageBox.question(
            self, "Conferma Eliminazione",
            f"Eliminare definitivamente il materiale '{nome_materiale}'?\n\nQuesta azione non può essere annullata.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if risposta == QMessageBox.Yes:
            try:
                id_materiale = self.materiale_corrente[0]
                success = self.db_manager.delete_materiale(id_materiale)
                if success:
                    QMessageBox.information(self, "Successo", f"Materiale '{nome_materiale}' eliminato con successo!")
                    self.carica_materiali()
                    self.reset_form()
                    self.abilita_form(False)
                    self.abilita_pulsanti_form(False)
                    self.materiali_modificati.emit()  # Notifica le modifiche
                else:
                    QMessageBox.critical(self, "Errore", "Errore durante l'eliminazione del materiale.")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore durante l'eliminazione:\n{str(e)}")


class NuovoMaterialeDialog(QDialog):
    """Dialog per aggiungere un nuovo materiale"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.init_ui()
    
    def init_ui(self):
        """Inizializza l'interfaccia del dialog"""
        self.setWindowTitle("Nuovo Materiale")
        self.setFixedSize(450, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #fafbfc;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QLabel {
                color: #2d3748;
                font-size: 14px;
                font-weight: 500;
            }
            QLineEdit, QDoubleSpinBox {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 14px;
                background-color: #ffffff;
                color: #2d3748;
                min-height: 18px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus {
                border-color: #718096;
                outline: none;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                padding: 12px 24px;
                min-height: 36px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(20)

        # Titolo
        title_label = QLabel("Aggiungi Nuovo Materiale")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 700;
                color: #2d3748;
                padding-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)

        # Form
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(16)

        self.edit_nome = QLineEdit()
        self.edit_nome.setPlaceholderText("es. HS400")

        self.edit_spessore = QDoubleSpinBox()
        self.edit_spessore.setDecimals(2)
        self.edit_spessore.setMaximum(999.99)
        self.edit_spessore.setSuffix(" mm")

        self.edit_prezzo = QDoubleSpinBox()
        self.edit_prezzo.setDecimals(2)
        self.edit_prezzo.setMaximum(9999.99)
        self.edit_prezzo.setSuffix(" €")

        self.edit_fornitore = QLineEdit()
        self.edit_fornitore.setPlaceholderText("es. Toray, Hexcel...")

        self.edit_prezzo_fornitore = QDoubleSpinBox()
        self.edit_prezzo_fornitore.setDecimals(2)
        self.edit_prezzo_fornitore.setMaximum(9999.99)
        self.edit_prezzo_fornitore.setSuffix(" €/m²")

        self.edit_capacita_magazzino = QDoubleSpinBox()
        self.edit_capacita_magazzino.setDecimals(2)
        self.edit_capacita_magazzino.setMaximum(99999.99)
        self.edit_capacita_magazzino.setSuffix(" m²")

        self.edit_giacenza = QDoubleSpinBox()
        self.edit_giacenza.setDecimals(2)
        self.edit_giacenza.setMaximum(99999.99)
        self.edit_giacenza.setSuffix(" m²")

        form_layout.addRow("Nome Materiale:", self.edit_nome)
        form_layout.addRow("Spessore:", self.edit_spessore)
        form_layout.addRow("Prezzo (Preventivo):", self.edit_prezzo)
        form_layout.addRow("Fornitore:", self.edit_fornitore)
        form_layout.addRow("Prezzo Fornitore:", self.edit_prezzo_fornitore)
        form_layout.addRow("Capacità Magazzino:", self.edit_capacita_magazzino)
        form_layout.addRow("Giacenza Iniziale:", self.edit_giacenza)

        layout.addLayout(form_layout)
        
        # Pulsanti
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        btn_annulla = QPushButton("Annulla")
        btn_annulla.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
            }
            QPushButton:hover {
                background-color: #edf2f7;
            }
        """)
        btn_annulla.clicked.connect(self.reject)
        
        btn_salva = QPushButton("Salva Materiale")
        btn_salva.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
        """)
        btn_salva.clicked.connect(self.salva_nuovo_materiale)
        
        buttons_layout.addWidget(btn_annulla)
        buttons_layout.addWidget(btn_salva)
        
        layout.addLayout(buttons_layout)
    
    def salva_nuovo_materiale(self):
        """Salva il nuovo materiale"""
        # Validazione
        nome = self.edit_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Errore", "Il nome del materiale è obbligatorio.")
            return
        
        spessore = self.edit_spessore.value()
        if spessore <= 0:
            QMessageBox.warning(self, "Errore", "Lo spessore deve essere maggiore di 0.")
            return
        
        prezzo = self.edit_prezzo.value()
        if prezzo <= 0:
            QMessageBox.warning(self, "Errore", "Il prezzo deve essere maggiore di 0.")
            return
        
        # Salva nel database
        try:
            fornitore = self.edit_fornitore.text().strip()
            prezzo_fornitore = self.edit_prezzo_fornitore.value()
            capacita_magazzino = self.edit_capacita_magazzino.value()
            giacenza = self.edit_giacenza.value()
            materiale_id = self.db_manager.add_materiale(
                nome, spessore, prezzo,
                fornitore, prezzo_fornitore, capacita_magazzino, giacenza
            )
            if materiale_id:
                self.accept()
            else:
                QMessageBox.critical(self, "Errore", "Nome materiale già esistente.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio:\n{str(e)}")