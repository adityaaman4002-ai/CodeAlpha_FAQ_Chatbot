"""
preprocess.py
--------------
Text preprocessing utilities for the FAQ chatbot, built with NLTK.

Pipeline: lowercase -> tokenize -> remove punctuation/stopwords -> lemmatize.
This normalizes both the stored FAQ questions and incoming user queries so
that minor wording differences ("How do I reset my password?" vs
"password reset kaise kare" -> "how to reset password") still match well.
"""

import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

_REQUIRED_NLTK_DATA = [
    ("tokenizers/punkt", "punkt"),
    ("tokenizers/punkt_tab", "punkt_tab"),
    ("corpora/stopwords", "stopwords"),
    ("corpora/wordnet", "wordnet"),
]


def ensure_nltk_data():
    """Download required NLTK corpora on first run if they aren't present."""
    for path, package in _REQUIRED_NLTK_DATA:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(package, quiet=True)


ensure_nltk_data()

_lemmatizer = WordNetLemmatizer()
_stop_words = set(stopwords.words("english"))

# Keep a few question-critical words that default stopword lists often drop
# but that can matter for intent (e.g. "how", "what", "why").
_KEEP_WORDS = {"how", "what", "why", "when", "where", "who", "which", "not", "no"}
_stop_words = _stop_words - _KEEP_WORDS


def clean_text(text: str) -> str:
    """Lowercase and strip characters that aren't letters, digits, or spaces."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def preprocess(text: str) -> str:
    """
    Full preprocessing pipeline for a single string.
    Returns a cleaned, lemmatized, stopword-filtered string ready for
    vectorization (e.g. by TfidfVectorizer).
    """
    text = clean_text(text)
    try:
        tokens = word_tokenize(text)
    except LookupError:
        # Fallback if punkt isn't available for some reason
        tokens = text.split()

    processed_tokens = [
        _lemmatizer.lemmatize(tok)
        for tok in tokens
        if tok not in _stop_words and len(tok) > 1
    ]
    return " ".join(processed_tokens)


if __name__ == "__main__":
    samples = [
        "How do I reset my password?",
        "Why is my internet connection so slow??",
        "can u tell me how 2 delete my account",
    ]
    for s in samples:
        print(f"{s!r:55} -> {preprocess(s)!r}")
