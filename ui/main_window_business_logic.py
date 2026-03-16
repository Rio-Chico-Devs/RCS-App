#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Main Window Business Logic - Logica di business per MainWindow
Uso riservato esclusivamente a RCS

Version: 1.1.0
Last Updated: 25/09/2025
Author: Sviluppatore PyQt5 + Claude

CHANGELOG:
v1.1.0 (25/09/2025):
- Rimosso riferimento a genera_documento_rtf obsoleto
- Aggiunto supporto per genera_documento_pdf
- Corretta gestione file generati senza apri_file_esterno
"""

# type: ignore
# pyright: reportUnknownParameterType=false, reportMissingParameterType=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportAttributeAccessIssue=false
# pyright: reportUnusedVariable=false

from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QLabel, QListWidgetItem
from PyQt5.QtCore import Qt
from ui.preventivo_window import PreventivoWindow
from ui.gestione_materiali_window import GestioneMaterialiWindow
from ui.magazzino_window import MagazzinoWindow
from ui.document_utils import DocumentUtils

class MainWindowBusinessLogic:

    @staticmethod
    def load_clienti_filtro(window_instance):
        """Carica la lista dei clienti nel filtro"""
        window_instance.filtro_cliente.clear()
        window_instance.filtro_cliente.addItem("Tutti i clienti", None)

        try:
            preventivi = window_instance.db_manager.get_all_preventivi()
            clienti = set()
            for prev in preventivi:
                if len(prev) >= 5:
                    nome_cliente = prev[4].strip() if prev[4] else ''
                    if nome_cliente:
                        clienti.add(nome_cliente)

            for cliente in sorted(clienti):
                window_instance.filtro_cliente.addItem(cliente, cliente)
        except Exception as e:
            print(f"Errore nel caricamento clienti filtro: {str(e)}")

    @staticmethod
    def load_preventivi(window_instance):
        """Carica preventivi o revisioni in base alla modalità di visualizzazione E ai filtri attivi"""
        window_instance.lista_preventivi.clear()

        # Ottieni i valori dei filtri
        filtro_origine_text = window_instance.filtro_origine.currentText()
        filtro_cliente_data = window_instance.filtro_cliente.currentData()
        filtro_keyword_text = window_instance.filtro_keyword.text().lower().strip()

        if window_instance.modalita_visualizzazione == 'preventivi':
            # Mostra solo preventivi originali (ultima revisione di ogni gruppo)
            preventivi = window_instance.db_manager.get_all_preventivi_latest()
        else:
            # Mostra solo le revisioni (escludendo i preventivi originali)
            preventivi = window_instance.db_manager.get_all_preventivi()
            # Filtra per mostrare solo le revisioni (numero_revisione > 1)
            preventivi_filtrati = []
            for prev in preventivi:
                if len(prev) >= 9:
                    numero_revisione = prev[8] if len(prev) > 8 else 1
                    if numero_revisione > 1:
                        preventivi_filtrati.append(prev)

            preventivi = preventivi_filtrati

        for preventivo in preventivi:
            # Formato: id, data_creazione, preventivo_finale, prezzo_cliente,
            # nome_cliente, numero_ordine, descrizione, codice, numero_revisione
            if len(preventivo) >= 9:
                id_prev, data_creazione, preventivo_finale, prezzo_cliente, nome_cliente, numero_ordine, descrizione, codice, numero_revisione = preventivo[:9]
            else:
                # Fallback per compatibilità
                id_prev, data_creazione, preventivo_finale, prezzo_cliente = preventivo[:4]
                nome_cliente, numero_ordine, descrizione, codice, numero_revisione = "", "", "", "", 1

            # APPLICA FILTRO ORIGINE
            if filtro_origine_text == "Originali" and numero_revisione != 1:
                continue  # Salta se non è originale
            elif filtro_origine_text == "Revisionati" and numero_revisione == 1:
                continue  # Salta se è originale
            elif filtro_origine_text == "Modificati" and numero_revisione == 1:
                continue  # Modificati = Revisionati (numero_revisione > 1)

            # APPLICA FILTRO CLIENTE
            if filtro_cliente_data and nome_cliente.strip() != filtro_cliente_data:
                continue  # Salta se il cliente non corrisponde

            # APPLICA FILTRO KEYWORD
            if filtro_keyword_text:
                # Cerca la keyword in TUTTI i campi del preventivo
                campi_ricerca = [
                    str(id_prev),
                    str(data_creazione),
                    str(preventivo_finale),
                    str(prezzo_cliente),
                    str(nome_cliente),
                    str(numero_ordine),
                    str(descrizione),
                    str(codice),
                    str(numero_revisione)
                ]
                testo_completo = " ".join(campi_ricerca).lower()
                if filtro_keyword_text not in testo_completo:
                    continue  # Salta se la keyword non è trovata

            # Formatta la data
            data_formattata = data_creazione.split('T')[0] if 'T' in data_creazione else data_creazione
            
            # Logica corretta per le etichette con formato migliorato
            if window_instance.modalita_visualizzazione == 'revisioni':
                # Nella sezione revisioni: mostra sempre [Revisione] per le revisioni
                prefisso_tipo = "Revisione"
                cliente_info = nome_cliente if nome_cliente else "Cliente non specificato"
                ordine_info = f" | {numero_ordine}" if numero_ordine else ""
                
                testo = f"#{id_prev:03d} [{prefisso_tipo}] - {data_formattata} - {cliente_info}{ordine_info}"
                testo += f"\nPreventivo: EUR {preventivo_finale:,.2f} | Cliente: EUR {prezzo_cliente:,.2f}"
                if descrizione:
                    testo += f"\nDescrizione: {descrizione[:60]}{'...' if len(descrizione) > 60 else ''}"
            else:
                # Nella sezione preventivi: distingui tra Originale e Revisionato
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
            item.setData(Qt.UserRole, id_prev)  # Salva l'ID del preventivo
            window_instance.lista_preventivi.addItem(item)
    
    @staticmethod
    def cambia_visualizzazione(window_instance, modalita):
        """Cambia tra visualizzazione Preventivi e Revisioni"""
        window_instance.modalita_visualizzazione = modalita
        
        # Aggiorna stili pulsanti
        if modalita == 'preventivi':
            window_instance.btn_mostra_preventivi.setStyleSheet("""
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
            window_instance.btn_mostra_revisioni.setStyleSheet("""
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
        else:  # revisioni
            window_instance.btn_mostra_revisioni.setStyleSheet("""
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
            window_instance.btn_mostra_preventivi.setStyleSheet("""
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
        
        # Ricarica la lista con la modalità corretta
        MainWindowBusinessLogic.load_preventivi(window_instance)
    
    @staticmethod
    def apri_preventivo(window_instance):
        """Apre la finestra per creare un nuovo preventivo"""
        window_instance.preventivo_window = PreventivoWindow(window_instance.db_manager, window_instance, modalita='nuovo')
        window_instance.preventivo_window.preventivo_salvato.connect(window_instance.preventivo_salvato)
        window_instance.preventivo_window.show()
    
    @staticmethod
    def modifica_preventivo(window_instance):
        """Apre un preventivo esistente per la modifica DIRETTA"""
        current_item = window_instance.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(window_instance, "Attenzione", "Seleziona un preventivo da modificare.")
            return
        
        preventivo_id = current_item.data(Qt.UserRole)
        window_instance.preventivo_window = PreventivoWindow(
            window_instance.db_manager, 
            window_instance, 
            preventivo_id=preventivo_id, 
            modalita='modifica'
        )
        window_instance.preventivo_window.preventivo_salvato.connect(window_instance.preventivo_salvato)
        window_instance.preventivo_window.show()
    
    @staticmethod
    def crea_revisione(window_instance):
        """Crea una revisione di un preventivo esistente"""
        current_item = window_instance.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(window_instance, "Attenzione", "Seleziona un preventivo per creare una revisione.")
            return
        
        preventivo_id = current_item.data(Qt.UserRole)
        
        # Dialog per inserire note sulla revisione
        note_revisione = MainWindowBusinessLogic.richiedi_note_revisione(window_instance)
        if note_revisione is None:  # L'utente ha annullato
            return
        
        window_instance.preventivo_window = PreventivoWindow(
            window_instance.db_manager, 
            window_instance, 
            preventivo_id=preventivo_id, 
            modalita='revisione',
            note_revisione=note_revisione
        )
        window_instance.preventivo_window.preventivo_salvato.connect(window_instance.preventivo_salvato)
        window_instance.preventivo_window.show()
    
    @staticmethod
    def genera_documento_preventivo(window_instance):
        """Genera documento di produzione dal preventivo selezionato"""
        current_item = window_instance.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(window_instance, "Attenzione",
                              "Seleziona un preventivo dalla lista per generare il documento.")
            return

        try:
            preventivo_id = current_item.data(Qt.UserRole)

            # Carica dati preventivo
            preventivo_data = None
            for metodo_name in ['get_preventivo_by_id', 'load_preventivo', 'fetch_preventivo']:
                if hasattr(window_instance.db_manager, metodo_name):
                    try:
                        preventivo_data = getattr(window_instance.db_manager, metodo_name)(preventivo_id)
                        break
                    except Exception:
                        continue

            # Estrai dati cliente e materiali
            if isinstance(preventivo_data, dict):
                dati_cliente = {
                    'nome_cliente': preventivo_data.get('nome_cliente', ''),
                    'numero_ordine': preventivo_data.get('numero_ordine', ''),
                    'oggetto_preventivo': preventivo_data.get('descrizione', ''),
                    'codice': preventivo_data.get('codice', f"PREV_{preventivo_id:03d}"),
                    'misura': preventivo_data.get('misura', ''),
                    'finitura': preventivo_data.get('finitura', '')
                }
                materiali = (preventivo_data.get('materiali_utilizzati')
                             or preventivo_data.get('materiali')
                             or preventivo_data.get('materiali_calcolati')
                             or [])
            elif isinstance(preventivo_data, (list, tuple)) and len(preventivo_data) >= 8:
                dati_cliente = {
                    'nome_cliente': preventivo_data[4] if len(preventivo_data) > 4 else '',
                    'numero_ordine': preventivo_data[5] if len(preventivo_data) > 5 else '',
                    'oggetto_preventivo': preventivo_data[6] if len(preventivo_data) > 6 else '',
                    'codice': preventivo_data[7] if len(preventivo_data) > 7 else f"PREV_{preventivo_id:03d}",
                    'misura': '',
                    'finitura': ''
                }
                materiali = []
            else:
                import re
                testo_item = current_item.text()
                prima_linea = testo_item.split('\n')[0] if testo_item else ""
                match = re.search(r'#(\d+)', prima_linea)
                codice = f"PREV_{match.group(1) if match else preventivo_id:03d}"
                dati_cliente = {
                    'nome_cliente': '',
                    'numero_ordine': '',
                    'oggetto_preventivo': '',
                    'codice': codice,
                    'misura': '',
                    'finitura': ''
                }
                materiali = []

            class PreventivoData:
                def __init__(self, codice, materiali_list):
                    self.codice_preventivo = codice
                    self.materiali = materiali_list or []

            preventivo_obj = PreventivoData(dati_cliente['codice'], materiali)

            # Mostra dialog per scegliere formato
            formato = DocumentUtils.mostra_dialog_formato(window_instance)
            if not formato:
                return

            # Genera documento nel formato scelto
            if formato == 'html':
                file_path = DocumentUtils.genera_documento_html(preventivo_obj, dati_cliente, window_instance)
            elif formato == 'odt':
                file_path = DocumentUtils.genera_documento_odt(preventivo_obj, dati_cliente, window_instance)
            else:
                return

            if file_path:
                QMessageBox.information(window_instance, "Successo", f"Documento generato:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(window_instance, "Errore",
                               f"Errore durante la generazione del documento:\n{str(e)}")
    
    @staticmethod
    def anteprima_documento_preventivo(window_instance):
        """Mostra anteprima del documento preventivo nel browser senza salvarlo"""
        current_item = window_instance.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(window_instance, "Attenzione",
                                "Seleziona un preventivo dalla lista per visualizzare l'anteprima.")
            return

        try:
            preventivo_id = current_item.data(Qt.UserRole)

            # Carica dati preventivo
            preventivo_data = None
            for metodo_name in ['get_preventivo_by_id', 'load_preventivo', 'fetch_preventivo']:
                if hasattr(window_instance.db_manager, metodo_name):
                    try:
                        preventivo_data = getattr(window_instance.db_manager, metodo_name)(preventivo_id)
                        break
                    except Exception:
                        continue

            # Prepara dati cliente e materiali
            if isinstance(preventivo_data, dict):
                dati_cliente = {
                    'nome_cliente': preventivo_data.get('nome_cliente', ''),
                    'numero_ordine': preventivo_data.get('numero_ordine', ''),
                    'oggetto_preventivo': preventivo_data.get('descrizione', ''),
                    'codice': preventivo_data.get('codice', f"PREV_{preventivo_id:03d}"),
                    'misura': preventivo_data.get('misura', ''),
                    'finitura': preventivo_data.get('finitura', '')
                }
                materiali = (preventivo_data.get('materiali_utilizzati')
                             or preventivo_data.get('materiali')
                             or preventivo_data.get('materiali_calcolati')
                             or [])
            elif isinstance(preventivo_data, (list, tuple)) and len(preventivo_data) >= 8:
                dati_cliente = {
                    'nome_cliente': preventivo_data[4] if len(preventivo_data) > 4 else '',
                    'numero_ordine': preventivo_data[5] if len(preventivo_data) > 5 else '',
                    'oggetto_preventivo': preventivo_data[6] if len(preventivo_data) > 6 else '',
                    'codice': preventivo_data[7] if len(preventivo_data) > 7 else f"PREV_{preventivo_id:03d}",
                    'misura': '',
                    'finitura': ''
                }
                materiali = []
            else:
                dati_cliente = {
                    'nome_cliente': '',
                    'numero_ordine': '',
                    'oggetto_preventivo': '',
                    'codice': f"PREV_{preventivo_id:03d}",
                    'misura': '',
                    'finitura': ''
                }
                materiali = []

            class PreventivoData:
                def __init__(self, codice, materiali_list):
                    self.codice_preventivo = codice
                    self.materiali = materiali_list or []

            preventivo_obj = PreventivoData(dati_cliente['codice'], materiali)

            DocumentUtils.anteprima_html(preventivo_obj, dati_cliente, window_instance)

        except Exception as e:
            QMessageBox.critical(window_instance, "Errore",
                                 f"Errore durante la generazione dell'anteprima:\n{e}")

    @staticmethod
    def apri_gestione_materiali(window_instance):
        """Apre la finestra per gestire i materiali"""
        window_instance.gestione_materiali_window = GestioneMaterialiWindow(window_instance.db_manager)

        # Collega il signal per aggiornare i preventivi aperti
        window_instance.gestione_materiali_window.materiali_modificati.connect(window_instance.aggiorna_preventivi_aperti)

        window_instance.gestione_materiali_window.show()

    @staticmethod
    def apri_magazzino(window_instance):
        """Apre la finestra per gestire il magazzino"""
        window_instance.magazzino_window = MagazzinoWindow(window_instance.db_manager)
        window_instance.magazzino_window.show()

    @staticmethod
    def apri_confronto_preventivi(window_instance):
        """NUOVO: Apre la finestra per confrontare due preventivi"""
        from ui.confronto_preventivi_window import ConfrontoPreventiviWindow

        window_instance.confronto_preventivi_window = ConfrontoPreventiviWindow(
            window_instance.db_manager,
            window_instance
        )
        window_instance.confronto_preventivi_window.show()
    
    @staticmethod
    def mostra_nascondi_preventivi(window_instance):
        """Apre la finestra per visualizzare i preventivi"""
        from ui.visualizza_preventivi_window import VisualizzaPreventiviWindow

        window_instance.visualizza_preventivi_window = VisualizzaPreventiviWindow(
            window_instance.db_manager,
            window_instance
        )
        window_instance.visualizza_preventivi_window.preventivo_modificato.connect(
            window_instance.preventivo_salvato
        )
        window_instance.visualizza_preventivi_window.show()
    
    @staticmethod
    def visualizza_preventivo(window_instance):
        """Visualizza i dettagli del preventivo selezionato"""
        current_item = window_instance.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(window_instance, "Attenzione", "Seleziona un preventivo da visualizzare.")
            return
        
        preventivo_id = current_item.data(Qt.UserRole)
        
        # Apre in modalità visualizzazione (sola lettura)
        window_instance.preventivo_window = PreventivoWindow(
            window_instance.db_manager, 
            window_instance, 
            preventivo_id=preventivo_id, 
            modalita='visualizza'
        )
        window_instance.preventivo_window.show()
    
    @staticmethod
    def elimina_preventivo(window_instance):
        """Elimina preventivo utilizzando il metodo del database"""
        current_item = window_instance.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(window_instance, "Attenzione", "Seleziona un preventivo da eliminare.")
            return
        
        preventivo_id = current_item.data(Qt.UserRole)

        # Determina se è una revisione o l'originale per mostrare il messaggio corretto
        prev_data = window_instance.db_manager.get_preventivo_by_id(preventivo_id)
        is_revisione = prev_data is not None and prev_data.get('preventivo_originale_id') is not None

        if is_revisione:
            testo_conferma = "Sei sicuro di voler eliminare questa revisione?\n\nSolo questa revisione verrà eliminata. Il preventivo originale e le altre revisioni rimarranno invariati."
            testo_successo = "Revisione eliminata con successo."
        else:
            revisioni = window_instance.db_manager.get_revisioni_preventivo(preventivo_id)
            # get_revisioni_preventivo restituisce originale + revisioni, quindi le revisioni sono len-1
            n_revisioni = max(0, len(revisioni) - 1)
            if n_revisioni > 0:
                avviso = f"\n\nAttenzione: questo preventivo ha {n_revisioni} revision{'e' if n_revisioni == 1 else 'i'} collegate che verranno eliminate insieme ad esso."
            else:
                avviso = ""
            testo_conferma = f"Sei sicuro di voler eliminare questo preventivo?{avviso}\n\nQuesta azione non può essere annullata."
            testo_successo = "Preventivo e tutte le sue revisioni sono stati eliminati con successo." if n_revisioni > 0 else "Preventivo eliminato con successo."

        # Dialog di conferma con stile unificato
        dialog = QMessageBox(window_instance)
        dialog.setWindowTitle("Conferma Eliminazione")
        dialog.setText(testo_conferma)
        dialog.setIcon(QMessageBox.Question)
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)
        dialog.setStyleSheet("""
            QMessageBox {
                background-color: #fafbfc;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QMessageBox QLabel {
                color: #2d3748;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
                min-width: 80px;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QMessageBox QPushButton[text="Yes"] {
                background-color: #e53e3e;
                color: #ffffff;
            }
            QMessageBox QPushButton[text="Yes"]:hover {
                background-color: #c53030;
            }
            QMessageBox QPushButton[text="No"] {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
            }
            QMessageBox QPushButton[text="No"]:hover {
                background-color: #edf2f7;
            }
        """)

        risposta = dialog.exec_()

        if risposta == QMessageBox.Yes:
            # Usa il metodo per eliminare preventivo e revisioni (o solo la revisione)
            if window_instance.db_manager.delete_preventivo_e_revisioni(preventivo_id):
                QMessageBox.information(window_instance, "Successo", testo_successo)
                MainWindowBusinessLogic.load_preventivi(window_instance)
            else:
                QMessageBox.critical(window_instance, "Errore",
                                "Errore durante l'eliminazione del preventivo.")
    
    @staticmethod
    def richiedi_note_revisione(window_instance):
        """Dialog per inserire note sulla revisione"""
        dialog = QDialog(window_instance)
        dialog.setWindowTitle("Note Revisione")
        dialog.setFixedSize(400, 250)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #fafbfc;
            }
            QLabel {
                color: #2d3748;
                font-size: 14px;
                font-weight: 500;
                font-family: system-ui, -apple-system, sans-serif;
            }
            QTextEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                background-color: #ffffff;
                color: #2d3748;
                font-family: system-ui, -apple-system, sans-serif;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        
        # Label descrittiva
        label = QLabel("Inserisci le note per questa revisione (opzionale):")
        layout.addWidget(label)
        
        # Campo di testo per le note
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Descrivi le modifiche apportate o il motivo della revisione...")
        layout.addWidget(text_edit)
        
        # Pulsanti
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec_() == QDialog.Accepted:
            return text_edit.toPlainText().strip()
        else:
            return None
    
    @staticmethod
    def aggiorna_preventivi_aperti(window_instance):
        """Aggiorna i preventivi aperti quando i materiali vengono modificati"""
        if window_instance.preventivo_window and window_instance.preventivo_window.isVisible():
            window_instance.preventivo_window.aggiorna_prezzi_materiali()
    
    @staticmethod
    def preventivo_salvato(window_instance):
        """Callback chiamato quando un preventivo viene salvato"""
        # Se la finestra visualizza preventivi è aperta, aggiornala
        if (hasattr(window_instance, 'visualizza_preventivi_window') and
                window_instance.visualizza_preventivi_window is not None and
                window_instance.visualizza_preventivi_window.isVisible()):
            window_instance.visualizza_preventivi_window.load_preventivi()
            window_instance.visualizza_preventivi_window.load_clienti_filtro()
        else:
            # Mostra un messaggio di successo
            QMessageBox.information(window_instance, "Successo",
                                  "Preventivo salvato con successo!\n\nUsa 'Visualizza Preventivi Salvati' per vederlo nella lista.")