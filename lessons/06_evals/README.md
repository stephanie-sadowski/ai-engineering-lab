# Lesson 6: Evals

**Goal:** replace "it seems to work" with numbers, so every change you make is a measured experiment.

```bash
python lessons/06_evals/main.py --label baseline --top-k 3 --effort low
python lessons/06_evals/main.py --label "top_k=1"  --top-k 1
python lessons/06_evals/main.py --label "top_k=5"  --top-k 5
python lessons/06_evals/main.py --label "high effort" --effort high
python -m http.server -d docs 8000   # then open http://localhost:8000
```

Each run is appended to `docs/data/experiments.json`, and the dashboard charts every run side by side.

## Concepts

- **Evals are the core skill.** Models are non-deterministic and prompts are fragile, so you need an eval to know whether a change helped. Most of AI engineering is building systems you can measure.
- **The eval set.** [`data/eval_set.json`](../../data/eval_set.json) has 18 cases with a question, the gold chunk ids, a reference answer, and whether the question is answerable at all. Include cases the system *should refuse*. They catch hallucination.
- **Use the cheapest grader that works:**
  - *Code graders* are free, fast and exact: retrieval recall, citation validity, abstaining when it should.
  - *LLM-as-judge* grades fuzzy things like "is this answer correct?" It uses a cheap model (Haiku) and needs spot-checking against your own judgement.
- **Measure components separately.** Retrieval recall vs answer accuracy tells you *where* a failure happens. A wrong answer with a retrieval miss is a search problem, not a prompt problem.
- **Quality, cost, latency.** Every config trades these off. The dashboard shows all three, because "most accurate" is rarely the right choice on its own.
- **Overfitting.** If you tune against the same 18 questions forever, you'll fit them. Real projects hold out a test set.

## Exercises

1. Run the four experiments above and open the dashboard. Which config would you ship, and why?
2. Find a FAIL. Is it a retrieval miss, a generation error, or a bad judge verdict? Read the `judge_reasoning`.
3. Add stemming to `lab/retrieval.py` (lesson 5, exercise 2), run `--label "stemming"`, and see whether `retrieval_recall` improves.
4. Add 5 adversarial questions: multi-part, misleading, or answerable only by combining two documents.
5. Calibrate the judge: grade 10 answers yourself and count how often you agree with Haiku.
