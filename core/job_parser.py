import re
from collections import Counter

from core.keyword_bank import extract_canonical_keywords, normalize_for_matching


def normalize_text(text: str) -> str:
    return normalize_for_matching(text)


def extract_keywords(job_description: str, keyword_bank=None) -> list[str]:
    """
    Extracts canonical keywords from the job description.
    Example:
    - sklearn -> scikit-learn
    - ml -> Machine Learning
    - data wrangling -> Data Cleaning
    """

    return extract_canonical_keywords(job_description)


def top_terms(job_description: str, n: int = 15) -> list[tuple[str, int]]:
    normalized = normalize_text(job_description)
    words = re.findall(r"[a-zA-Z][a-zA-Z\+\#\-\.]{1,}", normalized)

    stopwords = {
        "and", "the", "with", "for", "you", "are", "our", "will", "this",
        "that", "from", "your", "have", "has", "but", "not", "can", "all",
        "job", "role", "team", "work", "skills", "experience", "candidate",
        "looking", "responsibilities", "requirements", "preferred"
    }

    filtered = [word for word in words if word not in stopwords]
    return Counter(filtered).most_common(n)