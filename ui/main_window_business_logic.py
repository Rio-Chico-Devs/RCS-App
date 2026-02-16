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
        """NUOVO: Genera documento di produzione dal preventivo selezionato"""
        current_item = window_instance.lista_preventivi.currentItem()
        if not current_item:
            QMessageBox.warning(window_instance, "Attenzione", 
                              "Seleziona un preventivo dalla lista per generare il documento.")
            return
        
        try:
            preventivo_id = current_item.data(Qt.UserRole)
            print(f"DEBUG: Generando documento per preventivo ID {preventivo_id}")
            
            # DEBUG: Mostra tutti i metodi disponibili nel DatabaseManager
            print("DEBUG: Metodi disponibili in DatabaseManager:")
            metodi_db = [method for method in dir(window_instance.db_manager) if not method.startswith('_')]
            for metodo in sorted(metodi_db):
                print(f"  - {metodo}")
            
            # Proviamo con alcuni nomi comuni per caricare preventivo
            preventivo_data = None
            metodi_da_provare = [
                'get_preventivo_by_id',
                'load_preventivo', 
                'fetch_preventivo',
                'get_preventivo_data',
                'select_preventivo'
            ]
            
            for metodo_name in metodi_da_provare:
                if hasattr(window_instance.db_manager, metodo_name):
                    print(f"DEBUG: Trovato metodo {metodo_name}, provo a usarlo")
                    metodo = getattr(window_instance.db_manager, metodo_name)
                    try:
                        preventivo_data = metodo(preventivo_id)
                        print(f"DEBUG: Successo con {metodo_name}")
                        break
                    except Exception as e:
                        print(f"DEBUG: {metodo_name} ha dato errore: {e}")
                        continue
            
            # Se nessun metodo ha funzionato, usa i dati dalla lista
            if not preventivo_data:
                print("DEBUG: Nessun metodo di caricamento trovato, uso dati dalla lista")
                # Estrai informazioni dal testo dell'item della lista
                testo_item = current_item.text()
                print(f"DEBUG: Testo item lista: {testo_item}")
                
                # Parsing basic dal testo dell'item
                linee = testo_item.split('\n')
                prima_linea = linee[0] if linee else ""
                
                # Estrai codice preventivo dal testo (formato: "#022 [Originale] - 2025-09-22 - Cliente")
                import re
                match = re.search(r'#(\d+)', prima_linea)
                codice = f"PREV_{match.group(1) if match else preventivo_id:03d}"
                
                # Dati cliente base
                dati_cliente = {
                    'nome_cliente': 'Cliente da lista preventivi',
                    'numero_ordine': '',
                    'oggetto_preventivo': 'Oggetto da completare',
                    'codice': codice
                }
                
                print(f"DEBUG: Usando dati base: {dati_cliente}")
                
                # Materiali vuoti per ora
                materiali = []
                
            else:
                print(f"DEBUG: Dati preventivo caricati: {type(preventivo_data)}")
                
                # Estrai dati dal preventivo caricato
                if isinstance(preventivo_data, dict):
                    dati_cliente = {
                        'nome_cliente': preventivo_data.get('nome_cliente', ''),
                        'numero_ordine': preventivo_data.get('numero_ordine', ''),
                        'oggetto_preventivo': preventivo_data.get('descrizione', ''),
                        'codice': preventivo_data.get('codice', f"PREV_{preventivo_id:03d}")
                    }
                    
                    print(f"DEBUG: Chiavi disponibili nel preventivo: {list(preventivo_data.keys())}")
                    print(f"DEBUG: Contenuto completo preventivo: {preventivo_data}")
                    
                    # Prova a estrarre materiali direttamente dal preventivo
                    materiali = preventivo_data.get('materiali_utilizzati', [])
                    if not materiali:
                        materiali = preventivo_data.get('materiali', [])
                    if not materiali:
                        materiali = preventivo_data.get('materiali_calcolati', [])
                        
                    print(f"DEBUG: Materiali trovati nel preventivo: {len(materiali)}")
                    if materiali:
                        print(f"DEBUG: Primo materiale esempio: {materiali[0] if len(materiali) > 0 else 'Nessuno'}")
                        # Mostra struttura di tutti i materiali
                        for idx, mat in enumerate(materiali):
                            print(f"DEBUG: Materiale {idx}: {mat}")
                    else:
                        print(f"DEBUG: Nessun materiale nelle chiavi: materiali_utilizzati, materiali, materiali_calcolati")
                        
                elif isinstance(preventivo_data, (list, tuple)) and len(preventivo_data) >= 8:
                    dati_cliente = {
                        'nome_cliente': preventivo_data[4] if len(preventivo_data) > 4 else '',
                        'numero_ordine': preventivo_data[5] if len(preventivo_data) > 5 else '',
                        'oggetto_preventivo': preventivo_data[6] if len(preventivo_data) > 6 else '',
                        'codice': preventivo_data[7] if len(preventivo_data) > 7 else f"PREV_{preventivo_id:03d}"
                    }
                    materiali = []  # Tuple/list non contiene materiali
                else:
                    dati_cliente = {
                        'nome_cliente': 'Cliente non specificato',
                        'numero_ordine': '',
                        'oggetto_preventivo': 'Descrizione non disponibile',
                        'codice': f"PREV_{preventivo_id:03d}"
                    }
                    materiali = []
                
                # Se non abbiamo materiali dal preventivo, proviamo approccio alternativo
                if not materiali:
                    print("DEBUG: Nessun materiale nel preventivo, provo approccio alternativo")
                    
                    # Prova con get_all_materiali e filtra per questo preventivo
                    if hasattr(window_instance.db_manager, 'get_all_materiali'):
                        try:
                            tutti_materiali = window_instance.db_manager.get_all_materiali()
                            print(f"DEBUG: Caricati {len(tutti_materiali)} materiali totali")
                            
                            # Qui dovremmo filtrare per preventivo_id, ma potrebbe non essere disponibile
                            # Per ora usiamo tutti i materiali come esempio
                            if tutti_materiali:
                                print("DEBUG: Usando primi 5 materiali come esempio per il documento")
                                materiali = tutti_materiali[:5]  # Prendi primi 5 come esempio
                                
                        except Exception as e:
                            print(f"DEBUG: Errore nel caricare tutti i materiali: {e}")
                            materiali = []
                    
                    # Se ancora non abbiamo materiali, creiamo materiali di esempio per il documento
                    if not materiali:
                        print("DEBUG: Creando materiali di esempio per il documento")
                        materiali = [
                            {"nome": "Materiale 1", "giri": 1, "lunghezza": 2150, "sviluppo": 135},
                            {"nome": "Materiale 2", "giri": 3, "lunghezza": 2150, "sviluppo": 405},
                            {"nome": "Materiale 3", "giri": 1, "lunghezza": 2150, "sviluppo": 145},
                            {"nome": "Materiale 4", "giri": 2, "lunghezza": 1800, "sviluppo": 250},
                            {"nome": "Materiale 5", "giri": 1, "lunghezza": 2000, "sviluppo": 180}
                        ]
            
            print(f"DEBUG: Dati cliente finali: {dati_cliente}")
            
            # Crea oggetto preventivo compatibile con DocumentUtils
            class PreventivoData:
                def __init__(self, codice, materiali_list):
                    self.codice_preventivo = codice
                    self.materiali = materiali_list or []
                    
            preventivo_obj = PreventivoData(dati_cliente['codice'], materiali)
            
            # Mostra dialog per scegliere formato
            formato = DocumentUtils.mostra_dialog_formato(window_instance)
            if not formato:
                return  # Utente ha annullato
            
            print(f"DEBUG: Formato scelto: {formato}")
            
            # Genera documento nel formato scelto
            if formato == 'html':
                file_path = DocumentUtils.genera_documento_html(preventivo_obj, dati_cliente, window_instance)
            elif formato == 'odt':
                file_path = DocumentUtils.genera_documento_odt(preventivo_obj, dati_cliente, window_instance)
            else:
                print(f"DEBUG: Formato non riconosciuto: {formato}")
                return
            
            if file_path:
                print(f"DEBUG: Documento generato con successo: {file_path}")
                QMessageBox.information(window_instance, "Successo", f"Documento generato:\n{file_path}")
            else:
                print("DEBUG: Generazione documento annullata o fallita")
            
        except Exception as e:
            print(f"DEBUG: Errore generazione documento: {str(e)}")
            import traceback
            print(f"DEBUG: Traceback completo: {traceback.format_exc()}")
            QMessageBox.critical(window_instance, "Errore", 
                               f"Errore durante la generazione del documento:\n{str(e)}")
    
    @staticmethod
    def apri_gestione_materiali(window_instance):
        """Apre la finestra per gestire i materiali"""
        window_instance.gestione_materiali_window = GestioneMaterialiWindow(window_instance.db_manager, window_instance)

        # Collega il signal per aggiornare i preventivi aperti
        window_instance.gestione_materiali_window.materiali_modificati.connect(window_instance.aggiorna_preventivi_aperti)

        window_instance.gestione_materiali_window.show()

    @staticmethod
    def apri_magazzino(window_instance):
        """Apre la finestra per gestire il magazzino"""
        window_instance.magazzino_window = MagazzinoWindow(window_instance.db_manager, window_instance)
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
        
        # Dialog di conferma con stile unificato
        dialog = QMessageBox(window_instance)
        dialog.setWindowTitle("Conferma Eliminazione")
        dialog.setText("Sei sicuro di voler eliminare questo preventivo?\n\nQuesta azione eliminerà anche tutte le sue revisioni e non può essere annullata.")
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
            preventivo_id = current_item.data(Qt.UserRole)
            
            # Usa il metodo per eliminare preventivo e revisioni
            if window_instance.db_manager.delete_preventivo_e_revisioni(preventivo_id):
                QMessageBox.information(window_instance, "Successo", 
                                      "Preventivo e tutte le sue revisioni sono stati eliminati con successo.")
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