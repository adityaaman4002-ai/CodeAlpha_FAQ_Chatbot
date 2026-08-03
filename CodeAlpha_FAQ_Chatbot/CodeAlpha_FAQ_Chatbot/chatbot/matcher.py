"""
matcher.py
----------
Core FAQ-matching engine. Loads a JSON knowledge base of question/answer
pairs, vectorizes them with TF-IDF, and matches incoming user queries to the
most similar stored question using cosine similarity.
"""

import json
import os
from dataclasses import dataclass
from typing import List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .preprocess import preprocess

DEFAULT_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "faqs.json")

# Below this similarity score, we consider it "no confident match".
DEFAULT_CONFIDENCE_THRESHOLD = 0.20

FALLBACK_RESPONSE = (
    "I'm not fully sure I understood that. Could you try rephrasing your "
    "question, or ask about topics like account, billing, technical issues, "
    "or privacy & security?"
)


@dataclass
class MatchResult:
    matched: bool
    answer: str
    question: Optional[str] = None
    category: Optional[str] = None
    score: float = 0.0
    top_matches: Optional[List[dict]] = None


class FAQMatcher:
    """Loads FAQ data and answers user queries via TF-IDF cosine similarity."""

    def __init__(self, data_path: str = DEFAULT_DATA_PATH,
                 confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD):
        self.data_path = data_path
        self.confidence_threshold = confidence_threshold
        self.faqs: List[dict] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self._question_vectors = None
        self._load_and_fit()

    def _load_and_fit(self):
        with open(self.data_path, "r", encoding="utf-8") as f:
            self.faqs = json.load(f)

        if not self.faqs:
            raise ValueError(f"No FAQ entries found in {self.data_path}")

        processed_questions = [
            preprocess(item["question"] + " " + " ".join(item.get("keywords", [])))
            for item in self.faqs
        ]

        # ngram_range=(1,2) lets the model pick up short phrases ("reset password"),
        # not just single words, which improves matching accuracy noticeably.
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        self._question_vectors = self.vectorizer.fit_transform(processed_questions)

    def reload(self):
        """Reload the FAQ data and refit the vectorizer (e.g. after editing faqs.json)."""
        self._load_and_fit()

    def get_response(self, user_query: str, top_n: int = 3) -> MatchResult:
        if not user_query or not user_query.strip():
            return MatchResult(matched=False, answer="Please type a question and I'll do my best to help!")

        processed_query = preprocess(user_query)
        if not processed_query:
            return MatchResult(matched=False, answer=FALLBACK_RESPONSE)

        query_vector = self.vectorizer.transform([processed_query])
        similarities = cosine_similarity(query_vector, self._question_vectors).flatten()

        ranked_indices = similarities.argsort()[::-1]
        best_idx = ranked_indices[0]
        best_score = float(similarities[best_idx])

        top_matches = [
            {
                "question": self.faqs[i]["question"],
                "score": round(float(similarities[i]), 4),
            }
            for i in ranked_indices[:top_n]
        ]

        if best_score < self.confidence_threshold:
            return MatchResult(
                matched=False,
                answer=FALLBACK_RESPONSE,
                score=best_score,
                top_matches=top_matches,
            )

        best_faq = self.faqs[best_idx]
        return MatchResult(
            matched=True,
            answer=best_faq["answer"],
            question=best_faq["question"],
            category=best_faq.get("category"),
            score=best_score,
            top_matches=top_matches,
        )

    def list_categories(self) -> List[str]:
        return sorted({item.get("category", "General") for item in self.faqs})


if __name__ == "__main__":
    bot = FAQMatcher()
    test_queries = [
        "How can I reset my password?",
        "internet is very slow what do i do",
        "can I get my money back",
        "is it possible to pay with paypal",
        "asdkjaskdj random nonsense text",
    ]
    for q in test_queries:
        result = bot.get_response(q)
        print(f"\nQ: {q}")
        print(f"Matched: {result.matched} (score={result.score:.3f})")
        print(f"A: {result.answer}")
