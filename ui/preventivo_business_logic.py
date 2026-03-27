#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Preventivo Business Logic - Logica di business per preventivi
Uso riservato esclusivamente a RCS

Version: 1.0.0
Last Updated: 23/09/2025
Author: Antonio VB
"""

from PyQt5.QtWidgets import QMessageBox
from models.materiale import MaterialeCalcolato
from ui.materiale_window import MaterialeWindow
import json

class PreventivoBusinessLogic:
    """Classe per gestire la logica di business dei preventivi"""
    
    @staticmethod
    def aggiungi_materiale(window_instance):
        """Aggiunge nuovo materiale"""
        diametro_interno = 0
        if window_instance.preventivo.materiali_calcolati:
            ultimo_materiale = window_instance.preventivo.materiali_calcolati[-1]
            diametro_interno = ultimo_materiale.diametro_finale
        
        materiale_window = MaterialeWindow(
            window_instance.db_manager,
            parent=window_instance,
            diametro_interno=diametro_interno,
            modalita_sola_lettura=(window_instance.modalita == 'visualizza')
        )
        
        materiale_window.materiale_confermato.connect(window_instance.materiale_aggiunto)
        window_instance.materiale_windows.append(materiale_window)
        materiale_window.show()
    
    @staticmethod
    def modifica_materiale(window_instance, indice):
        """Modifica materiale esistente"""
        if 0 <= indice < len(window_instance.preventivo.materiali_calcolati):
            materiale_esistente = window_instance.preventivo.materiali_calcolati[indice]
            
            materiale_window = MaterialeWindow(
                window_instance.db_manager,
                parent=window_instance,
                materiale_esistente=materiale_esistente,
                indice_modifica=indice,
                modalita_sola_lettura=(window_instance.modalita == 'visualizza')
            )
            
            materiale_window.materiale_confermato.connect(window_instance.materiale_modificato)
            window_instance.materiale_windows.append(materiale_window)
            materiale_window.show()
    
    @staticmethod
    def elimina_materiale(window_instance, indice):
        """Elimina materiale"""
        if 0 <= indice < len(window_instance.preventivo.materiali_calcolati):
            risposta = QMessageBox.question(
                window_instance,
                "Conferma Eliminazione",
                "Sei sicuro di voler eliminare questo materiale?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if risposta == QMessageBox.Yes:
                del window_instance.preventivo.materiali_calcolati[indice]
                
                # Ricalcola diametri per i materiali successivi
                PreventivoBusinessLogic.ricalcola_diametri_successivi(window_instance, indice - 1)
                
                # Aggiorna interfaccia
                window_instance.aggiorna_materiali_info()
                window_instance.aggiorna_totali()
    
    @staticmethod
    def gestisci_materiale_aggiunto(window_instance, materiale_calcolato):
        """Gestisce nuovo materiale aggiunto"""
        window_instance.preventivo.materiali_calcolati.append(materiale_calcolato)
        
        # Ricalcola costo totale materiali
        window_instance.preventivo.ricalcola_costo_totale_materiali()
        
        # Aggiorna interfaccia
        window_instance.aggiorna_materiali_info()
        window_instance.aggiorna_totali()
    
    @staticmethod
    def gestisci_materiale_modificato(window_instance, materiale_calcolato, indice):
        """Gestisce modifica materiale"""
        # Sostituisci il materiale
        window_instance.preventivo.materiali_calcolati[indice] = materiale_calcolato
        
        # IMPORTANTE: Ricalcola i diametri successivi
        PreventivoBusinessLogic.ricalcola_diametri_successivi(window_instance, indice)
        
        # Ricalcola costo totale materiali
        window_instance.preventivo.ricalcola_costo_totale_materiali()
        
        # Aggiorna interfaccia
        window_instance.aggiorna_materiali_info()
        window_instance.aggiorna_totali()

    @staticmethod
    def ricalcola_diametri_successivi(window_instance, indice_modificato):
        """Ricalcola diametri per i materiali successivi"""
        for i in range(indice_modificato + 1, len(window_instance.preventivo.materiali_calcolati)):
            materiale_precedente = window_instance.preventivo.materiali_calcolati[i - 1]
            materiale_corrente = window_instance.preventivo.materiali_calcolati[i]

            # Aggiorna diametro interno del materiale corrente
            materiale_corrente.diametro_interno = materiale_precedente.diametro_finale

            # Ricalcola tutti i valori dipendenti
            materiale_corrente.ricalcola_tutto()
    
    @staticmethod
    def aggiorna_totali(window_instance):
        """Aggiorna tutti i totali del preventivo"""
        # Leggi valori dai controlli dell'interfaccia
        if hasattr(window_instance, 'edit_minuti_taglio'):
            window_instance.preventivo.minuti_taglio = window_instance.edit_minuti_taglio.value()
        if hasattr(window_instance, 'edit_minuti_avvolgimento'):
            window_instance.preventivo.minuti_avvolgimento = window_instance.edit_minuti_avvolgimento.value()
        if hasattr(window_instance, 'edit_minuti_pulizia'):
            window_instance.preventivo.minuti_pulizia = window_instance.edit_minuti_pulizia.value()
        if hasattr(window_instance, 'edit_minuti_rettifica'):
            window_instance.preventivo.minuti_rettifica = window_instance.edit_minuti_rettifica.value()
        if hasattr(window_instance, 'edit_minuti_imballaggio'):
            window_instance.preventivo.minuti_imballaggio = window_instance.edit_minuti_imballaggio.value()
        
        if hasattr(window_instance, 'edit_costo_orario'):
            window_instance.preventivo.costo_orario = window_instance.edit_costo_orario.value()
        if hasattr(window_instance, 'edit_costi_accessori'):
            window_instance.preventivo.costi_accessori = window_instance.edit_costi_accessori.value()
        
        # Ricalcola totali usando i metodi corretti
        window_instance.preventivo.ricalcola_costo_totale_materiali()
        
        # Calcola manodopera manualmente
        minuti_totali = (window_instance.preventivo.minuti_taglio + 
                        window_instance.preventivo.minuti_avvolgimento + 
                        window_instance.preventivo.minuti_pulizia + 
                        window_instance.preventivo.minuti_rettifica + 
                        window_instance.preventivo.minuti_imballaggio)
        ore_totali = minuti_totali / 60
        window_instance.preventivo.costo_totale_manodopera = ore_totali * window_instance.preventivo.costo_orario
        
        # Calcola totale finale
        window_instance.preventivo.costo_totale_finale = (window_instance.preventivo.costo_totale_materiali + 
                                                         window_instance.preventivo.costo_totale_manodopera + 
                                                         window_instance.preventivo.costi_accessori)
        
        # Aggiorna interfaccia
        window_instance.aggiorna_interface_totali()
    
    @staticmethod
    def on_costi_accessori_changed(window_instance):
        """Gestisce cambio costi accessori"""
        window_instance.preventivo.costi_accessori = window_instance.edit_costi_accessori.value()
        
        # Ricalcola totale finale
        window_instance.preventivo.costo_totale_finale = (window_instance.preventivo.costo_totale_materiali + 
                                                         window_instance.preventivo.costo_totale_manodopera + 
                                                         window_instance.preventivo.costi_accessori)
        
        window_instance.aggiorna_interface_totali()
    
    @staticmethod
    def on_mano_opera_changed(window_instance):
        """Gestisce cambio mano d'opera"""
        window_instance.preventivo.costo_orario = window_instance.edit_costo_orario.value()
        
        # Ricalcola manodopera
        minuti_totali = (window_instance.preventivo.minuti_taglio + 
                        window_instance.preventivo.minuti_avvolgimento + 
                        window_instance.preventivo.minuti_pulizia + 
                        window_instance.preventivo.minuti_rettifica + 
                        window_instance.preventivo.minuti_imballaggio)
        ore_totali = minuti_totali / 60
        window_instance.preventivo.costo_totale_manodopera = ore_totali * window_instance.preventivo.costo_orario
        
        # Ricalcola totale finale
        window_instance.preventivo.costo_totale_finale = (window_instance.preventivo.costo_totale_materiali + 
                                                         window_instance.preventivo.costo_totale_manodopera + 
                                                         window_instance.preventivo.costi_accessori)
        
        window_instance.aggiorna_interface_totali()
    
    @staticmethod
    def get_dati_cliente(window_instance):
        """Recupera dati cliente dai controlli"""
        return {
            'nome_cliente': window_instance.combo_nome_cliente.currentText().strip() if hasattr(window_instance, 'combo_nome_cliente') else "",
            'numero_ordine': window_instance.edit_numero_ordine.text().strip() if hasattr(window_instance, 'edit_numero_ordine') else "",
            'descrizione': window_instance.edit_descrizione.text().strip() if hasattr(window_instance, 'edit_descrizione') else "",
            'codice': window_instance.edit_codice.text().strip() if hasattr(window_instance, 'edit_codice') else "",
            'misura': window_instance.edit_misura.text().strip() if hasattr(window_instance, 'edit_misura') else "",
            'finitura': window_instance.edit_finitura.text().strip() if hasattr(window_instance, 'edit_finitura') else ""
        }
    
    @staticmethod
    def salva_preventivo(window_instance):
        """Salva preventivo nel database"""
        try:
            if not window_instance.preventivo.materiali_calcolati:
                QMessageBox.warning(window_instance, "Attenzione", "Aggiungi almeno un materiale prima di salvare il preventivo.")
                return

            # Recupera dati cliente
            dati_cliente = PreventivoBusinessLogic.get_dati_cliente(window_instance)

            # Ricalcola tutti i totali
            window_instance.preventivo.ricalcola_tutto()

            # Costruisci il dizionario dati per il DB
            preventivo_data = window_instance.preventivo.to_dict()
            preventivo_data.update(dati_cliente)

            if window_instance.modalita == 'revisione':
                preventivo_id = window_instance.db_manager.add_revisione_preventivo(
                    window_instance.preventivo_originale_id,
                    preventivo_data,
                    getattr(window_instance, 'note_revisione', '')
                )
                QMessageBox.information(window_instance, "Successo", f"Revisione salvata con successo! ID: {preventivo_id}")

            elif window_instance.modalita == 'modifica':
                window_instance.db_manager.update_preventivo(
                    window_instance.preventivo_id,
                    preventivo_data
                )
                QMessageBox.information(window_instance, "Successo", "Preventivo aggiornato con successo!")

            else:
                preventivo_id = window_instance.db_manager.add_preventivo(preventivo_data)
                QMessageBox.information(window_instance, "Successo", f"Preventivo salvato con successo! ID: {preventivo_id}")

            window_instance.preventivo_salvato.emit()
            window_instance.close()

        except Exception as e:
            QMessageBox.critical(window_instance, "Errore", f"Errore nel salvataggio: {str(e)}")
    
    @staticmethod
    def gestisci_chiusura_finestra(window_instance, event):
        """Gestisce chiusura finestra"""
        # Chiudi tutte le finestre materiale aperte
        for materiale_window in window_instance.materiale_windows[:]:
            materiale_window.close()
        
        event.accept()