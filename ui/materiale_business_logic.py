#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Materiale Business Logic - Logica di business per MaterialeWindow
Uso riservato esclusivamente a RCS

Version: 1.0.0
Last Updated: 23/09/2025
Author: Antonio VB + Claude
"""

from PyQt5.QtWidgets import QMessageBox, QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QWidget
from PyQt5.QtCore import Qt
from models.materiale import MaterialeCalcolato

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
        print("DEBUG: Materiale cambiato - resetting sviluppo manuale")
        
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
        print("DEBUG: Parametro cambiato - resetting sviluppo manuale")
        
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
        
        print(f"DEBUG: Sviluppo manuale cambiato a: {valore}")
        
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

        # Aggiorna valori in base alla modalità
        if window_instance.materiale_calcolato.is_conica:
            # Modalità conica: le sezioni sono già sincronizzate da on_sezione_changed
            pass
        else:
            # Modalità cilindrica standard
            window_instance.materiale_calcolato.diametro = window_instance.edit_diametro.value()
            window_instance.materiale_calcolato.lunghezza = window_instance.edit_lunghezza.value()
        
        # FIX: Logica sviluppo manuale corretta
        if window_instance.arrotondamento_modificato_manualmente and window_instance.edit_arrotondamento.value() > 0:
            # Usa sviluppo manuale
            sviluppo_manuale = window_instance.edit_arrotondamento.value()
            window_instance.materiale_calcolato.arrotondamento_manuale = sviluppo_manuale
            window_instance.materiale_calcolato.sviluppo = sviluppo_manuale
            print(f"DEBUG: Usando sviluppo manuale: {sviluppo_manuale}")
        else:
            # Calcola sviluppo automaticamente
            window_instance.materiale_calcolato.arrotondamento_manuale = 0.0
            window_instance.materiale_calcolato.ricalcola_tutto()
            print(f"DEBUG: Sviluppo calcolato automaticamente: {window_instance.materiale_calcolato.sviluppo}")
        
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
        except Exception as e:
            pass
    
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
            window_instance.cilindrico_widget.hide()
            window_instance.conica_widget.show()

            # Ricrea le sezioni dal materiale esistente
            if hasattr(window_instance.materiale_esistente, 'sezioni_coniche') and window_instance.materiale_esistente.sezioni_coniche:
                for sez in window_instance.materiale_esistente.sezioni_coniche:
                    MaterialeBusinessLogic.aggiungi_sezione_conica(window_instance)
                    last = window_instance.sezioni_widgets[-1]
                    last['lunghezza'].blockSignals(True)
                    last['d_inizio'].blockSignals(True)
                    last['d_fine'].blockSignals(True)
                    last['lunghezza'].setValue(int(sez.get('lunghezza', 0)))
                    last['d_inizio'].setValue(float(sez.get('d_inizio', 0.0)))
                    last['d_fine'].setValue(float(sez.get('d_fine', 0.0)))
                    last['lunghezza'].blockSignals(False)
                    last['d_inizio'].blockSignals(False)
                    last['d_fine'].blockSignals(False)

                # Sincronizza sezioni nel modello
                MaterialeBusinessLogic.on_sezione_changed(window_instance)

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

        # Validazione specifica per modalità conica vs cilindrica
        if window_instance.materiale_calcolato.is_conica:
            if not window_instance.materiale_calcolato.sezioni_coniche:
                QMessageBox.warning(window_instance, "Attenzione", "Aggiungi almeno una sezione conica.")
                return
            # Controlla che tutte le sezioni abbiano valori validi
            for i, sez in enumerate(window_instance.materiale_calcolato.sezioni_coniche):
                if sez.get('lunghezza', 0) <= 0:
                    QMessageBox.warning(window_instance, "Attenzione", f"Sezione {i+1}: inserisci una lunghezza valida.")
                    return
                if sez.get('d_inizio', 0) <= 0 and sez.get('d_fine', 0) <= 0:
                    QMessageBox.warning(window_instance, "Attenzione", f"Sezione {i+1}: inserisci almeno un diametro valido.")
                    return
        else:
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
        
        window_instance.materiale_confermato.emit(window_instance.materiale_calcolato, window_instance.indice_modifica)
        window_instance.close()
    
    # ========== CONICAL METHODS ==========

    @staticmethod
    def toggle_conica(window_instance):
        """Attiva/disattiva modalità conica"""
        is_conica = window_instance.btn_conica.isChecked()
        window_instance.materiale_calcolato.is_conica = is_conica

        if is_conica:
            window_instance.cilindrico_widget.hide()
            window_instance.conica_widget.show()
            # Aggiungi una sezione iniziale se vuota
            if len(window_instance.sezioni_widgets) == 0:
                MaterialeBusinessLogic.aggiungi_sezione_conica(window_instance)
        else:
            window_instance.cilindrico_widget.show()
            window_instance.conica_widget.hide()
            # Ripristina modalità cilindrica
            window_instance.materiale_calcolato.is_conica = False
            window_instance.materiale_calcolato.sezioni_coniche = []

        # Reset sviluppo manuale e ricalcola
        window_instance.materiale_calcolato.arrotondamento_manuale = 0.0
        window_instance.edit_arrotondamento.blockSignals(True)
        window_instance.edit_arrotondamento.setValue(0.0)
        window_instance.edit_arrotondamento.blockSignals(False)
        window_instance.arrotondamento_modificato_manualmente = False

        MaterialeBusinessLogic.ricalcola_tutto(window_instance)

    @staticmethod
    def aggiungi_sezione_conica(window_instance):
        """Aggiunge una riga sezione conica con i relativi widget"""
        idx = len(window_instance.sezioni_widgets) + 1

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        # Numero sezione
        lbl_num = QLabel(str(idx))
        lbl_num.setFixedWidth(20)
        lbl_num.setAlignment(Qt.AlignCenter)
        lbl_num.setStyleSheet("font-size: 12px; font-weight: 600; color: #718096;")
        row_layout.addWidget(lbl_num)

        # Lunghezza sezione (mm) - intero
        spin_lunghezza = QSpinBox()
        spin_lunghezza.setMaximum(99999)
        spin_lunghezza.setValue(0)
        spin_lunghezza.setSuffix(" mm")
        spin_lunghezza.setMinimumHeight(32)
        spin_lunghezza.valueChanged.connect(window_instance.on_sezione_changed)
        row_layout.addWidget(spin_lunghezza)

        # Diametro inizio (mm) - decimale
        spin_d_inizio = QDoubleSpinBox()
        spin_d_inizio.setMaximum(99999.99)
        spin_d_inizio.setDecimals(2)
        spin_d_inizio.setValue(0.0)
        spin_d_inizio.setSuffix(" mm")
        spin_d_inizio.setMinimumHeight(32)
        spin_d_inizio.valueChanged.connect(window_instance.on_sezione_changed)
        row_layout.addWidget(spin_d_inizio)

        # Diametro fine (mm) - decimale
        spin_d_fine = QDoubleSpinBox()
        spin_d_fine.setMaximum(99999.99)
        spin_d_fine.setDecimals(2)
        spin_d_fine.setValue(0.0)
        spin_d_fine.setSuffix(" mm")
        spin_d_fine.setMinimumHeight(32)
        spin_d_fine.valueChanged.connect(window_instance.on_sezione_changed)
        row_layout.addWidget(spin_d_fine)

        # Se c'è una sezione precedente, usa il suo d_fine come d_inizio di questa
        if window_instance.sezioni_widgets:
            prev = window_instance.sezioni_widgets[-1]
            prev_d_fine = prev['d_fine'].value()
            spin_d_inizio.setValue(prev_d_fine)

        # Inserisci prima dello stretch
        stretch_index = window_instance.sezioni_layout.count() - 1
        window_instance.sezioni_layout.insertWidget(stretch_index, row_widget)

        window_instance.sezioni_widgets.append({
            'widget': row_widget,
            'lbl_num': lbl_num,
            'lunghezza': spin_lunghezza,
            'd_inizio': spin_d_inizio,
            'd_fine': spin_d_fine
        })

        # Aggiorna calcoli
        MaterialeBusinessLogic.on_sezione_changed(window_instance)

    @staticmethod
    def rimuovi_sezione_conica(window_instance):
        """Rimuove l'ultima sezione conica"""
        if not window_instance.sezioni_widgets:
            return

        last = window_instance.sezioni_widgets.pop()
        last['widget'].setParent(None)
        last['widget'].deleteLater()

        # Aggiorna calcoli
        MaterialeBusinessLogic.on_sezione_changed(window_instance)

    @staticmethod
    def on_sezione_changed(window_instance):
        """Legge i valori dalle sezioni e ricalcola tutto"""
        sezioni = []
        for sw in window_instance.sezioni_widgets:
            sezioni.append({
                'lunghezza': sw['lunghezza'].value(),
                'd_inizio': sw['d_inizio'].value(),
                'd_fine': sw['d_fine'].value()
            })
        window_instance.materiale_calcolato.sezioni_coniche = sezioni

        # Reset sviluppo manuale
        window_instance.materiale_calcolato.arrotondamento_manuale = 0.0
        window_instance.edit_arrotondamento.blockSignals(True)
        window_instance.edit_arrotondamento.setValue(0.0)
        window_instance.edit_arrotondamento.blockSignals(False)
        window_instance.arrotondamento_modificato_manualmente = False

        MaterialeBusinessLogic.ricalcola_tutto(window_instance)

    @staticmethod
    def gestisci_chiusura_finestra(window_instance, event):
        """Gestisce la chiusura della finestra"""
        if hasattr(window_instance.parent(), 'materiale_windows'):
            try:
                window_instance.parent().materiale_windows.remove(window_instance)
            except ValueError:
                pass
        event.accept()