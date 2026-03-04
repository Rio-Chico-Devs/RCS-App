#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
TelaPreviewWidget - Widget di anteprima CAD per la tela tagliata
Uso riservato esclusivamente a RCS

Disegna la forma della tela (rettangolo per cilindrica, trapezio per conica)
con le quote dei diametri e delle lunghezze per ogni sezione.
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QPolygonF, QBrush, QPainterPath


class TelaPreviewWidget(QWidget):
    """Widget che disegna l'anteprima CAD della tela tagliata."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 200)
        self._sezioni = []       # [{lunghezza, d_inizio, d_fine}, ...]
        self._is_conica = False
        self._diametro = 0.0     # Per cilindrica
        self._lunghezza = 0.0    # Per cilindrica
        self._sviluppo = 0.0     # Per cilindrica
        self._scarto = 0.0       # Scarto calcolato (mm²)

        # Colori stile CAD
        self._bg_color = QColor(255, 255, 255)
        self._tela_fill = QColor(200, 220, 240, 80)
        self._tela_border = QColor(44, 62, 80)
        self._scarto_fill = QColor(255, 200, 200, 60)
        self._quota_color = QColor(100, 100, 100)
        self._dim_color = QColor(44, 62, 80)
        self._grid_color = QColor(230, 235, 240)

    # ── API pubblica ──────────────────────────────────────────────

    def aggiorna_cilindrica(self, diametro, lunghezza, sviluppo):
        """Aggiorna con dati cilindrica (rettangolo semplice)."""
        self._is_conica = False
        self._diametro = diametro
        self._lunghezza = lunghezza
        self._sviluppo = sviluppo
        self._sezioni = []
        self._scarto = 0.0
        self.update()

    def aggiorna_conica(self, sezioni):
        """Aggiorna con sezioni coniche e calcola scarto.
        sezioni: [{lunghezza, d_inizio, d_fine}, ...]
        Restituisce lo scarto in mm².
        """
        self._is_conica = True
        self._sezioni = sezioni or []
        self._scarto = self._calcola_scarto()
        self.update()
        return self._scarto

    def get_scarto_mm2(self):
        """Restituisce lo scarto attuale in mm²."""
        return self._scarto

    # ── Calcolo scarto ────────────────────────────────────────────

    def _calcola_scarto(self):
        """Calcola lo scarto: area rettangolare - area trapezoidale.
        La tela viene tagliata da un rettangolo largo quanto lo sviluppo
        massimo (il diametro più grande * pi) e lungo quanto la somma
        delle lunghezze. Lo scarto è la differenza."""
        if not self._sezioni:
            return 0.0

        # Calcola sviluppo per ogni sezione (basato solo sul diametro, senza spessore)
        sviluppi_inizio = []
        sviluppi_fine = []
        lunghezze = []

        for sez in self._sezioni:
            d_ini = sez.get('d_inizio', 0)
            d_fin = sez.get('d_fine', 0)
            l_sez = sez.get('lunghezza', 0)
            # Sviluppo = diametro * pi (solo geometrico, senza spessore tela)
            sv_ini = d_ini * 3.14
            sv_fin = d_fin * 3.14
            sviluppi_inizio.append(sv_ini)
            sviluppi_fine.append(sv_fin)
            lunghezze.append(l_sez)

        if not lunghezze:
            return 0.0

        # Lo sviluppo massimo determina la larghezza del rettangolo di taglio
        tutti_sviluppi = sviluppi_inizio + sviluppi_fine
        sviluppo_max = max(tutti_sviluppi) if tutti_sviluppi else 0
        lunghezza_totale = sum(lunghezze)

        if sviluppo_max <= 0 or lunghezza_totale <= 0:
            return 0.0

        # Area rettangolare (il foglio da cui tagliamo)
        area_rettangolo = lunghezza_totale * sviluppo_max

        # Area trapezoidale effettiva (la tela che usiamo)
        area_tela = 0.0
        for i, sez in enumerate(self._sezioni):
            l_sez = lunghezze[i]
            sv_ini = sviluppi_inizio[i]
            sv_fin = sviluppi_fine[i]
            # Area del trapezio: (base1 + base2) / 2 * altezza
            area_tela += (sv_ini + sv_fin) / 2.0 * l_sez

        scarto = area_rettangolo - area_tela
        return max(scarto, 0.0)

    # ── Disegno ───────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self._bg_color)

        if self._is_conica and self._sezioni:
            self._disegna_conica(painter)
        elif not self._is_conica and self._lunghezza > 0 and self._sviluppo > 0:
            self._disegna_cilindrica(painter)
        else:
            self._disegna_placeholder(painter)

        painter.end()

    def _disegna_placeholder(self, painter):
        """Disegna un messaggio placeholder."""
        painter.setPen(QColor(160, 174, 192))
        font = QFont("system-ui", 12)
        font.setItalic(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "Inserisci i parametri per\nvisualizzare l'anteprima tela")

    def _disegna_cilindrica(self, painter):
        """Disegna un rettangolo per tubo cilindrico."""
        w = self.width()
        h = self.height()
        margine = 60
        quota_spazio = 40  # Spazio per le quote

        # Area disponibile per il disegno
        draw_x = margine
        draw_y = margine + quota_spazio
        draw_w = w - 2 * margine
        draw_h = h - 2 * margine - 2 * quota_spazio

        if draw_w <= 0 or draw_h <= 0:
            return

        # Disegna il rettangolo della tela
        pen = QPen(self._tela_border, 2)
        painter.setPen(pen)
        painter.setBrush(QBrush(self._tela_fill))
        painter.drawRect(QRectF(draw_x, draw_y, draw_w, draw_h))

        # Quotatura - Font
        font_quota = QFont("system-ui", 10)
        font_quota.setBold(True)
        painter.setFont(font_quota)
        painter.setPen(QPen(self._dim_color, 1))

        # Quota superiore: sviluppo (larghezza tela)
        sv_text = f"Sviluppo: {self._sviluppo:.1f} mm"
        painter.drawText(QRectF(draw_x, draw_y - 30, draw_w, 25),
                         Qt.AlignCenter, sv_text)

        # Frecce quota superiore
        self._disegna_quota_orizzontale(painter, draw_x, draw_x + draw_w, draw_y - 12)

        # Quota laterale: lunghezza
        painter.save()
        painter.translate(draw_x - 15, draw_y + draw_h / 2)
        painter.rotate(-90)
        l_text = f"{self._lunghezza:.0f} mm"
        painter.drawText(QRectF(-50, -15, 100, 25), Qt.AlignCenter, l_text)
        painter.restore()

        # Frecce quota laterale
        self._disegna_quota_verticale(painter, draw_y, draw_y + draw_h, draw_x - 8)

        # Diametro al centro
        font_diam = QFont("system-ui", 9)
        painter.setFont(font_diam)
        painter.setPen(QPen(self._quota_color, 1))
        d_text = f"Ø {self._diametro:.1f}"
        painter.drawText(QRectF(draw_x, draw_y, draw_w, draw_h),
                         Qt.AlignCenter, d_text)

    def _disegna_conica(self, painter):
        """Disegna la tela conica con le sezioni trapezoidali."""
        w = self.width()
        h = self.height()
        margine_sx = 55
        margine_dx = 30
        margine_top = 50
        margine_bot = 55

        draw_w = w - margine_sx - margine_dx
        draw_h = h - margine_top - margine_bot

        if draw_w <= 0 or draw_h <= 0 or not self._sezioni:
            return

        # Calcola sviluppi per ogni punto (basato sul diametro)
        punti_sviluppo = []  # (posizione_x_mm, sviluppo)
        diametri = []        # diametro in ogni punto
        pos = 0

        for i, sez in enumerate(self._sezioni):
            d_ini = sez.get('d_inizio', 0)
            d_fin = sez.get('d_fine', 0)
            l_sez = sez.get('lunghezza', 0)

            if i == 0:
                punti_sviluppo.append((pos, d_ini * 3.14))
                diametri.append(d_ini)
            pos += l_sez
            punti_sviluppo.append((pos, d_fin * 3.14))
            diametri.append(d_fin)

        lunghezza_totale = sum(s.get('lunghezza', 0) for s in self._sezioni)
        tutti_sviluppi = [p[1] for p in punti_sviluppo]
        sviluppo_max = max(tutti_sviluppi) if tutti_sviluppi else 0
        sviluppo_min = min(tutti_sviluppi) if tutti_sviluppi else 0

        if lunghezza_totale <= 0 or sviluppo_max <= 0:
            self._disegna_placeholder(painter)
            return

        # Fattori di scala
        scala_x = draw_w / lunghezza_totale
        scala_y = draw_h / sviluppo_max  # Scala in base allo sviluppo max

        # Centro verticale per la tela
        centro_y = margine_top + draw_h / 2

        # --- Disegna il rettangolo di taglio (scarto) ---
        rect_top = centro_y - (sviluppo_max * scala_y) / 2
        rect_bot = centro_y + (sviluppo_max * scala_y) / 2
        rect_left = margine_sx
        rect_right = margine_sx + lunghezza_totale * scala_x

        # Rettangolo scarto (tratteggiato)
        if sviluppo_max != sviluppo_min:
            pen_scarto = QPen(QColor(200, 100, 100, 120), 1, Qt.DashLine)
            painter.setPen(pen_scarto)
            painter.setBrush(QBrush(self._scarto_fill))
            painter.drawRect(QRectF(rect_left, rect_top, rect_right - rect_left, rect_bot - rect_top))

        # --- Disegna la tela (poligono trapezoidale) ---
        polygon_top = []  # Bordo superiore
        polygon_bot = []  # Bordo inferiore

        for pos_mm, sv in punti_sviluppo:
            x = margine_sx + pos_mm * scala_x
            half_sv = (sv * scala_y) / 2
            polygon_top.append(QPointF(x, centro_y - half_sv))
            polygon_bot.append(QPointF(x, centro_y + half_sv))

        # Costruisci poligono chiuso
        poly_points = polygon_top + list(reversed(polygon_bot))
        polygon = QPolygonF(poly_points)

        pen_tela = QPen(self._tela_border, 2)
        painter.setPen(pen_tela)
        painter.setBrush(QBrush(self._tela_fill))
        painter.drawPolygon(polygon)

        # --- Linee verticali di separazione sezioni ---
        pen_sep = QPen(QColor(150, 160, 175), 1, Qt.DashDotLine)
        font_quota = QFont("system-ui", 8)
        painter.setFont(font_quota)

        pos_mm = 0
        for i, sez in enumerate(self._sezioni):
            l_sez = sez.get('lunghezza', 0)
            d_ini = sez.get('d_inizio', 0)
            d_fin = sez.get('d_fine', 0)

            x_ini = margine_sx + pos_mm * scala_x
            x_fin = margine_sx + (pos_mm + l_sez) * scala_x

            # Linea verticale di inizio sezione
            sv_ini = d_ini * 3.14
            half_ini = (sv_ini * scala_y) / 2
            painter.setPen(pen_sep)
            painter.drawLine(QPointF(x_ini, centro_y - half_ini),
                             QPointF(x_ini, centro_y + half_ini))

            # Se ultima sezione, disegna anche la linea di fine
            if i == len(self._sezioni) - 1:
                sv_fin = d_fin * 3.14
                half_fin = (sv_fin * scala_y) / 2
                painter.drawLine(QPointF(x_fin, centro_y - half_fin),
                                 QPointF(x_fin, centro_y + half_fin))

            # --- Quote diametri (sopra) ---
            painter.setPen(QPen(self._dim_color, 1))
            font_diam = QFont("system-ui", 8)
            font_diam.setBold(True)
            painter.setFont(font_diam)

            # Diametro inizio (solo per la prima sezione)
            if i == 0:
                sv_ini_draw = d_ini * 3.14
                y_top = centro_y - (sv_ini_draw * scala_y) / 2
                text_ini = f"Ø{d_ini:.1f}"
                painter.drawText(QRectF(x_ini - 30, y_top - 18, 60, 16),
                                 Qt.AlignCenter, text_ini)

            # Diametro fine
            sv_fin_draw = d_fin * 3.14
            y_top_fin = centro_y - (sv_fin_draw * scala_y) / 2
            text_fin = f"Ø{d_fin:.1f}"
            painter.drawText(QRectF(x_fin - 30, y_top_fin - 18, 60, 16),
                             Qt.AlignCenter, text_fin)

            # --- Quota lunghezza sezione (sotto) ---
            font_lung = QFont("system-ui", 8)
            painter.setFont(font_lung)
            painter.setPen(QPen(self._quota_color, 1))

            # Sviluppo alla fine della sezione per trovare il punto più basso
            y_bot_max = centro_y + (sviluppo_max * scala_y) / 2
            lung_text = f"{l_sez} mm"
            mid_x = (x_ini + x_fin) / 2
            painter.drawText(QRectF(mid_x - 35, y_bot_max + 8, 70, 16),
                             Qt.AlignCenter, lung_text)

            # Frecce quota lunghezza
            self._disegna_quota_orizzontale(painter, x_ini, x_fin, y_bot_max + 5)

            pos_mm += l_sez

        # --- Etichetta scarto ---
        if self._scarto > 0:
            font_scarto = QFont("system-ui", 9)
            font_scarto.setItalic(True)
            painter.setFont(font_scarto)
            painter.setPen(QPen(QColor(200, 80, 80), 1))

            scarto_m2 = self._scarto / 1000000.0
            scarto_text = f"Scarto: {self._scarto:.0f} mm² ({scarto_m2:.6f} m²)"
            painter.drawText(QRectF(margine_sx, h - 30, draw_w, 20),
                             Qt.AlignRight, scarto_text)

        # --- Lunghezza totale (sotto le quote sezioni) ---
        if len(self._sezioni) > 1:
            font_tot = QFont("system-ui", 9)
            font_tot.setBold(True)
            painter.setFont(font_tot)
            painter.setPen(QPen(self._dim_color, 1))

            y_bot_max = centro_y + (sviluppo_max * scala_y) / 2
            tot_text = f"Lunghezza totale: {lunghezza_totale:.0f} mm"
            painter.drawText(QRectF(margine_sx, y_bot_max + 24, draw_w, 18),
                             Qt.AlignCenter, tot_text)

    # ── Helpers per quotature ─────────────────────────────────────

    def _disegna_quota_orizzontale(self, painter, x1, x2, y):
        """Disegna una quota orizzontale con frecce."""
        if abs(x2 - x1) < 10:
            return
        pen = QPen(self._quota_color, 1)
        painter.setPen(pen)
        # Linea
        painter.drawLine(QPointF(x1, y), QPointF(x2, y))
        # Freccia sinistra
        painter.drawLine(QPointF(x1, y), QPointF(x1 + 5, y - 3))
        painter.drawLine(QPointF(x1, y), QPointF(x1 + 5, y + 3))
        # Freccia destra
        painter.drawLine(QPointF(x2, y), QPointF(x2 - 5, y - 3))
        painter.drawLine(QPointF(x2, y), QPointF(x2 - 5, y + 3))

    def _disegna_quota_verticale(self, painter, y1, y2, x):
        """Disegna una quota verticale con frecce."""
        if abs(y2 - y1) < 10:
            return
        pen = QPen(self._quota_color, 1)
        painter.setPen(pen)
        # Linea
        painter.drawLine(QPointF(x, y1), QPointF(x, y2))
        # Freccia su
        painter.drawLine(QPointF(x, y1), QPointF(x - 3, y1 + 5))
        painter.drawLine(QPointF(x, y1), QPointF(x + 3, y1 + 5))
        # Freccia giù
        painter.drawLine(QPointF(x, y2), QPointF(x - 3, y2 - 5))
        painter.drawLine(QPointF(x, y2), QPointF(x + 3, y2 - 5))
