from io import BytesIO
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

def export_roster_to_excel(roster_data, year, month):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Roster {month}-{year}"

    header_fill = PatternFill(start_color="1A252F", end_color="1A252F", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    center = Alignment(horizontal="center", vertical="center")
    border = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )

    headers = ["Date", "Analyst", "Role / Tier", "Shift Assigned"]
    ws.append(headers)

    for col in range(1, 5):
        cell = ws.cell(row=1, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center

    for idx, item in enumerate(roster_data, start=2):
        ws.cell(row=idx, column=1, value=item['Date']).alignment = center
        ws.cell(row=idx, column=2, value=item['Analyst'])
        ws.cell(row=idx, column=3, value=item['Role']).alignment = center
        
        shift_cell = ws.cell(row=idx, column=4, value=item['Shift'])
        shift_cell.alignment = center
        
        for c in range(1, 5):
            ws.cell(row=idx, column=c).border = border

    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 18

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream