"""Lesson 5: Retrieval-augmented generation (RAG).

Run:  python lessons/05_rag/main.py                     # demo questions
      python lessons/05_rag/main.py "your question here"
Read alongside: lab/retrieval.py (search) and lab/rag.py (the pipeline).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lab.common import header
from lab.rag import answer
from lab.retrieval import get_index

QUESTIONS = sys.argv[1:] or [
    "Can I return a helmet I've already tried on?",
    "How long is the warranty on an e-bike battery?",
    "Do you ship to Australia?",          # not covered: should say it doesn't know
    "What does a tune-up cost for a Lumen Plus member?",
]

for q in QUESTIONS:
    header(q)

    # Look at retrieval on its own first. If the right chunk isn't here, no
    # amount of prompt engineering will fix the answer.
    print("Retrieved:")
    for chunk, score in get_index().search(q, top_k=3):
        print(f"  {score:5.2f}  {chunk.id:<14} {chunk.title}")

    result = answer(q, top_k=3)
    a = result.answer
    print(f"\nAnswer: {a.answer}")
    print(f"Cited: {a.cited_ids}   answerable={a.answerable}")
    print(f"~${result.cost:.4f}, {result.latency_s:.1f}s")
