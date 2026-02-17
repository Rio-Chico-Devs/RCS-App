#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Preventivo Business Logic - Logica di business per preventivi
Uso riservato esclusivamente a RCS

Version: 1.0.0
Last Updated: 23/09/2025
Author: Antonio VB + Claude
"""

from PyQt5.QtWidgets import QMessageBox
from models.materiale import MaterialeCalcolato
from ui.materiale_window import MaterialeWindow
import json

class PreventivoBusinessLogic:
    """Classe per gestire la logica di business dei preventivi"""
    
    @staticmethod
    def carica_preventivo_dal_database(window_instance, preventivo_id):
        """Carica un preventivo esistente dal database"""
        preventivo_data = window_instance.db_manager.get_preventivo_by_id(preventivo_id)
        if not preventivo_data:
            QMessageBox.critical(window_instance, "Errore", "Preventivo non trovato nel database.")
            return
        
        # Carica dati base
        window_instance.preventivo.costo_totale_materiali = preventivo_data[4]  # costo_totale_materiali
        window_instance.preventivo.minuti_taglio = preventivo_data[5]
        window_instance.preventivo.minuti_avvolgimento = preventivo_data[6]
        window_instance.preventivo.minuti_pulizia = preventivo_data[7]
        window_instance.preventivo.minuti_rettifica = preventivo_data[8]
        window_instance.preventivo.minuti_imballaggio = preventivo_data[9]
        window_instance.preventivo.costo_orario = preventivo_data[10]
        window_instance.preventivo.costi_accessori = preventivo_data[11]
        window_instance.preventivo.costo_totale_manodopera = preventivo_data[12]
        window_instance.preventivo.costo_totale_finale = preventivo_data[13]
        
        # Carica dati cliente se disponibili
        if len(preventivo_data) > 14:
            window_instance.nome_cliente_data = preventivo_data[14] or ""
            window_instance.numero_ordine_data = preventivo_data[15] or ""
            window_instance.descrizione_data = preventivo_data[16] or ""
            window_instance.codice_data = preventivo_data[17] or ""
        else:
            window_instance.nome_cliente_data = ""
            window_instance.numero_ordine_data = ""
            window_instance.descrizione_data = ""
            window_instance.codice_data = ""
        
        # Gestione revisioni
        if len(preventivo_data) > 18:
            window_instance.preventivo_originale_id = preventivo_data[18]
            if not window_instance.preventivo_originale_id:
                window_instance.preventivo_originale_id = preventivo_id
        else:
            window_instance.preventivo_originale_id = preventivo_id
        
        # Carica materiali
        try:
            materiali_json = preventivo_data[3]
            if materiali_json:
                materiali_data = json.loads(materiali_json)
                window_instance.preventivo.materiali_calcolati = []
                
                for mat_data in materiali_data:
                    materiale = MaterialeCalcolato(
                        nome=mat_data['nome'],
                        diametro_interno=mat_data['diametro_interno'],
                        spessore=mat_data['spessore'],
                        costo_al_kg=mat_data['costo_al_kg'],
                        densita=mat_data['densita']
                    )
                    
                    # Imposta valori calcolati
                    if 'giri' in mat_data:
                        materiale.giri = mat_data['giri']
                    if 'sviluppo' in mat_data:
                        materiale.sviluppo = mat_data['sviluppo']
                    if 'diametro_finale' in mat_data:
                        materiale.diametro_finale = mat_data['diametro_finale']
                    if 'peso_totale' in mat_data:
                        materiale.peso_totale = mat_data['peso_totale']
                    if 'costo_totale' in mat_data:
                        materiale.costo_totale = mat_data['costo_totale']
                    
                    # Gestione tessitura
                    if 'tessitura' in mat_data:
                        materiale.tessitura = mat_data['tessitura']
                    if 'lunghezza_trama' in mat_data:
                        materiale.lunghezza_trama = mat_data['lunghezza_trama']
                    if 'lunghezza_ordito' in mat_data:
                        materiale.lunghezza_ordito = mat_data['lunghezza_ordito']
                    if 'spessore_trama' in mat_data:
                        materiale.spessore_trama = mat_data['spessore_trama']
                    if 'spessore_ordito' in mat_data:
                        materiale.spessore_ordito = mat_data['spessore_ordito']
                    
                    window_instance.preventivo.materiali_calcolati.append(materiale)
                    
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Errore nel caricamento materiali: {e}")
    
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
        print(f"DEBUG: Aggiungendo materiale: {materiale_calcolato.nome}, giri: {materiale_calcolato.giri}, sviluppo: {materiale_calcolato.sviluppo}")
        
        window_instance.preventivo.materiali_calcolati.append(materiale_calcolato)
        
        # Ricalcola costo totale materiali
        window_instance.preventivo.ricalcola_costo_totale_materiali()
        
        # Aggiorna interfaccia
        window_instance.aggiorna_materiali_info()
        window_instance.aggiorna_totali()
    
    @staticmethod
    def gestisci_materiale_modificato(window_instance, materiale_calcolato, indice):
        """Gestisce modifica materiale con debug specifico per i giri"""
        print(f"DEBUG: Modificando materiale {indice}: {materiale_calcolato.nome}")
        print(f"DEBUG: Giri: {materiale_calcolato.giri}, Sviluppo: {materiale_calcolato.sviluppo}")
        print(f"DEBUG: Diametro interno: {materiale_calcolato.diametro_interno}, finale: {materiale_calcolato.diametro_finale}")
        
        # Sostituisci il materiale
        window_instance.preventivo.materiali_calcolati[indice] = materiale_calcolato
        
        # IMPORTANTE: Ricalcola i diametri successivi
        PreventivoBusinessLogic.ricalcola_diametri_successivi(window_instance, indice)
        
        # Ricalcola costo totale materiali
        window_instance.preventivo.ricalcola_costo_totale_materiali()
        
        # Aggiorna interfaccia
        window_instance.aggiorna_materiali_info()
        window_instance.aggiorna_totali()
        
        print(f"DEBUG: Aggiornamento completato per materiale {indice}")
    
    @staticmethod
    def ricalcola_diametri_successivi(window_instance, indice_modificato):
        """Ricalcola diametri per i materiali successivi"""
        print(f"DEBUG: Ricalcolando diametri successivi a partire dall'indice {indice_modificato}")
        
        for i in range(indice_modificato + 1, len(window_instance.preventivo.materiali_calcolati)):
            materiale_precedente = window_instance.preventivo.materiali_calcolati[i - 1]
            materiale_corrente = window_instance.preventivo.materiali_calcolati[i]
            
            print(f"DEBUG: Materiale {i} - Diametro interno prima: {materiale_corrente.diametro_interno}")
            
            # Aggiorna diametro interno del materiale corrente
            materiale_corrente.diametro_interno = materiale_precedente.diametro_finale
            
            # Ricalcola tutti i valori dipendenti
            materiale_corrente.ricalcola_tutto()
            
            print(f"DEBUG: Materiale {i} - Diametro interno dopo: {materiale_corrente.diametro_interno}, finale: {materiale_corrente.diametro_finale}")
    
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
            'nome_cliente': window_instance.edit_nome_cliente.text().strip() if hasattr(window_instance, 'edit_nome_cliente') else "",
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
            
            # Aggiorna totali finali
            window_instance.preventivo.ricalcola_costo_totale_materiali()
            
            # Calcola manodopera
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
            
            # Converte materiali in JSON
            materiali_data = []
            for materiale in window_instance.preventivo.materiali_calcolati:
                mat_dict = {
                    'nome': materiale.nome,
                    'diametro_interno': materiale.diametro_interno,
                    'spessore': materiale.spessore,
                    'costo_al_kg': materiale.costo_al_kg,
                    'densita': materiale.densita,
                    'giri': materiale.giri,
                    'sviluppo': materiale.sviluppo,
                    'diametro_finale': materiale.diametro_finale,
                    'peso_totale': materiale.peso_totale,
                    'costo_totale': materiale.costo_totale
                }
                
                # Aggiungi dati tessitura se presenti
                if hasattr(materiale, 'tessitura'):
                    mat_dict['tessitura'] = materiale.tessitura
                if hasattr(materiale, 'lunghezza_trama'):
                    mat_dict['lunghezza_trama'] = materiale.lunghezza_trama
                if hasattr(materiale, 'lunghezza_ordito'):
                    mat_dict['lunghezza_ordito'] = materiale.lunghezza_ordito
                if hasattr(materiale, 'spessore_trama'):
                    mat_dict['spessore_trama'] = materiale.spessore_trama
                if hasattr(materiale, 'spessore_ordito'):
                    mat_dict['spessore_ordito'] = materiale.spessore_ordito
                
                materiali_data.append(mat_dict)
            
            materiali_json = json.dumps(materiali_data)
            
            if window_instance.modalita == 'revisione':
                # Salva come nuova revisione
                preventivo_id = window_instance.db_manager.salva_preventivo(
                    materiali_json,
                    window_instance.preventivo.costo_totale_materiali,
                    window_instance.preventivo.minuti_taglio,
                    window_instance.preventivo.minuti_avvolgimento,
                    window_instance.preventivo.minuti_pulizia,
                    window_instance.preventivo.minuti_rettifica,
                    window_instance.preventivo.minuti_imballaggio,
                    window_instance.preventivo.costo_orario,
                    window_instance.preventivo.costi_accessori,
                    window_instance.preventivo.costo_totale_manodopera,
                    window_instance.preventivo.costo_totale_finale,
                    dati_cliente['nome_cliente'],
                    dati_cliente['numero_ordine'],
                    dati_cliente['descrizione'],
                    dati_cliente['codice'],
                    window_instance.preventivo_originale_id,  # ID originale per revisione
                    window_instance.note_revisione
                )
                
                QMessageBox.information(window_instance, "Successo", f"Revisione salvata con successo! ID: {preventivo_id}")
                
            elif window_instance.modalita == 'modifica':
                # Aggiorna preventivo esistente
                window_instance.db_manager.aggiorna_preventivo(
                    window_instance.preventivo_id,
                    materiali_json,
                    window_instance.preventivo.costo_totale_materiali,
                    window_instance.preventivo.minuti_taglio,
                    window_instance.preventivo.minuti_avvolgimento,
                    window_instance.preventivo.minuti_pulizia,
                    window_instance.preventivo.minuti_rettifica,
                    window_instance.preventivo.minuti_imballaggio,
                    window_instance.preventivo.costo_orario,
                    window_instance.preventivo.costi_accessori,
                    window_instance.preventivo.costo_totale_manodopera,
                    window_instance.preventivo.costo_totale_finale,
                    dati_cliente['nome_cliente'],
                    dati_cliente['numero_ordine'],
                    dati_cliente['descrizione'],
                    dati_cliente['codice']
                )
                
                QMessageBox.information(window_instance, "Successo", "Preventivo aggiornato con successo!")
                
            else:
                # Nuovo preventivo
                preventivo_id = window_instance.db_manager.salva_preventivo(
                    materiali_json,
                    window_instance.preventivo.costo_totale_materiali,
                    window_instance.preventivo.minuti_taglio,
                    window_instance.preventivo.minuti_avvolgimento,
                    window_instance.preventivo.minuti_pulizia,
                    window_instance.preventivo.minuti_rettifica,
                    window_instance.preventivo.minuti_imballaggio,
                    window_instance.preventivo.costo_orario,
                    window_instance.preventivo.costi_accessori,
                    window_instance.preventivo.costo_totale_manodopera,
                    window_instance.preventivo.costo_totale_finale,
                    dati_cliente['nome_cliente'],
                    dati_cliente['numero_ordine'],
                    dati_cliente['descrizione'],
                    dati_cliente['codice']
                )
                
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