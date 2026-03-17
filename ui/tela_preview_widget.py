#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
TelaPreviewWidget - Widget di anteprima CAD per la tela tagliata
Uso riservato esclusivamente a RCS

Disegna la forma della tela (rettangolo per cilindrica, trapezio/pentagono per conica)
con le quote delle dimensioni e la linea di taglio per la conicità.
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QPolygonF, QBrush


class TelaPreviewWidget(QWidget):
    """Widget che disegna l'anteprima CAD della tela tagliata."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 200)
        self._is_conica = False
        self._lunghezza = 0.0
        self._sviluppo = 0.0
        self._diametro = 0.0
        self._scarto = 0.0

        # Parametri conicità semplificati
        self._conicita_lato = 'sinistra'      # 'sinistra', 'destra', 'entrambi'
        self._conicita_altezza = 0.0          # mm dall'alto sul bordo laterale
        self._conicita_lunghezza = 0.0        # mm estensione orizzontale del taglio

        # Trasformazioni disegno
        self._rotation = 0
        self._flip_h = False
        self._flip_v = False

        # Colori stile CAD
        self._bg_color = QColor(255, 255, 255)
        self._tela_fill = QColor(200, 220, 240, 80)
        self._tela_border = QColor(44, 62, 80)
        self._scarto_fill = QColor(255, 200, 200, 120)
        self._quota_color = QColor(100, 100, 100)
        self._dim_color = QColor(44, 62, 80)

    # ── API pubblica ──────────────────────────────────────────────

    def aggiorna_cilindrica(self, diametro, lunghezza, sviluppo):
        """Aggiorna con dati cilindrica (rettangolo semplice)."""
        self._is_conica = False
        self._diametro = diametro
        self._lunghezza = lunghezza
        self._sviluppo = sviluppo
        self._scarto = 0.0
        self.update()

    def aggiorna_conica(self, lato, altezza_mm, lunghezza_taglio_mm, lunghezza_tela=None, sviluppo=None):
        """Aggiorna con parametri conicità semplificati.
        lato: 'sinistra', 'destra', 'entrambi'
        altezza_mm: Y dall'alto sul bordo laterale dove inizia il taglio (0 = angolo)
        lunghezza_taglio_mm: estensione orizzontale del taglio
        lunghezza_tela, sviluppo: dimensioni tela (se None usa quelle già memorizzate)
        Restituisce lo scarto in mm².
        """
        self._is_conica = True
        self._conicita_lato = lato
        self._conicita_altezza = altezza_mm
        self._conicita_lunghezza = lunghezza_taglio_mm
        if lunghezza_tela is not None:
            self._lunghezza = lunghezza_tela
        if sviluppo is not None:
            self._sviluppo = sviluppo
        self._scarto = self._calcola_scarto_conica()
        self.update()
        return self._scarto

    def get_scarto_mm2(self):
        return self._scarto

    def rotate_left(self):
        self._rotation = (self._rotation - 90) % 360
        self.update()

    def rotate_right(self):
        self._rotation = (self._rotation + 90) % 360
        self.update()

    def flip_horizontal(self):
        self._flip_h = not self._flip_h
        self.update()

    def flip_vertical(self):
        self._flip_v = not self._flip_v
        self.update()

    def get_orientamento(self):
        return {'rotation': self._rotation, 'flip_h': self._flip_h, 'flip_v': self._flip_v}

    def set_orientamento(self, orientamento):
        if not orientamento:
            return
        self._rotation = orientamento.get('rotation', 0)
        self._flip_h = orientamento.get('flip_h', False)
        self._flip_v = orientamento.get('flip_v', False)
        self.update()

    # ── Calcolo scarto ────────────────────────────────────────────

    def _calcola_scarto_conica(self):
        """Scarto = area triangolo(i) del taglio diagonale.
        Triangolo: base = lunghezza_taglio, altezza = (sviluppo - altezza_inizio)
        """
        l = self._conicita_lunghezza
        s = self._sviluppo
        a = self._conicita_altezza
        if l <= 0 or s <= 0:
            return 0.0
        area = 0.5 * l * max(s - a, 0.0)
        if self._conicita_lato == 'entrambi':
            area *= 2
        return area

    # ── Disegno ───────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self._bg_color)

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

        if self._is_conica and self._lunghezza > 0 and self._sviluppo > 0:
            self._disegna_conica(painter)
        elif not self._is_conica and self._lunghezza > 0 and self._sviluppo > 0:
            self._disegna_cilindrica(painter)
        else:
            self._disegna_placeholder(painter)

        if has_transform:
            painter.restore()

        painter.end()

    def _disegna_placeholder(self, painter):
        painter.setPen(QColor(160, 174, 192))
        font = QFont("system-ui", 12)
        font.setItalic(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "Inserisci i parametri per\nvisualizzare l'anteprima tela")

    def _disegna_cilindrica(self, painter):
        """Rettangolo per tela cilindrica.
        Orientamento: X = lunghezza (larghezza), Y = sviluppo (altezza).
        """
        w = self.width()
        h = self.height()
        margine_sx = 75
        margine_dx = 20
        margine_top = 55
        margine_bot = 30

        avail_w = w - margine_sx - margine_dx
        avail_h = h - margine_top - margine_bot

        if avail_w <= 0 or avail_h <= 0:
            return

        # X = lunghezza (orizzontale), Y = sviluppo (verticale)
        scala = min(avail_w / self._lunghezza, avail_h / self._sviluppo)
        draw_w = self._lunghezza * scala
        draw_h = self._sviluppo * scala

        draw_x = margine_sx + (avail_w - draw_w) / 2
        draw_y = margine_top + (avail_h - draw_h) / 2

        pen = QPen(self._tela_border, 2)
        painter.setPen(pen)
        painter.setBrush(QBrush(self._tela_fill))
        painter.drawRect(QRectF(draw_x, draw_y, draw_w, draw_h))

        font_quota = QFont("system-ui", 10)
        font_quota.setBold(True)
        painter.setFont(font_quota)
        painter.setPen(QPen(self._dim_color, 1))

        # Quota superiore: lunghezza
        lun_text = f"Lunghezza: {self._lunghezza:.0f} mm"
        painter.drawText(QRectF(draw_x, draw_y - 32, draw_w, 22),
                         Qt.AlignCenter | Qt.TextDontClip, lun_text)
        self._disegna_quota_orizzontale(painter, draw_x, draw_x + draw_w, draw_y - 12)

        # Quota laterale: sviluppo
        painter.save()
        painter.translate(draw_x - 18, draw_y + draw_h / 2)
        painter.rotate(-90)
        painter.drawText(QRectF(-70, -15, 140, 25),
                         Qt.AlignCenter | Qt.TextDontClip,
                         f"Sviluppo: {self._sviluppo:.1f} mm")
        painter.restore()
        self._disegna_quota_verticale(painter, draw_y, draw_y + draw_h, draw_x - 8)

        font_diam = QFont("system-ui", 9)
        painter.setFont(font_diam)
        painter.setPen(QPen(self._quota_color, 1))
        painter.drawText(QRectF(draw_x, draw_y, draw_w, draw_h),
                         Qt.AlignCenter, f"Ø {self._diametro:.1f}")

    def _disegna_conica(self, painter):
        """Disegna la tela conica con il taglio diagonale.

        Orientamento FISSO (come sul tavolo di lavoro):
          X (orizzontale) = lunghezza tela
          Y (verticale)   = sviluppo

        Il taglio diagonale parte da un punto sul bordo laterale
        (sinistro o destro) e arriva a un punto sul bordo inferiore.
        L'area di scarto è evidenziata in rosa.
        """
        w = self.width()
        h = self.height()
        margine_sx = 80
        margine_dx = 30
        margine_top = 55
        margine_bot = 65

        draw_w = w - margine_sx - margine_dx
        draw_h = h - margine_top - margine_bot

        if draw_w <= 0 or draw_h <= 0:
            return

        L = self._lunghezza
        S = self._sviluppo
        alt = self._conicita_altezza
        lt = self._conicita_lunghezza
        lato = self._conicita_lato

        # Scala proporzionale
        scala = min(draw_w / L, draw_h / S)
        rect_w = L * scala
        rect_h = S * scala

        # Rettangolo centrato
        rect_left = margine_sx + (draw_w - rect_w) / 2
        rect_top = margine_top + (draw_h - rect_h) / 2
        rect_right = rect_left + rect_w
        rect_bot = rect_top + rect_h

        def px(x_mm): return rect_left + x_mm * scala
        def py(y_mm): return rect_top + y_mm * scala

        # --- 1. Disegna il rettangolo completo ---
        painter.setPen(QPen(self._tela_border, 2))
        painter.setBrush(QBrush(self._tela_fill))
        painter.drawRect(QRectF(rect_left, rect_top, rect_w, rect_h))

        # --- 2. Disegna aree scarto ---
        pen_no = Qt.NoPen
        brush_scarto = QBrush(self._scarto_fill)

        def disegna_scarto_sinistra():
            # Triangolo: (0, alt), (lt, S), (0, S)
            poly = QPolygonF([
                QPointF(px(0),  py(alt)),
                QPointF(px(lt), py(S)),
                QPointF(px(0),  py(S)),
            ])
            painter.setPen(pen_no)
            painter.setBrush(brush_scarto)
            painter.drawPolygon(poly)

        def disegna_scarto_destra():
            # Triangolo: (L, alt), (L-lt, S), (L, S)
            poly = QPolygonF([
                QPointF(px(L),      py(alt)),
                QPointF(px(L - lt), py(S)),
                QPointF(px(L),      py(S)),
            ])
            painter.setPen(pen_no)
            painter.setBrush(brush_scarto)
            painter.drawPolygon(poly)

        if lato == 'sinistra':
            disegna_scarto_sinistra()
        elif lato == 'destra':
            disegna_scarto_destra()
        else:  # entrambi
            disegna_scarto_sinistra()
            disegna_scarto_destra()

        # --- 3. Linee di taglio diagonali ---
        pen_taglio = QPen(QColor(200, 60, 60), 1.8)
        painter.setPen(pen_taglio)
        painter.setBrush(Qt.NoBrush)

        if lato in ('sinistra', 'entrambi'):
            painter.drawLine(QPointF(px(0),  py(alt)),
                             QPointF(px(lt), py(S)))

        if lato in ('destra', 'entrambi'):
            painter.drawLine(QPointF(px(L),      py(alt)),
                             QPointF(px(L - lt), py(S)))

        # --- 4. Linee trattegiate di riferimento posizione taglio ---
        pen_dash = QPen(QColor(150, 160, 175), 1, Qt.DashLine)
        painter.setPen(pen_dash)
        if lato in ('sinistra', 'entrambi') and lt > 0:
            painter.drawLine(QPointF(px(lt), rect_top), QPointF(px(lt), rect_bot))
        if lato in ('destra', 'entrambi') and lt > 0:
            painter.drawLine(QPointF(px(L - lt), rect_top), QPointF(px(L - lt), rect_bot))

        # --- 5. Etichetta SCARTO ---
        if self._scarto > 0:
            font_sc = QFont("system-ui", 7)
            font_sc.setItalic(True)
            painter.setFont(font_sc)
            painter.setPen(QPen(QColor(200, 80, 80), 1))
            if lato == 'sinistra':
                scarto_cx = (rect_left + min(px(lt), rect_left + rect_w * 0.4)) / 2
                scarto_cy = (rect_bot + py(alt)) / 2
            elif lato == 'destra':
                scarto_cx = (max(px(L - lt), rect_left + rect_w * 0.6) + rect_right) / 2
                scarto_cy = (rect_bot + py(alt)) / 2
            else:
                scarto_cx = (rect_left + min(px(lt), rect_left + rect_w * 0.3)) / 2
                scarto_cy = (rect_bot + py(alt)) / 2
            painter.drawText(QRectF(scarto_cx - 30, scarto_cy - 8, 60, 16),
                             Qt.AlignCenter | Qt.TextDontClip, "SCARTO")

        # --- 6. Quote dimensioni ---
        font_q = QFont("system-ui", 9)
        font_q.setBold(True)
        painter.setFont(font_q)
        painter.setPen(QPen(self._dim_color, 1))

        # Lunghezza totale (sopra)
        painter.drawText(QRectF(rect_left, rect_top - 34, rect_w, 22),
                         Qt.AlignCenter | Qt.TextDontClip, f"Lunghezza totale: {L:.0f} mm")
        self._disegna_quota_orizzontale(painter, rect_left, rect_right, rect_top - 14)

        # Sviluppo (a sinistra, verticale)
        painter.save()
        painter.translate(rect_left - 20, rect_top + rect_h / 2)
        painter.rotate(-90)
        painter.drawText(QRectF(-65, -12, 130, 22),
                         Qt.AlignCenter | Qt.TextDontClip,
                         f"Sviluppo: {S:.1f} mm")
        painter.restore()
        self._disegna_quota_verticale(painter, rect_top, rect_bot, rect_left - 8)

        # Quota lunghezza taglio (sotto, a sinistra o destra)
        font_lt = QFont("system-ui", 8)
        painter.setFont(font_lt)
        painter.setPen(QPen(self._quota_color, 1))
        if lato in ('sinistra', 'entrambi') and lt > 0:
            mid_lt = (rect_left + px(lt)) / 2
            painter.drawText(QRectF(mid_lt - 30, rect_bot + 6, 60, 18),
                             Qt.AlignCenter | Qt.TextDontClip, f"{lt:.0f} mm")
            self._disegna_quota_orizzontale(painter, rect_left, px(lt), rect_bot + 4)
        if lato in ('destra', 'entrambi') and lt > 0:
            mid_lt = (px(L - lt) + rect_right) / 2
            painter.drawText(QRectF(mid_lt - 30, rect_bot + 6, 60, 18),
                             Qt.AlignCenter | Qt.TextDontClip, f"{lt:.0f} mm")
            self._disegna_quota_orizzontale(painter, px(L - lt), rect_right, rect_bot + 4)

        # Quota altezza inizio (se > 0, sulla destra)
        if alt > 0:
            painter.setPen(QPen(self._quota_color, 1))
            painter.drawText(QRectF(rect_right + 5, rect_top, 55, max(py(alt) - rect_top, 18)),
                             Qt.AlignLeft | Qt.AlignVCenter | Qt.TextDontClip, f"{alt:.0f}")

        # Info taglio (in basso) — rettangolo che usa l'intera larghezza widget
        lato_txt = {'sinistra': 'Sinistra', 'destra': 'Destra', 'entrambi': 'Entrambi'}.get(lato, lato)
        font_info = QFont("system-ui", 8)
        font_info.setItalic(True)
        painter.setFont(font_info)
        painter.setPen(QPen(QColor(200, 80, 80), 1))
        info = f"Sbiegatura {lato_txt}: {lt:.0f} mm"
        if alt > 0:
            info += f"  (da {alt:.0f} mm)"
        painter.drawText(QRectF(5, h - 30, w - 10, 24),
                         Qt.AlignRight | Qt.TextDontClip, info)

    # ── Helpers per quotature ─────────────────────────────────────

    def _disegna_quota_orizzontale(self, painter, x1, x2, y):
        if abs(x2 - x1) < 10:
            return
        pen = QPen(self._quota_color, 1)
        painter.setPen(pen)
        painter.drawLine(QPointF(x1, y), QPointF(x2, y))
        painter.drawLine(QPointF(x1, y), QPointF(x1 + 5, y - 3))
        painter.drawLine(QPointF(x1, y), QPointF(x1 + 5, y + 3))
        painter.drawLine(QPointF(x2, y), QPointF(x2 - 5, y - 3))
        painter.drawLine(QPointF(x2, y), QPointF(x2 - 5, y + 3))

    def _disegna_quota_verticale(self, painter, y1, y2, x):
        if abs(y2 - y1) < 10:
            return
        pen = QPen(self._quota_color, 1)
        painter.setPen(pen)
        painter.drawLine(QPointF(x, y1), QPointF(x, y2))
        painter.drawLine(QPointF(x, y1), QPointF(x - 3, y1 + 5))
        painter.drawLine(QPointF(x, y1), QPointF(x + 3, y1 + 5))
        painter.drawLine(QPointF(x, y2), QPointF(x - 3, y2 - 5))
        painter.drawLine(QPointF(x, y2), QPointF(x + 3, y2 - 5))
