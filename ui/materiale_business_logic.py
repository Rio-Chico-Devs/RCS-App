#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Materiale Business Logic - Logica di business per MaterialeWindow
Uso riservato esclusivamente a RCS

Version: 1.0.0
Last Updated: 23/09/2025
Author: Antonio VB
"""

from PyQt5.QtWidgets import QMessageBox, QHBoxLayout, QLabel, QWidget
from PyQt5.QtCore import Qt
from models.materiale import MaterialeCalcolato
from ui.materiale_ui_components import NoScrollDoubleSpinBox

class MaterialeBusinessLogic:
    """Classe per gestire la logica di business per MaterialeWindow"""
    
    @staticmethod
    def carica_materiali(window_instance):
        """Carica la lista dei materiali disponibili"""
        window_instance.combo_materiale.clear()
        window_instance.combo_materiale.addItem("Seleziona un materiale...", None)
        
        try:
            window_instance.materiali_disponibili = window_instance.db_manager.get_all_materiali()
            for materiale in window_instance.materiali_disponibili:
                id_mat, nome, spessore, prezzo = materiale[:4]
                text = f"{nome} - {spessore}mm - €{prezzo:.2f}/m"
                window_instance.combo_materiale.addItem(text, id_mat)
        except Exception as e:
            QMessageBox.critical(window_instance, "Errore", f"Errore nel caricamento materiali: {str(e)}")
    
    @staticmethod
    def on_materiale_changed(window_instance):
        """FIX: Gestisce cambio materiale e reset sviluppo manuale"""
        # RESET sviluppo manuale quando cambia il materiale
        window_instance.materiale_calcolato.arrotondamento_manuale = 0.0
        window_instance.edit_arrotondamento.blockSignals(True)
        window_instance.edit_arrotondamento.setValue(0.0)
        window_instance.edit_arrotondamento.blockSignals(False)
        window_instance.arrotondamento_modificato_manualmente = False
        
        # Processa il cambio materiale
        MaterialeBusinessLogic.materiale_selezionato(window_instance)
    
    @staticmethod
    def on_parametro_changed(window_instance):
        """FIX: Gestisce cambio parametri e reset sviluppo manuale"""
        # RESET sviluppo manuale quando cambia qualsiasi parametro
        window_instance.materiale_calcolato.arrotondamento_manuale = 0.0
        window_instance.edit_arrotondamento.blockSignals(True)
        window_instance.edit_arrotondamento.setValue(0.0)
        window_instance.edit_arrotondamento.blockSignals(False)
        window_instance.arrotondamento_modificato_manualmente = False
        
        # Ricalcola tutto automaticamente
        MaterialeBusinessLogic.ricalcola_tutto(window_instance)
    
    @staticmethod
    def on_sviluppo_manuale_changed(window_instance):
        """FIX: Gestisce SOLO il cambio del campo sviluppo manuale"""
        valore = window_instance.edit_arrotondamento.value()

        if valore != 0:
            window_instance.arrotondamento_modificato_manualmente = True
            window_instance.materiale_calcolato.arrotondamento_manuale = valore
            # IMPORTANTE: Imposta sviluppo manuale nel materiale calcolato
            window_instance.materiale_calcolato.sviluppo = valore
            
            window_instance.lbl_arrotondamento_status.setText("(personalizzato)")
            window_instance.lbl_arrotondamento_status.setStyleSheet("""
                QLabel {
                    color: #e53e3e;
                    font-size: 11px;
                    font-style: italic;
                    font-weight: 600;
                }
            """)
        else:
            window_instance.arrotondamento_modificato_manualmente = False
            window_instance.materiale_calcolato.arrotondamento_manuale = 0.0
            # Ricalcola sviluppo automaticamente
            window_instance.materiale_calcolato.ricalcola_tutto()
            
            window_instance.lbl_arrotondamento_status.setText("(automatico)")
            window_instance.lbl_arrotondamento_status.setStyleSheet("""
                QLabel {
                    color: #a0aec0;
                    font-size: 11px;
                    font-style: italic;
                }
            """)
        
        # Aggiorna solo l'interfaccia, senza ricalcolare
        MaterialeBusinessLogic.aggiorna_display(window_instance)
    
    @staticmethod
    def materiale_selezionato(window_instance):
        """Gestisce la selezione di un materiale"""
        materiale_id = window_instance.combo_materiale.currentData()
        if materiale_id is None:
            return
        
        try:
            materiale_info = window_instance.db_manager.get_materiale_by_id(materiale_id)
            if materiale_info:
                # Il metodo restituisce (id, nome, spessore, prezzo)
                id_materiale, nome, spessore, prezzo = materiale_info[:4]
                
                window_instance.materiale_calcolato.materiale_id = materiale_id
                window_instance.materiale_calcolato.materiale_nome = nome
                window_instance.materiale_calcolato.spessore = spessore
                window_instance.materiale_calcolato.costo_materiale = prezzo
                
                # Ricalcola tutto dopo aver impostato il materiale
                MaterialeBusinessLogic.ricalcola_tutto(window_instance)
        except Exception as e:
            QMessageBox.critical(window_instance, "Errore", f"Errore nella selezione materiale: {str(e)}")
    
    @staticmethod
    def ricalcola_tutto(window_instance):
        """Ricalcola tutti i valori con logica sviluppo manuale CORRETTA"""
        if not hasattr(window_instance, 'edit_giri') or not hasattr(window_instance, 'lbl_spessore'):
            return

        # Aggiorna giri dal form
        window_instance.materiale_calcolato.giri = window_instance.edit_giri.value()

        # Aggiorna posa dal combo
        if hasattr(window_instance, 'combo_posa'):
            window_instance.materiale_calcolato.posa = window_instance.combo_posa.currentData()

        # Leggi sempre diametro e lunghezza dai campi cilindrici (base per i calcoli)
        window_instance.materiale_calcolato.diametro = window_instance.edit_diametro.value()
        window_instance.materiale_calcolato.lunghezza = window_instance.edit_lunghezza.value()

        # Aggiorna parametri conicità dall'UI
        if window_instance.materiale_calcolato.is_conica:
            MaterialeBusinessLogic._leggi_conicita_da_ui(window_instance)
        
        # FIX: Logica sviluppo manuale corretta
        if window_instance.arrotondamento_modificato_manualmente and window_instance.edit_arrotondamento.value() > 0:
            # Usa sviluppo manuale
            sviluppo_manuale = window_instance.edit_arrotondamento.value()
            window_instance.materiale_calcolato.arrotondamento_manuale = sviluppo_manuale
            window_instance.materiale_calcolato.sviluppo = sviluppo_manuale
        else:
            # Calcola sviluppo automaticamente
            window_instance.materiale_calcolato.arrotondamento_manuale = 0.0
            window_instance.materiale_calcolato.ricalcola_tutto()
        
        # Aggiorna interfaccia
        MaterialeBusinessLogic.aggiorna_display(window_instance)
    
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

            # Aggiorna anteprima tela
            if hasattr(window_instance, 'tela_preview'):
                mc = window_instance.materiale_calcolato
                if mc.is_conica and mc.conicita_lunghezza_mm > 0:
                    scarto = window_instance.tela_preview.aggiorna_conica(
                        mc.conicita_lato,
                        mc.conicita_altezza_mm,
                        mc.conicita_lunghezza_mm,
                        mc.lunghezza,
                        mc.sviluppo
                    )
                    mc.scarto_mm2 = scarto
                elif mc.is_conica:
                    # Conica attiva ma lunghezza taglio = 0: mostra solo rettangolo
                    window_instance.tela_preview.aggiorna_cilindrica(
                        mc.diametro, mc.lunghezza, mc.sviluppo)
                    mc.scarto_mm2 = 0.0
                else:
                    window_instance.tela_preview.aggiorna_cilindrica(
                        mc.diametro, mc.lunghezza, mc.sviluppo)
                    mc.scarto_mm2 = 0.0
        except Exception as e:
            import sys
            print(f"[aggiorna_display] errore aggiornamento interfaccia: {e}", file=sys.stderr)

    @staticmethod
    def copia_materiale(materiale_originale):
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
        # Copia dati conici
        if hasattr(materiale_originale, 'is_conica'):
            nuovo_materiale.is_conica = materiale_originale.is_conica
        if hasattr(materiale_originale, 'sezioni_coniche'):
            import copy
            nuovo_materiale.sezioni_coniche = copy.deepcopy(materiale_originale.sezioni_coniche)
        if hasattr(materiale_originale, 'conicita_lato'):
            nuovo_materiale.conicita_lato = materiale_originale.conicita_lato
        if hasattr(materiale_originale, 'conicita_altezza_mm'):
            nuovo_materiale.conicita_altezza_mm = materiale_originale.conicita_altezza_mm
        if hasattr(materiale_originale, 'conicita_lunghezza_mm'):
            nuovo_materiale.conicita_lunghezza_mm = materiale_originale.conicita_lunghezza_mm
        if hasattr(materiale_originale, 'scarto_mm2'):
            nuovo_materiale.scarto_mm2 = materiale_originale.scarto_mm2
        if hasattr(materiale_originale, 'orientamento'):
            import copy as _copy
            nuovo_materiale.orientamento = _copy.deepcopy(materiale_originale.orientamento)
        nuovo_materiale.ricalcola_tutto()
        return nuovo_materiale
    
    @staticmethod
    def carica_dati_esistenti(window_instance):
        """Carica i dati di un materiale esistente per la modifica"""
        if not window_instance.materiale_esistente:
            return
        
        # Blocca segnali per evitare reset sviluppo manuale durante caricamento
        window_instance.edit_diametro.blockSignals(True)
        window_instance.edit_lunghezza.blockSignals(True)
        window_instance.edit_giri.blockSignals(True)
        window_instance.combo_materiale.blockSignals(True)
        window_instance.edit_arrotondamento.blockSignals(True)
        
        # Carica valori esistenti
        window_instance.edit_diametro.setValue(window_instance.materiale_esistente.diametro)
        window_instance.edit_lunghezza.setValue(window_instance.materiale_esistente.lunghezza)
        window_instance.edit_giri.setValue(window_instance.materiale_esistente.giri)

        # Carica posa se presente
        if hasattr(window_instance, 'combo_posa'):
            posa = getattr(window_instance.materiale_esistente, 'posa', '==')
            for i in range(window_instance.combo_posa.count()):
                if window_instance.combo_posa.itemData(i) == posa:
                    window_instance.combo_posa.setCurrentIndex(i)
                    break

        # Carica sviluppo manuale se esistente
        if hasattr(window_instance.materiale_esistente, 'arrotondamento_manuale') and window_instance.materiale_esistente.arrotondamento_manuale != 0:
            window_instance.edit_arrotondamento.setValue(window_instance.materiale_esistente.arrotondamento_manuale)
            window_instance.arrotondamento_modificato_manualmente = True
        
        # Carica materiale se esistente
        if window_instance.materiale_esistente.materiale_id:
            for i in range(window_instance.combo_materiale.count()):
                if window_instance.combo_materiale.itemData(i) == window_instance.materiale_esistente.materiale_id:
                    window_instance.combo_materiale.setCurrentIndex(i)
                    break
        
        # Sblocca segnali
        window_instance.edit_diametro.blockSignals(False)
        window_instance.edit_lunghezza.blockSignals(False)
        window_instance.edit_giri.blockSignals(False)
        window_instance.combo_materiale.blockSignals(False)
        window_instance.edit_arrotondamento.blockSignals(False)

        # Carica modalità conica se esistente
        if hasattr(window_instance.materiale_esistente, 'is_conica') and window_instance.materiale_esistente.is_conica:
            window_instance.btn_conica.setChecked(True)
            window_instance.materiale_calcolato.is_conica = True
            window_instance.conica_widget.show()

            # Carica parametri conicità semplificati
            mc = window_instance.materiale_esistente
            lato = getattr(mc, 'conicita_lato', 'sinistra')
            altezza = getattr(mc, 'conicita_altezza_mm', 0.0)
            lunghezza = getattr(mc, 'conicita_lunghezza_mm', 0.0)

            # Imposta radio button lato
            if lato == 'destra':
                window_instance.radio_destra.setChecked(True)
            elif lato == 'entrambi':
                window_instance.radio_entrambi.setChecked(True)
            else:
                window_instance.radio_sinistra.setChecked(True)

            # Imposta valori spinbox
            window_instance.spin_conicita_altezza.blockSignals(True)
            window_instance.spin_conicita_lunghezza.blockSignals(True)
            window_instance.spin_conicita_altezza.setValue(altezza)
            window_instance.spin_conicita_lunghezza.setValue(lunghezza)
            window_instance.spin_conicita_altezza.blockSignals(False)
            window_instance.spin_conicita_lunghezza.blockSignals(False)

        # Ripristina orientamento nella preview
        if hasattr(window_instance, 'tela_preview') and hasattr(window_instance.materiale_esistente, 'orientamento'):
            window_instance.tela_preview.set_orientamento(window_instance.materiale_esistente.orientamento)

        # Aggiorna display
        MaterialeBusinessLogic.aggiorna_display(window_instance)
    
    @staticmethod
    def concludi_operazione(window_instance):
        """Valida e conferma il materiale con controllo sviluppo manuale"""
        if window_instance.materiale_calcolato.materiale_id is None:
            QMessageBox.warning(window_instance, "Attenzione", "Seleziona un materiale.")
            return

        if window_instance.materiale_calcolato.giri <= 0:
            QMessageBox.warning(window_instance, "Attenzione", "Inserisci un numero di giri valido.")
            return

        # Validazione sempre sui campi cilindrici (la conica è solo visiva)
        if window_instance.materiale_calcolato.diametro <= 0:
            QMessageBox.warning(window_instance, "Attenzione", "Inserisci un diametro valido.")
            return
        if window_instance.materiale_calcolato.lunghezza <= 0:
            QMessageBox.warning(window_instance, "Attenzione", "Inserisci una lunghezza valida.")
            return
        
        # Controllo sviluppo manuale personalizzato
        if window_instance.arrotondamento_modificato_manualmente and window_instance.edit_arrotondamento.value() != 0:
            # Calcola sviluppo automatico per confronto
            materiale_temp = MaterialeBusinessLogic.copia_materiale(window_instance.materiale_calcolato)
            materiale_temp.arrotondamento_manuale = 0.0
            materiale_temp.ricalcola_tutto()
            sviluppo_automatico = materiale_temp.sviluppo
            
            reply = QMessageBox.question(
                window_instance, 
                "Sviluppo Personalizzato", 
                f"Hai impostato un valore di sviluppo personalizzato ({window_instance.edit_arrotondamento.value():.2f}) "
                f"che sovrascriverà il valore calcolato automaticamente ({sviluppo_automatico:.2f}).\n\n"
                "Vuoi procedere con questo valore personalizzato?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        # Aggiorna il valore di sviluppo effettivo prima di emettere
        if window_instance.arrotondamento_modificato_manualmente and window_instance.edit_arrotondamento.value() != 0:
            window_instance.materiale_calcolato.arrotondamento_manuale = window_instance.edit_arrotondamento.value()
            window_instance.materiale_calcolato.sviluppo = window_instance.edit_arrotondamento.value()

        # Salva orientamento dalla preview
        if hasattr(window_instance, 'tela_preview'):
            window_instance.materiale_calcolato.orientamento = window_instance.tela_preview.get_orientamento()

        window_instance.materiale_confermato.emit(window_instance.materiale_calcolato, window_instance.indice_modifica)
        window_instance.close()
    
    # ========== CONICAL METHODS ==========

    @staticmethod
    def toggle_conica(window_instance):
        """Attiva/disattiva modalità conica"""
        is_conica = window_instance.btn_conica.isChecked()
        window_instance.materiale_calcolato.is_conica = is_conica

        if is_conica:
            window_instance.conica_widget.show()
        else:
            window_instance.conica_widget.hide()
            window_instance.materiale_calcolato.is_conica = False
            window_instance.materiale_calcolato.conicita_lunghezza_mm = 0.0

        # Reset sviluppo manuale e ricalcola
        window_instance.materiale_calcolato.arrotondamento_manuale = 0.0
        window_instance.edit_arrotondamento.blockSignals(True)
        window_instance.edit_arrotondamento.setValue(0.0)
        window_instance.edit_arrotondamento.blockSignals(False)
        window_instance.arrotondamento_modificato_manualmente = False

        MaterialeBusinessLogic.ricalcola_tutto(window_instance)

    @staticmethod
    def _leggi_conicita_da_ui(window_instance):
        """Legge i parametri conicità dai widget e li salva nel modello."""
        mc = window_instance.materiale_calcolato
        if window_instance.radio_destra.isChecked():
            mc.conicita_lato = 'destra'
        elif window_instance.radio_entrambi.isChecked():
            mc.conicita_lato = 'entrambi'
        else:
            mc.conicita_lato = 'sinistra'
        mc.conicita_altezza_mm = window_instance.spin_conicita_altezza.value()
        mc.conicita_lunghezza_mm = window_instance.spin_conicita_lunghezza.value()

    @staticmethod
    def on_conicita_changed(window_instance):
        """Callback quando un parametro conicità cambia."""
        if not window_instance.materiale_calcolato.is_conica:
            return
        MaterialeBusinessLogic._leggi_conicita_da_ui(window_instance)
        MaterialeBusinessLogic.aggiorna_display(window_instance)

    @staticmethod
    def gestisci_chiusura_finestra(window_instance, event):
        """Gestisce la chiusura della finestra"""
        if hasattr(window_instance.parent(), 'materiale_windows'):
            try:
                window_instance.parent().materiale_windows.remove(window_instance)
            except ValueError:
                pass
        event.accept()