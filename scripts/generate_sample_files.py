import os
import sys
import docx
import openpyxl
from pypdf import PdfWriter
import io

# Directory for sample files
SAMPLE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_test_files"))
os.makedirs(SAMPLE_DIR, exist_ok=True)

def generate_docx_sample():
    """Generates a realistic Marketing Proposal in DOCX format with synthetic PII"""
    doc = docx.Document()
    doc.add_heading("Apex Wealth Management - 2024 Private Portfolio Proposal", 0)
    
    doc.add_paragraph("Client Name: Robert Henderson")
    doc.add_paragraph("Email: robert.henderson@examplecorp.com")
    doc.add_paragraph("Phone: (555) 234-5678")
    doc.add_paragraph("Account Number: ACCT-982341")
    doc.add_paragraph("Address: 742 Evergreen Terrace, Springfield, IL 62704")
    doc.add_paragraph("Target Portfolio Value: $1,500,000")
    
    doc.add_heading("Executive Summary", level=1)
    doc.add_paragraph(
        "Dear Mr. Henderson,\n\n"
        "We are pleased to present this tailored investment strategy for your retirement portfolio. "
        "Our core thesis focuses on blue-chip dividend growth and short-duration Treasury notes. "
        "Over the past 12 months, our conservative growth sleeve delivered an exceptional return of 14.8% net of fees, "
        "outperforming the benchmark by 220 basis points."
    )

    doc.add_heading("Proposed Asset Allocation", level=2)
    table = doc.add_table(rows=1, cols=3)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Asset Class"
    hdr_cells[1].text = "Target %"
    hdr_cells[2].text = "Expected Yield"

    data = [
        ("US Large Cap Equities", "45%", "2.1%"),
        ("Short-Term US Treasuries", "35%", "4.8%"),
        ("Municipal Bonds", "15%", "3.6%"),
        ("Cash & Equivalents", "5%", "5.1%")
    ]
    for ac, pct, yld in data:
        row_cells = table.add_row().cells
        row_cells[0].text = ac
        row_cells[1].text = pct
        row_cells[2].text = yld

    doc.add_heading("Important Regulatory Disclosures", level=1)
    doc.add_paragraph(
        "Past performance is not indicative of future results. Investing in securities involves risk of loss. "
        "Securities offered through Apex Wealth Partners LLC, an SEC-Registered Investment Advisor. "
        "This document does not constitute tax or legal advice. Please consult your independent CPA."
    )

    file_path = os.path.join(SAMPLE_DIR, "sample_compliant_proposal.docx")
    doc.save(file_path)
    print(f"Generated DOCX: {file_path}")
    return file_path

def generate_xlsx_sample():
    """Generates an Investment Performance Sheet in XLSX format"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Performance Summary"

    ws.append(["Apex Wealth Advisors - Performance & Fee Breakdown"])
    ws.append(["Advisor:", "Sarah Jenkins"])
    ws.append(["Client Name:", "Eleanor Vance"])
    ws.append(["Account Number:", "PORT-554129"])
    ws.append(["Client Email:", "eleanor.vance@vancetech.io"])
    ws.append([])

    ws.append(["Strategy Sleeve", "1-Year Net Return", "3-Year Ann.", "5-Year Ann.", "Annual Fee"])
    ws.append(["Global Dividend Growth", "11.4%", "8.7%", "9.2%", "0.75%"])
    ws.append(["Core Fixed Income", "5.1%", "3.8%", "4.1%", "0.50%"])
    ws.append(["Alternative Real Assets", "8.9%", "7.2%", "8.0%", "1.00%"])
    ws.append([])

    ws.append(["Disclosures:"])
    ws.append(["1. Past performance is no guarantee of future results."])
    ws.append(["2. Returns presented net of all management and custodial fees."])
    ws.append(["3. Not FDIC Insured | May Lose Value | No Bank Guarantee."])

    file_path = os.path.join(SAMPLE_DIR, "sample_performance_sheet.xlsx")
    wb.save(file_path)
    print(f"Generated XLSX: {file_path}")
    return file_path

def generate_noncompliant_pdf_text():
    """Generates a text/PDF containing prohibited promissory claims and synthetic PII"""
    # Create simple minimal valid PDF with plain stream
    pdf_content = """%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 450 >>
stream
BT
/F1 12 Tf
72 710 Td
(High-Growth Crypto Strategy - Guaranteed Returns) Tj
0 -24 Td
(Prepared for: Alice Wonderland) Tj
0 -18 Td
(Email: alice.wonderland@cryptomoon.org | Phone: 555-888-9999) Tj
0 -18 Td
(Account: ACCT-778899 | Net Worth: $2,500,000) Tj
0 -30 Td
(Our new High-Growth Alpha fund offers a guaranteed 25% annual return!) Tj
0 -18 Td
(This strategy is 100% risk-free and you can't lose money.) Tj
0 -18 Td
(We guarantee you will double your wealth in 24 months.) Tj
0 -30 Td
(Sign up today at our Springfield office.) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000222 00000 n 
0000000724 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
793
%%EOF
"""
    file_path = os.path.join(SAMPLE_DIR, "sample_noncompliant_promo.pdf")
    with open(file_path, "wb") as f:
        f.write(pdf_content.encode("latin1"))
    print(f"Generated PDF: {file_path}")
    return file_path

if __name__ == "__main__":
    generate_docx_sample()
    generate_xlsx_sample()
    generate_noncompliant_pdf_text()
    print("All sample files generated successfully!")
