#!/usr/bin/env python3
"""
Applicazione per la gestione dei preventivi
Creata con PyQt5 e SQLite
"""

import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QDir

# Aggiungi la directory corrente al path per importare i moduli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow
from utils.logger import setup_logger


def _gestisci_eccezione_globale(exc_type, exc_value, exc_traceback):
    """Intercetta qualsiasi eccezione non gestita durante l'esecuzione
    e mostra un dialog all'utente invece di chiudere l'app in silenzio."""
    if issubclass(exc_type, KeyboardInterrupt):
        # Ctrl+C: comportamento normale
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    dettaglio = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"[ERRORE NON GESTITO]\n{dettaglio}", file=sys.stderr)

    QMessageBox.critical(
        None,
        "Errore Imprevisto",
        f"Si è verificato un errore imprevisto nell'applicazione:\n\n"
        f"{exc_type.__name__}: {exc_value}\n\n"
        f"L'operazione corrente potrebbe non essere stata completata.\n"
        f"Se il problema persiste, riavviare l'applicazione."
    )


sys.excepthook = _gestisci_eccezione_globale


def main():
    """Funzione principale dell'applicazione"""
    setup_logger()

    # Crea l'applicazione Qt
    app = QApplication(sys.argv)

    # Imposta le proprietà dell'applicazione
    app.setApplicationName("Gestione Preventivi")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("RCS")

    try:
        # Crea e mostra la finestra principale
        window = MainWindow()
        window.showMaximized()

        # Avvia il loop degli eventi
        sys.exit(app.exec_())

    except Exception as e:
        # Gestione errori di avvio
        QMessageBox.critical(None, "Errore Critico",
                           f"Errore durante l'avvio dell'applicazione:\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
