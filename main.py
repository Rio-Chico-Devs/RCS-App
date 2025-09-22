#!/usr/bin/env python3
"""
Applicazione per la gestione dei preventivi
Creata con PyQt5 e SQLite
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QDir

# Aggiungi la directory corrente al path per importare i moduli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow

def main():
    """Funzione principale dell'applicazione"""
    # Crea l'applicazione Qt
    app = QApplication(sys.argv)
    
    # Imposta le proprietà dell'applicazione
    app.setApplicationName("Gestione Preventivi")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("La Tua Azienda")
    
    try:
        # Crea e mostra la finestra principale
        window = MainWindow()
        window.show()
        
        # Avvia il loop degli eventi
        sys.exit(app.exec_())
        
    except Exception as e:
        # Gestione errori
        QMessageBox.critical(None, "Errore Critico", 
                           f"Errore durante l'avvio dell'applicazione:\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()