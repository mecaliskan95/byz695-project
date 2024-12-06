import cv2
import pytesseract
from difflib import get_close_matches

class ImageProcessor:    
    @staticmethod
    def process_image(image_path):
        image = cv2.imread(image_path)
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def correct_ocr_misreads(text, valid_terms):
        corrected_lines = []
        for line in text.splitlines():
            words = line.split()
            corrected_words = [
                get_close_matches(word, valid_terms, n=1, cutoff=0.8)[0]
                if get_close_matches(word, valid_terms, n=1, cutoff=0.8)
                else word
                for word in words
            ]
            corrected_lines.append(' '.join(corrected_words))
        return '\n'.join(corrected_lines)

    @staticmethod
    def extract_text(image_path):
        text = pytesseract.image_to_string(
            ImageProcessor.process_image(image_path),
            lang='tur+eng',
            config='--oem 3 --psm 6'
        ).upper()

        valid_terms = [
            "TARİH", "SAAT", "TOPLAM", "KDV", "V.D", "TOPKDV", "KREDİ KARTI", 
            "NAKİT", "BANKA KARTI", "TUTAR", "VKN", "VN", "V.D.", "VKN/TCKN"
        ]

        corrected_text = ImageProcessor.correct_ocr_misreads(text, valid_terms)
        return corrected_text