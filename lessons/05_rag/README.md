# Lesson 5: Retrieval-augmented generation (RAG)

**Goal:** answer questions from your own documents, with citations, without stuffing every document into every prompt.

```bash
python lessons/05_rag/main.py
python lessons/05_rag/main.py "What happens if my package is marked delivered but never arrived?"
```

Read [`lab/retrieval.py`](../../lab/retrieval.py) and [`lab/rag.py`](../../lab/rag.py). They are the core of this lesson.

## Concepts

- **Why RAG.** Lesson 2 put the whole handbook in the prompt. That stops working at thousands of documents: it costs too much and adds noise. RAG retrieves only the few relevant chunks for each question.
- **The pipeline.** *Chunk* the documents, then *retrieve* the top-k chunks for the question, *augment* the prompt with them, and *generate* the answer.
- **Retrieval is usually the bottleneck.** If the right chunk isn't retrieved, the model can't answer, however good the prompt. Always look at what was retrieved before you blame the model.
- **BM25 vs embeddings.** BM25 matches keywords. It's fast, transparent and good with ids and product names, but it misses synonyms ("bring back" vs "return"). Embeddings match meaning. Real systems often use both ("hybrid search").
- **Grounding and abstaining.** The system prompt tells the model to say "I don't know" rather than guess. For a support bot, a made-up refund policy is a serious failure, much worse than not answering.
- **Citations.** Returning `cited_ids` as data lets you check them in code. Lesson 6 does exactly that.

## Exercises

1. Try "Can I bring back my bike?" BM25 misses the synonym. How would you fix it? (Query rewriting with a cheap model call? Embeddings?)
2. BM25 here has no stemming, so "helmet" doesn't match "helmets". Add a simple stemmer to `tokenize()`, then measure the effect in lesson 6.
3. Change chunking from "one chunk per section" to "one chunk per file". What gets better, and what gets worse?
4. Look at Claude's built-in [citations](https://platform.claude.com/docs/en/build-with-claude/citations) feature, which cites exact character spans.
