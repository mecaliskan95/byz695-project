import re
from datetime import datetime
from fuzzywuzzy import fuzz
import difflib
import os
import json
from functools import lru_cache
from ocr_methods import OCRMethods

def find_lines_starting_with_or_similar(word, text, threshold=0.7):
    lines = text.split('\n')
    matching_lines = []
    matching_line_numbers = []
    for i, line in enumerate(lines):
        if line.strip().startswith(word) or any(fuzz.ratio(word.lower(), w.lower()) > threshold * 100 for w in line.split()):
            matching_lines.append(line)
            matching_line_numbers.append(i)
    return matching_lines, matching_line_numbers

class TextExtractor:
    _dictionary = None
    _testing_mode = False
    _test_ocr_method = None
    _valid_offices = None
    _cache = {}
    _patterns = {
        'date': [
            r'(?:^|[^\d])(\d{2})\.(\d{2})\.(\d{4})(?:$|[^\d])',
            r'(?:^|[^\d])(\d{2})/(\d{2})/(\d{4})(?:$|[^\d])',
            r'(?:^|[^\d])(\d{2})-(\d{2})-(\d{4})(?:$|[^\d])',
            r'(\d{2})\s*/\s*(\d{2})\s*/\s*(\d{4})',
        ],
        'time': [
            r"SAAT\s*[:.]?\s*(\d{2})[:.](\d{2})", # Add this as first pattern
            r"(?:^|[^\d])(\d{2}):(\d{2})(?::\d{2})?(?:$|[^\d])",
            r"(?:^|[^\d])(\d{2})\.(\d{2})(?:\.\d{2})?(?:$|[^\d])",
        ],
        'tax_office_name': [
            r"VERGİ\s*DAİRESİ\s*:\s*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)\b",  # New pattern
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)\s*VERGİ\s*DAİRESİ\s*VKN\s*\d+",
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\$\s]+?)(?:V\.D\.?|VD\.?|V\.D|VERGİ\s*DAİRESİ)", 
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+?)\s*V[\.\s]?D[\.\s]?", 
            r"(.+?)(?:\s*V\.D\.?|VD\.?|V\.D|VERGİ\s*DAİRESİ)", 
            r"VERGİ\s*DAİRESİ\s*[;:,]?\s*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)",
            r"\b([A-ZÇĞİÖŞÜa-zçğıöşü.\s]+)\s*V\.?D\.?", 
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)(?:\s*V\.D\.|VERGİ DAİRESİ)",
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)\s*VD\s*[:\s]*(?:[\d\s]{10,11})",
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)VD:?\s*\d+",
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)VD\.?\s*\d+",
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)V\.?D\.?\s*:?\s*\d+",
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+?)(?:VD|V\.D\.|V\.D)", 
        ],
        'total_cost': [
            r"TOP\s*[*+]?\s*(\d+)[\s,.]?\s*(\d{3})\s*[,.]?\s*(\d{2})\b",
            r"TOP\s*[*+]?\s*(\d+(?:[\s,.]\d{3})*)[,.\s]*(\d{2})\b",
            r"TOPLAM\s*[*+]?\s*(\d+)[\s,.]?\s*(\d{3})\s*[,.]?\s*(\d{2})\b",
            r"TOPLAM\s*[*+]?\s*(\d+(?:[\s,.]\d{3})*)[,.\s]*(\d{2})\b",
            r"TOPLAM\s*\*?\s*\*(\d+(?:\.\d{3})*)[,.](\d{2})\b",  
            r"TOPLAM.*?\*(\d+(?:\.\d{3})*)[,.](\d{2})\b",    
            r"TOPLAM\s*[+]?\s*(\d+)[\s.]+(\d{3})\s*[,.](\d{2})\b",
            r"TOPLAM\s*[+]?\s*(\d+)[\s.]*(\d{3})[,.](\d{2})\b", 
            r"TOPLAM\s*[*#:X]?\s*[*]?(\d+)[\s.](\d{3})[,.](\d{2})\b",
            r"TOPLAM\s*[*#:X]?\s*[*]?(\d+\s+\d{3})[,.](\d{2})\b",  
            r"TOPLAM\s*[*#:X]?\s*[*]?(\d+)\.(\d{3})[,.](\d{2})\b", 
            r"TUTAR\s*[*]?(\d+)\.(\d{3})[,.](\d{2})(?:\s*TL)?\b", 
            r"TOPLAM\s*[*#:X]?\s*[*]?(\d+)[,](\d{3})[,.](\d{2})\b",
            r"TOPLAM\s*[*#:X]?\s*[*]?(\d+(?:\.\d{3})*)[,.](\d{2})\b",
            r"TUTAR\s*[*]?(\d+(?:\.\d{3})*)[,.](\d{2})(?:\s*TL)?\b",
            r"\bTOPLAM\s*[*#:X]?\s*[*]?(\d+(?:[.,]\d{3})*)[,.](\d{2})\b",
            r"TOPLAM\s*[\*\#:X]?\s*(\d+)[,.](\d{2})\b",
            r"TUTAR\s*(\d{1,3}(?:\.\d{3})*)[,.](\d{2})\s*TL?\b",
            r"TOPLAM\s*\n\s*[*]?(\d+)[.,](\d+)",
            r"TOPLAM.*?\n\s*[*]?(\d+)[.,](\d+)",
            r"TOPLAM\s*\n\s*[*]?(\d+)[.](\d+)\b", 
            r"TOPLAM\s*[*#:X]?\s*[*]?(\d+)[.](\d+)\b",
            r"(?:[A-ZÇĞİÖŞÜ\s]+\s+)?TOPLAM\s*[*#:X+]?\s*[*]?(\d+)[\s.](\d{3})[,.](\d{2})\b",  
            r"(?:[A-ZÇĞİÖŞÜ\s]+\s+)?TOPLAM\s*[*#:X+]?\s*[*]?(\d+)[,.](\d{2})\b",  
        ],
        'vat': [
            r"(?:KDV|TOPKDV)\s*\*?\s*\*(\d+(?:\.\d{3})*)[,.](\d{2})\b",  
            r"(?:KDV|TOPKDV).*?\*(\d+(?:\.\d{3})*)[,.](\d{2})\b",    
            r"(?:KDV|TOPKDV)\s*[*]?\s*[*]?(\d+)\.(\d{3})[,.](\d{2})\b",  
            r"(?:KDV|TOPKDV)\s*[*]?\s*[*]?(\d+)[,](\d{3})[,.](\d{2})\b",
            r"(?:KDV|TOPKDV)\s*[#*«Xx]?\s*(\d+)[,.](\d{2})\b",
            r"(?:KDV|TOPKDV)\s*:\s*(\d+)[,.](\d{2})\b",
            r"TOPKDV\s*[*]?\s*(\d+)[,.](\d{2})\b",
            r"TOPKDV.*?[*]?(\d+)[,.](\d{2})\b",
            r"[*]?(\d+)[,.](\d{2})\s*TOPKDV\b",
            r"(?:[A-ZÇĞİÖŞÜ\s]+\s+)?(?:KDV|TOPKDV)\s*[*#:X+]?\s*[*]?(\d+)[,.](\d{2})\b",
            r"TOPKDV\s*\*(\d+)[,.](\d{2})\b", 
        ],
        'tax_office_number': [
            r"(?:V\.D\.?|VD\.?|VERGİ\s*DAİRESİ)\s*[.:]?\s*(\d+(?:\s+\d{3}\s+\d{4}|\s*\d{3}\s*\d{4}))\b",
            r"(?:V\.D\.?|VD\.?|VERGİ\s*DAİRESİ)[^0-9]*?(\d+)[\s.]*(\d{3})[\s.]*(\d{4})\b", 
            r"(?:VKN|TCKN|VKNTCKN)\s*:?\s*(\d{10,11})\b",
            r"(?:VKN|TCKN|VKNTCKN)\s*:?\s*(\d+(?:\s+\d+)*)",
            r"\b(?:V\.?D\.?|VN\.?|VKN\\TCKN)\s*[./-]?\s*(\d{10,11})\b",
            r"\b([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)\s*V\.?D\.?\s*[:\s]*([\d\s]{10,11})\b",
            r"(?:V\.?D|VERGİ DAİRESİ)\s*[:\s]*(\d{10,11})\b",
            r"^(\d{10,11})(?:\s|$)",
            r"VD:?\s*(\d+(?:\s+\d+)*)", 
            r"VD\.?\s*:?\s*(\d+(?:\s+\d+)*)", 
            r"[A-ZÇĞİÖŞÜa-zçğıöşü\s]+VD:?\s*(\d+(?:\s+\d+)*)" 
        ],
        'payment_method': [
            "NAKİT", "NAKIT", "KREDI", "KREDİ", "KREDI KARTI", "KREDİ KARTI", 
            "ORTAK POS", "BANK", "VISA CREDIT", "YEMEK FISI/KARTI", "KARTI", "KART" 
            r'\*\*PAYMENT METHOD:\s*\*\*\s*(KRED[İI] KARTI|NAK[İI]T)\b'
        ]
    }

    @classmethod
    def set_testing_mode(cls, enabled=True, ocr_method=None):
        cls._testing_mode = enabled
        cls._test_ocr_method = ocr_method

    @classmethod
    @lru_cache(maxsize=128)
    def get_dictionary(cls):
        if cls._dictionary is None:
            encodings = ['utf-8', 'iso-8859-9', 'cp1254', 'latin1']
            for encoding in encodings:
                try:
                    with open('words.dic', 'r', encoding=encoding) as f:
                        cls._dictionary = {line.strip().upper() for line in f.readlines() if line.strip()}
                        break
                except UnicodeDecodeError:
                    continue
                except FileNotFoundError:
                    print("Dictionary file not found.")
                    cls._dictionary = set()
                    break
            if cls._dictionary is None:
                print(f"Could not read dictionary file with any of the encodings: {encodings}")
                cls._dictionary = set()
        return cls._dictionary

    @staticmethod
    def correct_text(text):
        dictionary = TextExtractor.get_dictionary()
        corrected_lines = []
        
        lines = text.split('\n') if isinstance(text, str) else text
        
        for line in lines:
            if not isinstance(line, str):
                line = str(line)
            
            line = line.replace('$', 'Ş')
                
            words = line.split()
            corrected_words = []
            
            for word in words:
                if word.upper() in dictionary:
                    corrected_words.append(word)
                else:
                    best_match = max(dictionary, key=lambda w: fuzz.ratio(word.upper(), w), default=None)
                    if best_match and fuzz.ratio(word.upper(), best_match) >= 70:
                        corrected_words.append(best_match)
                    else:
                        corrected_words.append(word)
            
            corrected_lines.append(' '.join(corrected_words))
        
        return '\n'.join(corrected_lines)

    @staticmethod
    def validate_total_cost_and_vat(total_cost, vat):
        try:
            if total_cost == "N/A":
                return "N/A", "N/A"
            
            cost_value = float(total_cost)
            
            # If VAT is N/A or invalid, still return the total cost
            if vat == "N/A":
                return total_cost, "N/A"
                
            vat_value = float(vat)
            
            # Check if VAT is larger than total cost
            if vat_value >= cost_value:
                return total_cost, "N/A"
                
            # Calculate and validate VAT percentage
            vat_percentage = (vat_value / cost_value) * 100

            # Add check for VAT not exceeding 20% (+2% margin)
            if vat_percentage > 22:  # 20% + 2% margin
                return total_cost, "N/A"
                
            return total_cost, vat
            
        except (ValueError, TypeError, ZeroDivisionError):
            try:
                float(total_cost)
                return total_cost, "N/A"
            except (ValueError, TypeError):
                return "N/A", "N/A"

    @staticmethod
    def extract_all(texts, filenames=None):
        if filenames is None:
            filenames = ["Unnamed"] * len(texts)
        results = []

        for image_path, filename in zip(texts, filenames):
            text1 = text2 = text3 = text4 = None

            text1 = OCRMethods.extract_with_paddleocr(image_path)
            if text1:
                text1 = TextExtractor.correct_text(text1)
            
            def try_extraction(extraction_method, field_name):
                nonlocal text1, text2, text3, text4
                
                if text1:
                    if field_name in ["total_cost", "vat"]:
                        total = TextExtractor.extract_total_cost(text1)
                        vat = TextExtractor.extract_vat(text1)
                        total, vat = TextExtractor.validate_total_cost_and_vat(total, vat)
                        return total if field_name == "total_cost" else vat
                    else:
                        result = extraction_method(text1)
                        if result != "N/A":
                            return result

                if text2 is None:
                    text2 = OCRMethods.extract_with_pytesseract(image_path)
                    if text2:
                        text2 = TextExtractor.correct_text(text2)
                        result = extraction_method(text2)
                        if result != "N/A":
                            return result

                if text3 is None:
                    text3 = OCRMethods.extract_with_easyocr(image_path)
                    if text3:
                        text3 = TextExtractor.correct_text(text3)
                        result = extraction_method(text3)
                        if result != "N/A":
                            return result

                return "N/A"

            results.append({
                "filename": filename,
                "date": try_extraction(TextExtractor.extract_date, "date"),
                "time": try_extraction(TextExtractor.extract_time, "time"),
                "tax_office_name": try_extraction(TextExtractor.extract_tax_office_name, "tax_office_name"),
                "tax_office_number": try_extraction(TextExtractor.extract_tax_office_number, "tax_office_number"),
                "total_cost": try_extraction(TextExtractor.extract_total_cost, "total_cost"),
                "vat": try_extraction(TextExtractor.extract_vat, "vat"),
                "payment_method": try_extraction(TextExtractor.extract_payment_method, "payment_method")
            })

        return results

    @staticmethod
    def extract_tax_office_name(text):
        with open('vergidaireleri.txt', 'r', encoding='utf-8') as f:
            valid_offices = {office.strip().upper() for office in f.readlines() if office.strip()}
        
        keywords = ['VERGİ DAİRESİ', 'V.D.', 'VD.', 'V.D', 'VD', 'V.D', 'VERGİ', 'DAİRESİ']
        
        # Search line by line
        lines = text.split('\n')
        for line in lines:
            upper_line = line.upper()
            if any(keyword in upper_line for keyword in keywords):
                cleaned_line = re.sub(r'[©@"\'*:;.,]', ' ', upper_line)
                words = cleaned_line.split()
                
                best_match = None
                highest_ratio = 0
                
                for office in valid_offices:
                    office_words = office.split()
                    
                    for i in range(len(words)):
                        for j in range(i + 1, len(words) + 1):
                            candidate = ' '.join(words[i:j])
                            ratio = fuzz.ratio(candidate, office)
                            
                            if ratio > highest_ratio and ratio >= 90:
                                highest_ratio = ratio
                                best_match = office
                
                if best_match:
                    return best_match
        
        # If no match found with keywords, try the existing pattern matching
        for pattern in TextExtractor._patterns['tax_office_name']:
            if match := re.search(pattern, text, re.IGNORECASE):
                found_name = match.group(1).strip().upper()
                if found_name in valid_offices:
                    return found_name

                best_match = max(valid_offices, key=lambda office: fuzz.ratio(found_name, office), default=None)
                if best_match and fuzz.ratio(found_name, best_match) >= 80:
                    return best_match
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            tax_number_match = re.search(r'\b\d{10,11}\b', line)
            if tax_number_match:
                # Check current line for tax office name using fuzzy matching
                best_match = None
                highest_ratio = 0
                upper_line = line.upper()
                
                for office in valid_offices:
                    ratio = fuzz.ratio(office, upper_line)
                    if ratio > highest_ratio and ratio >= 80:
                        highest_ratio = ratio
                        best_match = office
                
                if best_match:
                    return best_match
                
                # Check line above
                if i > 0:
                    upper_prev_line = lines[i-1].upper()
                    best_match = None
                    highest_ratio = 0
                    
                    for office in valid_offices:
                        ratio = fuzz.ratio(office, upper_prev_line)
                        if ratio > highest_ratio and ratio >= 80:
                            highest_ratio = ratio
                            best_match = office
                    
                    if best_match:
                        return best_match

        # If still no match, try fallback methods
        # for line in text.split('\n'):
        #     line = line.strip().upper()
        #     if line in valid_offices:
        #         return line
        
        # for office in valid_offices:
        #     matching_lines, _, _, _ = TextExtractor.search_similar_word_in_text(office, text, 0.9)
        #     if matching_lines:
        #         return office

        return "N/A"

    @staticmethod
    def extract_date(text):
        for pattern in TextExtractor._patterns['date']:
            if match := re.search(pattern, text, re.IGNORECASE):
                day, month, year = match.groups() if len(match.groups()) == 3 else (None, None, None)
                if day and month and year:
                    try:
                        return datetime(int(year), int(month), int(day)).strftime("%d/%m/%Y")
                    except ValueError:
                        continue
        return "N/A"

    @staticmethod
    def extract_time(text):
        for pattern in TextExtractor._patterns['time']:
            if match := re.search(pattern, text):
                try:
                    time_str = match.group()
                    
                    if len(time_str) == 6 and time_str.isdigit():
                        hour = int(time_str[:2])
                        minute = int(time_str[2:4])
                        if 0 <= hour < 24 and 0 <= minute < 60:
                            return f"{hour:02d}:{minute:02d}"
                            
                    elif time_str.startswith('SAAT'):
                        digits = ''.join(c for c in time_str if c.isdigit())
                        if len(digits) >= 4:
                            hour = int(digits[:2])
                            minute = int(digits[2:4])
                            if 0 <= hour < 24 and 0 <= minute < 60:
                                return f"{hour:02d}:{minute:02d}"
                    else:
                        time_str = time_str.replace('.', ':')
                        parts = time_str.split(':')
                        if len(parts) >= 2:
                            hour = int(parts[0][-2:] if len(parts[0]) > 2 else parts[0])
                            minute = int(parts[1][:2])
                            if 0 <= hour < 24 and 0 <= minute < 60:
                                return f"{hour:02d}:{minute:02d}"
                except (ValueError, IndexError):
                    continue
        
        for line in text.split('\n'):
            if 'SAAT' in line.upper():
                digits = ''.join(c for c in line if c.isdigit())
                if len(digits) >= 4:
                    try:
                        hour = int(digits[:2])
                        minute = int(digits[2:4])
                        if 0 <= hour < 24 and 0 <= minute < 60:
                            return f"{hour:02d}:{minute:02d}"
                    except (ValueError, IndexError):
                        continue
        
        return "N/A"

    @staticmethod 
    def extract_total_cost(text):
        """Extract total cost without validation"""
        for pattern in TextExtractor._patterns['total_cost']:
            if match := re.search(pattern, text, re.IGNORECASE):
                try:
                    if len(match.groups()) == 3:
                        whole = match.group(1) + match.group(2)
                        decimal = match.group(3)
                    else:
                        whole = match.group(1)
                        decimal = match.group(2)
                    
                    whole = whole.replace('.', '').replace(',', '')
                    
                    if len(decimal) > 2:
                        whole = whole + decimal[:-2]
                        decimal = decimal[-2:]
                    
                    if len(decimal) < 2:
                        decimal = decimal + "0"
                        
                    return f"{whole}.{decimal}"
                except (IndexError, AttributeError):
                    continue

        return "N/A"

    @staticmethod
    def extract_vat(text):
        """Extract VAT without validation"""
        for pattern in TextExtractor._patterns['vat']:
            if match := re.search(pattern, text, re.IGNORECASE):
                try:
                    whole = match.group(1).replace('.', '')
                    decimal = match.group(2)
                    
                    if len(decimal) < 2:
                        decimal = decimal + "0"
                    
                    return f"{whole}.{decimal}"
                except (IndexError, ValueError, AttributeError):
                    continue

        # Try TOPKDV specific patterns
        for line in text.split('\n'):
            if 'TOPKDV' in line:
                if match := re.search(r'\*?(\d+)\b', line):
                    amount = match.group(1)
                    if len(amount) >= 3:
                        return f"{amount[:-2]}.{amount[-2:]}"

        return "N/A"

    @staticmethod
    def extract_tax_office_number(text):

        for pattern in TextExtractor._patterns['tax_office_number']:
            if match := re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                number = match.group(2).replace(' ', '') if len(match.groups()) > 1 else match.group(1).replace(' ', '')
                if number.isdigit() and len(number) in [10, 11]:
                    if not (number.startswith('0312') or number.startswith('0850') or number.startswith('850') or number == '11111111111'):
                        return number
        
        # Last resort - look for any 10-11 digit number
        lines = text.split('\n')
        for line in lines:
            numbers = re.findall(r'\b\d{10,11}\b', line)
            for number in numbers:
                if number.isdigit() and len(number) in [10, 11]:
                    if not (number.startswith('0312') or number.startswith('0850') or number.startswith('850') or number == '11111111111'):
                        return number

        return "N/A"

    @staticmethod
    def extract_payment_method(text):
        types = 'N/A'
        lines = text.split('\n')
        b, lines_type, match_type, match_word = [], [], [], []

        for i in TextExtractor._patterns['payment_method']:
            if isinstance(i, str):
                c, d, mt, word = TextExtractor.search_similar_word_in_text(i.lower(), text.lower(), 0.7)
                if c:
                    b.append(c[0])
                    lines_type.append(d[0])
                    match_type.append(mt[0])
                    match_word.append(word[0])
                    if i != "NAKİT" and i != "NAKIT":
                        types = "KREDİ KARTI"
                    else:
                        types = "NAKIT"
                        break
            else:
                if match := re.search(i, text, re.IGNORECASE):
                    types = match.group(1).upper()
                    break

        return types.upper()

    @staticmethod
    def search_similar_word_in_text(word, text, cutoff=0.6):
        lines = text.split('\n')
        matching_lines = []
        matching_line_numbers = []
        matching_word = []
        match_type = []
        
        for i, line in enumerate(lines):
            words = line.split()
            if word in words:
                match_type.append("exact match")
                matching_lines.append(line)
                matching_line_numbers.append(i)
                matching_word.append(word)
                continue
                
            close_matches = difflib.get_close_matches(word, words, n=1, cutoff=cutoff)
            if close_matches:
                match_type.append("similar match")
                matching_lines.append(line)
                matching_line_numbers.append(i)
                matching_word.append(close_matches[0])
                
        return matching_lines, matching_line_numbers, match_type, matching_word