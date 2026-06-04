import io
from fpdf import FPDF

def generate_form_12b(data: dict) -> bytes:
    """Generate Form 12B under Rule 26A."""
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "FORM NO. 12B", ln=True, align="C")
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "[See rule 26A]", ln=True, align="C")
    pdf.cell(0, 10, "Form for furnishing details of income under section 192(2) for the year ending 31st March, 2026", ln=True, align="C")
    pdf.ln(5)
    
    # Employee details
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Name and address of the employee: {data.get('employee_name', '_______________________')}", ln=True)
    pdf.cell(0, 8, f"Permanent Account Number (PAN): {data.get('pan', '__________')}", ln=True)
    pdf.cell(0, 8, "Residential status: Resident", ln=True)
    pdf.ln(5)
    
    # Part A
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Part A - Previous Employer Details", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Name and address of previous employer: {data.get('old_employer_name', '_______________________')}", ln=True)
    pdf.cell(0, 8, f"TAN of the previous employer: {data.get('old_employer_tan', '__________')}", ln=True)
    pdf.cell(0, 8, f"Period of employment: {data.get('employment_start', '____')} to {data.get('employment_end', '____')}", ln=True)
    pdf.ln(5)
    
    # Part B
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Part B - Details of Salary, Perquisites and Profits in lieu of Salary", ln=True)
    pdf.set_font("Arial", "", 11)
    gross = data.get('old_gross', 0.0)
    pdf.cell(0, 8, f"1. Salary Paid: Rs. {gross:,.2f}", ln=True)
    pdf.cell(0, 8, "2. Value of perquisites: Rs. 0.00", ln=True)
    pdf.cell(0, 8, "3. Profits in lieu of salary: Rs. 0.00", ln=True)
    pdf.cell(0, 8, f"4. Total: Rs. {gross:,.2f}", ln=True)
    pdf.ln(5)
    
    # Part C
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Part C - Details of Tax Deducted at Source (TDS)", ln=True)
    pdf.set_font("Arial", "", 11)
    tds = data.get('old_tds', 0.0)
    pdf.cell(0, 8, f"Total tax deducted and deposited by previous employer: Rs. {tds:,.2f}", ln=True)
    pdf.cell(0, 8, "Challan Details: As per Form 26AS / Part A of Form 16", ln=True)
    pdf.ln(10)
    
    # Verification
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Verification", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, f"I, {data.get('employee_name', '_______________________')}, do hereby declare that what is stated above is true to the best of my information and belief.")
    pdf.ln(10)
    pdf.cell(0, 8, "Date: _______________", ln=True)
    pdf.cell(0, 8, "Place: ______________", ln=True)
    pdf.cell(0, 8, "Signature: _______________________", ln=True, align="R")
    
    return bytes(pdf.output(dest="S"))

def generate_sec_192_letter(data: dict) -> bytes:
    """Generate Section 192(2) Employer Letter."""
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, "Date: _______________", ln=True)
    pdf.ln(5)
    
    pdf.cell(0, 8, "To,", ln=True)
    pdf.cell(0, 8, "The HR / Finance Department", ln=True)
    pdf.cell(0, 8, f"{data.get('new_employer_name', '_______________________')}", ln=True)
    pdf.ln(5)
    
    pdf.cell(0, 8, "Subject: Request for aggregation of previous employer's income and TDS under Section 192(2)", ln=True)
    pdf.ln(5)
    
    pdf.cell(0, 8, "Dear Sir/Madam,", ln=True)
    pdf.ln(2)
    
    body = (
        f"I, {data.get('employee_name', '_______________________')}, holding PAN {data.get('pan', '__________')}, "
        f"joined your esteemed organization recently. Prior to this, I was employed with "
        f"{data.get('old_employer_name', '_______________________')} from {data.get('employment_start', '____')} "
        f"to {data.get('employment_end', '____')}.\n\n"
        
        f"As per the provisions of Section 192(2) of the Income Tax Act, 1961, I am furnishing the details "
        f"of the income paid and tax deducted at source (TDS) by my previous employer. I have also enclosed "
        f"Form 12B for your ready reference.\n\n"
        
        f"Gross Salary from previous employer: Rs. {data.get('old_gross', 0.0):,.2f}\n"
        f"TDS deducted by previous employer: Rs. {data.get('old_tds', 0.0):,.2f}\n\n"
        
        f"I request you to kindly consider this past income and TDS while calculating my overall tax liability "
        f"for the Financial Year 2025-26 and adjust the monthly TDS deduction for the remaining months accordingly. "
        f"This will help me avoid any short-deduction or advance tax interest liabilities at year-end."
    )
    
    pdf.multi_cell(0, 8, body)
    pdf.ln(10)
    
    pdf.cell(0, 8, "Thanking you,", ln=True)
    pdf.cell(0, 8, "Yours faithfully,", ln=True)
    pdf.ln(8)
    pdf.cell(0, 8, "Signature: _______________________", ln=True)
    pdf.cell(0, 8, f"Name: {data.get('employee_name', '_______________________')}", ln=True)
    
    return bytes(pdf.output(dest="S"))
