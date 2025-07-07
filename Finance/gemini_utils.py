import google.generativeai as genai
from PIL import Image
import json
import fitz  # PyMuPDF
import os

genai.configure(api_key="AIzaSyD2RsJD7nS7oCXgemSoNpujaj0th9PZySA")
model = genai.GenerativeModel('gemini-1.5-flash')

def extract_receipt_info_gemini(filepath):
    image = Image.open(filepath)

    prompt = """Find the total amount in the POS receipt and return:
    {
      "amount": float,
      "date": "yyyy-mm-dd",
      "description": "string"
    }
    Only return valid JSON. No explanation.
    """

    try:
        response = model.generate_content([prompt, image])
        raw = response.text.strip()
        json_text = raw[raw.find('{'): raw.rfind('}') + 1]
        data = json.loads(json_text)

        return {
            "amount": float(data.get("amount", 0)),
            "date": data.get("date", "-"),
            "description": data.get("description", "Receipt Transaction"),
            "type": "expense",
            "category": "Receipt"
        }

    except Exception as e:
        print("Gemini OCR error:", e)
        return {
            "amount": 0,
            "date": "-",
            "type": "expense",
            "category": "Receipt"
        }

def extract_transactions_from_pdf(filepath):
    try:
        text = ""
        with fitz.open(filepath) as doc:
            for page in doc:
                text += page.get_text()

        prompt = """
        Find the total amount in the POS receipt and return:
        [
          {
            "date": "yyyy-mm-dd",
            "amount": float,
            "type": "income" or "expense",
            "description": "string",
            "category": "string"
          }
        ]
        Only return the JSON array. Do not include any extra text or explanation.
        """

        response = model.generate_content([prompt, text])
        raw = response.text.strip()

        json_start = raw.find('[')
        json_end = raw.rfind(']') + 1
        json_data = raw[json_start:json_end]

        transactions = json.loads(json_data)
        return transactions

    except Exception as e:
        print("Gemini PDF parsing error:", e)
        return []
