import re
import pdfplumber
import json
from anthropic import Anthropic

def extract_text_from_pdf(pdf_file) -> str:
    """Extract all text from a PDF file."""
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def layer_1_regex_extract(text: str) -> dict:
    """Layer 1: Fast Regex-based extraction."""
    data = {
        "employee_name": None,
        "pan": None,
        "old_gross": None,
        "old_tds": None,
        "new_basic": None,
        "new_hra": None,
        "new_special_allowance": None,
        "employment_start": None,
        "employment_end": None,
        "old_employer_name": None,
        "old_employer_tan": None
    }
    
    # 0. Employee Name (Simple attempt)
    name_match = re.search(r'(?:Name|Employee Name)\s*[:\-]?\s*([A-Za-z\s]+)(?:\n|$)', text, re.IGNORECASE)
    if name_match:
        data["employee_name"] = name_match.group(1).strip()
        
    # 1. PAN (10 chars: 5 letters, 4 numbers, 1 letter)
    pan_match = re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', text, re.IGNORECASE)
    if pan_match:
        data["pan"] = pan_match.group(0).upper()
        
    # 2. TAN (10 chars: 4 letters, 5 numbers, 1 letter)
    tan_match = re.search(r'\b[A-Z]{4}[0-9]{5}[A-Z]{1}\b', text, re.IGNORECASE)
    if tan_match:
        data["old_employer_tan"] = tan_match.group(0).upper()
        
    # 3. Simple regex for Gross and TDS (highly dependent on format)
    # Looking for lines like "Gross Salary 1500000"
    gross_match = re.search(r'Gross\s+(?:Salary|Earnings).*?(?:Rs\.?|INR)?\s*([\d,]+(?:\.\d{2})?)', text, re.IGNORECASE)
    if gross_match:
        val = gross_match.group(1).replace(',', '')
        try:
            data["old_gross"] = float(val)
        except:
            pass
            
    tds_match = re.search(r'TDS.*?([\d,]+(?:\.\d{2})?)', text, re.IGNORECASE)
    if tds_match:
        val = tds_match.group(1).replace(',', '')
        try:
            data["old_tds"] = float(val)
        except:
            pass
            
    return data

def layer_2_llm_extract(text: str, current_data: dict, api_key: str) -> dict:
    """Layer 2: LLM Fallback extraction if API key provided."""
    if not api_key:
        return current_data
        
    prompt = f"""
    You are an expert Indian payroll and tax document parser.
    Extract the following details from the document text. Return ONLY a valid JSON object. Do not include markdown formatting or explanations.
    Keys to return:
    - "pan" (string)
    - "old_gross" (number)
    - "old_tds" (number)
    - "new_basic" (number)
    - "new_hra" (number)
    - "new_special_allowance" (number)
    - "employment_start" (string)
    - "employment_end" (string)
    - "old_employer_name" (string)
    - "old_employer_tan" (string)
    
    If a value is not found, set it to null.
    
    Document Text:
    {text[:5000]} # Limit to 5000 chars to save tokens
    """
    
    try:
        client = Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        response_text = message.content[0].text.strip()
        # Clean up if the model includes markdown
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]
        elif response_text.startswith("```"):
            response_text = response_text[3:-3]
            
        llm_data = json.loads(response_text)
        
        # Merge, preferring LLM data if current_data is None
        for k, v in llm_data.items():
            if current_data.get(k) is None and v is not None:
                current_data[k] = v
                
    except Exception as e:
        print(f"LLM Extraction failed: {e}")
        
    return current_data

def parse_document(pdf_file, api_key: str = None) -> dict:
    """Main parsing orchestrator with fallback."""
    text = extract_text_from_pdf(pdf_file)
    
    # Layer 1
    data = layer_1_regex_extract(text)
    
    # Check if we need Layer 2 (if key fields are missing)
    missing_critical = (data["pan"] is None or data["old_gross"] is None or data["old_tds"] is None)
    if missing_critical and api_key:
        data = layer_2_llm_extract(text, data, api_key)
        
    # Layer 3 will be handled by the UI (we just return whatever we have)
    return data
