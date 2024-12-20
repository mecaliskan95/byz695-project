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
            r'\*\s*\*\*TAR[İI]H:\*\*\s*(\d{2}).(\d{2}).(\d{4})\b',
            r'\*\s*\*\*TARIH:\*\*\s*(\d{2}).(\d{2}).(\d{4})\b',
            r'\*\s*\*\*TARİH:\*\*\s*(\d{2}).(\d{2}).(\d{4})\b',
            r'\*?\s*TARIH:?\s*[*]?\s*(\d{2})[./](\d{2})[./](\d{4})\b',
            r'\b(\d{2})/(\d{2})/(\d{4})\b',
            r'\b(\d{2})-(\d{2})-(\d{4})\b',
            r'\b(\d{2}).(\d{2}).(\d{4})\b',
            r'\b(\d{4})/(\d{2})/(\d{2})\b',
            r'\b(\d{4})-(\d{2})-(\d{2})\b',
            r'\bDATE:\s*(\d{2})-(\d{2})-(\d{4})\b',
            r'\bTARİH\s*[+:]?\s*(\d{2}).(\d{2}).(\d{4})\b', 
            r'\bTARIH\s*[+:]?\s*(\d{2}).(\d{2}).(\d{4})\b',
            r'\bTARIH(?:\s*:)?\s*(\d{2})(\d{2})(\d{4})\b'
        ],
        'time': [
            r'\b\d{2}:\d{2}:\d{2}\b',
            r'\b\d{2}:\d{2}\b',
            r'\b\d{2}.\d{2}\b',
            r'\bTIME:\s*(\d{2}:\d{2})\b',
            r'\bSAAT\s*:\s*(\d{2}:\d{2})\b',
            r'\bSAAT(?:\s*:)?\s*(\d{2})(\d{2})\b'
        ],
        'tax_office_name': [
            r"(.+?)\s*V\.D", 
            r"VERGİ\s*DAİRESİ\s*[;:,]?\s*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)",
            r"\b([A-ZÇĞİÖŞÜa-zçğıöşü.\s]+)\s*V\.?D\.?", 
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)\s*(V\.D\.|VERGİ DAİRESİ)",
            r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)\s*VD\s*[:\s]*([\d\s]{10,11})"
        ],
        'total_cost': [
            r"TOPLAM\s*[*#:X]?\s*[*]?(\d+(?:\.\d{3})*)[,.](\d{2})\b",  # Ensures 2 decimals
            r"TUTAR\s*[*]?(\d+(?:\.\d{3})*)[,.](\d{2})(?:\s*TL)?\b",
            r"\bTOPLAM\s*[*#:X]?\s*[*]?(\d+(?:[.,]\d{3})*)[,.](\d{2})\b",
            r"TOPLAM\s*[\*\#:X]?\s*(\d+)[,.](\d{2})\b",
            r"TUTAR\s*(\d{1,3}(?:\.\d{3})*)[,.](\d{2})\s*TL?\b",
            r'\bTOTAL:\s*(\d{1,3}(?:[.,\s]\d{3})*)[,.](\d{2})\b',
            r'\bTOPLAM:\s*\*(\d{1,3}(?:[.,\s]\d{3})*)[,.](\d{2})\b',
            r"TOPLAM\s*\+\s*(\d+)[,.](\d{2})\b"
        ],
        'vat': [
            r"KDV\s*\*\s*(\d+)[,.](\d{2})\b",
            r"(?:KDV|TOPKDV)\s*[#*«Xx]?\s*(\d+)[,.](\d{2})\b",
            r"(?:KDV|TOPKDV)\s*:\s*(\d+)[,.](\d{2})\b",
            r'\bATM FEES:\s*(\d+)[,.](\d{2})\b',
            r'\bTOPKDV:\s*\*(\d+)[,.](\d{2})\b'
        ],
        'tax_office_number': [
            r"\b(?:V\.?D\.?|VN\.?|VKN\\TCKN)\s*[./-]?\s*(\d{10,11})\b",
            r"\b([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)\s*V\.?D\.?\s*[:\s]*([\d\s]{10,11})\b",
            r"(?:V\.?D|VERGİ DAİRESİ)\s*[:\s]*(\d{10,11})\b",
            r"^(\d{10,11})(?:\s|$)",
            r"TEL[:\s][\d\s-]+\s+(\d{10,11})\b"
        ],
        'payment_method': [
            "NAKİT", "NAKIT", "KREDI", "KREDİ", "KREDI KARTI", "KREDİ KARTI", 
            "ORTAK POS", "BANK", "VISA CREDIT", r'\*\*PAYMENT METHOD:\s*\*\*\s*(KRED[İI] KARTI|NAK[İI]T)\b'
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
        
        for line in text.split('\n'):
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
    def validate_cost_and_vat(total_cost, vat):
        try:
            if total_cost == "N/A" or vat == "N/A":
                return total_cost, vat
                
            cost_value = float(total_cost)
            vat_value = float(vat)
            
            if vat_value >= cost_value:
                return "N/A", "N/A"
                
            return total_cost, vat
            
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
                
                result = "N/A"
                if text1:
                    result = extraction_method(text1)
                    if result != "N/A":
                        return result

                if result == "N/A" and text2 is None:
                    text2 = OCRMethods.extract_with_easyocr(image_path)
                    if text2:
                        text2 = TextExtractor.correct_text(text2)
                        result = extraction_method(text2)
                        if result != "N/A":
                            return result
                
                if result == "N/A" and text3 is None:
                    text3 = OCRMethods.extract_with_pytesseract(image_path)
                    if text3:
                        text3 = TextExtractor.correct_text(text3)
                        result = extraction_method(text3)
                        if result != "N/A":
                            return result

                if result == "N/A" and text4 is None:
                    text4 = OCRMethods.extract_with_suryaocr(image_path)
                    if text4:
                        text4 = TextExtractor.correct_text(text4)
                        result = extraction_method(text4)
                        if result != "N/A":
                            return result
                
                return "N/A"

            total_cost = try_extraction(TextExtractor.extract_total_cost, "total_cost")
            vat = try_extraction(TextExtractor.extract_vat, "vat")
            total_cost, vat = TextExtractor.validate_cost_and_vat(total_cost, vat)

            results.append({
                "filename": filename,
                "date": try_extraction(TextExtractor.extract_date, "date"),
                "time": try_extraction(TextExtractor.extract_time, "time"),
                "tax_office_name": try_extraction(TextExtractor.extract_tax_office_name, "tax_office_name"),
                "tax_office_number": try_extraction(TextExtractor.extract_tax_office_number, "tax_office_number"),
                "total_cost": total_cost,
                "vat": vat,
                "payment_method": try_extraction(TextExtractor.extract_payment_method, "payment_method")
            })

        return results

    @staticmethod
    def extract_tax_office_name(text):
        with open('vergidaireleri.txt', 'r', encoding='utf-8') as f:
            valid_offices = {office.strip().upper() for office in f.readlines()}
        for pattern in TextExtractor._patterns['tax_office_name']:
            if match := re.search(pattern, text, re.IGNORECASE):
                found_name = match.group(1).strip().upper()
                if found_name in valid_offices:
                    return found_name
                best_match = max(valid_offices, key=lambda office: fuzz.ratio(found_name, office), default=None)
                if best_match and fuzz.ratio(found_name, best_match) >= 80:
                    return best_match
        for line in text.split('\n'):
            line = line.strip().upper()
            if line in valid_offices:
                return line
        for office in valid_offices:
            matching_lines, _, _, _ = TextExtractor.search_similar_word_in_text(office, text, 0.9)
            if matching_lines:
                return office
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
                    # Clean and validate time regardless of separator
                    if time_str.startswith('SAAT'):
                        time_parts = match.groups()
                    else:
                        # Replace dots with colons and split
                        time_str = time_str.replace('.', ':')
                        time_parts = time_str.split(':')
                        
                    # Extract hours and minutes
                    if len(time_parts) >= 2:
                        hour = int(time_parts[0][-2:] if len(time_parts[0]) > 2 else time_parts[0])
                        minute = int(time_parts[1][:2])  # Take only first 2 digits of minutes
                        
                        if 0 <= hour < 24 and 0 <= minute < 60:
                            return f"{hour:02d}:{minute:02d}"
                except (ValueError, IndexError):
                    continue
        return "N/A"

    @staticmethod 
    def extract_total_cost(text):
        for pattern in TextExtractor._patterns['total_cost']:
            if match := re.search(pattern, text, re.IGNORECASE):
                whole = match.group(1).replace('.', '')  # Remove thousand separators
                decimal = match.group(2)
                if len(decimal) < 2:  # Handle single digit decimals
                    decimal = decimal + "0"
                return f"{whole}.{decimal}"
        return "N/A"

    @staticmethod
    def extract_vat(text):
        for pattern in TextExtractor._patterns['vat']:
            if match := re.search(pattern, text):
                whole = match.group(1).replace(' ', '').replace('.', '')
                decimal = match.group(2) if len(match.groups()) > 1 else "00"
                if len(decimal) < 2:
                    decimal = decimal + "0" 
                return f"{whole}.{decimal}"
        return "N/A"

    @staticmethod
    def extract_tax_office_number(text):
        for pattern in TextExtractor._patterns['tax_office_number']:
            if match := re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                number = match.group(2).replace(' ', '') if len(match.groups()) > 1 else match.group(1).replace(' ', '')
                if len(number) in [10, 11] and number.isdigit():
                    return number
        
        lines = text.split('\n')
        for line in lines:
            numbers = re.findall(r'\b\d{10,11}\b', line)
            for number in numbers:
                if number.isdigit():
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

    def divideText(text):
        lines = text.split('\n')

        a, lines_a, match_type_a,match_word_a = TextExtractor.search_similar_word_in_text("tarih", text.lower(), 0.7)
        b, lines_b, match_type_b,match_word_b = TextExtractor.search_similar_word_in_text("saat", text.lower(), 0.7)
        c, lines_c, match_type_c,match_word_c = TextExtractor.search_similar_word_in_text("fis", text.lower(), 0.6)


        d, lines_d, match_type_d,match_word_d = TextExtractor.search_similar_word_in_text("topkdv", text.lower(), 0.7)
        e, lines_e, match_type_e,match_word_e = TextExtractor.search_similar_word_in_text("kdv", text.lower(), 0.6)
        kdv, line_kdv = find_lines_starting_with_or_similar("TOPKDV", text)

        f, lines_f, match_type_f,match_word_f = TextExtractor.search_similar_word_in_text("top", text.lower(), 0.6)
        g, lines_g, match_type_g,match_word_g = TextExtractor.search_similar_word_in_text("toplam", text.lower(), 0.7)
        top, line_top = find_lines_starting_with_or_similar("TOPLAM", text.lower())


        non_empty_lists = [lst[0] for lst in [lines_a,lines_b,lines_c] if lst]
        firstLast = max(non_empty_lists) if non_empty_lists else None

        non_empty_lists = [lst[0] for lst in [lines_d,lines_e,lines_f,lines_g] if lst]
        thirdBegin = min(non_empty_lists) if non_empty_lists else None

        if firstLast is None:
            firstLast=0
        if thirdBegin is None:
            thirdBegin = len(lines)
        return firstLast,thirdBegin

    @staticmethod
    def search_similar_word_in_text(word, text, cutoff=0.6):
        lines = text.split('\n')
        matching_lines = []
        matching_matching_line_numbers = []
        matching_word = []
        match_type = []
        for line in range(len(lines)):
            words = lines[line].split()
            if word in words:
                match_type.append("exact match")
                matching_lines.append(lines[line])
                matching_matching_line_numbers.append(line)
                matching_word.append(word)
                continue
            close_matches = difflib.get_close_matches(word, words, n=1, cutoff=cutoff)
            if close_matches:
                match_type.append("similar match")
                matching_lines.append(lines[line])
                matching_matching_line_numbers.append(line)
                matching_word.append(close_matches)
        return matching_lines, matching_matching_line_numbers, match_type, matching_word