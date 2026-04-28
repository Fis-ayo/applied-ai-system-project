"""
main.py
Entry point for the AI Music Recommender.

Run from the project root:
    python3 -m src.main            # interactive natural-language mode
    python3 -m src.main --eval     # run reliability evaluation suite
"""

import argparse
import logging
import os
import sys

from dotenv import load_dotenv
load_dotenv()


def setup_logging() -> None:
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("logs/app.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def interactive_mode(songs: list) -> None:
    try:
        from src.ai_interface import get_recommendations
    except ModuleNotFoundError:
        from ai_interface import get_recommendations

    print("\n" + "=" * 60)
    print("  AI Music Recommender — Natural Language Search")
    print("  Type a request, or 'quit' to exit.")
    print("=" * 60 + "\n")

    while True:
        try:
            query = input("What are you in the mood for? ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if query.lower() in ("quit", "exit", "q", ""):
            print("Goodbye!")
            break

        print("\nFinding recommendations...\n")
        try:
            result = get_recommendations(query, songs, k=5)
        except Exception as e:
            print(f"Something went wrong: {e}\n")
            continue

        prefs = result["interpreted_prefs"]
        print(f"Interpreted as: genre={prefs.get('genre')}  |  "
              f"mood={prefs.get('mood')}  |  energy={prefs.get('target_energy')}")
        if prefs.get("reasoning"):
            print(f"Reasoning: {prefs['reasoning']}")
        print()

        print("Top recommendations:")
        for i, (song, score, reasons) in enumerate(result["recommendations"], 1):
            print(f"  {i}. {song['title']} — {song['artist']}")
            print(f"     genre: {song['genre']}  |  mood: {song['mood']}  |  "
                  f"energy: {song['energy']:.2f}  |  score: {score:.2f}")
        print()
        print(result["explanation"])
        print()


def eval_mode(songs: list) -> None:
    try:
        from src.evaluator import run_evaluation
    except ModuleNotFoundError:
        from evaluator import run_evaluation

    print("\nRunning reliability evaluation — this will make several API calls...\n")
    summary = run_evaluation(songs)

    width = 60
    print("\n" + "=" * width)
    print(f"  EVALUATION RESULTS: {summary['passed']}/{summary['total']} passed  "
          f"({summary['pass_rate'] * 100:.0f}%)  |  avg confidence: {summary['avg_confidence']:.2f}")
    print(f"\n  {summary['summary_line']}")
    print("=" * width)

    for case in summary["cases"]:
        status = "PASS" if case.get("passed") else "FAIL"
        print(f"\n  [{status}] {case['case_id']}")
        if "error" in case:
            print(f"    Error: {case['error']}")
        else:
            print(f"    Query          : {case['query']}")
            print(f"    Interpreted    : genre={case['interpreted_genre']}  "
                  f"mood={case['interpreted_mood']}  energy={case['interpreted_energy']}")
            print(f"    Confidence     : {case['confidence']:.2f}")
            print(f"    Mood alignment : {case['mood_alignment_rate'] * 100:.0f}%")
            print(f"    Energy align   : {case['energy_alignment_rate'] * 100:.0f}%")
            print(f"    Top score      : {case['top_score']}")
            print(f"    Genre valid    : {case['genre_valid']}")
            print(f"    Latency        : {case['latency_s']}s")

    print()


def compare_mode(songs: list) -> None:
    try:
        from src.evaluator import run_comparison
    except ModuleNotFoundError:
        from evaluator import run_comparison

    print("\nRunning RAG enhancement comparison — this will make 2x API calls per case...\n")
    report = run_comparison(songs)

    width = 60
    print("\n" + "=" * width)
    print("  RAG ENHANCEMENT: WITH vs. WITHOUT KNOWLEDGE BASE CONTEXT")
    print("=" * width)
    print(f"\n  Cases passed — without context: {report['without_context_passed']}/{report['total']}")
    print(f"  Cases passed — with context:    {report['with_context_passed']}/{report['total']}")
    print(f"  Avg mood alignment — without:   {report['avg_mood_without'] * 100:.0f}%")
    print(f"  Avg mood alignment — with:      {report['avg_mood_with'] * 100:.0f}%")
    delta_pct = report['avg_mood_delta'] * 100
    print(f"  Mood alignment delta:           {delta_pct:+.0f}%")

    print(f"\n{'─' * width}")
    for row in report["cases"]:
        base = row["without_context"]
        rag  = row["with_context"]
        mood_delta = row["mood_delta"] * 100
        print(f"\n  {row['case_id']}")
        print(f"    Without context → genre={base['interpreted_genre']} "
              f"mood={base['interpreted_mood']}  mood_align={base['mood_alignment_rate']*100:.0f}%")
        print(f"    With context    → genre={rag['interpreted_genre']}  "
              f"mood={rag['interpreted_mood']}   mood_align={rag['mood_alignment_rate']*100:.0f}%")
        print(f"    Mood delta: {mood_delta:+.0f}%  |  Pass changed: {row['pass_changed']}")
    print()


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable is not set.")
        print("Set it with:  export GOOGLE_API_KEY=your_key_here")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="AI Music Recommender")
    parser.add_argument("--eval",    action="store_true", help="Run the reliability evaluation suite")
    parser.add_argument("--compare", action="store_true", help="Compare results with vs. without knowledge base context")
    args = parser.parse_args()

    try:
        from src.recommender import load_songs
    except ModuleNotFoundError:
        from recommender import load_songs

    songs = load_songs("data/songs.csv")
    logger.info("Loaded %d songs from catalog", len(songs))

    if args.eval:
        eval_mode(songs)
    elif args.compare:
        compare_mode(songs)
    else:
        interactive_mode(songs)


if __name__ == "__main__":
    main()
