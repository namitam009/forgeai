import os, csv
import numpy as np
from pypdf import PdfReader
from core.llm import embed


def read_file(path):
    """Return a list of (text, page) from a pdf, csv or txt file."""
    name = os.path.basename(path)
    ext = name.lower().split(".")[-1]
    pages = []
    if ext == "pdf":
        reader = PdfReader(path)
        for i, p in enumerate(reader.pages):
            t = p.extract_text() or ""
            if t.strip():
                pages.append((t, i + 1))
    elif ext == "csv":
        with open(path, encoding="utf-8", errors="ignore") as f:
            for i, row in enumerate(csv.DictReader(f)):
                line = ", ".join(f"{k}: {v}" for k, v in row.items())
                pages.append((line, i + 1))
    elif ext in ("txt", "md"):
        with open(path, encoding="utf-8", errors="ignore") as f:
            pages.append((f.read(), 1))
    return pages


def chunk_text(text, size=500, overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


def load_docs(folder, size=500, overlap=100):
    """Read every file in folder and return a list of chunk dicts."""
    chunks = []
    for fname in sorted(os.listdir(folder)):
        path = os.path.join(folder, fname)
        if not os.path.isfile(path):
            continue
        for text, page in read_file(path):
            # csv rows are already small, so keep them as one chunk
            pieces = [text] if fname.lower().endswith(".csv") else chunk_text(text, size, overlap)
            for piece in pieces:
                chunks.append({"source": fname, "page": page, "text": piece})
    return chunks


class Index:
    """Very simple vector search using numpy."""

    def __init__(self, chunks):
        self.chunks = chunks
        print(f"[ingest] embedding {len(chunks)} chunks...")
        vecs = np.array([embed(c["text"]) for c in chunks], dtype="float32")
        self.vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)

    def retrieve(self, query, k=4):
        q = np.array(embed(query), dtype="float32")
        q = q / np.linalg.norm(q)
        scores = self.vecs @ q
        top = np.argsort(scores)[::-1][:k]
        return [dict(self.chunks[i], score=float(scores[i])) for i in top]