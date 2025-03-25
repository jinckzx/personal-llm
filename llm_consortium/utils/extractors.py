import re
from typing import Optional

class ResponseExtractor:
    @staticmethod
    def extract_confidence(text: str) -> float:
        try:
            if match := re.search(r"### Confidence Score:\s*([0-9]\.[0-9]{2})", text, re.I):
                return float(match.group(1))
            if match := re.search(r"\b(0?\.\d{1,2}|1\.00)\b", text):
                return float(match.group())
            if match := re.search(r"(\d{1,3})%", text):
                return float(match.group(1)) / 100
            return 0.0
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def extract_answer(text: str) -> str:
        if match := re.search(r"### Answer:\s*(.*?)(?=\n###|$)", text, re.DOTALL):
            return match.group(1).strip()
        return text.strip()

    @staticmethod
    def extract_section(text: str, start_marker: str, end_marker: Optional[str] = None) -> str:
        try:
            start_idx = text.index(start_marker) + len(start_marker)
            end_idx = text.index(end_marker) if end_marker else len(text)
            return text[start_idx:end_idx].strip()
        except ValueError:
            return ""