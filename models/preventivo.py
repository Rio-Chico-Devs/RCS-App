class Preventivo:
    def __init__(self):
        self.materiali_calcolati = []  # Lista di MaterialeCalcolato
        self.costo_totale_materiali = 0.0
        self.costi_accessori = 0.0
        self.minuti_taglio = 0.0
        self.minuti_avvolgimento = 0.0
        self.minuti_pulizia = 0.0
        self.minuti_rettifica = 0.0
        self.minuti_imballaggio = 0.0
        self.tot_mano_opera = 0.0
        self.subtotale = 0.0
        self.maggiorazione_25 = 0.0
        self.preventivo_finale = 0.0
        self.prezzo_cliente = 0.0
    
    def aggiungi_materiale(self, materiale_calcolato):
        """Aggiunge un materiale calcolato al preventivo"""
        if len(self.materiali_calcolati) < 10:  # Limite massimo 10 materiali
            self.materiali_calcolati.append(materiale_calcolato)
            self.ricalcola_costo_totale_materiali()
            return True
        return False
    
    def rimuovi_materiale(self, indice):
        """Rimuove un materiale dal preventivo"""
        if 0 <= indice < len(self.materiali_calcolati):
            self.materiali_calcolati.pop(indice)
            self.ricalcola_costo_totale_materiali()
            return True
        return False
    
    def ricalcola_costo_totale_materiali(self):
        """Ricalcola il costo totale dei materiali sommando tutte le maggiorazioni"""
        self.costo_totale_materiali = sum(
            materiale.maggiorazione for materiale in self.materiali_calcolati
        )
        return self.costo_totale_materiali
    
    def calcola_tot_mano_opera(self):
        """Calcola il totale mano d'opera"""
        self.tot_mano_opera = (
            self.minuti_taglio + 
            self.minuti_avvolgimento + 
            self.minuti_pulizia + 
            self.minuti_rettifica + 
            self.minuti_imballaggio
        )
        return self.tot_mano_opera
    
    def calcola_subtotale(self):
        """Calcola il subtotale: costi_accessori + tot_mano_opera + costo_totale_materiali"""
        self.subtotale = (
            self.costi_accessori + 
            self.tot_mano_opera + 
            self.costo_totale_materiali
        )
        return self.subtotale
    
    def calcola_maggiorazione_25(self):
        """Calcola la maggiorazione del 25%"""
        self.maggiorazione_25 = self.subtotale * 0.25
        return self.maggiorazione_25
    
    def calcola_preventivo_finale(self):
        """Calcola il preventivo finale: subtotale + maggiorazione 25%"""
        self.preventivo_finale = self.subtotale + self.maggiorazione_25
        return self.preventivo_finale
    
    def ricalcola_tutto(self):
        """Ricalcola tutti i valori del preventivo"""
        self.ricalcola_costo_totale_materiali()
        self.calcola_tot_mano_opera()
        self.calcola_subtotale()
        self.calcola_maggiorazione_25()
        self.calcola_preventivo_finale()
    
    def to_dict(self):
        """Converte il preventivo in dizionario per il salvataggio"""
        return {
            'costo_totale_materiali': self.costo_totale_materiali,
            'costi_accessori': self.costi_accessori,
            'minuti_taglio': self.minuti_taglio,
            'minuti_avvolgimento': self.minuti_avvolgimento,
            'minuti_pulizia': self.minuti_pulizia,
            'minuti_rettifica': self.minuti_rettifica,
            'minuti_imballaggio': self.minuti_imballaggio,
            'tot_mano_opera': self.tot_mano_opera,
            'subtotale': self.subtotale,
            'maggiorazione_25': self.maggiorazione_25,
            'preventivo_finale': self.preventivo_finale,
            'prezzo_cliente': self.prezzo_cliente,
            'materiali_utilizzati': [m.to_dict() for m in self.materiali_calcolati]
        }