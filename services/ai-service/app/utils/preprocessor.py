import re

class TextPreprocessor:
    @staticmethod
    def clean_text(text: str) -> str:
        # Simple text cleaning
        text = text.lower()
        text = re.sub(r'\s+', ' ', text).strip()
        return text
