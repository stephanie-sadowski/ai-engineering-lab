"""Lesson 6: Evals - measuring whether your AI system actually works.

Run:  python lessons/06_evals/main.py --label baseline --top-k 3 --effort low
      python lessons/06_evals/main.py --label "top_k=1" --top-k 1
      python lessons/06_evals/main.py --label "high effort" --effort high

Each run is appended to docs/data/experiments.json, which the dashboard
(docs/index.html) charts. Every run costs money: ~18 model calls plus 15
judge calls.
"""
import argparse
import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lab.common import DATA_DIR, JUDGE_MODEL, MODEL, ROOT, client, cost_of, header
from lab.rag import answer

EVAL_SET = json.loads((DATA_DIR / "eval_set.json").read_text())
RESULTS_FILE = ROOT / "docs" / "data" / "experiments.json"


# --- Grader 1: LLM-as-judge ---------------------------------------------------
# Comparing free-text answers with exact string matching fails ("$79/yr" vs
# "79 dollars a year"), so a cheaper model grades meaning against a reference.
# Judges need calibration: spot-check their verdicts by hand before trusting them.
class Verdict(BaseModel):
    reasoning: str = Field(description="One sentence: what matches or differs")
    correct: bool = Field(description="True if the answer states the reference's key facts "
                                      "and adds nothing that contradicts it")


def judge(question: str, reference: str, candidate: str) -> tuple[Verdict, float]:
    response = client.messages.parse(
        model=JUDGE_MODEL,
        max_tokens=4000,
        output_config={"effort": "low"},
        system="You grade a support bot's answer against a reference answer. Be strict "
               "about facts (numbers, yes/no, conditions) and lenient about wording.",
        messages=[{"role": "user", "content":
                   f"<question>{question}</question>\n<reference>{reference}</reference>\n"
                   f"<candidate>{candidate}</candidate>"}],
        output_format=Verdict,
    )
    return response.parsed_output, cost_of(response)


# --- Run one eval case: deterministic graders + the judge ---------------------
def run_case(case: dict, top_k: int, effort: str, model: str) -> dict:
    result = answer(case["question"], top_k=top_k, effort=effort, model=model)
    a = result.answer
    gold = set(case["gold_ids"])
    row = {
        "id": case["id"],
        "question": case["question"],
        "answer": a.answer,
        "retrieved_ids": result.retrieved_ids,
        "cited_ids": a.cited_ids,
        "cost": result.cost,
        "latency_s": round(result.latency_s, 2),
        "answerable": case["answerable"],
    }
    if case["answerable"]:
        # Grader 2 (code): did retrieval find the right chunk? Free and exact.
        row["retrieval_hit"] = bool(gold & set(result.retrieved_ids))
        # Grader 3 (code): did it cite something it was actually given?
        row["citations_valid"] = bool(a.cited_ids) and set(a.cited_ids) <= set(result.retrieved_ids)
        verdict, judge_cost = judge(case["question"], case["reference"], a.answer)
        row["correct"] = verdict.correct and a.answerable
        row["judge_reasoning"] = verdict.reasoning
        row["cost"] += judge_cost
    else:
        # Grader 4 (code): for questions the handbook can't answer, the only
        # right move is to abstain. No judge needed.
        row["correct"] = not a.answerable
        row["judge_reasoning"] = "abstained" if not a.answerable else "answered an unanswerable question"
    return row


def summarize(rows: list[dict]) -> dict:
    answerable = [r for r in rows if r["answerable"]]
    unanswerable = [r for r in rows if not r["answerable"]]
    latencies = sorted(r["latency_s"] for r in rows)
    return {
        "accuracy": sum(r["correct"] for r in rows) / len(rows),
        "answer_accuracy": sum(r["correct"] for r in answerable) / len(answerable),
        "retrieval_recall": sum(r["retrieval_hit"] for r in answerable) / len(answerable),
        "citation_validity": sum(r["citations_valid"] for r in answerable) / len(answerable),
        "abstain_accuracy": sum(r["correct"] for r in unanswerable) / len(unanswerable),
        "total_cost": sum(r["cost"] for r in rows),
        "cost_per_question": sum(r["cost"] for r in rows) / len(rows),
        "latency_p50_s": statistics.median(latencies),
        "latency_p90_s": latencies[int(0.9 * (len(latencies) - 1))],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, help="Name for this experiment on the dashboard")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--effort", default="low", choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--notes", default="", help="What you changed and why")
    args = parser.parse_args()

    header(f"Eval: {args.label}  (model={args.model} top_k={args.top_k} effort={args.effort})")
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(lambda c: run_case(c, args.top_k, args.effort, args.model), EVAL_SET))

    for r in rows:
        mark = "PASS" if r["correct"] else "FAIL"
        print(f"  {mark}  {r['id']}  {r['question'][:55]:<55}  {r['judge_reasoning'][:60]}")

    metrics = summarize(rows)
    print()
    for k, v in metrics.items():
        print(f"  {k:<20} {v:.4f}" if "cost" in k else f"  {k:<20} {v:.2f}")

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(RESULTS_FILE.read_text()) if RESULTS_FILE.exists() else {"experiments": []}
    data["experiments"].append({
        "label": args.label,
        "notes": args.notes,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config": {"model": args.model, "judge_model": JUDGE_MODEL,
                   "top_k": args.top_k, "effort": args.effort},
        "metrics": metrics,
        "results": rows,
    })
    RESULTS_FILE.write_text(json.dumps(data, indent=2))
    print(f"\nSaved to {RESULTS_FILE.relative_to(ROOT)}. Open docs/index.html to compare runs.")


if __name__ == "__main__":
    main()
