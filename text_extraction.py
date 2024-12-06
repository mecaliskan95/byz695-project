import re
from datetime import datetime

class TextExtractor:
    @staticmethod
    def extract_tax_office_name(text):
        with open('vergidaireleri.txt', 'r', encoding='utf-8') as f:
            valid_offices = {office.strip().upper() for office in f.readlines()}

        patterns = [
            r"([A-ZÇĞİÖŞÜa-zçğıöşü]+)\s*V\.?D\.?",
            r"VERGİ\s*DAİRESİ\s*:?\s*([A-ZÇĞİÖŞÜa-zçğıöşü]+)",
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)\s*(V\.D\.|VERGİ DAİRESİ)"
        ]
        
        for pattern in patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                found_name = match.group(1).strip().upper()
                for office in valid_offices:
                    if found_name in office or office in found_name:
                        return office
                return found_name
        return "N/A"

    @staticmethod
    def extract_date(text):
        pattern = r"\b(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})\b"
        if match := re.search(pattern, text):
            day, month, year = map(int, match.groups())
            try:
                return datetime(year, month, day).strftime("%d/%m/%Y")
            except:
                return "N/A"
        return "N/A"

    @staticmethod
    def extract_time(text):
        pattern = r"\b(\d{2}):(\d{2})(?::(\d{2}))?\b"
        if match := re.search(pattern, text):
            hour, minute = map(int, match.groups()[:2]) 
            if 0 <= hour < 24 and 0 <= minute < 60:
                return f"{hour:02d}:{minute:02d}"
        return "N/A"

    @staticmethod
    def extract_total_cost(text):
        patterns = [
            r"TOPLAM\s*\*?\s*(\d+(?:[\s,.]\d{2})?)",
            r"TOPLAM\s*:?\s*([\d{1,3}(?:\.\d{3})*,]*\d+)"
        ]
        for pattern in patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                return match.group(1).replace(' ', '').replace('.', '').replace(',', '.')
        return "N/A"

    @staticmethod
    def extract_vat(text):
        pattern = r"KDV\s*\*?\s*(\d+(?:,\d{2})?)"
        if match := re.search(pattern, text):
            return match.group(1).replace(',', '.')
        return "N/A"

    @staticmethod
    def extract_tax_office_number(text):
        pattern = r"(?:.*)?(?:V\.?D\.?\s*:?\s*|VKN\\TCKN\s*:?\s*)(\d{10})"
        if match := re.search(pattern, text):
            return match.group(1)
        return "N/A"

    @staticmethod
    def extract_payment_methods(text):
        pattern = r"\b(KREDİ KARTI|NAKİT|BANKA KARTI|ÇEK|HAVALE|EFT)\b"
        if match := re.search(pattern, text, re.IGNORECASE):
            return match.group(1).upper()
        return "N/A"

    @staticmethod
    def extract_all(texts, filenames=None):
        results = []
        if filenames is None:
            filenames = ["Unnamed"] * len(texts)
            
        for text, filename in zip(texts, filenames):
            result = {
                "filename": filename,
                "date": TextExtractor.extract_date(text),
                "time": TextExtractor.extract_time(text),
                "tax_office_name": TextExtractor.extract_tax_office_name(text),
                "tax_office_number": TextExtractor.extract_tax_office_number(text),
                "total_cost": TextExtractor.extract_total_cost(text),
                "vat": TextExtractor.extract_vat(text),
                "payment_methods": TextExtractor.extract_payment_methods(text),
                "text": text
            }
            results.append(result)
        return results