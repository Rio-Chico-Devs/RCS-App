#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Settings Window - Finestra Impostazioni
Uso riservato esclusivamente a RCS
"""

# type: ignore
# pyright: reportUnknownParameterType=false, reportMissingParameterType=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportAttributeAccessIssue=false

import os
import sys
import json

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QFileDialog, QFrame,
                             QMessageBox, QGroupBox, QRadioButton, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _leggi_config():
    """Ritorna il contenuto di config.json o {} se non esiste."""
    config_path = os.path.join(_get_base_dir(), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _salva_config(cfg: dict):
    config_path = os.path.join(_get_base_dir(), "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def _percorso_db_corrente():
    """Ritorna il percorso DB attualmente configurato (da config.json o default locale)."""
    cfg = _leggi_config()
    if cfg.get("db_path"):
        return cfg["db_path"]
    base_dir = _get_base_dir()
    return os.path.join(base_dir, "data", "materiali.db")


class SettingsWindow(QDialog):
    """
    Finestra Impostazioni - permette di cambiare il database usato dall'applicazione.
    Dopo il salvataggio, il MainWindow reinizializza il DatabaseManager.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Impostazioni - RCS Preventivi")
        self.setMinimumWidth(580)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._percorso_salvato = None   # Impostato a None = locale, stringa = rete

        self._build_ui()
        self._carica_impostazioni_correnti()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(28, 24, 28, 24)

        # Titolo
        titolo = QLabel("Impostazioni")
        font_titolo = QFont()
        font_titolo.setPointSize(14)
        font_titolo.setBold(True)
        titolo.setFont(font_titolo)
        titolo.setStyleSheet("color: #2d3748;")
        layout.addWidget(titolo)

        # --- Sezione Database ---
        db_group = QGroupBox("Database")
        db_group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: 600;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 4px 6px;
                background-color: #ffffff;
            }
        """)
        db_layout = QVBoxLayout(db_group)
        db_layout.setContentsMargins(18, 18, 18, 18)
        db_layout.setSpacing(12)

        # Percorso corrente (info)
        lbl_corrente = QLabel("Percorso database attuale:")
        lbl_corrente.setStyleSheet("color: #718096; font-size: 12px;")
        db_layout.addWidget(lbl_corrente)

        self.lbl_percorso_corrente = QLabel()
        self.lbl_percorso_corrente.setWordWrap(True)
        self.lbl_percorso_corrente.setStyleSheet("""
            color: #2d3748;
            font-size: 12px;
            background-color: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            padding: 6px 10px;
        """)
        db_layout.addWidget(self.lbl_percorso_corrente)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #e2e8f0;")
        db_layout.addWidget(sep)

        # Opzioni
        lbl_modifica = QLabel("Scegli il database da usare:")
        lbl_modifica.setStyleSheet("color: #4a5568; font-size: 13px; font-weight: 600;")
        db_layout.addWidget(lbl_modifica)

        # Radio: locale
        self.radio_locale = QRadioButton("Usa database locale (cartella dell'applicazione)")
        self.radio_locale.setStyleSheet("font-size: 13px; color: #2d3748;")
        db_layout.addWidget(self.radio_locale)

        desc_locale = QLabel("Il database si trova nella cartella data/ dell'applicazione.\n"
                              "Adatto se usi il programma su un solo computer.")
        desc_locale.setStyleSheet("color: #a0aec0; font-size: 11px; margin-left: 22px;")
        desc_locale.setWordWrap(True)
        db_layout.addWidget(desc_locale)

        db_layout.addSpacing(4)

        # Radio: rete / personalizzato
        self.radio_rete = QRadioButton("Usa un database specifico (cartella di rete o percorso personalizzato)")
        self.radio_rete.setStyleSheet("font-size: 13px; color: #2d3748;")
        db_layout.addWidget(self.radio_rete)

        desc_rete = QLabel("Punta a un file .db su un'altra posizione (cartella condivisa in rete,\n"
                            "chiavetta USB, altro PC, ecc.). Tutti i PC che usano lo stesso percorso\n"
                            "condividono gli stessi dati.")
        desc_rete.setStyleSheet("color: #a0aec0; font-size: 11px; margin-left: 22px;")
        desc_rete.setWordWrap(True)
        db_layout.addWidget(desc_rete)

        # Campo percorso + sfoglia
        self.frame_percorso = QFrame()
        self.frame_percorso.setEnabled(False)
        layout_percorso = QHBoxLayout(self.frame_percorso)
        layout_percorso.setContentsMargins(22, 4, 0, 0)
        layout_percorso.setSpacing(6)

        self.campo_path = QLineEdit()
        self.campo_path.setPlaceholderText(
            r"Es: \\NOMEPC\RCS\materiali.db  oppure  Z:\RCS\materiali.db"
        )
        self.campo_path.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
                color: #2d3748;
                background-color: #ffffff;
            }
            QLineEdit:disabled {
                background-color: #f7fafc;
                color: #a0aec0;
            }
        """)
        layout_percorso.addWidget(self.campo_path)

        self.btn_sfoglia = QPushButton("Sfoglia...")
        self.btn_sfoglia.setFixedWidth(90)
        self.btn_sfoglia.setStyleSheet("""
            QPushButton {
                background-color: #edf2f7;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #e2e8f0; }
            QPushButton:disabled { color: #a0aec0; }
        """)
        self.btn_sfoglia.clicked.connect(self._on_sfoglia)
        layout_percorso.addWidget(self.btn_sfoglia)

        db_layout.addWidget(self.frame_percorso)

        # Nota rete
        self.nota_rete = QLabel(
            "Il percorso deve essere accessibile da questo PC.\n"
            "Se il file non esiste ancora verra' creato automaticamente al salvataggio."
        )
        self.nota_rete.setStyleSheet("color: #a0aec0; font-size: 11px; margin-left: 22px;")
        self.nota_rete.setWordWrap(True)
        self.nota_rete.setVisible(False)
        db_layout.addWidget(self.nota_rete)

        # Connessioni radio
        self.radio_locale.toggled.connect(self._on_radio_cambiato)
        self.radio_rete.toggled.connect(self._on_radio_cambiato)

        layout.addWidget(db_group)

        # --- Bottoni OK / Annulla ---
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFrameShadow(QFrame.Sunken)
        sep2.setStyleSheet("color: #e2e8f0;")
        layout.addWidget(sep2)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_annulla = QPushButton("Annulla")
        btn_annulla.setMinimumWidth(100)
        btn_annulla.setStyleSheet("""
            QPushButton {
                background-color: #f7fafc;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #edf2f7; }
        """)
        btn_annulla.clicked.connect(self.reject)
        btn_row.addWidget(btn_annulla)

        btn_row.addSpacing(8)

        self.btn_salva = QPushButton("Salva e Riavvia")
        self.btn_salva.setDefault(True)
        self.btn_salva.setMinimumWidth(130)
        self.btn_salva.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #2d3748; }
            QPushButton:pressed { background-color: #1a202c; }
        """)
        self.btn_salva.clicked.connect(self._on_salva)
        btn_row.addWidget(self.btn_salva)

        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Logica
    # ------------------------------------------------------------------

    def _carica_impostazioni_correnti(self):
        """Popola la UI con i valori attuali letti da config.json."""
        cfg = _leggi_config()
        percorso_attuale = _percorso_db_corrente()
        self.lbl_percorso_corrente.setText(percorso_attuale)

        if cfg.get("db_path"):
            self.radio_rete.setChecked(True)
            self.campo_path.setText(cfg["db_path"])
        else:
            self.radio_locale.setChecked(True)

    def _on_radio_cambiato(self):
        usa_rete = self.radio_rete.isChecked()
        self.frame_percorso.setEnabled(usa_rete)
        self.nota_rete.setVisible(usa_rete)

    def _on_sfoglia(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona file database",
            "",
            "Database SQLite (*.db);;Tutti i file (*)"
        )
        if path:
            self.campo_path.setText(path)

    def _on_salva(self):
        base_dir = _get_base_dir()

        if self.radio_locale.isChecked():
            # Rimuovi db_path da config.json (o elimina il file se è vuoto)
            cfg = _leggi_config()
            if "db_path" in cfg:
                del cfg["db_path"]
            if cfg:
                _salva_config(cfg)
            else:
                config_path = os.path.join(base_dir, "config.json")
                if os.path.exists(config_path):
                    os.remove(config_path)
            self._percorso_salvato = None   # segnale: usa locale
        else:
            path_scelto = self.campo_path.text().strip()
            if not path_scelto:
                QMessageBox.warning(self, "Percorso mancante",
                                    "Inserisci il percorso del file database.")
                return

            if not os.path.exists(path_scelto):
                risposta = QMessageBox.question(
                    self,
                    "File non trovato",
                    f"Il file '{path_scelto}' non esiste.\n\n"
                    "Potrebbe essere un percorso di rete non ancora raggiungibile, "
                    "o il database non è ancora stato creato in quella posizione.\n\n"
                    "Vuoi usare comunque questo percorso?\n"
                    "(Il database verrà creato automaticamente.)",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if risposta != QMessageBox.Yes:
                    return

            cfg = _leggi_config()
            cfg["db_path"] = path_scelto
            _salva_config(cfg)
            self._percorso_salvato = path_scelto

        QMessageBox.information(
            self,
            "Impostazioni salvate",
            "Le impostazioni sono state salvate.\n\n"
            "L'applicazione verrà riavviata per applicare le modifiche."
        )
        self.accept()

    # ------------------------------------------------------------------
    # Accessori pubblici
    # ------------------------------------------------------------------

    def nuovo_percorso_db(self):
        """
        Ritorna il nuovo percorso DB scelto dall'utente, oppure None se
        ha scelto il database locale (default).
        Usato dal chiamante per reinizializzare il DatabaseManager.
        """
        return self._percorso_salvato
