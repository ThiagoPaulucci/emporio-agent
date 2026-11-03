
"""Local retrieval system for the Empório da Música policy manual."""

from __future__ import annotations

import math
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

from pypdf import PdfReader


DEFAULT_PDF_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "politicas_da_loja.pdf"
)

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_OVERLAP = 150

TOKEN_PATTERN = re.compile(r"\b[\w-]+\b", re.UNICODE)

STOPWORDS = {
    "a", "as", "o", "os", "um", "uma", "uns", "umas",
    "de", "da", "das", "do", "dos", "em", "no", "na",
    "nos", "nas", "por", "para", "com", "sem", "e",
    "ou", "que", "se", "ao", "aos", "à", "às",
    "é", "ser", "ter", "tem", "são", "como", "qual",
    "quais", "quando", "onde", "me", "minha", "meu",
}


def normalize_text(text: str) -> str:
    """Normalize text for language-independent lexical matching."""
    normalized = unicodedata.normalize("NFKD", text.lower())

    return "".join(
        char for char in normalized
        if not unicodedata.combining(char)
    )


def tokenize(text: str) -> list[str]:
    """Tokenize Portuguese text and remove common stopwords."""
    normalized = normalize_text(text)

    return [
        token
        for token in TOKEN_PATTERN.findall(normalized)
        if token not in STOPWORDS and len(token) > 1
    ]


def normalize_token_for_coverage(token: str) -> str:
    """Normalize common Portuguese plural endings for query coverage."""
    if len(token) > 4 and token.endswith("oes"):
        return token[:-3] + "ao"

    if len(token) > 3 and token.endswith("s"):
        return token[:-1]

    return token


def extract_pdf_pages(
    pdf_path: Path = DEFAULT_PDF_PATH,
) -> list[dict]:
    """Extract and normalize text from each PDF page."""
    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Policy manual not found: {pdf_path}"
        )

    reader = PdfReader(str(pdf_path))
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        content = page.extract_text() or ""

        # PDFs may insert a newline between every extracted word.
        content = re.sub(r"\s+", " ", content).strip()

        if content:
            pages.append({
                "page": page_number,
                "text": content,
            })

    if not pages:
        raise ValueError(
            "No extractable text found in the policy PDF. "
            "The document may require OCR."
        )

    return pages


def detect_section(text: str) -> str:
    """Identify a section heading inside a chunk."""
    match = re.search(
        r"(?<!\d)(\d+(?:\.\d+)*)(?:\s+)([A-ZÀ-Ú][^•]{0,100})",
        text,
    )

    if match:
        return f"{match.group(1)}. {match.group(2).strip()[:100]}"

    return "General policies"


def split_into_chunks(
    text: str,
    page: int,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[dict[str, Any]]:
    """Split normalized page text into sentence-aware chunks."""
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Invalid chunk_size or overlap.")

    # Preserve bullet points as independent content units.
    text = re.sub(r"\s+", " ", text).strip()

    units = re.split(
        r"(?<=[.!?])\s+|(?=•\s)",
        text,
    )

    chunks = []
    current = ""

    for unit in units:
        unit = unit.strip()

        if not unit:
            continue

        if len(unit) > chunk_size:
            if current:
                chunks.append(current)
                current = ""

            start = 0

            while start < len(unit):
                end = start + chunk_size
                chunks.append(unit[start:end])
                start += chunk_size - overlap

            continue

        candidate = f"{current} {unit}".strip() if current else unit

        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)

            overlap_text = current[-overlap:] if overlap else ""
            current = f"{overlap_text} {unit}".strip()

    if current:
        chunks.append(current)

    return [
        {
            "page": page,
            "section": detect_section(chunk),
            "text": chunk,
        }
        for chunk in chunks
        if tokenize(chunk)
    ]


def build_corpus(pages: list[dict]) -> list[dict]:
    """Build the searchable document corpus."""
    corpus = []

    for page_data in pages:
        corpus.extend(
            split_into_chunks(
                text=page_data["text"],
                page=page_data["page"],
            )
        )

    return corpus


def calculate_idf(
    documents: list[list[str]],
) -> dict[str, float]:
    """Calculate inverse document frequency for each term."""
    total_documents = len(documents)
    document_frequency: dict[str, int] = {}

    for tokens in documents:
        for token in set(tokens):
            document_frequency[token] = (
                document_frequency.get(token, 0) + 1
            )

    return {
        token: math.log(
            1 + (total_documents - frequency + 0.5)
            / (frequency + 0.5)
        )
        for token, frequency in document_frequency.items()
    }


def bm25_score(
    query_tokens: list[str],
    document_tokens: list[str],
    idf: dict[str, float],
    average_length: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Calculate a BM25 relevance score."""
    if not document_tokens or average_length <= 0:
        return 0.0

    frequencies: dict[str, int] = {}

    for token in document_tokens:
        frequencies[token] = frequencies.get(token, 0) + 1

    document_length = len(document_tokens)
    score = 0.0

    for token in set(query_tokens):
        if token not in frequencies or token not in idf:
            continue

        frequency = frequencies[token]

        denominator = frequency + k1 * (
            1 - b + b * document_length / average_length
        )

        score += idf[token] * (
            frequency * (k1 + 1) / denominator
        )

    return score


@lru_cache(maxsize=1)
def load_policy_corpus() -> tuple[dict, ...]:
    """Load and cache the policy manual corpus."""
    pages = extract_pdf_pages()
    return tuple(build_corpus(pages))


def retrieve_policy(
    query: str,
    top_k: int = 4,
) -> dict[str, Any]:
    """
    Retrieve the most relevant policy chunks.

    Returns source page, section, text and relevance score.
    """
    if not query or not query.strip():
        return {
            "status": "invalid_query",
            "query": query,
            "chunks": [],
        }

    if isinstance(top_k, bool) or not isinstance(top_k, int):
        raise ValueError("top_k must be an integer.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    query_tokens = tokenize(query)

    if not query_tokens:
        return {
            "status": "no_relevant_context",
            "query": query,
            "chunks": [],
        }

    corpus = load_policy_corpus()

    tokenized_documents = [
        tokenize(chunk["text"])
        for chunk in corpus
    ]

    idf = calculate_idf(tokenized_documents)

    average_length = (
        sum(map(len, tokenized_documents))
        / len(tokenized_documents)
        if tokenized_documents
        else 0
    )

    normalized_query_tokens = {
        normalize_token_for_coverage(token)
        for token in query_tokens
    }

    results = []

    for chunk, document_tokens in zip(
        corpus, tokenized_documents
    ):
        score = bm25_score(
            query_tokens=query_tokens,
            document_tokens=document_tokens,
            idf=idf,
            average_length=average_length,
        )

        normalized_document_tokens = {
            normalize_token_for_coverage(token)
            for token in document_tokens
        }

        matched_terms = (
            normalized_query_tokens
            & normalized_document_tokens
        )

        query_coverage = (
            len(matched_terms) / len(normalized_query_tokens)
            if normalized_query_tokens
            else 0.0
        )

        if score > 0 and query_coverage >= 0.5:
            results.append({
                **chunk,
                "score": round(score, 4),
            })

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    selected = results[:top_k]

    return {
        "status": "found" if selected else "no_relevant_context",
        "query": query,
        "chunks": selected,
    }
