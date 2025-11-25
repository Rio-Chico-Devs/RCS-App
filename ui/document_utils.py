#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Document Utils - Utilità per generazione documenti di produzione
Template aggiornato per matchare il formato richiesto

Version: 1.3.0
Last Updated: 03/10/2025
Author: Sviluppatore PyQt5 + Claude

CHANGELOG:
v1.3.0 (03/10/2025):
- Ripristinato codice funzionante
- Gestione flessibile formati materiale (oggetti/dict)
- Layout DOCX semplificato
"""

import os
from datetime import datetime
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QFileDialog

class DocumentUtils:
    """Utilità per generazione documenti di produzione"""
    
    @staticmethod
    def mostra_dialog_formato(parent=None):
        """Mostra dialog per selezione formato documento"""
        dialog = QDialog(parent)
        dialog.setWindowTitle("Genera Documento")
        dialog.setFixedSize(300, 120)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QPushButton("Seleziona formato per il documento:"))
        
        buttons_layout = QHBoxLayout()
        btn_html = QPushButton("HTML")
        btn_docx = QPushButton("DOCX") 
        btn_cancel = QPushButton("Annulla")
        
        buttons_layout.addWidget(btn_html)
        buttons_layout.addWidget(btn_docx)
        buttons_layout.addWidget(btn_cancel)
        layout.addLayout(buttons_layout)
        
        formato_scelto = None
        
        def on_html():
            nonlocal formato_scelto
            formato_scelto = 'html'
            dialog.accept()
            
        def on_docx():
            nonlocal formato_scelto
            formato_scelto = 'docx'
            dialog.accept()
            
        def on_cancel():
            dialog.reject()
            
        btn_html.clicked.connect(on_html)
        btn_docx.clicked.connect(on_docx)
        btn_cancel.clicked.connect(on_cancel)
        
        if dialog.exec_() == QDialog.Accepted:
            return formato_scelto
        return None
    
    @staticmethod
    def genera_documento_html(preventivo, dati_cliente, parent=None):
        """Genera documento HTML editabile per la produzione"""
        try:
            # Dialog per salvare file
            nome_file = f"SchediaTaglio_{preventivo.codice_preventivo}_{datetime.now().strftime('%Y%m%d')}"
            file_path, _ = QFileDialog.getSaveFileName(
                parent,
                "Salva Scheda di Taglio HTML",
                nome_file,
                "HTML Files (*.html)"
            )
            
            if not file_path:
                return None
                
            # Genera contenuto HTML
            html_content = DocumentUtils._genera_html_template_specifico(preventivo, dati_cliente)
            
            # Salva file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            print(f"DEBUG: Documento HTML generato: {file_path}")
            
            # Apri automaticamente
            os.startfile(file_path)
            
            return file_path
            
        except Exception as e:
            print(f"DEBUG: Errore generazione HTML: {e}")
            if parent:
                QMessageBox.warning(parent, "Errore", f"Errore nella generazione HTML: {e}")
            return None
    
    @staticmethod
    def genera_documento_docx(preventivo, dati_cliente, parent=None):
        """Genera documento DOCX editabile per la produzione"""
        try:
            try:
                from docx import Document
                from docx.shared import Inches, Pt
                from docx.enum.text import WD_ALIGN_PARAGRAPH
            except ImportError:
                if parent:
                    QMessageBox.information(
                        parent, 
                        "Libreria Mancante",
                        "Per generare DOCX è necessario installare python-docx:\n\npip install python-docx"
                    )
                return None
            
            # Dialog per salvare file
            nome_file = f"SchediaTaglio_{preventivo.codice_preventivo}_{datetime.now().strftime('%Y%m%d')}"
            file_path, _ = QFileDialog.getSaveFileName(
                parent,
                "Salva Scheda di Taglio DOCX",
                nome_file,
                "DOCX Files (*.docx)"
            )
            
            if not file_path:
                return None
                
            # Crea documento
            doc = Document()
            
            # Header centrato
            header = doc.add_paragraph()
            header.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = header.add_run("RCS - Scheda di Taglio")
            run.bold = True
            run.font.size = Pt(14)
            
            doc.add_paragraph()  # Spazio
            
            # Informazioni cliente - Tabella 3x2
            info_table = doc.add_table(rows=3, cols=2)
            info_table.style = 'Table Grid'
            
            # Riga 1
            info_table.cell(0, 0).text = f"Cliente: {dati_cliente.get('nome_cliente', '')}"
            info_table.cell(0, 1).text = f"Ordine No: {dati_cliente.get('numero_ordine', '')}"
            
            # Riga 2
            info_table.cell(1, 0).text = f"Data: {datetime.now().strftime('%d/%m/%Y')}"
            info_table.cell(1, 1).text = f"Descrizione: {dati_cliente.get('oggetto_preventivo', '')}"
            
            # Riga 3
            info_table.cell(2, 0).text = "Finitura: ________________________"
            info_table.cell(2, 1).text = f"Codice: {dati_cliente.get('codice', '')}"
            
            doc.add_paragraph()  # Spazio
            
            # Materiali - Layout identico all'HTML
            if hasattr(preventivo, 'materiali') and preventivo.materiali:
                for i, materiale in enumerate(preventivo.materiali):
                    # Gestisci diversi formati di materiale
                    if hasattr(materiale, 'giri'):
                        giri = materiale.giri
                        lunghezza = getattr(materiale, 'lunghezza', 0)
                        sviluppo = getattr(materiale, 'sviluppo', 0)
                        nome = getattr(materiale, 'nome', f'Materiale {i+1}')
                    elif isinstance(materiale, dict):
                        giri = materiale.get('giri', 0)
                        lunghezza = materiale.get('lunghezza', 0)
                        sviluppo = materiale.get('sviluppo', 0)
                        nome = materiale.get('nome', materiale.get('materiale_nome', f'Materiale {i+1}'))
                    else:
                        giri = 1
                        lunghezza = 1000
                        sviluppo = 100
                        nome = f'Materiale {i+1}'
                    
                    # Lunghezza centrata sopra
                    lungh_para = doc.add_paragraph()
                    lungh_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    lungh_para.space_after = Pt(2)
                    run = lungh_para.add_run(f"{int(lunghezza)} mm")
                    run.bold = True
                    run.font.size = Pt(10)
                    
                    # Tabella 1x3 per layout orizzontale: Giri | Rettangolo | Sviluppo
                    layout_table = doc.add_table(rows=1, cols=3)
                    # NON applicare stile - tabella senza bordi di default
                    
                    # Celle
                    cell_giri = layout_table.cell(0, 0)
                    cell_rect = layout_table.cell(0, 1)  
                    cell_svil = layout_table.cell(0, 2)
                    
                    # Larghezze
                    layout_table.columns[0].width = Inches(0.5)
                    layout_table.columns[1].width = Inches(5.5)
                    layout_table.columns[2].width = Inches(1.0)
                    
                    # FORZA altezza riga leggermente più alta
                    from docx.oxml.shared import OxmlElement
                    from docx.oxml.ns import qn
                    
                    tr = layout_table.rows[0]._element
                    trPr = tr.get_or_add_trPr()
                    trHeight = OxmlElement('w:trHeight')
                    trHeight.set(qn('w:val'), '280')  # Altezza leggermente aumentata (280 twips = ~5mm)
                    trHeight.set(qn('w:hRule'), 'exact')
                    trPr.append(trHeight)
                    
                    # Aggiungi bordi SOLO al rettangolo centrale
                    tcPr = cell_rect._element.get_or_add_tcPr()
                    tcBorders = OxmlElement('w:tcBorders')
                    
                    # Aggiungi tutti e 4 i bordi al rettangolo
                    for border_name in ['top', 'left', 'bottom', 'right']:
                        border = OxmlElement(f'w:{border_name}')
                        border.set(qn('w:val'), 'single')
                        border.set(qn('w:sz'), '12')
                        border.set(qn('w:space'), '0')
                        border.set(qn('w:color'), '000000')
                        tcBorders.append(border)
                    
                    tcPr.append(tcBorders)
                    
                    # Giri (allineata a destra, NESSUN bordo)
                    para_giri = cell_giri.paragraphs[0]
                    para_giri.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    para_giri.paragraph_format.space_before = Pt(0)
                    para_giri.paragraph_format.space_after = Pt(0)
                    run_giri = para_giri.add_run(f"G{giri}")
                    run_giri.bold = True
                    run_giri.font.size = Pt(10)
                    
                    # Rettangolo centrale - == a sinistra, nome centrato con spazi
                    para_rect = cell_rect.paragraphs[0]
                    para_rect.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    para_rect.paragraph_format.space_before = Pt(0)
                    para_rect.paragraph_format.space_after = Pt(0)
                    
                    # == a sinistra
                    run_eq = para_rect.add_run("==")
                    run_eq.font.size = Pt(8)
                    run_eq.bold = True
                    
                    # Spazi per distanziare il nome (ridotti per mantenere visibilità)
                    para_rect.add_run("               ")  # ~15 spazi
                    
                    # Nome materiale 
                    run_nome = para_rect.add_run(nome)
                    run_nome.bold = True
                    run_nome.font.size = Pt(10)
                    
                    # Sviluppo (allineata a sinistra, NESSUN bordo)
                    para_svil = cell_svil.paragraphs[0]
                    para_svil.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    run_svil = para_svil.add_run(f"H {int(sviluppo)} mm")
                    run_svil.bold = True
                    run_svil.font.size = Pt(10)
                    
                    doc.add_paragraph()  # Spazio tra materiali
            
            # Tabella operazioni
            doc.add_paragraph()
            ops_table = doc.add_table(rows=6, cols=7)
            ops_table.style = 'Table Grid'
            
            # Header tabella
            headers = ['Operazione', 'Inizio', 'Fine', 'Tempo Tot.', 'Num. Pezzi', 'Data', 'Note']
            for i, header in enumerate(headers):
                cell = ops_table.cell(0, i)
                cell.text = header
                cell.paragraphs[0].runs[0].bold = True
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Larghezze colonne (Note più ampia)
            for i, width in enumerate([1.0, 0.6, 0.6, 0.7, 0.7, 0.6, 3.0]):
                for row in ops_table.rows:
                    row.cells[i].width = Inches(width)
            
            # Footer
            doc.add_paragraph()
            footer = doc.add_paragraph(f"Documento generato automaticamente dal sistema RCS - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = footer.runs[0]
            run.font.size = Pt(8)
            
            # Salva documento
            doc.save(file_path)
            print(f"DEBUG: Documento DOCX generato: {file_path}")
            
            # Apri automaticamente
            os.startfile(file_path)
            
            return file_path
            
        except Exception as e:
            print(f"DEBUG: Errore generazione DOCX: {e}")
            import traceback
            traceback.print_exc()
            if parent:
                QMessageBox.warning(parent, "Errore", f"Errore nella generazione DOCX: {e}")
            return None
    
    @staticmethod
    def _genera_html_template_specifico(preventivo, dati_cliente):
        """Template HTML che replica esattamente il documento di esempio"""
        
        # Sezione materiali dettagliata
        materiali_html = ""
        if hasattr(preventivo, 'materiali') and preventivo.materiali:
            for i, materiale in enumerate(preventivo.materiali):
                # Gestisci diversi formati di materiale
                if hasattr(materiale, 'giri'):
                    giri = materiale.giri
                    lunghezza = getattr(materiale, 'lunghezza', 0)
                    sviluppo = getattr(materiale, 'sviluppo', 0)
                    nome = getattr(materiale, 'nome', f'Materiale {i+1}')
                elif isinstance(materiale, dict):
                    giri = materiale.get('giri', 0)
                    lunghezza = materiale.get('lunghezza', 0)
                    sviluppo = materiale.get('sviluppo', 0)
                    nome = materiale.get('nome', materiale.get('materiale_nome', f'Materiale {i+1}'))
                else:
                    giri = 1
                    lunghezza = 1000
                    sviluppo = 100
                    nome = f'Materiale {i+1}'
                
                materiali_html += f"""
                <div style="width: 120mm; margin: 12mm auto; position: relative; page-break-inside: avoid;">
                    <!-- Lunghezza (sopra al centro del rettangolo) -->
                    <div style="position: absolute; left: 50%; top: -6mm; transform: translateX(-50%); font-size: 10px;">
                        <strong>{lunghezza}mm</strong>
                    </div>
                    
                    <!-- Rettangolo materiale con orientamento interno -->
                    <div style="width: 80mm; height: 8mm; margin: 0 auto; border: 2px solid #000; display: flex; align-items: center; justify-content: space-between; background: #fff; padding: 0 3mm; position: relative;">
                        <!-- Orientamento a sinistra dentro il rettangolo -->
                        <input type="text" placeholder="Orient." style="width: 18mm; border: none; font-size: 8px; background: transparent; border-bottom: none;">
                        <!-- Nome materiale al centro -->
                        <strong style="font-size: 11px; position: absolute; left: 50%; transform: translateX(-50%);">{nome}</strong>
                    </div>
                    
                    <!-- Giri (a metà del lato sinistro del rettangolo, molto vicino) -->
                    <div style="position: absolute; left: -2mm; top: 50%; transform: translateY(-50%); font-size: 10px;">
                        <strong>G{giri}</strong>
                    </div>
                    
                    <!-- Sviluppo (a metà del lato destro del rettangolo) -->
                    <div style="position: absolute; right: -6mm; top: 50%; transform: translateY(-50%); font-size: 10px;">
                        <strong>H {int(sviluppo)} mm</strong>
                    </div>
                </div>
                """
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Scheda di Taglio - {preventivo.codice_preventivo}</title>
    <style>
        @page {{
            size: A4;
            margin: 15mm;
        }}
        body {{ 
            font-family: Arial, sans-serif; 
            max-width: 180mm;
            margin: 0 auto;
            font-size: 10px;
            line-height: 1.2;
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 15mm;
        }}
        .info-section {{ 
            margin-bottom: 3mm;
        }}
        .info-label {{ 
            font-weight: bold; 
            display: inline-block; 
            width: 25mm;
        }}
        .editable-field {{
            border: none;
            border-bottom: 1px solid #000;
            background: transparent;
            font-size: 10px;
            padding: 1mm 0;
        }}
        .operations-table {{ 
            width: 100%; 
            max-width: 180mm;
            border-collapse: collapse; 
            margin: 15mm auto 0;
        }}
        .operations-table th, .operations-table td {{ 
            border: 1px solid #000; 
            padding: 1mm; 
            text-align: center;
            height: 8mm;
        }}
        .operations-table th {{ 
            background: #f0f0f0; 
            font-weight: bold;
            font-size: 9px;
        }}
        .editable-area {{
            width: 100%;
            border: none;
            background: transparent;
            resize: none;
            font-size: 10px;
            text-align: center;
        }}
        @media print {{
            body {{ margin: 0; }}
            .editable-field {{ 
                border-bottom: 1px solid #000 !important; 
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h2 style="text-align: center; margin: 0; font-size: 14px;">RCS - Scheda di Taglio</h2>
    </div>

    <!-- INFORMAZIONI CLIENTE (2 colonne) -->
    <div style="display: flex; justify-content: space-between;">
        <div style="width: 48%;">
            <div class="info-section">
                <span class="info-label">Cliente:</span>
                <input type="text" class="editable-field" value="{dati_cliente.get('nome_cliente', '')}" style="width: 50mm;">
            </div>
            <div class="info-section">
                <span class="info-label">Data:</span>
                <input type="text" class="editable-field" value="{datetime.now().strftime('%d/%m/%Y')}" style="width: 30mm;">
            </div>
            <div class="info-section">
                <span class="info-label">Finitura:</span>
                <input type="text" class="editable-field" style="width: 50mm;">
            </div>
        </div>
        <div style="width: 48%;">
            <div class="info-section">
                <span class="info-label">Ordine No:</span>
                <input type="text" class="editable-field" value="{dati_cliente.get('numero_ordine', '')}" style="width: 30mm;">
            </div>
            <div class="info-section">
                <span class="info-label">Descrizione:</span>
                <input type="text" class="editable-field" value="{dati_cliente.get('oggetto_preventivo', '')}" style="width: 50mm;">
            </div>
            <div class="info-section">
                <span class="info-label">Codice:</span>
                <input type="text" class="editable-field" value="{dati_cliente.get('codice', '')}" style="width: 30mm;">
            </div>
        </div>
    </div>

    <!-- SEZIONE MATERIALI -->
    {materiali_html}

    <!-- TABELLA OPERAZIONI -->
    <table class="operations-table">
        <thead>
            <tr>
                <th style="width: 12%;">Operazione</th>
                <th style="width: 8%;">Inizio</th>
                <th style="width: 8%;">Fine</th>
                <th style="width: 8%;">Tempo Tot.</th>
                <th style="width: 8%;">Num. Pezzi</th>
                <th style="width: 8%;">Data</th>
                <th style="width: 48%;">Note</th>
            </tr>
        </thead>
        <tbody>
            {"".join(['<tr>' + ''.join([f'<td style="height: 8mm;"><textarea class="editable-area" rows="1"></textarea></td>' for _ in range(7)]) + '</tr>' for _ in range(5)])}
        </tbody>
    </table>

    <div style="margin-top: 10mm; font-size: 8px; color: #666; text-align: center;">
        Documento generato automaticamente dal sistema RCS - {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </div>
</body>
</html>
        """