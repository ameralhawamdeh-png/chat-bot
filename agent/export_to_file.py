
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from docx import Document
import pandas as pd
from pandas.api.types import is_datetime64tz_dtype


def export_to_pdf(data, filename="report.pdf"):
    
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    table_data = [list(data[0].keys())] + [list(row.values()) for row in data]
    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold")
    ]))
    elements = [Paragraph("Exported Report", styles["Title"]), table]
    doc.build(elements)
    return filename

def export_to_word(data, filename="report.docx"):
    doc = Document()
    table = doc.add_table(rows=1, cols=len(data[0]))
    hdr_cells = table.rows[0].cells
    for i, key in enumerate(data[0].keys()):
        hdr_cells[i].text = str(key)
    for row in data:
        row_cells = table.add_row().cells
        for i, value in enumerate(row.values()):
            row_cells[i].text = str(value)
    doc.save(filename)
    return filename

# def export_to_excel(data, filename="report.xlsx"):
#     df = pd.DataFrame(data)
#     df.to_excel(filename, index=False)
#     return filename
def export_to_excel(data, filename="report.xlsx"):
    df = pd.DataFrame(data)

    # Remove timezone info from any datetime columns
    for col in df.columns:
        if is_datetime64tz_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    df.to_excel(filename, index=False)
    return filename