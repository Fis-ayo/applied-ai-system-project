# AI Music Recommender

A natural language music recommendation system powered by Gemini 2.5 Flash and Retrieval-Augmented Generation (RAG). Type anything — a mood, an activity, a vibe — and the system finds matching songs and explains why they fit.

**GitHub:** [Repo]
**Demo:** <div style="position: relative; padding-bottom: 52.708333333333336%; height: 0;"><iframe src="https://www.loom.com/embed/653ecdb954204b1da4cdbe9cd5f6171c" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div>

---

## Original Project

This project started as a rule-based music recommender simulation. The original system loaded a hand-curated catalog of 18 songs, scored each one against a hardcoded user profile using weighted genre, mood, and energy matching, and returned the top results with a plain-language explanation. It had no user interface and no AI — preferences were set directly in code as Python dictionaries.

---

## What Changed and Why It Matters

The final project replaces the static interface and small catalog with a full AI-powered pipeline:

- **Natural language input** — users describe what they want in plain English instead of setting structured fields in code
- **Gemini 2.5 Flash** interprets each request and maps it to `{genre, mood, target_energy}` before retrieval
- **RAG retrieval** — the rule-based scorer now runs against 3,420 real songs across 114 genres (sourced from the Kaggle Spotify dataset), not 18 hardcoded tracks
- **AI explanation** — Gemini writes a personalised response describing why the returned songs fit the request
- **Reliability evaluation** — a built-in evaluator runs 5 benchmark queries and measures mood alignment, energy alignment, genre validity, and score quality
- **Streamlit UI** — a browser-based interface replaces the terminal runner

This matters because it demonstrates how a rule-based retrieval system and an AI language model can be combined cleanly: the model handles ambiguous human language, the scorer handles deterministic ranking, and the result is both accurate and explainable.

---

## System Architecture

![System Diagram](assets/System%20Diagram.png)

| Component | Role |
|---|---|
| **Gemini Interpreter** | Converts a natural language query into `{genre, mood, target_energy}` |
| **Song Catalog** | 3,420 songs · 114 genres · sourced from Kaggle Spotify dataset |
| **Rule-based Scorer** | Scores every song against the interpreted preferences using weighted matching |
| **Gemini Explainer** | Reads the top candidates and writes a plain-language recommendation response |
| **Streamlit UI** | Browser interface — search bar, result cards, score bars, evaluation panel |
| **Evaluator** | Runs 5 fixed benchmark queries through the full pipeline and reports metrics |
| **Human Review** | Developer reads the pass/fail report to assess reliability before sharing |

**Data flow in brief:**
```
User query → Gemini interprets → Rule-based scorer retrieves from catalog
          → Gemini explains → Results displayed in UI
```

---

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- A Google AI Studio API key ([get one here](https://aistudio.google.com/apikey))
- The Kaggle Spotify Tracks dataset (`dataset.csv`) placed in `data/`

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd applied-ai-systems-final
```

### 2. Create and activate a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate        # Mac / Linux
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your API key

```bash
cp .env.example .env
# Open .env and replace the placeholder with your real key:
# GOOGLE_API_KEY=your_key_here
```

### 5. Build the song catalog

```bash
python3 data/preprocess.py
```

This reads `data/dataset.csv`, samples 30 songs from each of the 114 genres, derives mood labels from audio features, and writes `data/songs.csv` (3,420 songs).

### 6. Run the app

```bash
streamlit run app.py
```

Or use the terminal interface:

```bash
python3 -m src.main              # interactive mode
python3 -m src.main --eval       # reliability evaluation
```

### 7. Run tests

```bash
pytest
```

---

## Sample Interactions

### Example 1 — Study session

**Input:** `something calm and focused for studying late at night`

**Interpreted as:** genre: `study` · mood: `focused` · energy: `0.30`

**Top result:** *"Weightless" by Marconi Union* — genre: ambient · mood: focused · energy: 0.18 · score: 3.64 / 4.0

**AI explanation:**
> These tracks are ideal for a late-night study session — they sit at very low energy levels and carry a focused, undistracted mood. "Weightless" in particular is specifically designed to reduce anxiety and aid concentration, making it a natural top pick for your request.

---

### Example 2 — Gym session

**Input:** `high energy hype music for the gym`

**Interpreted as:** genre: `hip-hop` · mood: `energetic` · energy: `0.90`

**Top result:** *"HUMBLE." by Kendrick Lamar* — genre: hip-hop · mood: energetic · energy: 0.89 · score: 3.98 / 4.0

**AI explanation:**
> These are high-octane tracks built for pushing through a tough workout. "HUMBLE." by Kendrick Lamar hits almost exactly your target energy and delivers the hard-hitting mood you're after — it's the kind of track that makes you push one more rep.

---

### Example 3 — Dinner date

**Input:** `romantic background music for a dinner date`

**Interpreted as:** genre: `r-n-b` · mood: `romantic` · energy: `0.45`

**Top result:** *"Adorn" by Miguel* — genre: r-n-b · mood: romantic · energy: 0.47 · score: 3.96 / 4.0

**AI explanation:**
> These songs create exactly the right warm, intimate atmosphere for a dinner date. "Adorn" by Miguel is a standout — its smooth r-n-b sound and romantic mood sit right at the moderate energy level you want: present enough to fill the room, relaxed enough to let conversation flow.

---

## Design Decisions

**Why RAG instead of sending all songs to the AI?**
Sending 3,420 songs in a prompt would be slow, expensive, and unreliable. Instead the rule-based scorer acts as a fast retrieval filter — it narrows 3,420 songs down to the top 5–10 — and Gemini only sees those candidates. This keeps API costs low and response times fast while still producing natural, contextual explanations.

**Why keep the rule-based scorer at all?**
The scorer is deterministic and fully explainable. Every recommendation comes with a numeric score and a reason string showing exactly which rules fired. This makes the system auditable in a way that a pure LLM approach is not — you can always trace why a song ranked where it did.

**Why Gemini 2.5 Flash?**
It is fast, cost-effective, and available on a free API tier. For a two-step pipeline (interpret + explain) that makes two API calls per user request, latency and cost matter more than maximum capability. Gemini 2.5 Flash handles both structured JSON extraction and conversational explanation well.

**Why derive mood from audio features instead of using genre alone?**
Spotify's dataset does not include mood labels. Deriving mood from `valence` and `energy` (e.g. high valence + high energy → euphoric, low valence + low energy → melancholic) produces a consistent, rule-based label that maps naturally to how users describe what they want to hear.

**Trade-offs:**
- The rule-based scorer uses exact genre and mood matching — a `hip-hop` query returns zero genre points for a `rap` song even though they are acoustically close neighbors
- Derived mood labels are approximations — the boundary between "focused" and "chill" is a hard numeric threshold, not human judgment
- The catalog is sampled (30 songs per genre), so rare or niche sub-genres may have limited representation

---

## Testing Summary

**What the evaluator checks:**

The reliability system in `src/evaluator.py` runs 5 benchmark queries (study, gym, sad, happy, romantic) through the full pipeline and measures four metrics per case:

| Metric | What it checks |
|---|---|
| Mood alignment rate | % of top-5 results with a mood that matches the expected category |
| Energy alignment rate | % of top-5 results within the expected energy band |
| Genre validity | Whether Gemini mapped the query to a genre that exists in the catalog |
| Top score | Whether the highest-ranked song scored above a minimum threshold (≥ 0.5) |

A case passes if mood alignment ≥ 40%, genre is valid, and top score ≥ 0.5.

**What worked well:**
- Gemini consistently maps common activities (studying, gym, sleep) to sensible genre and mood combinations
- The scorer reliably surfaces genre and mood matches when they exist in the catalog
- The explainer produces natural, specific responses that mention real song details

**What did not work as expected:**
- Niche or cross-genre requests (e.g. "jazz-funk fusion") sometimes map to a broad fallback genre, missing the nuance
- Derived mood labels occasionally mis-classify edge cases — a very quiet sad song can score as "chill" rather than "melancholic" because the energy threshold is a blunt instrument
- The 30-songs-per-genre cap means some genres have limited diversity, so repeated queries in the same genre surface overlapping results

**What this taught me:**
Building the evaluation system made the system's failure modes visible in a structured way that informal testing never would. Seeing a 60% mood alignment rate on the "sad" benchmark forced a closer look at the mood derivation thresholds — something that would have gone unnoticed without measurable benchmarks.

---

## Reflection

**What this project says about me as an AI engineer**

I did not just add AI to a project — I thought carefully about where AI actually belongs in the system and where it does not. The rule-based scorer stayed because it is deterministic, auditable, and fast; Gemini was added only where human language needed to be understood and explained. That boundary — knowing when to use a model and when not to — is something I think a lot of engineers overlook. I also built measurement into the system before calling it done, because I have learned that confidence in an AI system without benchmarks is just optimism. The evaluation suite, the confidence scoring, and the before/after RAG comparison all exist because I wanted to know whether the system actually worked, not just whether it looked like it did. This project also taught me to treat AI tools as collaborators with limitations — the knowledge base context injection came from recognizing that Gemini alone was making poor genre choices for niche activity queries, and that a structured retrieval step could correct that without making the model more complex. That is the kind of architectural instinct I want to keep developing.

---

Building this project made two things clear that reading about AI systems did not.

First, **the retrieval step is where most of the quality lives.** Gemini's explanations are only as good as the candidates the scorer surfaces. When the scorer returns five songs of the wrong mood because the genre matched and the energy was close enough, Gemini will write a confident explanation for all five — and it will sound plausible. The AI layer amplifies whatever the retrieval layer gives it, good or bad.

Second, **evaluation changes how you build.** Without the benchmark system, the subjective sense that "results seem reasonable" is the only signal. Once there are numeric metrics, it becomes obvious which failure modes are consistent and which are edge cases. The difference between a 40% and an 80% mood alignment rate is not visible in a demo — it only shows up when you run the same query twenty times and measure the results.

For a future employer: the architecture pattern here — fast deterministic retrieval feeding a language model that handles explanation and ambiguity — is the same pattern used in production RAG systems at scale. The catalog is small and the model is free-tier, but the design decisions are the same ones that matter in real systems.

---

## Project Structure

```
├── app.py                  # Streamlit UI
├── data/
│   ├── preprocess.py       # Builds songs.csv from dataset.csv
│   ├── dataset.csv         # Raw Kaggle Spotify dataset (not committed)
│   └── songs.csv           # Processed catalog (3,420 songs)
├── src/
│   ├── ai_interface.py     # Gemini integration — interpret + explain
│   ├── evaluator.py        # Reliability benchmark system
│   ├── recommender.py      # Rule-based scorer + data models
│   └── main.py             # CLI entry point
├── tests/
│   └── test_recommender.py # Unit tests for Recommender class
├── assets/
│   └── System Diagram.png  # Architecture diagram
├── .env.example            # API key template
├── requirements.txt
└── README.md
```

---

## Requirements

```
google-genai
pandas
pytest
python-dotenv
streamlit
```
