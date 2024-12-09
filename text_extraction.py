import re
from datetime import datetime
from fuzzywuzzy import fuzz
import easyocr

class TextExtractor:
    # Check if CUDA is available
    import torch
    use_gpu = torch.cuda.is_available()
    easyocr_reader = easyocr.Reader(['en', 'tr'], gpu=use_gpu)
    
    @staticmethod
    def find_sections(text):
        lines = text.splitlines()
        header_end = 0
        footer_start = len(lines)
        
        terms = {
            'header': {'TARİH', 'SAAT', 'FİŞ', 'VERGİ', 'VKN', 'VD', 'ADRES'},
            'footer': {'KDV', 'TOPLAM', 'NAKİT', 'KART', 'TUTAR', 'TOPKDV'}
        }
        
        for i, line in enumerate(lines):
            words = set(line.upper().split())
            if any(fuzz.ratio(term, word) > 80 for term in terms['header'] for word in words):
                header_end = max(header_end, i + 1)
            if any(fuzz.ratio(term, word) > 80 for term in terms['footer'] for word in words):
                footer_start = i
                break

        header = '\n'.join(lines[:header_end])
        body = '\n'.join(lines[header_end:footer_start])
        footer = '\n'.join(lines[footer_start:])
        
        return header, body, footer
    
    @staticmethod
    def extract_tax_office_name(text):
        with open('vergidaireleri.txt', 'r', encoding='utf-8') as f:
            valid_offices = {office.strip().upper() for office in f.readlines()}

        patterns = [
            r"(.+?)\s*V\.D", 
            r"VERGİ\s*DAİRESİ\s*[;:,]?\s*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)",
            r"\b([A-ZÇĞİÖŞÜa-zçğıöşü.\s]+)\s*V\.?D\.?", 
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)\s*(V\.D\.|VERGİ DAİRESİ)",
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)\s*VD\s*[:\s]*([\d\s]{10,11})"
        ]
        
        for pattern in patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                found_name = match.group(1).strip().upper()
                if found_name in valid_offices:
                    return found_name

                best_match = max(valid_offices, key=lambda office: fuzz.ratio(found_name, office), default=None)
                if best_match and fuzz.ratio(found_name, best_match) >= 70:
                    return best_match
                return found_name
            
        return "N/A"

    @staticmethod
    def extract_date(text):
        patterns = [
            r"\b(\d{2})[.](\d{2})[.](\d{4})\b",  # DD.MM.YYYY
            r"\b(\d{2})[/](\d{2})[/](\d{4})\b",  # DD/MM/YYYY
            r"\b(\d{2})[-](\d{2})[-](\d{4})\b"   # DD-MM-YYYY
        ]
        for pattern in patterns:
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
            r"TOPLAM\s*[\*\#:X]?\s*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)",
            r"TUTAR\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2}|\.\d{2})?)\s*TL?"
        ]
        for pattern in patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                value = match.group(1)
                return value.replace(',', '.') if ',' in value else value
        return "N/A"

    @staticmethod
    def extract_vat(text):
        patterns = [
            r"(?:KDV|TOPKDV)\s*[#*«Xx]?\s*(\d+(?:,\d{2})?)",
            r"(?:KDV|TOPKDV)\s*:\s*(\d+(?:,\d{2})?)"
            r"KDV\s[*]?\s?\d{1,3}(\.\d{3})*,\d{2}\s?[A-Z]?"
        ]
        for pattern in patterns:
            if match := re.search(pattern, text):
                return match.group(1).replace(',', '.')
        return "N/A"

    @staticmethod
    def extract_tax_office_number(text):
        patterns = [
            r"\b(?:V\.?D\.?|VN\.?|VKN\\TCKN)\s*[./-]?\s*(\d{10,11})\b",
            r"\b([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)\s*V\.?D\.?\s*[:\s]*([\d\s]{10,11})\b"
        ]
        for pattern in patterns:
            if match := re.search(pattern, text):
                return match.group(2).replace(' ', '') if len(match.groups()) > 1 else match.group(1).replace(' ', '')
        return "N/A"

    @staticmethod
    def extract_payment_methods(text):
        corrections = {
            "KREDI": "KREDI KARTI", "CREDIT": "KREDI KARTI", "KREDİ": "KREDI KARTI",
            "BANKA": "BANKA KARTI", "DEBIT": "BANKA KARTI", "NAKIT": "NAKIT",
            "NAKİT": "NAKIT", "ÇEK": "CEK", "HAVALE": "HAVALE", "EFT": "EFT",
            'K.KARTI': 'KREDI KARTI',
        }

        pattern = r"\b(KREDİ KARTI|CREDIT|DEBIT|NAKİT|NAKIT|MAKIT|K.KARTI|BANKA KARTI|ÇEK|HAVALE|KREDI|KREDİ|EFT|BANKA)\b"
        if match := re.search(pattern, text, re.IGNORECASE):
            extracted = match.group(1).upper()
            return corrections.get(extracted, extracted)
        return "N/A"

    @staticmethod
    def extract_product_names(text):
        names = []
        for line in text.splitlines():
            if match := re.search(r"(.+?)\s*\*\s*[\d.,]+\s*(?:TL)?$", line):
                name = match.group(1).strip()
                if name and len(name) > 1:
                    names.append(name)
        return names

    @staticmethod
    def extract_product_costs(text):
        costs = []
        for line in text.splitlines():
            if match := re.search(r".+?\s*\*\s*([\d.,]+)\s*(?:TL)?$", line):
                try:
                    cost = float(match.group(1).replace(',', '.').strip('₺ '))
                    if cost > 0:
                        costs.append(cost)
                except ValueError:
                    continue
        return costs

    @staticmethod
    def extract_all(texts, filenames=None):
        if filenames is None:
            filenames = ["Unnamed"] * len(texts)
            
        results = []
        for text, filename in zip(texts, filenames):
            try:
                header, body, footer = TextExtractor.find_sections(text)
                
                result = {
                    "filename": filename,
                    "date": TextExtractor.extract_date(header),
                    "time": TextExtractor.extract_time(header),
                    "tax_office_name": TextExtractor.extract_tax_office_name(header),
                    "tax_office_number": TextExtractor.extract_tax_office_number(header),
                    "total_cost": TextExtractor.extract_total_cost(footer),
                    "vat": TextExtractor.extract_vat(footer),
                    "payment_methods": TextExtractor.extract_payment_methods(footer),
                    "product_names": TextExtractor.extract_product_names(body),
                    "product_costs": TextExtractor.extract_product_costs(body),
                    "text": text,
                }

                if result["date"] == "N/A":
                    result["date"] = TextExtractor.extract_with_easyocr(text, TextExtractor.extract_date)
                if result["time"] == "N/A":
                    result["time"] = TextExtractor.extract_with_easyocr(text, TextExtractor.extract_time)
                if result["tax_office_name"] == "N/A":
                    result["tax_office_name"] = TextExtractor.extract_with_easyocr(text, TextExtractor.extract_tax_office_name)
                if result["tax_office_number"] == "N/A":
                    result["tax_office_number"] = TextExtractor.extract_with_easyocr(text, TextExtractor.extract_tax_office_number)
                if result["total_cost"] == "N/A":
                    result["total_cost"] = TextExtractor.extract_with_easyocr(text, TextExtractor.extract_total_cost)
                if result["vat"] == "N/A":
                    result["vat"] = TextExtractor.extract_with_easyocr(text, TextExtractor.extract_vat)
                if result["payment_methods"] == "N/A":
                    result["payment_methods"] = TextExtractor.extract_with_easyocr(text, TextExtractor.extract_payment_methods)

                results.append(result)
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue
        
        return results

    @staticmethod
    def extract_with_easyocr(text, extraction_function):
        try:
            if isinstance(text, str):
                return extraction_function(text)
            easyocr_text = "\n".join([line[1] for line in TextExtractor.easyocr_reader.readtext(text)])
            return extraction_function(easyocr_text)
        except Exception as e:
            print(f"EasyOCR extraction error: {e}")
            return "N/A"