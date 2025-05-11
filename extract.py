import pytesseract
from pdf2image import convert_from_bytes
from io import BytesIO
import PyPDF2

def extract_text_from_pdf(pdf_asbytes):
    try:
        reader= PyPDF2.PdfReader(BytesIO(pdf_asbytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ''
        if text.strip():
            return text
    except Exception as e:
        print(f"Error reading for first step  of pdf scan : {e}")
        return None
def extract_text_from_scanned_pdf(pdf_asbytes):
    try:
        pages = convert_from_bytes(pdf_asbytes,300)
        text = ""
        for page in pages:
            print("trying for scanning")  
            text += pytesseract.image_to_string(page)
            text+=text+"\n"
        return text
    except Exception as e:
        print(f"Error reading for second step of  PDF: {e}")
        return None
 