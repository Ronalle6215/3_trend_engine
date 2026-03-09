"""
Vietnamese text processing utilities
"""

import re
import unicodedata
from difflib import SequenceMatcher

VIETNAMESE_STOP_WORDS = {
    "và", "của", "có", "là", "được", "cho", "các", "trong", "với",
    "không", "một", "này", "để", "từ", "theo", "đã", "những", "về",
    "khi", "người", "như", "tại", "đến", "còn", "hay", "nhiều",
    "cũng", "sau", "trên", "đó", "nhưng", "lại", "bởi", "vì",
    "nếu", "thì", "rằng", "mà", "sẽ", "phải", "nên", "hoặc",
    # English common
    "the", "a", "an", "in", "on", "at", "to", "for", "of", "with",
    "and", "or", "is", "are", "was", "were", "be", "been", "being",
    "that", "this", "it", "not", "but", "by", "from", "as", "can",
}


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[#@]\w+", "", text)
    text = re.sub(r"[^\w\sàáâãèéêìíòóôõùúýăđĩũơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_keyword(text: str) -> str:
    return clean_text(text).lower().strip()


def remove_diacritics(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def extract_words(text: str, min_len: int = 2) -> list[str]:
    cleaned = clean_text(text).lower()
    words = cleaned.split()
    return [w for w in words if w not in VIETNAMESE_STOP_WORDS and len(w) >= min_len]


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def is_similar(a: str, b: str, threshold: float = 0.7) -> bool:
    return similarity(a, b) >= threshold
