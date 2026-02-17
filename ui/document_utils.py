#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
© 2025 RCS - Software Proprietario
Document Utils - Utilità per generazione documenti di produzione
Template aggiornato per matchare il formato richiesto

Version: 1.3.0
Last Updated: 03/10/2025
Author: Sviluppatore antonio

CHANGELOG:
v1.3.0 (03/10/2025):
- Ripristinato codice funzionante
- Gestione flessibile formati materiale (oggetti/dict)
- Layout DOCX semplificato
"""

# type: ignore
# pyright: reportUnknownParameterType=false, reportMissingParameterType=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportAttributeAccessIssue=false
# pyright: reportUnusedVariable=false
# type: ignore
# pyright: reportUnusedImport=false
# type: ignore  
# pyright: reportPrivateImportUsage=false, reportPrivateUsage=false



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
        dialog.setFixedSize(350, 120)

        layout = QVBoxLayout(dialog)
        layout.addWidget(QPushButton("Seleziona formato per il documento:"))

        buttons_layout = QHBoxLayout()
        btn_html = QPushButton("HTML")
        btn_odt = QPushButton("ODT (OpenOffice)")
        btn_cancel = QPushButton("Annulla")

        buttons_layout.addWidget(btn_html)
        buttons_layout.addWidget(btn_odt)
        buttons_layout.addWidget(btn_cancel)
        layout.addLayout(buttons_layout)

        formato_scelto = None

        def on_html():
            nonlocal formato_scelto
            formato_scelto = 'html'
            dialog.accept()

        def on_odt():
            nonlocal formato_scelto
            formato_scelto = 'odt'
            dialog.accept()

        def on_cancel():
            dialog.reject()

        btn_html.clicked.connect(on_html)
        btn_odt.clicked.connect(on_odt)
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
            
            # Informazioni cliente - Tabella 3x3 con ultima riga merged
            info_table = doc.add_table(rows=3, cols=3)
            info_table.style = 'Table Grid'

            # Riga 1: Cliente | Ordine n. | Data
            info_table.cell(0, 0).text = f"Cliente: {dati_cliente.get('nome_cliente', '')}"
            info_table.cell(0, 1).text = f"Ordine n.: {dati_cliente.get('numero_ordine', '')}"
            info_table.cell(0, 2).text = f"Data: {datetime.now().strftime('%d/%m/%Y')}"

            # Riga 2: Codice | Misura | Finitura
            info_table.cell(1, 0).text = f"Codice: {dati_cliente.get('codice', '')}"
            info_table.cell(1, 1).text = f"Misura: {dati_cliente.get('misura', '')}"
            info_table.cell(1, 2).text = f"Finitura: {dati_cliente.get('finitura', '')}"

            # Riga 3: Descrizione (merge delle 3 celle)
            descrizione = dati_cliente.get('oggetto_preventivo', dati_cliente.get('descrizione', ''))
            cell_a = info_table.cell(2, 0)
            cell_c = info_table.cell(2, 2)
            cell_a.merge(cell_c)
            cell_a.text = f"Descrizione: {descrizione}"
            
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
    def genera_documento_odt(preventivo, dati_cliente, parent=None):
        """Genera documento ODT scalabile (1-25 materiali) per OpenOffice/LibreOffice"""
        try:
            try:
                from odf.opendocument import OpenDocumentText
                from odf.style import Style, TextProperties, ParagraphProperties, TableColumnProperties, TableCellProperties, TableRowProperties
                from odf.text import P, Span
                from odf.table import Table, TableColumn, TableRow, TableCell
            except ImportError:
                if parent:
                    QMessageBox.information(
                        parent,
                        "Libreria Mancante",
                        "Per generare ODT è necessario installare odfpy:\n\npip install odfpy"
                    )
                return None

            # Dialog per salvare file
            nome_file = f"SchediaTaglio_{preventivo.codice_preventivo}_{datetime.now().strftime('%Y%m%d')}"
            file_path, _ = QFileDialog.getSaveFileName(
                parent,
                "Salva Scheda di Taglio ODT",
                nome_file,
                "ODT Files (*.odt)"
            )

            if not file_path:
                return None

            # Calcola scala
            num_mat = len(preventivo.materiali) if hasattr(preventivo, 'materiali') and preventivo.materiali else 0
            sc = DocumentUtils._calcola_scala(num_mat)

            # Mappa font size
            font_map = {'10px': '10pt', '9px': '9pt', '8px': '8pt', '11px': '11pt', '7px': '7pt', '6px': '6pt'}
            ft_info = font_map.get(sc['font_info'], '10pt')
            ft_nome = font_map.get(sc['font_nome'], '10pt')
            ft_giri = font_map.get(sc['font_giri'], '10pt')

            # Mappa margini
            margin_map = {'12mm': '1.2cm', '6mm': '0.6cm', '3mm': '0.3cm'}
            margin_mat = margin_map.get(sc['margin_mat'], '1.2cm')

            # Mappa altezza rettangolo
            rect_map = {'8mm': '0.8cm', '6mm': '0.6cm', '5mm': '0.5cm'}
            rect_h = rect_map.get(sc['rect_height'], '0.8cm')

            # Padding cella materiale basato su scala
            mat_padding = '0.15cm' if num_mat <= 10 else ('0.08cm' if num_mat <= 17 else '0.04cm')
            cell_padding = '0.2cm' if num_mat <= 10 else ('0.12cm' if num_mat <= 17 else '0.08cm')
            no_border_padding = '0.1cm' if num_mat <= 10 else ('0.05cm' if num_mat <= 17 else '0.02cm')

            doc = OpenDocumentText()

            # === STILI (adattivi) ===
            style_title = Style(name="TitoloScheda", family="paragraph")
            style_title.addElement(ParagraphProperties(textalign="center", marginbottom="0.3cm"))
            style_title.addElement(TextProperties(fontsize="14pt", fontweight="bold"))
            doc.styles.addElement(style_title)

            style_normal = Style(name="Normale", family="paragraph")
            style_normal.addElement(TextProperties(fontsize=ft_info))
            doc.styles.addElement(style_normal)

            style_bold = Style(name="Bold", family="text")
            style_bold.addElement(TextProperties(fontweight="bold", fontsize=ft_info))
            doc.styles.addElement(style_bold)

            style_bold_nome = Style(name="BoldNome", family="text")
            style_bold_nome.addElement(TextProperties(fontweight="bold", fontsize=ft_nome))
            doc.styles.addElement(style_bold_nome)

            style_centered = Style(name="Centrato", family="paragraph")
            style_centered.addElement(ParagraphProperties(textalign="center", marginbottom="0cm", margintop="0cm"))
            style_centered.addElement(TextProperties(fontsize=ft_info, fontweight="bold"))
            doc.styles.addElement(style_centered)

            # Stile paragrafo con margine ridotto per materiali
            style_mat_label = Style(name="MatLabel", family="paragraph")
            style_mat_label.addElement(ParagraphProperties(textalign="center", marginbottom="0cm", margintop=margin_mat))
            style_mat_label.addElement(TextProperties(fontsize=ft_info, fontweight="bold"))
            doc.styles.addElement(style_mat_label)

            style_cell = Style(name="CellaBordo", family="table-cell")
            style_cell.addElement(TableCellProperties(border="0.05pt solid #000000", padding=cell_padding))
            doc.automaticstyles.addElement(style_cell)

            style_cell_header = Style(name="CellaHeader", family="table-cell")
            style_cell_header.addElement(TableCellProperties(border="0.05pt solid #000000", padding=cell_padding, backgroundcolor="#f0f0f0"))
            doc.automaticstyles.addElement(style_cell_header)

            style_table_info = Style(name="TabellaInfo", family="table")
            doc.automaticstyles.addElement(style_table_info)

            style_col_info = Style(name="ColInfo", family="table-column")
            style_col_info.addElement(TableColumnProperties(columnwidth="6cm"))
            doc.automaticstyles.addElement(style_col_info)

            style_col_info_wide = Style(name="ColInfoWide", family="table-column")
            style_col_info_wide.addElement(TableColumnProperties(columnwidth="18cm"))
            doc.automaticstyles.addElement(style_col_info_wide)

            style_table_ops = Style(name="TabellaOps", family="table")
            doc.automaticstyles.addElement(style_table_ops)

            col_widths_ops = ["2.5cm", "1.8cm", "1.8cm", "1.8cm", "1.8cm", "1.8cm", "6cm"]
            style_cols_ops = []
            for i, w in enumerate(col_widths_ops):
                st = Style(name=f"ColOps{i}", family="table-column")
                st.addElement(TableColumnProperties(columnwidth=w))
                doc.automaticstyles.addElement(st)
                style_cols_ops.append(st)

            style_mat_box = Style(name="MatBox", family="table-cell")
            style_mat_box.addElement(TableCellProperties(border="1.5pt solid #000000", padding=mat_padding))
            doc.automaticstyles.addElement(style_mat_box)

            style_cell_no_border = Style(name="CellaNoBordo", family="table-cell")
            style_cell_no_border.addElement(TableCellProperties(border="none", padding=no_border_padding))
            doc.automaticstyles.addElement(style_cell_no_border)

            style_col_mat_narrow = Style(name="ColMatNarrow", family="table-column")
            style_col_mat_narrow.addElement(TableColumnProperties(columnwidth="2cm"))
            doc.automaticstyles.addElement(style_col_mat_narrow)

            style_col_mat_wide = Style(name="ColMatWide", family="table-column")
            style_col_mat_wide.addElement(TableColumnProperties(columnwidth="12cm"))
            doc.automaticstyles.addElement(style_col_mat_wide)

            style_right = Style(name="AllineatoDestra", family="paragraph")
            style_right.addElement(ParagraphProperties(textalign="end"))
            style_right.addElement(TextProperties(fontsize=ft_giri, fontweight="bold"))
            doc.styles.addElement(style_right)

            style_giri_text = Style(name="GiriText", family="text")
            style_giri_text.addElement(TextProperties(fontweight="bold", fontsize=ft_giri))
            doc.styles.addElement(style_giri_text)

            # Stile riga materiale con altezza fissa
            style_mat_row = Style(name="MatRow", family="table-row")
            style_mat_row.addElement(TableRowProperties(rowheight=rect_h))
            doc.automaticstyles.addElement(style_mat_row)

            # === CONTENUTO ===

            # Titolo (solo se <= 10 materiali)
            if sc['show_title']:
                p_title = P(stylename=style_title)
                p_title.addElement(Span(stylename=style_bold, text="RCS - Scheda di Taglio"))
                doc.text.addElement(p_title)

            # Tabella info cliente (3 colonne)
            info_table = Table(name="InfoCliente", stylename=style_table_info)
            info_table.addElement(TableColumn(stylename=style_col_info))
            info_table.addElement(TableColumn(stylename=style_col_info))
            info_table.addElement(TableColumn(stylename=style_col_info))

            # Riga 1: Cliente | Ordine n. | Data
            tr1 = TableRow()
            for text in [f"Cliente: {dati_cliente.get('nome_cliente', '')}", f"Ordine n.: {dati_cliente.get('numero_ordine', '')}", f"Data: {datetime.now().strftime('%d/%m/%Y')}"]:
                tc = TableCell(stylename=style_cell)
                tc.addElement(P(stylename=style_normal, text=text))
                tr1.addElement(tc)
            info_table.addElement(tr1)

            # Riga 2: Codice | Misura | Finitura
            tr2 = TableRow()
            for text in [f"Codice: {dati_cliente.get('codice', '')}", f"Misura: {dati_cliente.get('misura', '')}", f"Finitura: {dati_cliente.get('finitura', '')}"]:
                tc = TableCell(stylename=style_cell)
                tc.addElement(P(stylename=style_normal, text=text))
                tr2.addElement(tc)
            info_table.addElement(tr2)

            # Riga 3: Descrizione (occupa tutte e 3 le colonne)
            tr3 = TableRow()
            descrizione = dati_cliente.get('oggetto_preventivo', dati_cliente.get('descrizione', ''))
            tc_desc = TableCell(stylename=style_cell, numbercolumnsspanned="3")
            tc_desc.addElement(P(stylename=style_normal, text=f"Descrizione: {descrizione}"))
            tr3.addElement(tc_desc)
            # Celle coperte dal colspan
            tr3.addElement(TableCell())
            tr3.addElement(TableCell())
            info_table.addElement(tr3)

            doc.text.addElement(info_table)

            # Sezione materiali
            if hasattr(preventivo, 'materiali') and preventivo.materiali:
                for i, materiale in enumerate(preventivo.materiali):
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

                    # Lunghezza centrata sopra (con margine top adattivo)
                    doc.text.addElement(P(stylename=style_mat_label, text=f"{int(lunghezza)} mm"))

                    # Tabella 1x3: Giri | Rettangolo | Sviluppo
                    mat_table = Table(name=f"Materiale{i}")
                    mat_table.addElement(TableColumn(stylename=style_col_mat_narrow))
                    mat_table.addElement(TableColumn(stylename=style_col_mat_wide))
                    mat_table.addElement(TableColumn(stylename=style_col_mat_narrow))

                    mat_row = TableRow(stylename=style_mat_row)

                    cell_giri = TableCell(stylename=style_cell_no_border)
                    cell_giri.addElement(P(stylename=style_right, text=f"G{giri}"))
                    mat_row.addElement(cell_giri)

                    cell_rect = TableCell(stylename=style_mat_box)
                    p_rect = P(stylename=style_centered)
                    p_rect.addElement(Span(stylename=style_bold_nome, text=f"==          {nome}"))
                    cell_rect.addElement(p_rect)
                    mat_row.addElement(cell_rect)

                    cell_svil = TableCell(stylename=style_cell_no_border)
                    p_svil = P(stylename=style_normal)
                    p_svil.addElement(Span(stylename=style_giri_text, text=f"H {int(sviluppo)} mm"))
                    cell_svil.addElement(p_svil)
                    mat_row.addElement(cell_svil)

                    mat_table.addElement(mat_row)
                    doc.text.addElement(mat_table)

            # Spazio prima tabella operazioni
            doc.text.addElement(P(stylename=style_normal, text=""))

            # Tabella operazioni
            ops_table = Table(name="Operazioni", stylename=style_table_ops)
            for st in style_cols_ops:
                ops_table.addElement(TableColumn(stylename=st))

            headers = ['Operazione', 'Inizio', 'Fine', 'Tempo', 'Pezzi', 'Data', 'Note']
            header_row = TableRow()
            for h in headers:
                tc = TableCell(stylename=style_cell_header)
                p = P(stylename=style_centered)
                p.addElement(Span(stylename=style_bold, text=h))
                tc.addElement(p)
                header_row.addElement(tc)
            ops_table.addElement(header_row)

            for _ in range(sc['ops_rows']):
                tr = TableRow()
                for _ in range(7):
                    tc = TableCell(stylename=style_cell)
                    tc.addElement(P(stylename=style_normal, text=""))
                    tr.addElement(tc)
                ops_table.addElement(tr)

            doc.text.addElement(ops_table)

            # Salva documento
            doc.save(file_path)
            print(f"DEBUG: Documento ODT generato: {file_path}")

            # Apri automaticamente
            os.startfile(file_path)

            return file_path

        except Exception as e:
            print(f"DEBUG: Errore generazione ODT: {e}")
            import traceback
            traceback.print_exc()
            if parent:
                QMessageBox.warning(parent, "Errore", f"Errore nella generazione ODT: {e}")
            return None

    @staticmethod
    def _calcola_scala(num_materiali):
        """Calcola i parametri di scala in base al numero di materiali.
        Ritorna dict con tutte le misure adattive. Tabella operazioni sempre 5 righe."""
        if num_materiali <= 10:
            return {
                'margin_mat': '12mm', 'rect_height': '8mm', 'font_nome': '11px',
                'font_info': '10px', 'font_giri': '10px', 'top_offset': '-6mm',
                'orient_font': '8px', 'orient_width': '18mm',
                'show_title': True, 'ops_rows': 5, 'ops_height': '8mm',
                'info_margin': '3mm', 'ops_margin_top': '15mm',
            }
        elif num_materiali <= 17:
            return {
                'margin_mat': '6mm', 'rect_height': '6mm', 'font_nome': '10px',
                'font_info': '9px', 'font_giri': '9px', 'top_offset': '-4mm',
                'orient_font': '7px', 'orient_width': '15mm',
                'show_title': False, 'ops_rows': 5, 'ops_height': '6mm',
                'info_margin': '2mm', 'ops_margin_top': '8mm',
            }
        elif num_materiali <= 25:
            return {
                'margin_mat': '3mm', 'rect_height': '5mm', 'font_nome': '9px',
                'font_info': '8px', 'font_giri': '8px', 'top_offset': '-3mm',
                'orient_font': '6px', 'orient_width': '12mm',
                'show_title': False, 'ops_rows': 5, 'ops_height': '5mm',
                'info_margin': '1mm', 'ops_margin_top': '5mm',
            }
        else:  # 26-30
            return {
                'margin_mat': '2mm', 'rect_height': '4mm', 'font_nome': '8px',
                'font_info': '7px', 'font_giri': '7px', 'top_offset': '-2mm',
                'orient_font': '6px', 'orient_width': '10mm',
                'show_title': False, 'ops_rows': 5, 'ops_height': '4mm',
                'info_margin': '1mm', 'ops_margin_top': '3mm',
            }

    @staticmethod
    def _genera_html_template_specifico(preventivo, dati_cliente):
        """Template HTML scalabile - adatta il layout al numero di materiali (1-25)"""

        num_materiali = len(preventivo.materiali) if hasattr(preventivo, 'materiali') and preventivo.materiali else 0
        s = DocumentUtils._calcola_scala(num_materiali)

        # Sezione materiali dettagliata
        materiali_html = ""
        if hasattr(preventivo, 'materiali') and preventivo.materiali:
            for i, materiale in enumerate(preventivo.materiali):
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
                <div style="width: 120mm; margin: {s['margin_mat']} auto; position: relative; page-break-inside: avoid;">
                    <div style="position: absolute; left: 50%; top: {s['top_offset']}; transform: translateX(-50%); font-size: {s['font_info']};">
                        <strong>{lunghezza}mm</strong>
                    </div>
                    <div style="width: 80mm; height: {s['rect_height']}; margin: 0 auto; border: 2px solid #000; display: flex; align-items: center; justify-content: space-between; background: #fff; padding: 0 3mm; position: relative;">
                        <input type="text" placeholder="Orient." style="width: {s['orient_width']}; border: none; font-size: {s['orient_font']}; background: transparent;">
                        <strong style="font-size: {s['font_nome']}; position: absolute; left: 50%; transform: translateX(-50%);">{nome}</strong>
                    </div>
                    <div style="position: absolute; left: -2mm; top: 50%; transform: translateY(-50%); font-size: {s['font_giri']};">
                        <strong>G{giri}</strong>
                    </div>
                    <div style="position: absolute; right: -6mm; top: 50%; transform: translateY(-50%); font-size: {s['font_giri']};">
                        <strong>H {int(sviluppo)} mm</strong>
                    </div>
                </div>
                """

        # Titolo condizionale
        title_html = ""
        if s['show_title']:
            title_html = '<div class="header"><h2 style="text-align: center; margin: 0; font-size: 14px;">RCS - Scheda di Taglio</h2></div>'

        # Righe tabella operazioni
        ops_rows_html = "".join([
            '<tr>' + ''.join([f'<td style="height: {s["ops_height"]};"><textarea class="editable-area" rows="1"></textarea></td>' for _ in range(7)]) + '</tr>'
            for _ in range(s['ops_rows'])
        ])

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Scheda di Taglio - {preventivo.codice_preventivo}</title>
    <style>
        @page {{
            size: A4;
            margin: 10mm;
        }}
        body {{
            font-family: Arial, sans-serif;
            max-width: 180mm;
            margin: 0 auto;
            font-size: {s['font_info']};
            line-height: 1.2;
        }}
        .header {{
            text-align: center;
            margin-bottom: 8mm;
        }}
        .info-section {{
            margin-bottom: {s['info_margin']};
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
            font-size: {s['font_info']};
            padding: 1mm 0;
        }}
        .operations-table {{
            width: 100%;
            max-width: 180mm;
            border-collapse: collapse;
            margin: {s['ops_margin_top']} auto 0;
        }}
        .operations-table th, .operations-table td {{
            border: 1px solid #000;
            padding: 1mm;
            text-align: center;
            height: {s['ops_height']};
        }}
        .operations-table th {{
            background: #f0f0f0;
            font-weight: bold;
            font-size: {s['font_info']};
        }}
        .editable-area {{
            width: 100%;
            border: none;
            background: transparent;
            resize: none;
            font-size: {s['font_info']};
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
    {title_html}

    <!-- INFORMAZIONI CLIENTE (3 colonne per riga) -->
    <table style="width: 100%; border-collapse: collapse; margin-bottom: {s['info_margin']};">
        <tr>
            <td style="padding: 2mm; border: 1px solid #000; width: 33%;">
                <span class="info-label">Cliente:</span>
                <input type="text" class="editable-field" value="{dati_cliente.get('nome_cliente', '')}" style="width: 28mm;">
            </td>
            <td style="padding: 2mm; border: 1px solid #000; width: 33%;">
                <span class="info-label">Ordine n.:</span>
                <input type="text" class="editable-field" value="{dati_cliente.get('numero_ordine', '')}" style="width: 25mm;">
            </td>
            <td style="padding: 2mm; border: 1px solid #000; width: 34%;">
                <span class="info-label">Data:</span>
                <input type="text" class="editable-field" value="{datetime.now().strftime('%d/%m/%Y')}" style="width: 25mm;">
            </td>
        </tr>
        <tr>
            <td style="padding: 2mm; border: 1px solid #000;">
                <span class="info-label">Codice:</span>
                <input type="text" class="editable-field" value="{dati_cliente.get('codice', '')}" style="width: 28mm;">
            </td>
            <td style="padding: 2mm; border: 1px solid #000;">
                <span class="info-label">Misura:</span>
                <input type="text" class="editable-field" value="{dati_cliente.get('misura', '')}" style="width: 25mm;">
            </td>
            <td style="padding: 2mm; border: 1px solid #000;">
                <span class="info-label">Finitura:</span>
                <input type="text" class="editable-field" value="{dati_cliente.get('finitura', '')}" style="width: 25mm;">
            </td>
        </tr>
        <tr>
            <td style="padding: 2mm; border: 1px solid #000;" colspan="3">
                <span class="info-label">Descrizione:</span>
                <input type="text" class="editable-field" value="{dati_cliente.get('oggetto_preventivo', dati_cliente.get('descrizione', ''))}" style="width: calc(100% - 30mm);">
            </td>
        </tr>
    </table>

    <!-- SEZIONE MATERIALI -->
    {materiali_html}

    <!-- TABELLA OPERAZIONI -->
    <table class="operations-table">
        <thead>
            <tr>
                <th style="width: 12%;">Operazione</th>
                <th style="width: 8%;">Inizio</th>
                <th style="width: 8%;">Fine</th>
                <th style="width: 8%;">Tempo</th>
                <th style="width: 8%;">Pezzi</th>
                <th style="width: 8%;">Data</th>
                <th style="width: 48%;">Note</th>
            </tr>
        </thead>
        <tbody>
            {ops_rows_html}
        </tbody>
    </table>
</body>
</html>
        """