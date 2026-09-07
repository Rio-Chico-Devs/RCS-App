#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del registro delle schermate di preventivo aperte.

È la correzione del difetto per cui, aprendo un secondo preventivo, il primo
veniva distrutto insieme al lavoro non salvato. Qui si verifica che le
schermate restino tutte in vita e che quelle chiuse vengano tolte
dall'elenco (altrimenti resterebbero a occupare memoria).

Si usano finte finestre: quello che conta è la logica del registro, non Qt.

Esegui con:  python -m unittest tests.test_finestre_preventivo -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui import finestre_preventivo as reg


class FintaFinestra:
    """Imita una schermata di preventivo per quel poco che serve al registro."""

    def __init__(self, cliente="", visibile=True):
        self.cliente = cliente
        self.visibile = visibile
        self.prezzi_aggiornati = 0

    def isVisible(self):
        return self.visibile

    def get_dati_cliente(self):
        return {"nome_cliente": self.cliente}

    def aggiorna_prezzi_materiali(self):
        self.prezzi_aggiornati += 1


class FinestraDistrutta:
    """Imita una finestra il cui oggetto Qt è già stato eliminato: qualunque
    chiamata solleva RuntimeError, come fa PyQt."""

    def isVisible(self):
        raise RuntimeError("wrapped C/C++ object has been deleted")

    def get_dati_cliente(self):
        raise RuntimeError("wrapped C/C++ object has been deleted")

    def aggiorna_prezzi_materiali(self):
        raise RuntimeError("wrapped C/C++ object has been deleted")


class BaseRegistro(unittest.TestCase):
    def setUp(self):
        reg._aperte.clear()

    def tearDown(self):
        reg._aperte.clear()


class TestRegistro(BaseRegistro):

    def test_registro_vuoto(self):
        self.assertEqual(reg.aperte(), [])
        self.assertEqual(reg.quante(), 0)
        self.assertIsNone(reg.piu_recente())

    def test_piu_schermate_restano_tutte_aperte(self):
        """Il punto di tutta la correzione: aprendone una seconda, la prima
        NON deve sparire."""
        prima = reg.registra(FintaFinestra("Bianchi SpA"))
        seconda = reg.registra(FintaFinestra("Verdi Srl"))
        terza = reg.registra(FintaFinestra("Neri & Co"))

        self.assertEqual(reg.quante(), 3)
        self.assertIn(prima, reg.aperte())
        self.assertIn(seconda, reg.aperte())
        self.assertIn(terza, reg.aperte())

    def test_la_piu_recente_e_lultima_aperta(self):
        reg.registra(FintaFinestra("Prima"))
        ultima = reg.registra(FintaFinestra("Ultima"))
        self.assertIs(reg.piu_recente(), ultima)

    def test_registrare_due_volte_non_duplica(self):
        finestra = FintaFinestra("Bianchi")
        reg.registra(finestra)
        reg.registra(finestra)
        self.assertEqual(reg.quante(), 1)

    def test_le_schermate_chiuse_vengono_tolte(self):
        """Ottimizzazione delle risorse: chi è chiuso non resta in memoria."""
        aperta = reg.registra(FintaFinestra("Aperta"))
        chiusa = reg.registra(FintaFinestra("Chiusa"))
        chiusa.visibile = False

        self.assertEqual(reg.quante(), 1)
        self.assertIs(reg.aperte()[0], aperta)

    def test_dimentica_esplicito(self):
        prima = reg.registra(FintaFinestra("Prima"))
        seconda = reg.registra(FintaFinestra("Seconda"))
        reg.dimentica(prima)
        self.assertEqual(reg.aperte(), [seconda])

    def test_dimenticare_qualcosa_di_sconosciuto_non_rompe(self):
        reg.registra(FintaFinestra("Prima"))
        reg.dimentica(FintaFinestra("Mai registrata"))
        self.assertEqual(reg.quante(), 1)

    def test_finestra_distrutta_da_qt_non_fa_esplodere_nulla(self):
        """PyQt solleva RuntimeError sugli oggetti già eliminati: il registro
        deve limitarsi a toglierli."""
        viva = reg.registra(FintaFinestra("Viva"))
        reg.registra(FinestraDistrutta())

        self.assertEqual(reg.quante(), 1)
        self.assertIs(reg.aperte()[0], viva)


class TestDescrizione(BaseRegistro):

    def test_con_cliente(self):
        self.assertEqual(reg.descrivi(FintaFinestra("Bianchi SpA")), "Bianchi SpA")

    def test_senza_cliente(self):
        self.assertEqual(reg.descrivi(FintaFinestra("")), "cliente non ancora indicato")

    def test_finestra_distrutta(self):
        self.assertEqual(reg.descrivi(FinestraDistrutta()), "cliente non ancora indicato")


class TestAggiornamentoPrezzi(BaseRegistro):

    def test_aggiorna_tutte_le_schermate(self):
        """Prima veniva aggiornata solo l'ultima aperta."""
        finestre = [reg.registra(FintaFinestra(f"Cliente {i}")) for i in range(3)]
        reg.aggiorna_prezzi_ovunque()
        for f in finestre:
            self.assertEqual(f.prezzi_aggiornati, 1)

    def test_una_finestra_problematica_non_blocca_le_altre(self):
        buona1 = reg.registra(FintaFinestra("Buona 1"))
        reg.registra(FinestraDistrutta())
        buona2 = reg.registra(FintaFinestra("Buona 2"))

        reg.aggiorna_prezzi_ovunque()

        self.assertEqual(buona1.prezzi_aggiornati, 1)
        self.assertEqual(buona2.prezzi_aggiornati, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
