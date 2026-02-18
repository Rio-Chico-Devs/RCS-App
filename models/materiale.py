class Materiale:
    def __init__(self, nome="", spessore=0.0, prezzo=0.0, fornitore="", prezzo_fornitore=0.0, capacita_magazzino=0.0, giacenza=0.0):
        self.nome = nome
        self.spessore = spessore
        self.prezzo = prezzo
        self.fornitore = fornitore
        self.prezzo_fornitore = prezzo_fornitore
        self.capacita_magazzino = capacita_magazzino
        self.giacenza = giacenza

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
        self.prezzo = 0.0  # Alias per costo_materiale

        # Modalità conica
        self.is_conica = False
        self.sezioni_coniche = []  # [{lunghezza, d_inizio, d_fine}, ...]

    @property
    def stratifica(self):
        """Alias per sviluppo - per compatibilità con codice esistente"""
        return self.sviluppo

    @stratifica.setter
    def stratifica(self, value):
        """Setter per l'alias stratifica"""
        self.sviluppo = value

    def calcola_diametro_finale(self):
        """Calcola il diametro finale"""
        if self.is_conica and self.sezioni_coniche:
            # Per la conica: d_fine dell'ultima sezione + spessore da avvolgimento
            ultima_sezione = self.sezioni_coniche[-1]
            d_fine_ultima = ultima_sezione.get('d_fine', 0.0)
            self.diametro_finale = d_fine_ultima + (self.spessore * (self.giri * 2))
        else:
            # Cilindrico standard
            self.diametro_finale = self.diametro + (self.spessore * (self.giri * 2))
        return self.diametro_finale

    def calcola_sviluppo(self):
        """Calcola lo sviluppo"""
        if self.arrotondamento_manuale > 0:
            self.sviluppo = self.arrotondamento_manuale
        elif self.is_conica and self.sezioni_coniche:
            self._calcola_sviluppo_conico()
        else:
            # Cilindrico standard
            self.sviluppo = ((self.diametro + self.giri * self.spessore) * 3.14) * self.giri + 5
        return self.sviluppo

    def _calcola_sviluppo_conico(self):
        """Calcola sviluppo e lunghezza_utilizzata per tubo conico.
        Ogni sezione ha forma trapezoidale: usa la media dei diametri."""
        lunghezza_totale = 0
        area_totale = 0

        for sez in self.sezioni_coniche:
            l_sez = sez.get('lunghezza', 0)
            d_ini = sez.get('d_inizio', 0)
            d_fin = sez.get('d_fine', 0)
            d_medio = (d_ini + d_fin) / 2

            # Sviluppo di questa sezione (formula cilindrica con diametro medio)
            sviluppo_sez = ((d_medio + self.giri * self.spessore) * 3.14) * self.giri

            # Area trapezoidale della sezione (mm²)
            area_totale += l_sez * sviluppo_sez
            lunghezza_totale += l_sez

        # Aggiungi offset una volta
        if lunghezza_totale > 0:
            area_totale += lunghezza_totale * 5  # +5mm di margine sulla larghezza

        # Sviluppo equivalente medio (per display)
        if lunghezza_totale > 0:
            self.sviluppo = area_totale / lunghezza_totale
        else:
            self.sviluppo = 0

        # Aggiorna lunghezza totale
        self.lunghezza = lunghezza_totale

    def calcola_stratifica(self):
        """Alias per calcola_sviluppo - per compatibilità"""
        return self.calcola_sviluppo()

    def calcola_lunghezza_utilizzata(self):
        """Calcola lunghezza utilizzata in m²"""
        if self.is_conica and self.sezioni_coniche and self.arrotondamento_manuale <= 0:
            # Per la conica, calcola direttamente dalla somma delle aree trapezoidali
            area_totale = 0
            for sez in self.sezioni_coniche:
                l_sez = sez.get('lunghezza', 0)
                d_ini = sez.get('d_inizio', 0)
                d_fin = sez.get('d_fine', 0)
                d_medio = (d_ini + d_fin) / 2
                sviluppo_sez = ((d_medio + self.giri * self.spessore) * 3.14) * self.giri
                area_totale += l_sez * sviluppo_sez
            lunghezza_totale = sum(s.get('lunghezza', 0) for s in self.sezioni_coniche)
            if lunghezza_totale > 0:
                area_totale += lunghezza_totale * 5
            self.lunghezza_utilizzata = area_totale / 1000000
        else:
            # Cilindrico standard
            if self.sviluppo > 0:
                self.lunghezza_utilizzata = (self.lunghezza * self.sviluppo) / 1000000
        return self.lunghezza_utilizzata

    def calcola_costo_totale(self):
        """Calcola costo totale: lunghezza_utilizzata * costo_materiale"""
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
        d = {
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
            'maggiorazione': self.maggiorazione,
            'is_conica': self.is_conica,
            'sezioni_coniche': self.sezioni_coniche
        }
        return d