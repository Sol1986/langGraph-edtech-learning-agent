"""PDF ingestion: extract -> clean -> chunk -> embed & upsert into Qdrant.

Produces the plain-dict chunk shape ({"page_number", "chunk_number", "text"})
required by quiz_agent.State["chunks"] (see quiz_agent.document_chunk_reviewer,
which reads chunk['page_number'] / chunk['text'] off plain dicts, not
LangChain Document objects -- this is the bug the original main.py had, where
this exact dict list was built and then immediately discarded).
"""

from io import BytesIO

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from qdrant_client import QdrantClient

from src.config import QDRANT_COLLECTION_NAME, require_qdrant_config

MAX_PDF_SIZE_BYTES = 25 * 1024 * 1024  # sets a maximum file size limit of exactly 25 Megabytes (MB)

_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")


class InvalidPdfError(ValueError):
    """Raised when the uploaded file is not a usable PDF (wrong type, empty, too large, corrupt)."""


class EmptyPdfError(ValueError):
    """Raised when a PDF parses but contains no extractable text (e.g. a scanned/image-only PDF)."""


def extract_pages(pdf_bytes: bytes) -> list[dict]:
    """Extract raw per-page text; page_number is 1-indexed."""
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except PdfReadError as exc:
        raise InvalidPdfError(f"Could not parse PDF: {exc}") from exc
    return [
        {"page_number": i, "text": page.extract_text() or ""}
        for i, page in enumerate(reader.pages, start=1)
    ]


def clean_pages(pages: list[dict]) -> list[dict]:
    """Strip whitespace and drop pages with no extractable text."""
    cleaned = [{"page_number": p["page_number"], "text": p["text"].strip()} for p in pages]
    return [p for p in cleaned if p["text"]]


def chunk_pages(clean: list[dict], chunk_size: int = 3000, chunk_overlap: int = 300) -> list[dict]:
    """Split each page into overlapping chunks, preserving dict shape.

    This is the fix for the original main.py bug, where an identical dict-shaped
    chunks list was built this way and then immediately overwritten by a second
    pass that produced LangChain Document objects instead.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks: list[dict] = []
    for page in clean:
        for chunk_number, text in enumerate(splitter.split_text(page["text"]), start=1):
            chunks.append(
                {"page_number": page["page_number"], "chunk_number": chunk_number, "text": text}
            )
    return chunks


def upsert_chunks(chunks: list[dict]) -> None:
    """(Re)creates the shared 'pdf_documents' Qdrant collection from the given chunks.

    Overwrite-on-new-upload is intentional (single active document, no
    per-session isolation -- confirmed MVP scope). The existing collection is
    explicitly deleted first, since QdrantVectorStore.from_documents' overwrite
    behavior on an already-existing collection can vary by installed version --
    this guarantees the "fully replaced" contract regardless.
    """
    url, api_key = require_qdrant_config()
    client = QdrantClient(url=url, api_key=api_key)
    if client.collection_exists(QDRANT_COLLECTION_NAME):
        client.delete_collection(QDRANT_COLLECTION_NAME)

    documents = [
        Document(
            page_content=c["text"],
            metadata={"page_number": c["page_number"], "chunk_number": c["chunk_number"]},
        )
        for c in chunks
    ]
    QdrantVectorStore.from_documents(
        documents=documents,
        embedding=_embeddings,
        url=url,
        api_key=api_key,
        collection_name=QDRANT_COLLECTION_NAME,
    )


def ingest_pdf(pdf_bytes: bytes, filename: str) -> list[dict]:
    """End-to-end ingestion. Returns the dict-shaped chunks for the graph's initial state."""
    if not filename.lower().endswith(".pdf"):
        raise InvalidPdfError("Only .pdf files are supported.")
    if not pdf_bytes:
        raise InvalidPdfError("Uploaded file is empty.")
    if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
        raise InvalidPdfError(f"PDF exceeds max size of {MAX_PDF_SIZE_BYTES} bytes.")

    cleaned = clean_pages(extract_pages(pdf_bytes))
    if not cleaned:
        raise EmptyPdfError("No extractable text found (possibly a scanned/image-only PDF).")

    chunks = chunk_pages(cleaned)
    upsert_chunks(chunks)
    return chunks
