import re
from datetime import datetime
from fuzzywuzzy import fuzz
import difflib
import os
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
    dictionary = OCRMethods.load_dictionary()

    @staticmethod
    def correct_text(text):
        words = text.split()
        corrected_words = []
        for word in words:
            if word.upper() in TextExtractor.dictionary:
                corrected_words.append(word)
            else:
                best_match = max(TextExtractor.dictionary, key=lambda w: fuzz.ratio(word.upper(), w), default=None)
                if best_match and fuzz.ratio(word.upper(), best_match) >= 70:
                    corrected_words.append(best_match)
                else:
                    corrected_words.append(word)
        return ' '.join(corrected_words)

    @staticmethod
    def extract_with_pytesseract(image_path):
        return OCRMethods.extract_with_pytesseract(image_path)

    @staticmethod
    def extract_with_easyocr(image_path):
        return OCRMethods.extract_with_easyocr(image_path)

    # @staticmethod
    # def extract_with_llamaocr(image_path):
    #    return OCRMethods.extract_with_llamaocr(image_path)

    @staticmethod
    def extract_with_paddleocr(image_path):
        return OCRMethods.extract_with_paddleocr(image_path)

    @staticmethod
    def extract_with_suryaocr(image_path):
        return OCRMethods.extract_with_suryaocr(image_path)

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
        ocr_methods = [
            ('PaddleOCR', TextExtractor.extract_with_paddleocr),
            ('docTR', TextExtractor.extract_with_doctr),
            ('SuryaOCR', TextExtractor.extract_with_suryaocr),
            ('EasyOCR', TextExtractor.extract_with_easyocr),
            ('PyTesseract', TextExtractor.extract_with_pytesseract),
            # ('LlamaOCR', TextExtractor.extract_with_llamaocr),
        ]

        for image_path, filename in zip(texts, filenames):
            ocr_results = {}

            def extract_field(extraction_method):
                for method_name, ocr_method in ocr_methods:
                    if (method_name not in ocr_results) or (ocr_results[method_name] is None):
                        ocr_results[method_name] = ocr_method(image_path)
                    text = ocr_results[method_name]
                    if text:
                        result = extraction_method(text)
                        if result and result != "N/A":
                            return result, method_name
                return "N/A", "N/A"

            date, date_method = extract_field(TextExtractor.extract_date)
            time, time_method = extract_field(TextExtractor.extract_time)
            tax_office_name, tax_office_name_method = extract_field(TextExtractor.extract_tax_office_name)
            tax_office_number, tax_office_number_method = extract_field(TextExtractor.extract_tax_office_number)
            total_cost, total_cost_method = extract_field(TextExtractor.extract_total_cost)
            vat, vat_method = extract_field(TextExtractor.extract_vat)
            payment_methods, payment_methods_method = extract_field(TextExtractor.extract_payment_methods)

            results.append({
                "filename": filename,
                "date": date,
                "date_method": date_method,
                "time": time,
                "time_method": time_method,
                "tax_office_name": tax_office_name,
                "tax_office_name_method": tax_office_name_method,
                "tax_office_number": tax_office_number,
                "tax_office_number_method": tax_office_number_method,
                "total_cost": total_cost,
                "total_cost_method": total_cost_method,
                "vat": vat,
                "vat_method": vat_method,
                "payment_methods": payment_methods,
                "payment_methods_method": payment_methods_method
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
            r'\b(\d{2})/(\d{2})/(\d{4})\b',  # Matches DD/MM/YYYY
            r'\b(\d{2})-(\d{2})-(\d{4})\b',  # Matches DD-MM-YYYY
            r'\b(\d{2}).(\d{2}).(\d{4})\b',  # Matches DD.MM.YYYY
            r'\b(\d{4})/(\d{2})/(\d{2})\b',  # Matches YYYY/MM/DD
            r'\b(\d{4})-(\d{2})-(\d{2})\b'   # Matches YYYY-MM-DD
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
            r'\b\d{2}.\d{2}\b'  # Matches HH.MM
        ]
        for pattern in patterns:
            if match := re.search(pattern, text):
                time_parts = match.group().replace('.', ':').split(':')
                hour, minute = map(int, time_parts[:2])
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
    def extract_numerical_part(text):
        match = re.search(r'\d+(?:,\d{2})?', text)
        return match.group(0).replace(',', '.') if match else "N/A"

    @staticmethod
    def extract_vat(text):
        patterns = [
            r"(?:KDV|TOPKDV)\s*[#*«Xx]?\s*(\d+(?:,\d{2})?)",
            r"(?:KDV|TOPKDV)\s*:\s*(\d+(?:,\d{2})?)",
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
        types = 'N/A'
        lines = text.split('\n')
        word_list = ["NAKİT", "Nakit", "Kredi", "KREDI", "KREDİ", "Kredi Kartı", "KREDİ KARTI", "KREDI KARTI", "ORTAK POS", "BANK"]
        b, lines_type, match_type, match_word = [], [], [], []
        kdv_line = 0

        for i in word_list:
            c, d, mt, word = search_similar_word_in_text(i.lower(), text.lower(), 0.7)
            if c:
                b.append(c[0])
                lines_type.append(d[0])
                match_type.append(mt[0])
                match_word.append(word[0])
                if i != "NAKİT" and i != "Nakit":
                    types = "Kredi Kartı"
                else:
                    types = "Nakit"
                    break

        x = 1
        return types.upper()