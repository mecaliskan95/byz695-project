import re
from fuzzywuzzy import process
from datetime import datetime
from typing import Union

class TextExtractor:
    @staticmethod
    def extract_tax_office_name(text: str) -> str:
        def get_best_match(word: str, choices: list[str]) -> str:
            # Normalize the word for common OCR errors
            word = word.upper().strip()
            word = word.replace('I', 'İ').replace('E', 'E')
            matches = process.extract(word, choices, limit=5)
            min_score = 80  # Lower threshold to handle OCR errors
            good_matches = [(name, score) for name, score in matches if score >= min_score]
            if not good_matches:
                return None
            return max(good_matches, key=lambda x: x[1])[0]

        vd_patterns = [
            # Add pattern specifically for EMDAG V.D. format
            r"([A-ZÇĞİÖŞÜa-zçğıöşü]+)\s*V\.?D\.?[/\s]",
            r"VERGİ\s*DAİRESİ\s*:?\s*([A-ZÇĞİÖŞÜa-zçğıöşü\s\.]+?)(?:\s|$)",
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\s\.]+?)\s*(?:(?:VD|V\.?D\.?|VERGİ DAİRESİ|VN)\s*[:\-]?)",
            r"\b(\w+\s+KURUMLAR)\b",
            r"V\.D\.([A-ZÇĞİÖŞÜa-zçğıöşü\s\.]+)",
            r"([A-ZÇĞİÖŞÜa-zçğıöşü]+)\s*V\.D\.",
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\s\.]+)\s+V\.D\.\s+\d{10,11}",  # Specific pattern for tax office name followed by number
            r"([A-ZÇĞİÖŞÜa-zçğıöşü]+)\s+\d{10,11}",  # Specific pattern for tax office name followed by number without spaces
            r"VERGİ DAİRESİ BAŞKANLIĞI\s*:?\s*([A-ZÇĞİÖŞÜa-zçğıöşü\s\.]+?)(?:\s|$)",
            r"VDB\s*:?\s*([A-ZÇĞİÖŞÜa-zçğıöşü\s\.]+?)(?:\s|$)"
        ]
        
        try:
            with open('vergidaireleri.txt', 'r', encoding='utf-8') as f:
                tax_offices = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return "N/A"
        
        if not tax_offices:
            return "N/A"

        for pattern in vd_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                matched_name = match.group(1).strip()
                if matched_name:
                    best_match = get_best_match(matched_name.upper(), tax_offices)
                    if best_match:
                        return best_match

        return "N/A"

    @staticmethod
    def extract_date(text: str) -> str:
        patterns = [
            r"\b(\d{1,2})-(\d{1,2})-(\d{4})\b",
            r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b",
            r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
            r"(?:TARIH|TARİH)\s*[:\-]?\s*(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})",
            r"\b(\d{1,2})/(\d{1,2})/(\d{4})\s+\d{1,2}:\d{2}",
            r"(?:TARIH|TARİH)\s*[:\-]?\s*(\d{1,2})/(\d{1,2})/(\d{4})",
            r"(?:TARIH|TARİH)\s*[:\-]?\s*(\d{1,2})-(\d{1,2})-(\d{4})",
            r"(?:TARIH|TARİH)\s*[:\-]?\s*(\d{1,2})\.(\d{1,2})\.(\d{4})",
            r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",  # MM/DD/YYYY
            r"\b(\d{2})-(\d{2})-(\d{4})\b",  # DD-MM-YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day, month, year = map(int, match.groups()[-3:])
                try:
                    if pattern == r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b" and month > 12:
                        month, day = day, month
                    date = datetime(year, month, day)
                    return date.strftime("%d/%m/%Y")
                except ValueError:
                    continue
            
        return "N/A"

    @staticmethod
    def extract_time(text: str) -> str:
        time_patterns = [
            r"\b(\d{2}):(\d{2}):(\d{2})\b",
            r"\b(\d{2}):(\d{2})\b"
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                hour, minute = int(match.group(1)), int(match.group(2))
                if 0 <= hour < 24 and 0 <= minute < 60:
                    return f"{str(hour).zfill(2)}:{str(minute).zfill(2)}"
            
        return "N/A"

    @staticmethod
    def extract_total_cost(text: str) -> str:
        pattern = r"(?<!KDV)(?<!TOP)\s*(?:TOPLAM|TUTAR|TOP)\s*\*?\s*(\d+(?:[\s,.]+\d{1,3})*(?:[,.]\d{2})?)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Clean up the number by removing spaces and standardizing decimal separator
            total_str = match.group(1)
            # Handle numbers with thousands separator
            total_str = total_str.replace(' ', '').replace('.', '')
            if ',' in total_str:
                parts = total_str.split(',')
                total_cost = parts[0] + '.' + parts[1] if len(parts) > 1 else parts[0]
            else:
                total_cost = total_str + '.00'
            return total_cost
        return "N/A"

    @staticmethod
    def extract_vat(text: str) -> str:
        pattern = r"(?:TOPKDV|TOPLAM KDV|KDV(?:\s+\w+)?)\s*[:\.«]?\s*[\*\+\s]?[\#]?\s*(\d{1,3}(?:\.\d{3})*(?:,\s*\d{1,2}))"
        match = re.search(pattern, text)
        return match.group(1).replace(',', '.').replace(' ', '') if match else "N/A"

    @staticmethod
    def extract_tax_office_number(text: str) -> str:
        patterns = [
            r'(?:VD|V\.?D\.?|VERGİ DAİRESİ)\s*:?\s*(\d+(?:\s+\d+)*)',
            r'(?:VD|V\.?D\.?|VERGİ DAİRESİ)\s*:?\s*(\d{10,11})',
            r'(\d{10,11})\s*(?:VD|V\.?D\.?|VERGİ DAİRESİ)',
            r'(?:VKN|TCKN|VN)\s*:?\s*(\d{10,11})',
            r'MÜKELLEFLER\s+V\.?D\.?\s+(\d{10,11})',
            r'KURUMLAR\s*;?\s*(\d{10,11})',
            r'\b(\d{10,11})\b'
        ]
        
        for line in text.splitlines():
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    number = match.group(1).replace(' ', '')
                    if len(number) in [10, 11]:
                        return number
        
        return "N/A"

    @staticmethod
    def extract_product_names(text: str) -> list[str]:
        product_names = re.findall(r"([A-Za-zÇĞİÖŞÜçğıöşü\s]+)\s+\d+\s*\*", text)
        return [name.strip() for name in product_names] if product_names else []

    @staticmethod
    def extract_product_costs(text: str) -> list[str]:
        product_costs = re.findall(r"\*\s*([\d.,]+)", text)
        return [cost.strip() for cost in product_costs] if product_costs else []

    @staticmethod
    def extract_payment_methods(text: str) -> Union[list[str], str]:
        patterns = [
            r"\b(KREDI KARTI|KREDİ KARTI|KREDİ|NAKIT|NAKİT|BANKA KARTI|ÇEK|HAVALE|EFT)\b"
        ]
        payment_methods = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            payment_methods.update(matches)
        if not payment_methods:
            return "N/A"
        payment_methods = ["KREDİ KARTI" if method.upper() in ["KREDİ", "KREDI KARTI"] else method for method in payment_methods]
        payment_methods = ["NAKİT" if method.upper() == "NAKIT" else method for method in payment_methods]
        payment_methods = list(set(payment_methods))  # Ensure unique values
        return payment_methods[0] if len(payment_methods) == 1 else payment_methods

    @staticmethod
    def extract_all(texts: list[str]) -> list[dict]:
        results = []
        for text in texts:
            result = {
                "date": TextExtractor.extract_date(text),
                "time": TextExtractor.extract_time(text),
                "tax_office_name": TextExtractor.extract_tax_office_name(text),
                "tax_office_number": TextExtractor.extract_tax_office_number(text),
                "product_names": TextExtractor.extract_product_names(text),
                "product_costs": TextExtractor.extract_product_costs(text),
                "payment_methods": TextExtractor.extract_payment_methods(text),
                "total_cost": TextExtractor.extract_total_cost(text),
                "vat": TextExtractor.extract_vat(text),
                "text": text
            }
            results.append(result)
        return results