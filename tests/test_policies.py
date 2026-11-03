
"""Automated tests for the local policy retrieval system."""

import pytest

from emporio import policies


def test_normalize_text_removes_accents():
    assert policies.normalize_text("Devolução e Garantia") == (
        "devolucao e garantia"
    )


def test_tokenize_removes_stopwords():
    tokens = policies.tokenize(
        "Qual é o prazo para devolução online?"
    )

    assert "prazo" in tokens
    assert "devolucao" in tokens
    assert "online" in tokens
    assert "para" not in tokens
    assert "qual" not in tokens


def test_split_into_chunks_preserves_page():
    text = (
        "4.1 Direito de Arrependimento. "
        "O cliente pode solicitar devolução em até sete dias. "
        "O reembolso será feito na forma de pagamento original."
    )

    chunks = policies.split_into_chunks(
        text=text,
        page=4,
        chunk_size=100,
        overlap=20,
    )

    assert len(chunks) >= 1
    assert all(chunk["page"] == 4 for chunk in chunks)
    assert all(chunk["text"].strip() for chunk in chunks)


def test_split_into_chunks_rejects_invalid_parameters():
    with pytest.raises(ValueError):
        policies.split_into_chunks(
            text="Some text",
            page=1,
            chunk_size=100,
            overlap=100,
        )


def test_retrieve_policy_returns_relevant_chunk(monkeypatch):
    corpus = (
        {
            "page": 4,
            "section": "4.1 Direito de Arrependimento",
            "text": (
                "O cliente pode solicitar devolução online "
                "em até sete dias corridos após o recebimento."
            ),
        },
        {
            "page": 7,
            "section": "8.1 Garantia Legal",
            "text": (
                "Todos os produtos possuem garantia legal "
                "de noventa dias após o recebimento."
            ),
        },
        {
            "page": 3,
            "section": "3. Formas de Pagamento",
            "text": (
                "O pagamento por PIX possui cinco por cento "
                "de desconto sobre o preço de tabela."
            ),
        },
    )

    monkeypatch.setattr(
        policies,
        "load_policy_corpus",
        lambda: corpus,
    )

    result = policies.retrieve_policy(
        "Qual é o prazo para devolução online?",
        top_k=2,
    )

    assert result["status"] == "found"
    assert result["chunks"]
    assert result["chunks"][0]["page"] == 4
    assert "sete dias" in result["chunks"][0]["text"]
    assert result["chunks"][0]["score"] > 0


def test_retrieve_policy_returns_no_context_for_unrelated_query(
    monkeypatch,
):
    corpus = (
        {
            "page": 4,
            "section": "4.1 Direito de Arrependimento",
            "text": (
                "O cliente pode solicitar devolução online "
                "em até sete dias corridos."
            ),
        },
    )

    monkeypatch.setattr(
        policies,
        "load_policy_corpus",
        lambda: corpus,
    )

    result = policies.retrieve_policy(
        "Como preparar uma receita de bolo?"
    )

    assert result["status"] == "no_relevant_context"
    assert result["chunks"] == []


def test_retrieve_policy_rejects_empty_query():
    result = policies.retrieve_policy("   ")

    assert result["status"] == "invalid_query"
    assert result["chunks"] == []


def test_retrieve_policy_rejects_invalid_top_k():
    with pytest.raises(ValueError):
        policies.retrieve_policy(
            "prazo de devolução",
            top_k=0,
        )


def test_extract_pdf_pages_raises_when_file_is_missing(tmp_path):
    missing_pdf = tmp_path / "missing.pdf"

    with pytest.raises(FileNotFoundError):
        policies.extract_pdf_pages(missing_pdf)


def test_extract_pdf_pages_raises_when_pdf_has_no_text(
    monkeypatch,
    tmp_path,
):
    class FakePage:
        def extract_text(self):
            return ""

    class FakePdfReader:
        def __init__(self, path):
            self.pages = [FakePage(), FakePage()]

    monkeypatch.setattr(
        policies,
        "PdfReader",
        FakePdfReader,
    )

    fake_pdf = tmp_path / "empty.pdf"
    fake_pdf.touch()

    with pytest.raises(ValueError, match="OCR"):
        policies.extract_pdf_pages(fake_pdf)
