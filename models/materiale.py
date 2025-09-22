class Materiale:
    def __init__(self, nome="", spessore=0.0, prezzo=0.0):
        self.nome = nome
        self.spessore = spessore
        self.prezzo = prezzo

class MaterialeCalcolato:
    def __init__(self):
        # Sezione sviluppo
        self.diametro = 0.0
        self.lunghezza = 0.0
        self.materiale_id = None
        self.materiale_nome = ""
        self.giri = 0
        self.spessore = 0.0  # Dal materiale selezionato
        self.diametro_finale = 0.0  # Calcolato
        self.sviluppo = 0.0  # Calcolato
        self.arrotondamento_manuale = 0.0
        
        # Sezione costo materiale
        self.costo_materiale = 0.0  # Dal materiale selezionato
        self.lunghezza_utilizzata = 0.0  # Calcolato
        self.costo_totale = 0.0  # Calcolato
        self.maggiorazione = 0.0  # Calcolato
        
        # Aggiungo anche un alias per compatibilità con il codice esistente
        # Questo permette di accedere con entrambi i nomi durante la transizione
        self.prezzo = 0.0  # Alias per costo_materiale
    
    @property
    def stratifica(self):
        """Alias per sviluppo - per compatibilità con codice esistente"""
        return self.sviluppo
    
    @stratifica.setter
    def stratifica(self, value):
        """Setter per l'alias stratifica"""
        self.sviluppo = value
    
    def calcola_diametro_finale(self):
        """Calcola il diametro finale: diametro + (spessore * (giri * 2))"""
        self.diametro_finale = self.diametro + (self.spessore * (self.giri * 2))
        return self.diametro_finale
    
    def calcola_sviluppo(self):
        """Calcola lo sviluppo: ((diametro + giri * spessore) * 3.14) * giri + 5"""
        # Se c'è un arrotondamento manuale, usa quello
        if self.arrotondamento_manuale > 0:
            self.sviluppo = self.arrotondamento_manuale
        else:
            self.sviluppo = ((self.diametro + self.giri * self.spessore) * 3.14) * self.giri + 5
        return self.sviluppo
    
    def calcola_stratifica(self):
        """Alias per calcola_sviluppo - per compatibilità"""
        return self.calcola_sviluppo()
    
    def calcola_lunghezza_utilizzata(self):
        """Calcola lunghezza utilizzata: (lunghezza * sviluppo) / 1000000"""
        if self.sviluppo > 0:
            self.lunghezza_utilizzata = (self.lunghezza * self.sviluppo) / 1000000
        return self.lunghezza_utilizzata
    
    def calcola_costo_totale(self):
        """Calcola costo totale: lunghezza_utilizzata * costo_materiale"""
        # Sincronizza prezzo con costo_materiale
        if self.prezzo > 0:
            self.costo_materiale = self.prezzo
        
        self.costo_totale = self.lunghezza_utilizzata * self.costo_materiale
        return self.costo_totale
    
    def calcola_maggiorazione(self):
        """Calcola maggiorazione: costo_totale * 1.1"""
        self.maggiorazione = self.costo_totale * 1.1
        return self.maggiorazione
    
    def ricalcola_tutto(self):
        """Ricalcola tutti i valori derivati"""
        self.calcola_diametro_finale()
        self.calcola_sviluppo()
        self.calcola_lunghezza_utilizzata()
        self.calcola_costo_totale()
        self.calcola_maggiorazione()
    
    def to_dict(self):
        """Converte l'oggetto in dizionario per il salvataggio"""
        return {
            'diametro': self.diametro,
            'lunghezza': self.lunghezza,
            'materiale_id': self.materiale_id,
            'materiale_nome': self.materiale_nome,
            'giri': self.giri,
            'spessore': self.spessore,
            'diametro_finale': self.diametro_finale,
            'sviluppo': self.sviluppo,
            'stratifica': self.sviluppo,  # Per compatibilità
            'arrotondamento_manuale': self.arrotondamento_manuale,
            'costo_materiale': self.costo_materiale,
            'lunghezza_utilizzata': self.lunghezza_utilizzata,
            'costo_totale': self.costo_totale,
            'maggiorazione': self.maggiorazione
        }