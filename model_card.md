# Model Card: AI Music Recommender

## 1. Model Name

**VibeMatch 2.0**

A natural language music recommendation system powered by Gemini 2.5 Flash and Retrieval-Augmented Generation (RAG). Users describe what they want in plain English — an activity, a mood, a vibe — and the system finds matching songs from a catalog of 3,420 real tracks across 114 genres, then explains the results in conversational language.

---

## 2. Intended Use

**What it does:**
VibeMatch 2.0 takes a natural language query, interprets it into structured music preferences using Gemini, retrieves the best matching songs from a large catalog using a rule-based scorer, and returns the top results with a plain-language explanation of why each song fits.

**Who it is for:**
Music listeners who want recommendations without filling out structured forms. Also a demonstration of how deterministic retrieval and AI language models can be combined cleanly in a production-style RAG pipeline.

**What it should NOT be used for:**
- Making high-stakes decisions about user taste or identity
- Profiling users emotionally based on their queries
- Any context where genre or cultural representation must be audited for fairness at scale

---

## 3. How the System Works

The system has two AI calls and one deterministic retrieval step per request:

**Step 1 — Context retrieval (RAG, data source 1):**
Before Gemini sees the user's query, the knowledge base (`data/music_knowledge.json`) is searched for matching entries using keyword overlap. If a match is found — e.g., the query mentions "gym" or "studying" — the relevant domain context (recommended genres, expected moods, energy range) is injected into Gemini's prompt.

**Step 2 — Query interpretation (Gemini 2.5 Flash):**
Gemini reads the user's query plus any injected context and returns a structured JSON object:
`{ genre, mood, target_energy, reasoning, confidence }`

**Step 3 — Song retrieval (RAG, data source 2):**
The rule-based scorer runs against all 3,420 songs in `data/songs.csv`. Each song is scored on three rules:

| Rule | Points (balanced mode) | Logic |
|---|---|---|
| Genre match | +1.0 | Exact string match |
| Mood match | +1.0 | Exact string match |
| Energy proximity | 0–2.0 | `2.0 × (1 − |song.energy − target|)` |

Maximum score: **4.0**. Songs are sorted by score and the top 5–10 are returned.

**Step 4 — Explanation (Gemini 2.5 Flash):**
Gemini reads the top candidates and writes a 2–3 sentence response explaining why they fit the request.

---

## 4. Data

**Song catalog:** 3,420 songs sampled from the [Kaggle Spotify Tracks Dataset](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset). 30 songs per genre across 114 genres.

**Mood labels:** Derived algorithmically from two Spotify audio features using hard thresholds:

| Condition | Assigned Mood |
|---|---|
| valence > 0.7 AND energy > 0.7 | euphoric |
| valence > 0.6 AND energy > 0.5 | happy |
| valence > 0.6 AND energy ≤ 0.5 | romantic |
| valence ≤ 0.3 AND energy > 0.7 | angry |
| valence ≤ 0.4 AND energy > 0.6 | intense |
| valence ≤ 0.4 AND energy ≤ 0.4 | melancholic |
| energy ≤ 0.35 | chill |
| energy > 0.6 | energetic |
| else | focused |

**Knowledge base:** 10 hand-authored entries in `data/music_knowledge.json` mapping common activities and feelings (study, gym, sleep, party, sad, romantic, road trip, morning, angry, atmospheric) to their expected genres, moods, and energy ranges. This is the second data source in the RAG pipeline.

**Known gaps:**
- Mood labels are approximations — the boundary between "focused" and "chill" is a hard numeric threshold, not human judgment
- 30 songs per genre means niche genres have limited diversity
- The catalog skews toward Western, English-language music; non-Western genres are underrepresented

---

## 5. Strengths

- **Natural language input** removes the friction of structured preference forms — users describe what they want the same way they would tell a friend
- **Fully explainable results** — every recommendation includes a numeric score and reason string showing exactly which rules fired
- **Measurable reliability** — the benchmark system runs 6 fixed test cases with mood alignment, energy alignment, genre validity, and score thresholds
- **RAG enhancement is demonstrable** — running the comparison mode shows a quantified before/after improvement in mood alignment from adding the knowledge base context

---

## 6. Limitations and Bias

**Mood labels are approximations, not ground truth.**
The `mood` column was derived algorithmically from valence and energy. The boundaries are hard numeric thresholds. A song with valence 0.41 is labelled "focused"; a song with valence 0.39 is labelled "melancholic." There is nothing musically meaningful about that line — it means a user asking for sad music might receive songs that do not feel sad to a human listener.

**Exact genre and mood matching penalises adjacent styles.**
The scorer awards genre points only on an exact string match. A user who asks for "rock" receives zero genre points for a "metal" or "punk" result, even though those genres are acoustically close neighbours. "Chill" and "focused" are treated as completely different moods despite significant overlap.

**The catalog sample is uneven in practice.**
While every genre gets exactly 30 songs, genres like pop and hip-hop have thousands of well-known tracks to sample from, while niche genres may return 30 mostly obscure results.

**Gemini's interpretations reflect its training data.**
Queries that reference non-Western listening contexts or culturally specific moods may be mapped to the closest Western equivalent rather than something genuinely appropriate.

---

## 7. Potential for Misuse

**Emotional profiling.** A user who consistently asks for sad, angry, or anxious music is implicitly revealing their emotional state over time. If query history were stored and linked to an identity, that data could be used for targeting or manipulation without consent. This system stores nothing beyond the session.

**Reinforcing echo chambers.** Recommenders that always return the closest match reward familiarity and suppress discovery. A user who asks for hip-hop will always get hip-hop.

**Mitigations built into this system:**
- Session-only processing — no query history stored
- No user accounts or cross-session profiling
- Open scoring logic — every recommendation includes a numeric score and reason string, leaving no room for opaque manipulation

---

## 8. Evaluation

The reliability system in `src/evaluator.py` runs 6 benchmark queries through the full pipeline and measures four metrics per case:

| Metric | What it checks | Pass threshold |
|---|---|---|
| Mood alignment rate | % of top-5 results with an expected mood | ≥ 40% |
| Energy alignment rate | % of top-5 results within expected energy band | — |
| Genre validity | Gemini mapped to a genre that exists in the catalog | Must be true |
| Top score | Highest-ranked song scored above minimum | ≥ 0.5 |

A case passes if mood alignment ≥ 40%, genre is valid, and top score ≥ 0.5.

**RAG comparison:** The `run_comparison` function runs each benchmark twice — with and without knowledge base context injection — and reports mood alignment delta per case. This demonstrates the measurable impact of the second data source.

**What worked well:**
- Gemini consistently maps common activities (studying, gym, sleep) to sensible genre and mood combinations
- The scorer reliably surfaces genre and mood matches when they exist in the catalog
- The explainer produces natural, specific responses that mention real song details

**What did not work as expected:**
- Niche or cross-genre requests sometimes map to a broad fallback genre, missing the nuance
- Derived mood labels occasionally mis-classify edge cases — a quiet sad song can score as "chill" rather than "melancholic" because the energy threshold is a blunt instrument

---

## 9. What Surprised Me While Testing

Two things stood out during reliability testing.

**The catalog had a genre called "study."** When running the benchmark for a study query, Gemini sometimes mapped it directly to the genre `study` — a real Spotify micro-genre in the dataset — rather than `ambient` or `lofi`. The results were actually reasonable, but it revealed a gap between how users think about genres and how the catalog labels them. A user would never type "study" intending a Spotify micro-genre; they mean a feeling.

**Lower confidence did not always mean worse results.** I expected Gemini's confidence scores to track closely with result quality. That was not always true. Some of the most musically coherent recommendations came from queries where Gemini rated its own confidence at 0.6 or 0.7, because the ambiguity in the query forced a more creative interpretation. The clearest queries returned the most predictable, genre-locked results.

---

## 10. Ideas for Future Improvement

- **Partial credit for adjacent genres** — a lookup table pairing sonic neighbours (rock ↔ metal, lofi ↔ ambient) and awarding 0.5 points for a near-match would fix the hard genre boundary problem immediately
- **Semantic search using embeddings** — replacing exact-match scoring with vector similarity would let the system find songs that feel right even without a genre label match
- **Include valence and tempo in scoring** — both features are stored for every song but currently ignored; adding them with small weights would let the system distinguish between an intense pop song (high valence) and an intense rock song (low valence)
- **Session-level preference learning** — tracking what a user accepts or skips within a session and adjusting weights accordingly, without storing data across sessions

---

## 11. Personal Reflection

**Collaboration with AI during this project**

This project was built with significant AI assistance throughout, primarily using Claude (Anthropic) as a coding collaborator.

*A helpful suggestion:* Early in the project I was not sure whether to send the full song catalog to Gemini and let it rank everything, or to keep the rule-based scorer and only use Gemini for interpretation and explanation. Claude recommended the hybrid approach — use the deterministic scorer as a fast pre-filter to narrow 3,420 songs down to the top 10, then pass only those to Gemini for explanation. This was the right call. It kept API costs low, response times fast, and preserved full explainability in the scoring step.

*A flawed suggestion:* When switching the project to the Google Gemini API, Claude recommended installing the `google-generativeai` Python package. Only when the import ran did a deprecation warning appear: *"All support for the `google.generativeai` package has ended. Please switch to the `google.genai` package."* The package Claude recommended had already been retired. The entire `ai_interface.py` had to be rewritten against the new SDK. It was a good reminder that AI suggestions about third-party libraries can go stale — always check official documentation before committing to a dependency.

**What this project taught me about AI and problem-solving**

I did not just add AI to a project — I thought carefully about where AI actually belongs in the system and where it does not. The rule-based scorer stayed because it is deterministic, auditable, and fast; Gemini was added only where human language needed to be understood and explained. That boundary — knowing when to use a model and when not to — is something I think a lot of engineers overlook.

Building the evaluation system made the system's failure modes visible in a structured way that informal testing never would. Seeing a low mood alignment rate on the "sad" benchmark forced a closer look at the mood derivation thresholds — something that would have gone unnoticed without measurable benchmarks. The difference between a system that works and a system that seems like it works only shows up when you run the same query repeatedly and measure the results.

The retrieval step is also where most of the quality lives. Gemini's explanations are only as good as the candidates the scorer surfaces. When the scorer returns five songs of the wrong mood, Gemini will write a confident explanation for all five — and it will sound plausible. The AI layer amplifies whatever the retrieval layer gives it, good or bad.
