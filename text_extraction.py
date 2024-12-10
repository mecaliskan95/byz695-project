import re
from datetime import datetime
from fuzzywuzzy import fuzz
import easyocr
import difflib
import pytesseract
import torch
import os  # Add this import
from image_processing import ImageProcessor

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
    # Split the text into lines
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

    if not matching_lines:
        return matching_lines, matching_matching_line_numbers, match_type, matching_word

    return matching_lines, matching_matching_line_numbers, match_type, matching_word

class TextExtractor:
    use_gpu = torch.cuda.is_available()
    easyocr_reader = easyocr.Reader(['en', 'tr'], gpu=use_gpu)
    
    @staticmethod
    def extract_with_pytesseract(image_path):
        if not os.path.isfile(image_path):
            return None
        processed_image = ImageProcessor.process_image(image_path)
        if processed_image is None:
            return None
        return pytesseract.image_to_string(
            processed_image,
            lang='tur+eng',
            config='--oem 3 --psm 6'
        ).upper()

    @staticmethod
    def extract_with_easyocr(image_path):
        if not os.path.isfile(image_path):
            return None
        result = TextExtractor.easyocr_reader.readtext(image_path)
        return "\n".join([line[1] for line in result]).upper() if result else None

    @staticmethod
    def divideText(text):
        lines = text.split('\n')

        a, lines_a, match_type_a, match_word_a = search_similar_word_in_text("tarih", text.lower(), 0.7)
        b, lines_b, match_type_b, match_word_b = search_similar_word_in_text("saat", text.lower(), 0.7)
        c, lines_c, match_type_c, match_word_c = search_similar_word_in_text("fis", text.lower(), 0.6)

        d, lines_d, match_type_d, match_word_d = search_similar_word_in_text("topkdv", text.lower(), 0.7)
        e, lines_e, match_type_e, match_word_e = search_similar_word_in_text("kdv", text.lower(), 0.6)
        kdv, line_kdv = find_lines_starting_with_or_similar("TOPKDV", text)

        f, lines_f, match_type_f, match_word_f = search_similar_word_in_text("top", text.lower(), 0.6)
        g, lines_g, match_type_g, match_word_g = search_similar_word_in_text("toplam", text.lower(), 0.7)
        top, line_top = find_lines_starting_with_or_similar("TOPLAM", text.lower())

        non_empty_lists = [lst[0] for lst in [lines_a, lines_b, lines_c] if lst]
        firstLast = max(non_empty_lists) if non_empty_lists else None

        non_empty_lists = [lst[0] for lst in [lines_d, lines_e, lines_f, lines_g] if lst]
        thirdBegin = min(non_empty_lists) if non_empty_lists else None

        if firstLast is None:
            firstLast = 0
        if thirdBegin is None:
            thirdBegin = len(lines)

        return firstLast, thirdBegin

    @staticmethod
    def extract_all(texts, filenames=None):
        if filenames is None:
            filenames = ["Unnamed"] * len(texts)
            
        results = []
        for image_path, filename in zip(texts, filenames):
            text1 = TextExtractor.extract_with_pytesseract(image_path)
            text2 = TextExtractor.extract_with_easyocr(image_path)

            def extract_field(extraction_method):
                if text1:
                    result = extraction_method(text1)
                    if result and result != "N/A":
                        return result
                if text2:
                    result = extraction_method(text2)
                    if result and result != "N/A":
                        return result
                return "N/A"

            results.append({
                "filename": filename,
                "date": extract_field(TextExtractor.extract_date),
                "time": extract_field(TextExtractor.extract_time),
                "tax_office_name": extract_field(TextExtractor.extract_tax_office_name),
                "tax_office_number": extract_field(TextExtractor.extract_tax_office_number),
                "total_cost": extract_field(TextExtractor.extract_total_cost),
                "vat": extract_field(TextExtractor.extract_vat),
                "payment_methods": extract_field(TextExtractor.extract_payment_methods)
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
            r'\b\d{4}/\d{2}/\d{2}\b',  # YYYY/MM/DD
            r'\b\d{4}-\d{2}-\d{2}\b'  # YYYY-MM-DD
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