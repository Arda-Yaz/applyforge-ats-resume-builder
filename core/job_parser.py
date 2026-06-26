import re
from collections import Counter


DEFAULT_KEYWORDS = [
    "python", "sql", "machine learning", "deep learning", "data science",
    "data analysis", "pandas", "numpy", "scikit-learn", "sklearn",
    "tensorflow", "pytorch", "opencv", "yolo", "computer vision",
    "nlp", "llm", "hugging face", "streamlit", "flask", "fastapi",
    "git", "docker", "linux", "api", "data visualization", "plotly",
    "power bi", "tableau", "statistics", "regression", "classification",
    "model evaluation", "preprocessing", "feature engineering",
    "etl", "data cleaning", "supabase"
]


def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_keywords(job_description: str, keyword_bank=None) -> list[str]:
    if keyword_bank is None:
        keyword_bank = DEFAULT_KEYWORDS

    normalized = normalize_text(job_description)
    found = []

    for keyword in keyword_bank:
        pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
        if re.search(pattern, normalized):
            found.append(keyword)

    return sorted(set(found))


def top_terms(job_description: str, n: int = 15) -> list[tuple[str, int]]:
    normalized = normalize_text(job_description)
    words = re.findall(r"[a-zA-Z][a-zA-Z\+\#\-\.]{1,}", normalized)

    stopwords = {
        "and", "the", "with", "for", "you", "are", "our", "will", "this",
        "that", "from", "your", "have", "has", "but", "not", "can", "all",
        "job", "role", "team", "work", "skills", "experience"
    }

    filtered = [word for word in words if word not in stopwords]
    return Counter(filtered).most_common(n)