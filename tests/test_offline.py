"""Tests that run without an API key or network: the deterministic parts of
the system. Model behaviour is tested by the eval harness (lesson 6) instead.
"""
import importlib.util
import json
from pathlib import Path

import pytest

from lab import orders
from lab.common import DATA_DIR
from lab.retrieval import BM25, Chunk, get_index, tokenize

ROOT = Path(__file__).resolve().parent.parent


def load_eval_module():
    spec = importlib.util.spec_from_file_location("evals", ROOT / "lessons/06_evals/main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- retrieval -----------------------------------------------------------------
def test_tokenize_drops_stopwords_and_punctuation():
    assert tokenize("What is the return window?") == ["return", "window"]


def test_bm25_prefers_rare_matching_terms():
    index = BM25([
        Chunk("a#1", "Bikes", "bike bike bike frame"),
        Chunk("b#1", "Helmets", "helmet hygiene seal bike"),
    ])
    assert index.search("helmet seal")[0][0].id == "b#1"


def test_handbook_chunks_have_unique_ids():
    ids = [c.id for c in get_index().chunks]
    assert len(ids) == len(set(ids)) > 10


def test_eval_set_gold_ids_exist():
    ids = {c.id for c in get_index().chunks}
    for case in json.loads((DATA_DIR / "eval_set.json").read_text()):
        assert set(case["gold_ids"]) <= ids, case["id"]
        assert case["answerable"] == bool(case["gold_ids"]), case["id"]


def test_retrieval_recall_at_3_baseline():
    """Guards against regressions in retrieval. Raise the bar as you improve it."""
    cases = [c for c in json.loads((DATA_DIR / "eval_set.json").read_text()) if c["answerable"]]
    hits = sum(
        bool(set(c["gold_ids"]) & {chunk.id for chunk, _ in get_index().search(c["question"], 3)})
        for c in cases
    )
    assert hits / len(cases) >= 0.8


# --- tools ----------------------------------------------------------------------
def test_lookup_order_normalizes_id_and_computes_days():
    order = orders.lookup_order(" lb-1001 ")
    assert order["days_since_delivery"] == 12


def test_lookup_unknown_order_raises():
    with pytest.raises(KeyError):
        orders.lookup_order("LB-9999")


@pytest.mark.parametrize("amount", [0, -5, 99999])
def test_refund_rejects_invalid_amounts(amount):
    with pytest.raises(ValueError):
        orders.issue_refund("LB-1001", amount, "test")


def test_refund_records_valid_amount():
    before = len(orders.REFUNDS)
    result = orders.issue_refund("LB-1001", 1241.0, "change of mind minus $49 fee")
    assert result["status"] == "refund issued"
    assert len(orders.REFUNDS) == before + 1


# --- eval metrics ---------------------------------------------------------------
def test_summarize_metrics():
    evals = load_eval_module()
    rows = [
        {"answerable": True, "correct": True, "retrieval_hit": True, "citations_valid": True, "cost": 0.01, "latency_s": 1.0},
        {"answerable": True, "correct": False, "retrieval_hit": False, "citations_valid": True, "cost": 0.01, "latency_s": 3.0},
        {"answerable": False, "correct": True, "cost": 0.02, "latency_s": 2.0},
    ]
    m = evals.summarize(rows)
    assert m["accuracy"] == pytest.approx(2 / 3)
    assert m["retrieval_recall"] == 0.5
    assert m["abstain_accuracy"] == 1.0
    assert m["total_cost"] == pytest.approx(0.04)
    assert m["latency_p50_s"] == 2.0
