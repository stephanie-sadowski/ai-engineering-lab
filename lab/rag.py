"""The RAG pipeline: retrieve -> build prompt -> generate a cited answer.

Lesson 5 runs it interactively; lesson 6 evaluates it under different settings.
"""
import time
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from lab.common import MODEL, client, cost_of
from lab.retrieval import format_context, get_index

SYSTEM = """You answer customer questions for Lumen Bikes using ONLY the documents provided.

Rules:
- If the documents don't contain the answer, set answerable=false and say you don't know.
  Never fill gaps with general knowledge: a confident wrong policy is worse than "I don't know".
- Cite the id of every document you used."""


class RagAnswer(BaseModel):
    answer: str = Field(description="A concise answer, 1-3 sentences")
    cited_ids: list[str] = Field(description="Ids of the documents the answer relies on")
    answerable: bool = Field(description="False if the documents don't contain the answer")


@dataclass
class RagResult:
    question: str
    answer: RagAnswer
    retrieved_ids: list[str]
    cost: float
    latency_s: float
    usage: dict = field(default_factory=dict)


def answer(question: str, top_k: int = 3, effort: str = "low", model: str = MODEL) -> RagResult:
    start = time.perf_counter()

    # 1. Retrieve: find the few chunks most likely to contain the answer.
    hits = get_index().search(question, top_k=top_k)

    # 2. Augment: put them in the prompt. Documents first, question last,
    #    which tends to work better than the other way round.
    prompt = f"<documents>\n{format_context(hits)}\n</documents>\n\nQuestion: {question}"

    # 3. Generate: structured, so citations come back as data you can check.
    response = client.messages.parse(
        model=model,
        max_tokens=16000,
        output_config={"effort": effort},
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_format=RagAnswer,
    )
    return RagResult(
        question=question,
        answer=response.parsed_output,
        retrieved_ids=[c.id for c, _ in hits],
        cost=cost_of(response),
        latency_s=time.perf_counter() - start,
        usage={"input": response.usage.input_tokens, "output": response.usage.output_tokens},
    )
