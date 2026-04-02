#!/usr/bin/env python3
"""
Applicazione per la gestione dei preventivi
Creata con PyQt5 e SQLite
"""

import sys
import os
import json
import traceback
from PyQt5.QtWidgets import (QApplication, QMessageBox, QDialog, QVBoxLayout,
                              QHBoxLayout, QLabel, QPushButton, QLineEdit,
                              QFileDialog, QFrame, QButtonGroup, QRadioButton)
from PyQt5.QtCore import QDir, Qt
from PyQt5.QtGui import QFont

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


def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _is_primo_avvio(base_dir):
    """Ritorna True se non esiste config.json né il DB locale."""
    config_path = os.path.join(base_dir, "config.json")
    db_locale = os.path.join(base_dir, "data", "materiali.db")
    return not os.path.exists(config_path) and not os.path.exists(db_locale)


def _mostra_dialogo_primo_avvio(base_dir):
    """
    Mostra il dialogo di configurazione al primo avvio.
    Ritorna True se l'utente ha completato la configurazione, False se ha annullato.
    """

    dialog = QDialog()
    dialog.setWindowTitle("Configurazione iniziale - RCS Preventivi")
    dialog.setMinimumWidth(560)
    dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)

    layout = QVBoxLayout(dialog)
    layout.setSpacing(16)
    layout.setContentsMargins(24, 24, 24, 24)

    # Titolo
    titolo = QLabel("Benvenuto in RCS Preventivi")
    font_titolo = QFont()
    font_titolo.setPointSize(13)
    font_titolo.setBold(True)
    titolo.setFont(font_titolo)
    layout.addWidget(titolo)

    # Descrizione
    desc = QLabel(
        "Nessun database trovato. Scegli come vuoi configurare l'applicazione:"
    )
    desc.setWordWrap(True)
    layout.addWidget(desc)

    # Separatore
    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setFrameShadow(QFrame.Sunken)
    layout.addWidget(sep)

    # Opzione 1: DB locale
    radio_locale = QRadioButton("Crea un nuovo database locale su questo PC")
    radio_locale.setChecked(True)
    font_radio = QFont()
    font_radio.setBold(True)
    radio_locale.setFont(font_radio)
    layout.addWidget(radio_locale)

    desc_locale = QLabel("Il database sarà creato nella cartella dell'applicazione.\n"
                          "Adatto se usi l'app su un solo computer.")
    desc_locale.setStyleSheet("color: #666; margin-left: 22px;")
    desc_locale.setWordWrap(True)
    layout.addWidget(desc_locale)

    layout.addSpacing(8)

    # Opzione 2: DB esistente/condiviso
    radio_rete = QRadioButton("Usa un database esistente (cartella condivisa in rete)")
    radio_rete.setFont(font_radio)
    layout.addWidget(radio_rete)

    desc_rete = QLabel("Punta a un database già esistente su un altro PC o cartella condivisa.\n"
                        "Tutti i PC che puntano allo stesso percorso usano lo stesso database.")
    desc_rete.setStyleSheet("color: #666; margin-left: 22px;")
    desc_rete.setWordWrap(True)
    layout.addWidget(desc_rete)

    # Campo percorso
    frame_percorso = QFrame()
    frame_percorso.setEnabled(False)
    layout_percorso = QHBoxLayout(frame_percorso)
    layout_percorso.setContentsMargins(22, 4, 0, 0)
    layout_percorso.setSpacing(6)

    campo_path = QLineEdit()
    campo_path.setPlaceholderText(r"Es: \\NOMEPC\RCS\materiali.db  oppure  Z:\RCS\materiali.db")
    layout_percorso.addWidget(campo_path)

    btn_sfoglia = QPushButton("Sfoglia...")
    btn_sfoglia.setFixedWidth(90)
    layout_percorso.addWidget(btn_sfoglia)

    layout.addWidget(frame_percorso)

    # Nota rete
    nota_rete = QLabel(
        "Nota: il percorso di rete deve essere accessibile da questo PC.\n"
        "Su altri PC inserisci lo stesso percorso nella stessa schermata.\n"
        "Verrà salvato un file config.json nella cartella dell'applicazione."
    )
    nota_rete.setStyleSheet("color: #888; font-size: 11px; margin-left: 22px;")
    nota_rete.setWordWrap(True)
    nota_rete.setVisible(False)
    layout.addWidget(nota_rete)

    # Abilita/disabilita campo percorso al cambio radio
    def on_radio_cambiato():
        usa_rete = radio_rete.isChecked()
        frame_percorso.setEnabled(usa_rete)
        nota_rete.setVisible(usa_rete)

    radio_locale.toggled.connect(on_radio_cambiato)
    radio_rete.toggled.connect(on_radio_cambiato)

    # Sfoglia file
    def on_sfoglia():
        path, _ = QFileDialog.getOpenFileName(
            dialog,
            "Seleziona database esistente",
            "",
            "Database SQLite (*.db);;Tutti i file (*)"
        )
        if path:
            campo_path.setText(path)

    btn_sfoglia.clicked.connect(on_sfoglia)

    # Separatore finale
    sep2 = QFrame()
    sep2.setFrameShape(QFrame.HLine)
    sep2.setFrameShadow(QFrame.Sunken)
    layout.addWidget(sep2)

    # Bottoni
    btn_layout = QHBoxLayout()
    btn_layout.addStretch()
    btn_conferma = QPushButton("Conferma")
    btn_conferma.setDefault(True)
    btn_conferma.setMinimumWidth(110)
    btn_layout.addWidget(btn_conferma)
    layout.addLayout(btn_layout)

    risultato = {"ok": False}

    def on_conferma():
        if radio_rete.isChecked():
            path_scelto = campo_path.text().strip()
            if not path_scelto:
                QMessageBox.warning(dialog, "Percorso mancante",
                                    "Inserisci il percorso del database esistente.")
                return
            # Controlla se il file è raggiungibile
            if not os.path.exists(path_scelto):
                risposta = QMessageBox.question(
                    dialog,
                    "File non trovato",
                    f"Il file '{path_scelto}' non è stato trovato.\n\n"
                    "Potrebbe essere un percorso di rete non ancora accessibile, "
                    "o il database non esiste ancora in quella posizione.\n\n"
                    "Vuoi usare comunque questo percorso?\n"
                    "(Il database verrà creato lì al primo avvio.)",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if risposta != QMessageBox.Yes:
                    return
            # Salva config.json
            config = {"db_path": path_scelto}
            config_path = os.path.join(base_dir, "config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            # Se esiste una cartella data/ locale con un db, avvisa l'utente
            db_locale = os.path.join(base_dir, "data", "materiali.db")
            if os.path.exists(db_locale):
                QMessageBox.information(
                    dialog,
                    "Database locale esistente",
                    f"È stato trovato un database locale in:\n{db_locale}\n\n"
                    f"L'applicazione userà il percorso di rete configurato.\n"
                    f"Il database locale NON verrà eliminato automaticamente: "
                    f"puoi farlo manualmente se non ti serve più."
                )
        # Locale: nessun config.json → comportamento default
        risultato["ok"] = True
        dialog.accept()

    btn_conferma.clicked.connect(on_conferma)

    dialog.exec_()
    return risultato["ok"]


def main():
    """Funzione principale dell'applicazione"""
    setup_logger()

    # Crea l'applicazione Qt
    app = QApplication(sys.argv)

    # Imposta le proprietà dell'applicazione
    app.setApplicationName("Gestione Preventivi")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("RCS")

    base_dir = _get_base_dir()

    # Primo avvio: nessun DB e nessun config → chiedi configurazione
    if _is_primo_avvio(base_dir):
        configurato = _mostra_dialogo_primo_avvio(base_dir)
        if not configurato:
            sys.exit(0)

    try:
        # Crea e mostra la finestra principale massimizzata
        window = MainWindow()
        window.setWindowState(Qt.WindowMaximized)
        window.show()

        # Avvia il loop degli eventi
        sys.exit(app.exec_())

    except Exception as e:
        # Gestione errori di avvio
        QMessageBox.critical(None, "Errore Critico",
                           f"Errore durante l'avvio dell'applicazione:\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
