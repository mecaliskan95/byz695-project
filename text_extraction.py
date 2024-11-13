import re
from fuzzywuzzy import process

class TextExtractor:
    @staticmethod
    def extract_tax_office_name(text):
        def get_best_match(word, choices):
            matches = process.extract(word, choices)
            min_score = 45
            good_matches = [(name, score) for name, score in matches if score >= min_score]
            
            if not good_matches:
                return None
                
            adjusted_matches = []
            for name, score in good_matches:
                length_diff = abs(len(word) - len(name))
                adjusted_score = score - (length_diff * 2)
                adjusted_matches.append((name, adjusted_score))
                
            return max(adjusted_matches, key=lambda x: x[1])[0]

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

        vd_word_pattern = r"(\w+)\s*V\.D\."
        match = re.search(vd_word_pattern, text, re.IGNORECASE)
        if match:
            word = match.group(1).strip().upper()
            best_match = get_best_match(word, tax_offices)
            if best_match:
                return best_match

        for pattern in vd_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                matched_name = match.group(1).strip()
                if matched_name:
                    for office in tax_offices:
                        if matched_name.upper() in office or office in matched_name.upper():
                            return office
                    
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
            if not match:
                continue
                
            day, month, year = map(int, match.groups())
            
            if not (1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100):
                continue
                
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
            if not match:
                continue
                
            hour, minute = int(match.group(1)), int(match.group(2))
            if 0 <= hour < 24 and 0 <= minute < 60:
                return f"{str(hour).zfill(2)}:{str(minute).zfill(2)}"
            
        return "N/A"

    @staticmethod
    def extract_total_cost(text):
        pattern = r"(?:TOPLAM|TUTAR|TOP)\s*[:.\*\★\©\#]?\s*(\d{1,3}(?:\.\d{3})*(?:[.,]\d{2})?|\d+(?:[.,]\d{2})?)(?:\s*TL)?"
        
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).replace(',', '.')
        return "N/A"

    @staticmethod
    def extract_vat(text):
        pattern = r"(?:TOPKDV|TOPLAM KDV|KDV(?:\s+\w+)?)\s*[:\.]?\s*[\*\+\s]?[\#]?\s*(\d{1,3}(?:\.\d{3})*(?:,\s*\d{1,2}))"
        match = re.search(pattern, text)
        return match.group(1).replace(',', '.').replace(' ', '') if match else "N/A"

    @staticmethod
    def extract_tax_office_number(text):
        lines = text.splitlines()
        
        tax_indicators = [
            r"\bVD\b", r"\bV\.?D\.?\b", r"\bVERGİ DAİRESİ\b", 
            r"\bVN\b", r"\bVKN\b", r"\bTCKN\b", 
            r"\bMÜKELLEFLER\b", r"\bKURUMLAR\b"
        ]
        
        patterns = [
            r'(?:VD|V\.?D\.?|VERGİ DAİRESİ)\s*:?\s*(\d{10,11})',
            r'(\d{10,11})\s*(?:VD|V\.?D\.?|VERGİ DAİRESİ)',
            r'(?:VKN|TCKN|VN)\s*:?\s*(\d{10,11})',
            r'MÜKELLEFLER\s+V\.?D\.?\s+(\d{10,11})',
            r'KURUMLAR\s*;?\s*(\d{10,11})',
            r'\b(\d{10,11})\b'
        ]
        
        for i, line in enumerate(lines):
            if any(re.search(indicator, line, re.IGNORECASE) for indicator in tax_indicators):
                for pattern in patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        return match.group(1)
                
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.replace(';', '').strip().isdigit() and len(next_line.replace(';', '').strip()) >= 10:
                        return next_line.replace(';', '').strip()
                    
                    numbers = re.findall(r'\b(\d{10,11})\b', next_line)
                    if numbers:
                        return numbers[0]
        
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
        patterns = [
            r"FI\$?\s*NO\s*:\s*(\d+)",
            r"F[İIiŞS\$][ŞS$]?\s*(?:NO|NU|N0)\s*[:.-]?\s*(\d{2,4})",
            r"(?:FIŞ|FIS|FİŞ|FİS|FI\$)\s*(?:NO|NU|N0)\s*[:.-]?\s*(\d{2,4})",
            r"FS\s*(?:NO|NU|N0)\s*[:.-]?\s*(\d{2,4})"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                result = match.group(1).strip()
                if result.isdigit() and 1 <= len(result) <= 4:
                    return result
        
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if re.search(r'F[İIiŞS\$]|FS|FIS|FİS|FI\$', line, re.IGNORECASE):
                numbers = re.findall(r'(?:NO|NU|N0)\s*[:.-]?\s*(\d{2,4})', line)
                if numbers:
                    return numbers[0]
                
                if i + 1 < len(lines):
                    numbers = re.findall(r'\b(\d{2,4})\b', lines[i + 1])
                    if numbers:
                        return numbers[0]
        
        return "N/A"