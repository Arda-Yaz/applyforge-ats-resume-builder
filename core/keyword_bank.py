import re


KEYWORD_ALIASES = {
    "Python": ["python"],
    "SQL": ["sql"],
    "Machine Learning": [
        "machine learning",
        "ml",
        "predictive modeling",
        "predictive modelling",
        "model development",
    ],
    "Deep Learning": [
        "deep learning",
        "neural network",
        "neural networks",
    ],
    "Data Science": [
        "data science",
        "data scientist",
    ],
    "Data Analysis": [
        "data analysis",
        "data analytics",
        "analyze data",
        "analyse data",
    ],
    "Data Cleaning": [
        "data cleaning",
        "data cleansing",
        "data wrangling",
        "cleaning data",
    ],
    "Preprocessing": [
        "preprocessing",
        "data preprocessing",
        "pre-process",
        "preprocess",
    ],
    "Feature Engineering": [
        "feature engineering",
        "feature extraction",
        "feature selection",
    ],
    "Model Evaluation": [
        "model evaluation",
        "evaluate models",
        "model performance",
        "confusion matrix",
        "classification report",
    ],
    "Classification": [
        "classification",
        "classifier",
        "classifiers",
    ],
    "Regression": [
        "regression",
        "regressor",
        "regressors",
    ],
    "Pandas": ["pandas"],
    "NumPy": ["numpy", "num py"],
    "scikit-learn": [
        "scikit-learn",
        "scikit learn",
        "sklearn",
    ],
    "TensorFlow": ["tensorflow", "tensor flow"],
    "PyTorch": ["pytorch", "torch"],
    "OpenCV": ["opencv", "open cv"],
    "YOLO": ["yolo", "you only look once"],
    "Computer Vision": [
        "computer vision",
        "cv",
        "image processing",
        "object detection",
    ],
    "NLP": [
        "nlp",
        "natural language processing",
    ],
    "LLM": [
        "llm",
        "large language model",
        "large language models",
        "generative ai",
        "genai",
    ],
    "Hugging Face": [
        "hugging face",
        "huggingface",
        "transformers",
    ],
    "Streamlit": ["streamlit"],
    "Plotly": ["plotly"],
    "Git": ["git", "github"],
    "Docker": ["docker"],
    "FastAPI": ["fastapi", "fast api"],
    "Flask": ["flask"],
    "API": ["api", "apis", "rest api", "restful api"],
    "ETL": ["etl", "extract transform load"],
    "Data Visualization": [
        "data visualization",
        "data visualisation",
        "visualization",
        "visualisation",
        "dashboard",
        "dashboards",
    ],
    "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau"],
    "Statistics": [
        "statistics",
        "statistical analysis",
        "probability",
    ],
    "Supabase": ["supabase"],
}


def normalize_for_matching(text: str) -> str:
    text = text.lower()
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def alias_exists_in_text(alias: str, text: str) -> bool:
    alias = normalize_for_matching(alias)

    # Short aliases like "ml", "cv", "ai" need word boundaries.
    pattern = r"\b" + re.escape(alias) + r"\b"

    return re.search(pattern, text) is not None


def extract_canonical_keywords(text: str) -> list[str]:
    normalized_text = normalize_for_matching(text)
    found = []

    for canonical, aliases in KEYWORD_ALIASES.items():
        for alias in aliases:
            if alias_exists_in_text(alias, normalized_text):
                found.append(canonical)
                break

    return found