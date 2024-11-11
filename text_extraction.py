import re

class TextExtractor:
    """Regex-based information extraction from OCR output."""
    
    @staticmethod
    def extract_date(text):
        pattern = r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b"
        match = re.search(pattern, text)
        if match:
            day, month, year = match.groups()
            day, month, year = int(day), int(month), int(year)
            if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                if month == 2:
                    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                        if day > 29:
                            return "N/A"
                    else:
                        if day > 28:
                            return "N/A"
                elif month in [4, 6, 9, 11] and day > 30:
                    return "N/A"
                return f"{str(day).zfill(2)}/{str(month).zfill(2)}/{str(year)}"
        return "N/A"

    @staticmethod
    def extract_time(text):
        time_pattern = r"\b(\d{2}):(\d{2})(?::\d{2})?\b"
        match = re.search(time_pattern, text)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            if 0 <= hour < 24 and 0 <= minute < 60:
                return f"{str(hour).zfill(2)}:{str(minute).zfill(2)}"
        return "N/A"

    @staticmethod
    def extract_total_cost(text):
        pattern = r"(?:TOPLAM|TUTAR)\s*[:\.]?\s*[\*\©\#]?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{1,2}))"
        match = re.search(pattern, text)
        return match.group(1).replace(',', '.') if match else "N/A"

    @staticmethod
    def extract_vat(text):
        pattern = r"(?:TOPKDV|TOPLAM KDV|KDV(?:\s+\w+)?)\s*[:\.]?\s*[\*\+\s]?[\#]?\s*(\d{1,3}(?:\.\d{3})*(?:,\s*\d{1,2}))"
        match = re.search(pattern, text)
        return match.group(1).replace(',', '.').replace(' ', '') if match else "N/A"

    @staticmethod
    def extract_tax_office_name(text):
        pattern = r"([A-ZÇĞİÖŞÜa-zçğıöşü\s\.]+?)\s*(?:(?:VD|V\.?D\.?|VERGİ DAİRESİ|VN)\s*[:\-]?)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            matched_name = match.group(1).strip()
            if matched_name:
                return matched_name.split()[-1]
            else:
                return "N/A"
        return "N/A"

    @staticmethod
    def extract_tax_office_number(text):
        lines = text.splitlines()
        keywords = [r"\bVD\b", r"\bVERGİ DAİRESİ\b", r"\bVN\b", r"\bVKN\b", r"\bTCKN\b", r"\bV\.D\."]
        for line in lines:
            if any(re.search(keyword, line, re.IGNORECASE) for keyword in keywords):
                match = re.search(r"(?:(?:V\.?D\.?|VD|VERGİ DAİRESİ|VN|VKN|TCKN)\s*[:\-]?\s*)?(\d{10,11})", line)
                if match:
                    return match.group(1).strip()
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
    def extract_invoice_number(text):
        patterns = [r"FİŞ NO[:\s]*([A-Za-z0-9\-]+)"]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "N/A"