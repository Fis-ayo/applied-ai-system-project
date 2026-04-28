"""
app.py
Streamlit UI for the AI Music Recommender.

Run from the project root:
    streamlit run app.py
"""

import os
import sys
import logging

from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# Allow imports from src/ without installing the package
sys.path.insert(0, os.path.dirname(__file__))

from src.recommender import load_songs
from src.ai_interface import get_recommendations
from src.evaluator import run_evaluation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler("logs/app.log")] if os.path.exists("logs") else [],
)
os.makedirs("logs", exist_ok=True)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Music Recommender",
    page_icon="🎵",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Guard: API key
# ---------------------------------------------------------------------------
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("**GOOGLE_API_KEY is not set.** Add it to your environment before running the app.")
    st.code("export GOOGLE_API_KEY=your_key_here", language="bash")
    st.stop()

# ---------------------------------------------------------------------------
# Load catalog (cached so it only reads the CSV once per session)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading song catalog...")
def load_catalog():
    return load_songs("data/songs.csv")

songs = load_catalog()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🎵 AI Music Recommender")
    st.markdown(
        "Type anything — an activity, a mood, a vibe — and the AI will "
        "find songs that match using **natural language understanding + RAG**."
    )
    st.divider()
    st.metric("Songs in catalog", len(songs))
    st.metric("Genres covered", len({s["genre"] for s in songs}))

    st.divider()
    num_results = st.slider("Number of recommendations", min_value=3, max_value=10, value=5)
    scoring_mode = st.selectbox(
        "Scoring strategy",
        options=["balanced", "genre_first", "mood_first", "energy_focused"],
        index=0,
        help="Controls how genre, mood, and energy are weighted when ranking songs.",
    )

    st.divider()
    run_eval    = st.button("Run Reliability Evaluation", use_container_width=True)
    run_compare = st.button("Compare RAG Enhancement", use_container_width=True,
                            help="Runs each benchmark with and without knowledge base context to measure improvement")

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title("What are you in the mood for?")
st.caption("Describe any vibe, activity, or feeling. The AI interprets it and finds matching songs.")

query = st.text_input(
    label="Your request",
    placeholder='e.g. "something chill for studying" or "hype music for the gym"',
    label_visibility="collapsed",
)
search = st.button("Find Songs", type="primary", use_container_width=False)

# ---------------------------------------------------------------------------
# Recommendation results
# ---------------------------------------------------------------------------
if search and query.strip():
    with st.spinner("Asking Claude to find your songs..."):
        try:
            result = get_recommendations(query.strip(), songs, k=num_results, mode=scoring_mode)
        except Exception as e:
            st.error(f"Something went wrong: {e}")
            st.stop()

    prefs = result["interpreted_prefs"]
    recs  = result["recommendations"]

    # --- Interpreted preferences ---
    st.subheader("Interpreted as")
    col1, col2, col3 = st.columns(3)
    col1.metric("Genre", prefs.get("genre", "—"))
    col2.metric("Mood", prefs.get("mood", "—"))
    col3.metric("Energy target", f"{prefs.get('target_energy', 0):.2f}")

    if prefs.get("reasoning"):
        st.caption(f"Reasoning: {prefs['reasoning']}")

    st.divider()

    # --- Claude's explanation ---
    st.subheader("Why these songs?")
    st.info(result["explanation"])

    st.divider()

    # --- Song cards ---
    st.subheader(f"Top {len(recs)} Recommendations")

    from src.recommender import SCORING_MODES
    max_score = SCORING_MODES[scoring_mode].max_score

    for rank, (song, score, reasons) in enumerate(recs, start=1):
        with st.container(border=True):
            left, right = st.columns([3, 1])
            with left:
                st.markdown(f"**{rank}. {song['title']}** &nbsp; *{song['artist']}*")
                badge_cols = st.columns(4)
                badge_cols[0].caption(f"🎸 {song['genre']}")
                badge_cols[1].caption(f"💭 {song['mood']}")
                badge_cols[2].caption(f"⚡ energy {song['energy']:.2f}")
                badge_cols[3].caption(f"🎵 tempo {song['tempo_bpm']:.0f} bpm")
                with st.expander("Scoring details"):
                    st.caption(reasons)
            with right:
                st.metric("Score", f"{score:.2f} / {max_score:.1f}")
                st.progress(score / max_score)

elif search and not query.strip():
    st.warning("Please enter a request before searching.")

# ---------------------------------------------------------------------------
# RAG comparison panel
# ---------------------------------------------------------------------------
if run_compare:
    st.divider()
    st.subheader("RAG Enhancement: With vs. Without Knowledge Base Context")
    st.caption("Each benchmark runs twice — once with context injection, once without — to measure the improvement.")

    with st.spinner("Running comparison — this makes 2× API calls per case..."):
        try:
            from src.evaluator import run_comparison
            report = run_comparison(songs)
        except Exception as e:
            st.error(f"Comparison failed: {e}")
            st.stop()

    cols = st.columns(4)
    cols[0].metric("Without context", f"{report['without_context_passed']}/{report['total']} passed")
    cols[1].metric("With context",    f"{report['with_context_passed']}/{report['total']} passed")
    cols[2].metric("Avg mood (without)", f"{report['avg_mood_without']*100:.0f}%")
    cols[3].metric("Avg mood (with)",    f"{report['avg_mood_with']*100:.0f}%",
                   delta=f"{report['avg_mood_delta']*100:+.0f}%")

    st.divider()
    for row in report["cases"]:
        base = row["without_context"]
        rag  = row["with_context"]
        with st.container(border=True):
            st.markdown(f"**{row['case_id']}** — *{row['query']}*")
            c1, c2 = st.columns(2)
            with c1:
                st.caption("Without context")
                st.write(f"genre: `{base['interpreted_genre']}` · mood: `{base['interpreted_mood']}`")
                st.progress(base["mood_alignment_rate"], text=f"Mood alignment: {base['mood_alignment_rate']*100:.0f}%")
            with c2:
                st.caption("With context")
                st.write(f"genre: `{rag['interpreted_genre']}` · mood: `{rag['interpreted_mood']}`")
                st.progress(rag["mood_alignment_rate"], text=f"Mood alignment: {rag['mood_alignment_rate']*100:.0f}%")
            delta = row["mood_delta"] * 100
            st.caption(f"Mood delta: **{delta:+.0f}%** · Pass changed: **{row['pass_changed']}**")

# ---------------------------------------------------------------------------
# Evaluation panel
# ---------------------------------------------------------------------------
if run_eval:
    st.divider()
    st.subheader("Reliability Evaluation")
    st.caption("Running 5 benchmark queries through the full pipeline...")

    with st.spinner("Running evaluation — this makes several API calls..."):
        try:
            summary = run_evaluation(songs)
        except Exception as e:
            st.error(f"Evaluation failed: {e}")
            st.stop()

    pass_rate = summary["pass_rate"]
    color = "normal" if pass_rate >= 0.8 else "inverse"

    res_cols = st.columns(4)
    res_cols[0].metric("Total cases", summary["total"])
    res_cols[1].metric("Passed", summary["passed"])
    res_cols[2].metric("Pass rate", f"{pass_rate * 100:.0f}%")
    res_cols[3].metric("Avg confidence", f"{summary['avg_confidence']:.2f}")

    st.info(summary["summary_line"])

    st.divider()
    for case in summary["cases"]:
        status_icon = "✅" if case.get("passed") else "❌"
        with st.expander(f"{status_icon} {case['case_id']} — *{case['query']}*"):
            if "error" in case:
                st.error(case["error"])
            else:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Mood alignment", f"{case['mood_alignment_rate'] * 100:.0f}%")
                c2.metric("Energy alignment", f"{case['energy_alignment_rate'] * 100:.0f}%")
                c3.metric("Top score", case["top_score"])
                c4.metric("Latency", f"{case['latency_s']}s")
                st.caption(
                    f"Interpreted → genre: **{case['interpreted_genre']}** | "
                    f"mood: **{case['interpreted_mood']}** | "
                    f"energy: **{case['interpreted_energy']}** | "
                    f"confidence: **{case.get('confidence', 'n/a')}** | "
                    f"genre valid: **{case['genre_valid']}**"
                )
