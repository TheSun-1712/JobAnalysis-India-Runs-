from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any

def xml_escape(val: Any) -> str:
    if val is None:
        return ""
    s = str(val)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

def write_xlsx(rows: list[dict[str, Any]], output_path: str | Path) -> Path:
    """
    Write ranking rows to an Excel (.xlsx) file using only standard python zipfile and XML.
    Each row in rows must have candidate_id, rank, score, and reasoning.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. [Content_Types].xml
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        '  <Default Extension="xml" ContentType="application/xml"/>\n'
        '  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>\n'
        '  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>\n'
        '</Types>'
    )
    
    # 2. _rels/.rels
    dot_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>\n'
        '</Relationships>'
    )
    
    # 3. xl/workbook.xml
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">\n'
        '  <sheets>\n'
        '    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>\n'
        '  </sheets>\n'
        '</workbook>'
    )
    
    # 4. xl/_rels/workbook.xml.rels
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>\n'
        '</Relationships>'
    )
    
    # 5. xl/worksheets/sheet1.xml
    sheet_lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        '  <sheetData>'
    ]
    
    # Header Row
    headers = ["candidate_id", "rank", "score", "reasoning"]
    sheet_lines.append('    <row r="1">')
    cols = ["A", "B", "C", "D"]
    for col, h in zip(cols, headers):
        sheet_lines.append(f'      <c r="{col}1" t="inlineStr"><is><t>{xml_escape(h)}</t></is></c>')
    sheet_lines.append('    </row>')
    
    # Data Rows
    for r_idx, row in enumerate(rows, start=2):
        sheet_lines.append(f'    <row r="{r_idx}">')
        # candidate_id
        sheet_lines.append(f'      <c r="A{r_idx}" t="inlineStr"><is><t>{xml_escape(row["candidate_id"])}</t></is></c>')
        # rank
        sheet_lines.append(f'      <c r="B{r_idx}"><v>{int(row["rank"])}</v></c>')
        # score
        sheet_lines.append(f'      <c r="C{r_idx}"><v>{float(row["score"]):.6f}</v></c>')
        # reasoning
        sheet_lines.append(f'      <c r="D{r_idx}" t="inlineStr"><is><t>{xml_escape(row["reasoning"])}</t></is></c>')
        sheet_lines.append('    </row>')
        
    sheet_lines.extend([
        '  </sheetData>',
        '</worksheet>'
    ])
    sheet_xml = "\n".join(sheet_lines)
    
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", dot_rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        
    return path
