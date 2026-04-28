"""
evaluator.py
Reliability and evaluation system for the AI music recommender.

Runs a fixed set of benchmark queries through the full pipeline and
measures how well results align with expected mood, energy, and quality thresholds.

Usage:
    python3 -m src.main --eval
"""

import logging
import time

try:
    from src.ai_interface import get_recommendations
except ModuleNotFoundError:
    from ai_interface import get_recommendations

logger = logging.getLogger(__name__)

BENCHMARK_CASES = [
    {
        "id": "study_chill",
        "query": "something calm and chill to study to",
        "expected_moods": ["chill", "focused"],
        "max_energy": 0.55,
    },
    {
        "id": "workout_hype",
        "query": "high energy music for the gym",
        "expected_moods": ["energetic", "euphoric", "intense"],
        "min_energy": 0.65,
    },
    {
        "id": "sad_rainy",
        "query": "sad melancholic songs for a rainy afternoon",
        "expected_moods": ["melancholic", "romantic"],
        "max_energy": 0.5,
    },
    {
        "id": "happy_morning",
        "query": "happy upbeat songs to start my morning",
        "expected_moods": ["happy", "euphoric"],
        "min_energy": 0.5,
    },
    {
        "id": "romantic_dinner",
        "query": "romantic background music for a dinner date",
        "expected_moods": ["romantic", "happy"],
        "max_energy": 0.65,
    },
    {
        "id": "angry_release",
        "query": "something aggressive and loud to let off steam",
        "expected_moods": ["angry", "intense"],
        "min_energy": 0.7,
    },
]


def _evaluate_case(case: dict, result: dict, all_genres: set) -> dict:
    recs  = result["recommendations"]
    prefs = result["interpreted_prefs"]
    top_songs = [song for song, _, _ in recs]

    # Metric 1: mood alignment — fraction of top results with an expected mood
    expected_moods = case.get("expected_moods", [])
    mood_hits = sum(1 for s in top_songs if s["mood"] in expected_moods)
    mood_rate = round(mood_hits / len(top_songs), 2) if top_songs else 0.0

    # Metric 2: energy alignment — fraction of top results within expected energy band
    min_e = case.get("min_energy", 0.0)
    max_e = case.get("max_energy", 1.0)
    energy_hits = sum(1 for s in top_songs if min_e <= s["energy"] <= max_e)
    energy_rate = round(energy_hits / len(top_songs), 2) if top_songs else 0.0

    # Metric 3: genre validity — Gemini mapped to a genre that exists in the catalog
    genre_valid = prefs.get("genre", "") in all_genres

    # Metric 4: top result has a non-trivial score
    top_score = round(recs[0][1], 2) if recs else 0.0
    score_ok  = top_score >= 0.5

    # Metric 5: AI confidence in its own interpretation
    confidence = round(float(prefs.get("confidence", 0.0)), 2)

    passed = mood_rate >= 0.4 and genre_valid and score_ok

    return {
        "case_id":              case["id"],
        "query":                case["query"],
        "interpreted_genre":    prefs.get("genre"),
        "interpreted_mood":     prefs.get("mood"),
        "interpreted_energy":   prefs.get("target_energy"),
        "confidence":           confidence,
        "mood_alignment_rate":  mood_rate,
        "energy_alignment_rate": energy_rate,
        "genre_valid":          genre_valid,
        "top_score":            top_score,
        "passed":               passed,
    }


def _build_summary_line(summary: dict) -> str:
    """Produce a one-line human-readable summary of evaluation results."""
    passed     = summary["passed"]
    total      = summary["total"]
    avg_conf   = summary["avg_confidence"]
    failed_ids = [c["case_id"] for c in summary["cases"] if not c.get("passed")]

    line = f"{passed} out of {total} benchmark cases passed. "
    line += f"Average confidence: {avg_conf:.2f}. "

    if not failed_ids:
        line += "All cases passed — no systematic failures detected."
    else:
        line += f"Failed cases: {', '.join(failed_ids)}. "
        # Identify the most common failure reason
        low_mood  = [c for c in summary["cases"] if not c.get("passed") and c.get("mood_alignment_rate", 1) < 0.4]
        bad_genre = [c for c in summary["cases"] if not c.get("passed") and not c.get("genre_valid", True)]
        if bad_genre:
            line += "The AI mapped some queries to genres not in the catalog."
        elif low_mood:
            line += "The AI struggled to align moods for ambiguous or niche requests."
        else:
            line += "Results did not meet score or alignment thresholds."

    return line


def run_evaluation(songs: list) -> dict:
    """
    Run all benchmark cases through the full RAG pipeline.
    Returns a summary report with per-case metrics, an overall pass rate,
    average confidence score, and a plain-language summary line.
    """
    all_genres   = {s["genre"] for s in songs}
    case_results = []

    for case in BENCHMARK_CASES:
        logger.info("Running benchmark: %s — %r", case["id"], case["query"])
        start = time.time()
        try:
            result  = get_recommendations(case["query"], songs, k=5)
            metrics = _evaluate_case(case, result, all_genres)
        except Exception as e:
            logger.error("Benchmark %s raised an exception: %s", case["id"], e)
            metrics = {
                "case_id": case["id"], "query": case["query"],
                "error": str(e), "passed": False, "confidence": 0.0,
            }

        metrics["latency_s"] = round(time.time() - start, 2)
        case_results.append(metrics)
        logger.info(
            "Benchmark %s — passed=%s confidence=%.2f latency=%.2fs",
            case["id"], metrics["passed"],
            metrics.get("confidence", 0.0), metrics["latency_s"],
        )

    total        = len(case_results)
    passed       = sum(1 for r in case_results if r.get("passed"))
    avg_conf     = round(
        sum(r.get("confidence", 0.0) for r in case_results) / total, 2
    ) if total else 0.0

    summary = {
        "total":          total,
        "passed":         passed,
        "failed":         total - passed,
        "pass_rate":      round(passed / total, 2) if total else 0.0,
        "avg_confidence": avg_conf,
        "cases":          case_results,
    }
    summary["summary_line"] = _build_summary_line(summary)

    logger.info("Evaluation complete — %s", summary["summary_line"])
    return summary


def run_comparison(songs: list) -> dict:
    """
    Run all benchmark cases twice — once without knowledge base context and once with it —
    and report the measurable difference in mood alignment, energy alignment, and pass rate.
    This demonstrates the RAG enhancement's impact on output quality.
    """
    all_genres = {s["genre"] for s in songs}
    comparison_rows = []

    for case in BENCHMARK_CASES:
        logger.info("Comparing case: %s", case["id"])
        row = {"case_id": case["id"], "query": case["query"]}

        for use_ctx in (False, True):
            label = "with_context" if use_ctx else "without_context"
            try:
                result  = get_recommendations(case["query"], songs, k=5, use_context=use_ctx)
                metrics = _evaluate_case(case, result, all_genres)
            except Exception as e:
                logger.error("Comparison %s (%s) failed: %s", case["id"], label, e)
                metrics = {"mood_alignment_rate": 0.0, "energy_alignment_rate": 0.0,
                           "passed": False, "interpreted_genre": "error",
                           "interpreted_mood": "error", "confidence": 0.0}
            row[label] = metrics

        # Compute deltas
        base = row["without_context"]
        rag  = row["with_context"]
        row["mood_delta"]   = round(rag["mood_alignment_rate"]   - base["mood_alignment_rate"],   2)
        row["energy_delta"] = round(rag["energy_alignment_rate"] - base["energy_alignment_rate"], 2)
        row["pass_changed"] = rag["passed"] != base["passed"]
        comparison_rows.append(row)
        logger.info(
            "Case %s — mood delta: %+.0f%%  energy delta: %+.0f%%  pass changed: %s",
            case["id"], row["mood_delta"] * 100, row["energy_delta"] * 100, row["pass_changed"],
        )

    base_passed = sum(1 for r in comparison_rows if r["without_context"]["passed"])
    rag_passed  = sum(1 for r in comparison_rows if r["with_context"]["passed"])
    total       = len(comparison_rows)

    avg_mood_base = round(sum(r["without_context"]["mood_alignment_rate"] for r in comparison_rows) / total, 2)
    avg_mood_rag  = round(sum(r["with_context"]["mood_alignment_rate"]    for r in comparison_rows) / total, 2)

    return {
        "total":               total,
        "without_context_passed": base_passed,
        "with_context_passed":    rag_passed,
        "avg_mood_without":    avg_mood_base,
        "avg_mood_with":       avg_mood_rag,
        "avg_mood_delta":      round(avg_mood_rag - avg_mood_base, 2),
        "cases":               comparison_rows,
    }
