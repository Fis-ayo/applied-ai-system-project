# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

This simulation builds a content-based music recommender that scores songs against a user's taste profile using weighted feature matching. It loads a small catalog from `data/songs.csv`, computes a similarity score for each song, and returns the top-ranked matches with a plain-language explanation of why each song was recommended.

---

## How The System Works

Real-world recommenders like Spotify and YouTube Music typically combine two strategies: **collaborative filtering**, which surfaces songs that users with similar taste have enjoyed, and **content-based filtering**, which matches songs based on their intrinsic audio and metadata attributes. This simulation focuses entirely on content-based filtering — it never looks at what other users listened to. Instead, it compares each song's measurable features directly against a user's stated preferences and computes a weighted similarity score. The priority is transparency and interpretability: every recommendation comes with a plain-language reason so it is clear exactly why a song was suggested, which is something real production systems rarely surface.

---

### Song Features

Each `Song` object stores the following attributes drawn from `data/songs.csv`:

| Feature | Type | Description |
|---|---|---|
| `id` | int | Unique identifier |
| `title` | str | Song title |
| `artist` | str | Artist name |
| `genre` | str | Style category — e.g. `pop`, `lofi`, `rock`, `ambient`, `jazz`, `synthwave`, `indie pop` |
| `mood` | str | Emotional quality — e.g. `happy`, `chill`, `intense`, `relaxed`, `focused`, `moody` |
| `energy` | float (0–1) | Activation level from very calm to very intense |
| `tempo_bpm` | float | Beats per minute — physical pace of the track |
| `valence` | float (0–1) | Musical positivity — low is dark/somber, high is bright/upbeat |
| `danceability` | float (0–1) | How strongly the track drives rhythmic movement |
| `acousticness` | float (0–1) | Degree of organic/acoustic vs. electronic/produced texture |

---

### UserProfile Features

Each `UserProfile` stores the user's taste preferences that the scorer compares against:

| Field | Type | Description |
|---|---|---|
| `favorite_genre` | str | The genre the user most wants to hear — matched exactly against `Song.genre` |
| `favorite_mood` | str | The emotional feel the user is after — matched exactly against `Song.mood` |
| `target_energy` | float (0–1) | The user's ideal activation level — scored by proximity to `Song.energy` |
| `likes_acoustic` | bool | Whether the user prefers acoustic texture — influences `Song.acousticness` weight |

---

### How a Score Is Computed

Each song receives a total score between 0.0 and 1.0 using weighted feature matching:

```
total_score = (genre_match  × 0.35)
            + (mood_match   × 0.30)
            + (energy_score × 0.20)
            + (valence_score × 0.10)
            + (acousticness_score × 0.05)
```

- Categorical features (`genre`, `mood`) score **1.0** on an exact match, **0.0** otherwise.
- Numerical features (`energy`, `valence`, `acousticness`) use a proximity formula: `1.0 - |song_value - user_target|`, which rewards closeness rather than absolute magnitude.

---

### How Songs Are Ranked

After every song in the catalog is scored, the recommender sorts the full list by score in descending order and returns the top `k` results. Each result is returned as a `(song, score, explanation)` tuple so the caller can display both the recommendation and the reasoning behind it.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this


---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}  

```markdown
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> VibeFinder 1.0

---

## 2. Intended Use

- What is this system trying to do
- Who is it for

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

## 3. How It Works (Short Explanation)

Describe your scoring logic in plain language.

- What features of each song does it consider
- What information about the user does it use
- How does it turn those into a number

Try to avoid code in this section, treat it like an explanation to a non programmer.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`
- Did you add or remove any songs
- What kinds of genres or moods are represented
- Whose taste does this data mostly reflect

---

## 5. Strengths

Where does your recommender work well

You can think about:
- Situations where the top results "felt right"
- Particular user profiles it served well
- Simplicity or transparency benefits

---

## 6. Limitations and Bias

Where does your recommender struggle

Some prompts:
- Does it ignore some genres or moods
- Does it treat all users as if they have the same taste shape
- Is it biased toward high energy or one genre by default
- How could this be unfair if used in a real product

---

## 7. Evaluation

How did you check your system

Examples:
- You tried multiple user profiles and wrote down whether the results matched your expectations
- You compared your simulation to what a real app like Spotify or YouTube tends to recommend
- You wrote tests for your scoring logic

You do not need a numeric metric, but if you used one, explain what it measures.

---

## 8. Future Work

If you had more time, how would you improve this recommender

Examples:

- Add support for multiple users and "group vibe" recommendations
- Balance diversity of songs instead of always picking the closest match
- Use more features, like tempo ranges or lyric themes

---

## 9. Personal Reflection

A few sentences about what you learned:

- What surprised you about how your system behaved
- How did building this change how you think about real music recommenders
- Where do you think human judgment still matters, even if the model seems "smart"

