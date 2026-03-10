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

        # Trasformazioni disegno
        self._rotation = 0       # Gradi: 0, 90, 180, 270
        self._flip_h = False     # Capovolgi orizzontalmente
        self._flip_v = False     # Capovolgi verticalmente

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

    def rotate_left(self):
        """Ruota il disegno di 90° in senso antiorario."""
        self._rotation = (self._rotation - 90) % 360
        self.update()

    def rotate_right(self):
        """Ruota il disegno di 90° in senso orario."""
        self._rotation = (self._rotation + 90) % 360
        self.update()

    def flip_horizontal(self):
        """Capovolge il disegno orizzontalmente (specchio sinistra-destra)."""
        self._flip_h = not self._flip_h
        self.update()

    def flip_vertical(self):
        """Capovolge il disegno verticalmente (specchio sopra-sotto)."""
        self._flip_v = not self._flip_v
        self.update()

    def get_orientamento(self):
        """Restituisce il dizionario orientamento corrente."""
        return {'rotation': self._rotation, 'flip_h': self._flip_h, 'flip_v': self._flip_v}

    def set_orientamento(self, orientamento):
        """Imposta orientamento da dizionario (rotation, flip_h, flip_v)."""
        if not orientamento:
            return
        self._rotation = orientamento.get('rotation', 0)
        self._flip_h = orientamento.get('flip_h', False)
        self._flip_v = orientamento.get('flip_v', False)
        self.update()

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

        # Applica trasformazioni globali (rotate + flip) centrate sul widget
        has_transform = self._rotation != 0 or self._flip_h or self._flip_v
        if has_transform:
            painter.save()
            cx, cy = self.width() / 2.0, self.height() / 2.0
            painter.translate(cx, cy)
            if self._flip_h:
                painter.scale(-1, 1)
            if self._flip_v:
                painter.scale(1, -1)
            painter.rotate(self._rotation)
            painter.translate(-cx, -cy)

        if self._is_conica and self._sezioni:
            self._disegna_conica(painter)
        elif not self._is_conica and self._lunghezza > 0 and self._sviluppo > 0:
            self._disegna_cilindrica(painter)
        else:
            self._disegna_placeholder(painter)

        if has_transform:
            painter.restore()

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
        avail_w = w - 2 * margine
        avail_h = h - 2 * margine - 2 * quota_spazio

        if avail_w <= 0 or avail_h <= 0:
            return

        # Scala uniforme per preservare l'aspect ratio reale (sviluppo x lunghezza)
        scala = min(avail_w / self._sviluppo, avail_h / self._lunghezza)
        draw_w = self._sviluppo * scala
        draw_h = self._lunghezza * scala

        # Centra il rettangolo nell'area disponibile
        draw_x = margine + (avail_w - draw_w) / 2
        draw_y = margine + quota_spazio + (avail_h - draw_h) / 2

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
        """Disegna la tela conica come rettangolo di taglio (come viene realmente tagliata).
        Il rettangolo rappresenta il foglio di tela tagliato (sviluppo_max x lunghezza_totale).
        Il profilo conico è disegnato come linea di riferimento all'interno.
        Lo scarto (triangolo) è evidenziato tra il rettangolo e il profilo conico.
        """
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

        # Scala uniforme per preservare l'aspect ratio reale
        scala = min(draw_w / lunghezza_totale, draw_h / sviluppo_max)
        scala_x = scala
        scala_y = scala

        # Centra il rettangolo nell'area disponibile
        rect_w_px = lunghezza_totale * scala
        rect_h_px = sviluppo_max * scala
        rect_left = margine_sx + (draw_w - rect_w_px) / 2
        rect_right = rect_left + rect_w_px

        # Il rettangolo di taglio è allineato in basso (bordo inferiore comune)
        rect_h = rect_h_px
        rect_top = margine_top + (draw_h - rect_h)
        rect_bot = rect_top + rect_h

        # --- 1. Disegna il rettangolo di taglio (la tela reale) ---
        pen_tela = QPen(self._tela_border, 2)
        painter.setPen(pen_tela)
        painter.setBrush(QBrush(self._tela_fill))
        painter.drawRect(QRectF(rect_left, rect_top, rect_right - rect_left, rect_bot - rect_top))

        # --- 2. Disegna lo scarto (area tra rettangolo e profilo conico) ---
        # Il profilo conico ha bordo inferiore allineato al rettangolo,
        # bordo superiore variabile in base allo sviluppo di ogni punto.
        if sviluppo_max != sviluppo_min:
            # Costruisci il poligono dello scarto:
            # - bordo superiore del rettangolo (da sinistra a destra)
            # - bordo superiore del profilo conico (da destra a sinistra)
            scarto_poly = []

            # Bordo superiore rettangolo: angolo top-left -> top-right
            scarto_poly.append(QPointF(rect_left, rect_top))
            scarto_poly.append(QPointF(rect_right, rect_top))

            # Bordo superiore profilo conico: da destra a sinistra
            for pos_mm, sv in reversed(punti_sviluppo):
                x = margine_sx + pos_mm * scala_x
                sv_h = sv * scala_y
                y_top_cono = rect_bot - sv_h  # Allineato in basso
                scarto_poly.append(QPointF(x, y_top_cono))

            scarto_polygon = QPolygonF(scarto_poly)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 150, 150, 100)))
            painter.drawPolygon(scarto_polygon)

            # Etichetta "SCARTO" nell'area dello scarto
            if self._scarto > 0:
                # Posiziona l'etichetta verso il lato dove lo scarto è più grande
                # (dove lo sviluppo è minore = dove il bordo conico è più lontano dal rettangolo)
                min_idx = tutti_sviluppi.index(sviluppo_min)
                if min_idx < len(punti_sviluppo):
                    pos_min_mm, sv_min = punti_sviluppo[min_idx]
                    x_label = margine_sx + pos_min_mm * scala_x
                    y_label_top = rect_top
                    y_label_bot = rect_bot - sv_min * scala_y
                    y_label = (y_label_top + y_label_bot) / 2

                    font_sc = QFont("system-ui", 7)
                    font_sc.setItalic(True)
                    painter.setFont(font_sc)
                    painter.setPen(QPen(QColor(200, 80, 80), 1))
                    # Offset per non uscire dal widget
                    lbl_x = max(rect_left + 2, min(x_label - 25, rect_right - 55))
                    painter.drawText(QRectF(lbl_x, y_label - 8, 55, 16),
                                     Qt.AlignCenter, "SCARTO")

        # --- 3. Disegna il profilo conico (linea diagonale di riferimento) ---
        profilo_points = []
        for pos_mm, sv in punti_sviluppo:
            x = margine_sx + pos_mm * scala_x
            sv_h = sv * scala_y
            y_top_cono = rect_bot - sv_h
            profilo_points.append(QPointF(x, y_top_cono))

        pen_profilo = QPen(QColor(44, 62, 80, 180), 1.5, Qt.DashLine)
        painter.setPen(pen_profilo)
        for j in range(len(profilo_points) - 1):
            painter.drawLine(profilo_points[j], profilo_points[j + 1])

        # --- 4. Linee verticali di separazione sezioni ---
        pen_sep = QPen(QColor(150, 160, 175), 1, Qt.DashDotLine)

        pos_mm = 0
        for i, sez in enumerate(self._sezioni):
            l_sez = sez.get('lunghezza', 0)
            d_ini = sez.get('d_inizio', 0)
            d_fin = sez.get('d_fine', 0)

            x_ini = margine_sx + pos_mm * scala_x
            x_fin = margine_sx + (pos_mm + l_sez) * scala_x

            # Linea verticale tratteggiata per separare le sezioni
            if i > 0:
                painter.setPen(pen_sep)
                painter.drawLine(QPointF(x_ini, rect_top), QPointF(x_ini, rect_bot))

            # --- Quote diametri (sopra il rettangolo) ---
            painter.setPen(QPen(self._dim_color, 1))
            font_diam = QFont("system-ui", 8)
            font_diam.setBold(True)
            painter.setFont(font_diam)

            # Diametro inizio (solo per la prima sezione)
            if i == 0:
                text_ini = f"Ø{d_ini:.1f}"
                painter.drawText(QRectF(x_ini - 30, rect_top - 18, 60, 16),
                                 Qt.AlignCenter, text_ini)

            # Diametro fine
            text_fin = f"Ø{d_fin:.1f}"
            painter.drawText(QRectF(x_fin - 30, rect_top - 18, 60, 16),
                             Qt.AlignCenter, text_fin)

            # --- Quota lunghezza sezione (sotto) ---
            font_lung = QFont("system-ui", 8)
            painter.setFont(font_lung)
            painter.setPen(QPen(self._quota_color, 1))

            lung_text = f"{l_sez} mm"
            mid_x = (x_ini + x_fin) / 2
            painter.drawText(QRectF(mid_x - 35, rect_bot + 8, 70, 16),
                             Qt.AlignCenter, lung_text)

            # Frecce quota lunghezza
            self._disegna_quota_orizzontale(painter, x_ini, x_fin, rect_bot + 5)

            pos_mm += l_sez

        # --- 5. Quota sviluppo max a sinistra (altezza rettangolo) ---
        font_sv = QFont("system-ui", 9)
        font_sv.setBold(True)
        painter.setFont(font_sv)
        painter.setPen(QPen(self._dim_color, 1))

        painter.save()
        painter.translate(rect_left - 15, (rect_top + rect_bot) / 2)
        painter.rotate(-90)
        sv_text = f"Sviluppo: {sviluppo_max:.1f} mm"
        painter.drawText(QRectF(-60, -15, 120, 25), Qt.AlignCenter, sv_text)
        painter.restore()

        # Frecce quota laterale
        self._disegna_quota_verticale(painter, rect_top, rect_bot, rect_left - 8)

        # --- 6. Etichetta scarto ---
        if self._scarto > 0:
            font_scarto = QFont("system-ui", 9)
            font_scarto.setItalic(True)
            painter.setFont(font_scarto)
            painter.setPen(QPen(QColor(200, 80, 80), 1))

            scarto_m2 = self._scarto / 1000000.0
            scarto_text = f"Scarto: {self._scarto:.0f} mm² ({scarto_m2:.6f} m²)"
            painter.drawText(QRectF(margine_sx, h - 30, draw_w, 20),
                             Qt.AlignRight, scarto_text)

        # --- 7. Lunghezza totale (sotto le quote sezioni) ---
        if len(self._sezioni) > 1:
            font_tot = QFont("system-ui", 9)
            font_tot.setBold(True)
            painter.setFont(font_tot)
            painter.setPen(QPen(self._dim_color, 1))

            tot_text = f"Lunghezza totale: {lunghezza_totale:.0f} mm"
            painter.drawText(QRectF(margine_sx, rect_bot + 24, draw_w, 18),
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
