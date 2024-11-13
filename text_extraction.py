import re
from fuzzywuzzy import process

class TextExtractor:
    @staticmethod
    def extract_tax_office_name(text):
        def get_best_match(word, choices):
            matches = process.extract(word, choices, limit=5)
            min_score = 45
            good_matches = [(name, score) for name, score in matches if score >= min_score]
            if not good_matches:
                return None
            return max(good_matches, key=lambda x: x[1])[0]

        vd_patterns = [
            r"VERGİ\s*DAİRESİ\s*:?\s*([A-ZÇĞİÖŞÜa-zçğıöşü\s\.]+?)(?:\s|$)",
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\s\.]+?)\s*(?:(?:VD|V\.?D\.?|VERGİ DAİRESİ|VN)\s*[:\-]?)",
            r"\b(\w+\s+KURUMLAR)\b",
            r"V\.D\.([A-ZÇĞİÖŞÜa-zçğıöşü\s\.]+)",
            r"([A-ZÇĞİÖŞÜa-zçğıöşü]+)\s*V\.D\."
        ]
        
        try:
            with open('vergidaireleri.txt', 'r', encoding='utf-8') as f:
                tax_offices = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return "N/A"
        
        if not tax_offices:
            return "N/A"

        for pattern in vd_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                matched_name = match.group(1).strip()
                best_match = get_best_match(matched_name.upper(), tax_offices)
                if best_match:
                    return best_match

        return "N/A"

    @staticmethod
    def extract_date(text):
        patterns = [
            r"\b(\d{1,2})-(\d{1,2})-(\d{4})\b",
            r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b",
            r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                day, month, year = map(int, match.groups())
                if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                    if month == 2:
                        is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
                        if (is_leap and day > 29) or (not is_leap and day > 28):
                            continue
                    if month in [4, 6, 9, 11] and day > 30:
                        continue
                    return f"{str(day).zfill(2)}/{str(month).zfill(2)}/{str(year)}"
            
        return "N/A"

    @staticmethod
    def extract_time(text):
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
    def extract_total_cost(text):
        pattern = r"(?:TOPLAM|TUTAR|TOP)\s*[:.\*\★\©\#]?\s*(\d{1,3}(?:\.\d{3})*(?:[.,]\d{2})?|\d+(?:[.,]\d{2})?)(?:\s*TL)?"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).replace(',', '.') if match else "N/A"

    @staticmethod
    def extract_vat(text):
        pattern = r"(?:TOPKDV|TOPLAM KDV|KDV(?:\s+\w+)?)\s*[:\.]?\s*[\*\+\s]?[\#]?\s*(\d{1,3}(?:\.\d{3})*(?:,\s*\d{1,2}))"
        match = re.search(pattern, text)
        return match.group(1).replace(',', '.').replace(' ', '') if match else "N/A"

    @staticmethod
    def extract_tax_office_number(text):
        patterns = [
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
                    return match.group(1)
        
        return "N/A"

    @staticmethod
    def extract_product_names(text):
        product_names = re.findall(r"([A-Za-zÇĞİÖŞÜçğıöşü\s]+)\s+\d+\s*\*", text)
        return [name.strip() for name in product_names] if product_names else []

    @staticmethod
    def extract_product_costs(text):
        product_costs = re.findall(r"\*\s*([\d.,]+)", text)
        return [cost.strip() for cost in product_costs] if product_costs else []

    @staticmethod
    def extract_payment_methods(text):
        patterns = [
            r"(?:KREDİ KARTI|NAKİT|BANKA KARTI|ÇEK|HAVALE|EFT)\s*[:\-]?\s*(\d{1,3}(?:\.\d{3})*(?:[.,]\d{2})?|\d+(?:[.,]\d{2})?)"
        ]
        payment_methods = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            payment_methods.extend(matches)
        return payment_methods if payment_methods else "N/A"

    @staticmethod
    def extract_all(texts):
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