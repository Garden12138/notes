"""Dependency-free text embedding used by the local memory practice."""

from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import Iterable, List


class EmbeddingModel(ABC):
    """Minimal embedding interface that can be replaced by a cloud model."""

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Encode texts into vectors from one shared vocabulary."""

    def similarities(self, query: str, documents: Iterable[str]) -> List[float]:
        docs = list(documents)
        if not docs:
            return []
        vectors = self.embed([query, *docs])
        query_vector = vectors[0]
        return [cosine_similarity(query_vector, vector) for vector in vectors[1:]]


class TFIDFEmbedding(EmbeddingModel):
    """Small TF-IDF encoder suitable for an offline learning example.

    The vocabulary is rebuilt for each candidate set. This keeps the example
    deterministic and dependency-free; production deployments can inject a
    Transformer or hosted embedding implementation through ``EmbeddingModel``.
    """

    def __init__(self, max_features: int = 2048) -> None:
        if max_features <= 0:
            raise ValueError("max_features must be positive")
        self.max_features = max_features

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        tokenized = [tokenize(text) for text in texts]
        document_frequency: Counter[str] = Counter()
        for tokens in tokenized:
            document_frequency.update(set(tokens))

        ranked_terms = sorted(
            document_frequency,
            key=lambda term: (-document_frequency[term], term),
        )[: self.max_features]
        vocabulary = {term: index for index, term in enumerate(ranked_terms)}
        size = len(texts)

        vectors: List[List[float]] = []
        for tokens in tokenized:
            vector = [0.0] * len(vocabulary)
            counts = Counter(tokens)
            for term, count in counts.items():
                index = vocabulary.get(term)
                if index is None:
                    continue
                tf = 1.0 + math.log(count)
                idf = math.log((1.0 + size) / (1.0 + document_frequency[term])) + 1.0
                vector[index] = tf * idf
            vectors.append(normalize(vector))
        return vectors


def tokenize(text: str) -> List[str]:
    """Tokenize English words and add Chinese unigrams/bigrams."""
    normalized = text.lower().strip()
    tokens: List[str] = re.findall(r"[a-z0-9_]+", normalized)
    for sequence in re.findall(r"[\u4e00-\u9fff]+", normalized):
        tokens.append(sequence)
        tokens.extend(sequence)
        tokens.extend(
            sequence[index : index + 2]
            for index in range(max(0, len(sequence) - 1))
        )
    return tokens


def keyword_overlap(left: str, right: str) -> float:
    """Return Jaccard overlap for the retrieval formula."""
    left_tokens = set(tokenize(left))
    right_tokens = set(tokenize(right))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def normalize(vector: List[float]) -> List[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(left: List[float], right: List[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have equal dimensions")
    return max(0.0, min(1.0, sum(a * b for a, b in zip(left, right))))
