import re
from datetime import datetime
from fuzzywuzzy import fuzz
import difflib
import os
from ocr_methods import OCRMethods
import json

def find_lines_starting_with_or_similar(word, text, threshold=0.7):
    lines = text.split('\n')
    matching_lines = []
    matching_line_numbers = []
    for i, line in enumerate(lines):
        if line.strip().startswith(word) or any(fuzz.ratio(word.lower(), w.lower()) > threshold * 100 for w in line.split()):
            matching_lines.append(line)
            matching_line_numbers.append(i)
    return matching_lines, matching_line_numbers

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

class TextExtractor:
    _dictionary = None

    @classmethod
    def get_dictionary(cls):
        if cls._dictionary is None:
            encodings = ['utf-8', 'iso-8859-9', 'cp1254', 'latin1']  # Turkish encodings
            for encoding in encodings:
                try:
                    with open('words.dic', 'r', encoding=encoding) as f:
                        cls._dictionary = {line.strip().upper() for line in f.readlines() if line.strip()}
                        break  # Successfully loaded dictionary, exit loop
                except UnicodeDecodeError:
                    continue
                except FileNotFoundError:
                    print("Dictionary file not found.")
                    cls._dictionary = set()
                    break  # Exit loop if file not found
            if cls._dictionary is None:  # If none of the encodings worked
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
                    text2 = OCRMethods.extract_with_pytesseract(image_path)
                    if text2:
                        text2 = TextExtractor.correct_text(text2)
                        result = extraction_method(text2)
                        if result != "N/A":
                            return result
                
                if result == "N/A" and text3 is None:
                    text3 = OCRMethods.extract_with_easyocr(image_path)
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
                if best_match and fuzz.ratio(found_name, best_match) >= 80:
                    return best_match
        for line in text.split('\n'):
            line = line.strip().upper()
            if line in valid_offices:
                return line
        for office in valid_offices:
            matching_lines, _, _, _ = search_similar_word_in_text(office, text, 0.9)
            if matching_lines:
                return office
        return "N/A"

    @staticmethod
    def extract_date(text):
        patterns = [
            r'\b(\d{2})/(\d{2})/(\d{4})\b',  # Matches DD/MM/YYYY
            r'\b(\d{2})-(\d{2})-(\d{4})\b',  # Matches DD-MM-YYYY
            r'\b(\d{2}).(\d{2}).(\d{4})\b',  # Matches DD.MM.YYYY
            r'\b(\d{4})/(\d{2})/(\d{2})\b',  # Matches YYYY/MM/DD
            r'\b(\d{4})-(\d{2})-(\d{2})\b',  # Matches YYYY-MM-DD
            r'\bDATE:\s*(\d{2})-(\d{2})-(\d{4})\b',  # Matches Date: DD-MM-YYYY
            r'\bTARİH\s*:\s*(\d{2}).(\d{2}).(\d{4})\b',  # Matches TARİH : DD.MM.YYYY
            r'\bTARIH\s*:\s*(\d{2}).(\d{2}).(\d{4})\b'  # Matches TARIH : DD.MM.YYYY
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                day, month, year = match.groups() if len(match.groups()) == 3 else (None, None, None)
                if day and month and year:
                    try:
                        return datetime(int(year), int(month), int(day)).strftime("%d/%m/%Y")
                    except ValueError:
                        continue
        return "N/A"

    @staticmethod
    def extract_time(text):
        patterns = [
            r'\b\d{2}:\d{2}:\d{2}\b',  # Matches HH:MM:SS
            r'\b\d{2}:\d{2}\b',  # Matches HH:MM
            r'\b\d{2}.\d{2}\b',  # Matches HH.MM
            r'\bTIME:\s*(\d{2}:\d{2})\b',  # Matches Time: HH:MM
            r'\bSAAT\s*:\s*(\d{2}:\d{2})\b'  # Matches SAAT : HH:MM
        ]
        for pattern in patterns:
            if match := re.search(pattern, text):
                time_parts = match.group().replace('.', ':').replace(',', ':').split(':')
                try:
                    hour, minute = map(int, time_parts[:2])
                    if 0 <= hour < 24 and 0 <= minute < 60:
                        return f"{hour:02d}:{minute:02d}"
                except ValueError:
                    continue
        return "N/A"

    @staticmethod
    def extract_total_cost(text):
        patterns = [
            r"TOPLAM\s*[\*\#:X]?\s*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)",
            r"TUTAR\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2}|\.\d{2})?)\s*TL?",
            r'\bTOTAL:\s*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\b',
            r'\bTOPLAM:\s*\*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\b',  # Matches TOPLAM: *44,40
            r'\*\*TOTAL COST:\s*\*\*\s*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\b'  # Matches **Total Cost:** 44,40
        ]
        for pattern in patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                value = match.group(1)
                return value.replace(',', '.') if ',' in value else value
        return "N/A"

    @staticmethod
    def extract_numerical_part(text):
        match = re.search(r'\d+(?:,\d{2})?', text)
        return match.group(0).replace(',', '.') if match else "N/A"

    @staticmethod
    def extract_vat(text):
        patterns = [
            r"(?:KDV|TOPKDV)\s*[#*«Xx]?\s*(\d+(?:,\d{2})?)",
            r"(?:KDV|TOPKDV)\s*:\s*(\d+(?:,\d{2})?)",
            r"KDV\s[*]?\s?\d{1,3}(\.\d{3})*,\d{2}\s?[A-Z]?",
            r'\bATM FEES:\s*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\b',
            r'\bTOPKDV:\s*\*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\b'  # Matches TOPKDV: *3,29
        ]
        for pattern in patterns:
            if match := re.search(pattern, text):
                return match.group(1).replace(',', '.')
        return "N/A"

    @staticmethod
    def extract_tax_office_number(text):
        patterns = [
            r"\b(?:V\.?D\.?|VN\.?|VKN\\TCKN)\s*[./-]?\s*(\d{10,11})\b",
            r"\b([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)\s*V\.?D\.?\s*[:\s]*([\d\s]{10,11})\b",
        ]
        for pattern in patterns:
            if match := re.search(pattern, text):
                return match.group(2).replace(' ', '') if len(match.groups()) > 1 else match.group(1).replace(' ', '')
        return "N/A"

    @staticmethod
    def extract_payment_method(text):
        types = 'N/A'
        lines = text.split('\n')
        word_list = [
            "NAKİT", "NAKIT", "KREDI", "KREDİ", "KREDI KARTI", "KREDİ KARTI", 
            "ORTAK POS", "BANK", "VISA CREDIT", r'\*\*PAYMENT METHOD:\s*\*\*\s*(KRED[İI] KARTI|NAK[İI]T)\b'
        ]
        b, lines_type, match_type, match_word = [], [], [], []

        for i in word_list:
            if isinstance(i, str):
                c, d, mt, word = search_similar_word_in_text(i.lower(), text.lower(), 0.7)
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