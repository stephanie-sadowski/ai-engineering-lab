"""Retrieval for RAG: chunk documents, then rank chunks with BM25.

BM25 is the classic keyword-ranking algorithm behind most search engines. It is
written out by hand here (no libraries) so you can see there is no magic:
a chunk scores high when it contains the query's words, especially rare words,
and the score is normalized so long chunks don't win just by being long.

Production systems often add embeddings (semantic search) on top of this, or
replace it. A strong, common setup is "hybrid": BM25 + embeddings, merged.
"""
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from lab.common import DATA_DIR

HANDBOOK_DIR = DATA_DIR / "handbook"

STOPWORDS = set(
    "a an and are as at be by can do does for from how i if in is it my of on or "
    "the to what when where which who will with you your".split()
)


@dataclass
class Chunk:
    id: str      # e.g. "returns#2" - used for citations
    title: str   # the section heading
    text: str


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in STOPWORDS]


def load_chunks(directory: Path = HANDBOOK_DIR) -> list[Chunk]:
    """Split each markdown file into one chunk per '## ' section.

    Chunking strategy matters a lot in RAG. Splitting on headings keeps each
    chunk about one topic. Alternatives: fixed-size windows with overlap,
    or sentence-based splitting. Lesson 6's eval is how you'd compare them.
    """
    chunks = []
    for path in sorted(directory.glob("*.md")):
        sections = re.split(r"^## ", path.read_text(), flags=re.MULTILINE)[1:]
        for i, section in enumerate(sections, start=1):
            title, _, body = section.partition("\n")
            chunks.append(Chunk(id=f"{path.stem}#{i}", title=title.strip(), text=body.strip()))
    return chunks


class BM25:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1, self.b = k1, b
        # Index the title too: headings are strong signals of what a chunk is about.
        self.docs = [tokenize(f"{c.title} {c.text}") for c in chunks]
        self.avg_len = sum(len(d) for d in self.docs) / len(self.docs)
        self.term_freqs = [Counter(d) for d in self.docs]
        doc_freq = Counter(term for d in self.docs for term in set(d))
        n = len(self.docs)
        # IDF: rare words ("helmet") matter more than common ones ("bike").
        self.idf = {t: math.log(1 + (n - df + 0.5) / (df + 0.5)) for t, df in doc_freq.items()}

    def score(self, query_terms: list[str], i: int) -> float:
        tf, length = self.term_freqs[i], len(self.docs[i])
        total = 0.0
        for term in query_terms:
            if term not in tf:
                continue
            freq = tf[term]
            norm = freq + self.k1 * (1 - self.b + self.b * length / self.avg_len)
            total += self.idf[term] * freq * (self.k1 + 1) / norm
        return total

    def search(self, query: str, top_k: int = 3) -> list[tuple[Chunk, float]]:
        terms = tokenize(query)
        scored = [(c, self.score(terms, i)) for i, c in enumerate(self.chunks)]
        scored = [s for s in scored if s[1] > 0]
        scored.sort(key=lambda s: s[1], reverse=True)
        return scored[:top_k]


_index: BM25 | None = None


def get_index() -> BM25:
    """Build the index once and reuse it."""
    global _index
    if _index is None:
        _index = BM25(load_chunks())
    return _index


def format_context(results: list[tuple[Chunk, float]]) -> str:
    """Wrap retrieved chunks in XML tags. Claude handles tagged context well,
    and the ids give it something concrete to cite."""
    return "\n".join(
        f'<document id="{c.id}" title="{c.title}">\n{c.text}\n</document>'
        for c, _ in results
    )
