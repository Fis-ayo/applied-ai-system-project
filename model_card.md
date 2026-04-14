# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatch 1.0**

A content-based music recommender that matches songs to a listener's stated genre, mood,
and energy preferences using a simple point-based scoring system.

---

## 2. Intended Use

**What it does:**
VibeMatch suggests songs from a small catalog based on three things you tell it:
what genre you like, what mood you're in, and how high-energy you want the music to be.
It returns the top 5 matches along with a plain-language explanation of why each song was picked.

**Who it is for:**
This system is for classroom exploration only. It is a learning tool built to demonstrate
how real recommenders work, not a product meant for actual listeners.

**What it assumes:**
It assumes the user knows their preferred genre and mood and can express them as exact labels
(e.g., "lofi" not "chill indie study beats"). It also assumes all songs in the catalog are
correctly and consistently tagged.

**What it should NOT be used for:**
- Making real music recommendations for real users
- Any situation where fairness across all music genres matters (it favors lofi and chill)
- Replacing a system that learns from actual listening behavior over time
- Any catalog larger than a few hundred songs without significant redesign

---

## 3. How the Model Works

Imagine you hand a librarian three sticky notes: your favorite genre, your current mood, and a
number from 0 to 10 representing how energetic you want the music to feel. The librarian walks
through every shelf in the library and gives each album a score based on how well it matches
your notes. Albums that match all three notes score the highest. Then the librarian hands you
the top five picks in order.

That is exactly what this system does, using three rules:

**Rule 1 — Genre:** If a song's genre matches yours exactly, it earns 1 point. If not, it earns
nothing. There is no in-between — "rock" and "metal" are treated as completely different.

**Rule 2 — Mood:** If a song's mood label matches yours exactly, it earns 1 point. Same
all-or-nothing rule. "Chill" and "relaxed" score the same as "chill" and "metal" — zero points.

**Rule 3 — Energy:** Every song gets a score between 0 and 2 based on how close its energy is
to your target. A perfect match earns 2.0 points. A complete mismatch earns 0. Songs that are
almost right earn something in between.

The three scores are added together. The maximum any song can earn is 4.0 points.
The top 5 scorers are returned as recommendations.

**One change made during experiments:**
The original system gave genre 2.0 points and energy only 0–1.0 points. After testing, genre
was reduced to 1.0 and energy was doubled to 0–2.0. This made the results feel more musically
accurate — especially for rock listeners, where a high-energy metal song now outranks a
low-energy pop song even without a genre match.

---

## 4. Data

The catalog contains **18 songs** stored in `data/songs.csv`.

**Where it came from:** The original 10 songs were provided as a starter dataset. Eight more
were added manually to improve genre and mood diversity.

**What genres are included:**
pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip-hop, classical, r&b, metal, folk,
electronic, blues, country — 15 genres across 18 songs.

**What moods are included:**
happy, chill, intense, relaxed, focused, moody, energetic, melancholic, romantic, angry,
nostalgic, euphoric, soulful, uplifting — 14 mood labels across 18 songs.

**What each song tracks:**
Genre, mood, energy (0–1), tempo in BPM, valence (brightness), danceability, and acousticness.
Only genre, mood, and energy are currently used in scoring. The other features are stored but idle.

**Known gaps in the data:**
- Lofi is the only genre with more than 2 songs (it has 3), giving lofi listeners an unfair advantage
- Most genres and moods appear only once, meaning most users will get at most one strong genre match
- The energy values cluster at the low end (under 0.42) and high end (above 0.75), leaving a gap in the middle where few songs live
- The catalog reflects a fairly narrow slice of global music — no Latin, African, or South Asian genres are represented

---

## 5. Strengths

**Lofi and chill listeners get genuinely useful results.** Because the dataset has three lofi songs
and three chill-mood songs, users with those preferences see a real top-3 with strong matches,
not just a score winner followed by random filler.

**The results are fully explainable.** Every recommendation comes with a reason — "genre match,
mood match, energy 0.35 near target 0.38." A user can read it and immediately understand why
a song was picked. Most real recommenders offer no explanation at all.

**Extreme preferences are handled correctly.** A user who wants maximum energy gets high-energy
songs at the top. A user who wants minimal energy gets quiet songs. The direction of the
recommendations is always right, even if the specific songs vary.

**The system is easy to audit and change.** Because the scoring logic is three simple rules in
one function, adjusting a weight or adding a new feature takes minutes. This transparency is a
genuine advantage for learning and experimentation.

---

## 6. Limitations and Bias

The most significant bias in this system is **catalog imbalance across user types**: lofi and
chill listeners receive systematically better service than every other listener because the
dataset contains three lofi songs and three chill-mood songs, while every other genre and most
other moods appear exactly once. A lofi/chill user can earn genre and mood points on three
different songs and get a genuinely strong top-3 result, whereas a blues or country listener
matches genre on a single song and then relies entirely on energy proximity to fill positions
2–5 — producing recommendations that may share an energy level but nothing else musically
meaningful.

A second structural weakness is the **mid-energy dead zone**: energy values in the catalog
cluster at two extremes (six songs below 0.42, eight songs above 0.75), with only three songs
in the moderate 0.42–0.72 range. A user who wants background music at a comfortable medium
energy has almost no good matches, and doubling the energy weight in the experimental version
makes this gap more punishing rather than less.

Finally, mood matching uses **binary exact comparison** with no partial credit for semantically
adjacent labels — the system treats "relaxed" and "chill" as completely unrelated, so a relaxed
user gets zero mood points on every chill-tagged song in the catalog even though a human listener
would consider them nearly identical.

---

## 7. Evaluation

Seven user profiles were tested in total — three standard listeners and four adversarial edge
cases designed to stress-test the scoring logic.

**Standard profiles tested:**
- *High-Energy Pop* (genre=pop, mood=happy, energy=0.80) — designed to have clear, obvious matches in the catalog
- *Chill Lofi* (genre=lofi, mood=chill, energy=0.38) — the most well-served profile given the dataset's lofi bias
- *Deep Intense Rock* (genre=rock, mood=intense, energy=0.90) — only one rock song exists, so results drop steeply after rank 1

**Edge case profiles tested:**
- *Conflicting Mood + Energy* (lofi/chill but energy=0.92) — testing whether high energy could override a calm mood match
- *Genre Not in Catalog* (jazz-fusion) — testing what happens when genre matches nothing
- *Opposing Genre + Mood* (metal/relaxed) — no song has both; forcing the scorer to choose one or the other
- *Dead-Centre Energy* (energy=0.50) — neutralising the energy feature to see if genre and mood alone produce sensible results

**What was expected:** The pop/happy profile should return upbeat pop songs. The lofi profile
should return quiet, acoustic-textured tracks. The rock profile should return loud, fast,
electric songs.

**What was surprising:** The biggest unexpected result was that *Gym Hero* — a workout pop
track tagged as "intense" — consistently ranked #2 for a *happy pop* listener. It kept appearing
not because it felt right, but because its genre tag said "pop," and genre is worth enough points
to float it above songs that matched the mood perfectly but belonged to a different genre. A real
happy-pop listener would skip Gym Hero immediately, but the algorithm had no way to know that
"pop + intense" is a worse mood fit than "indie pop + happy." This revealed that the genre label
was doing too much work on its own.

A second surprise came from the conflicting profile (lofi/chill but energy=0.92): even with a
near-maximum energy target, lofi songs still ranked first. The genre and mood points were large
enough to absorb the energy penalty — showing the system is more resistant to conflicting signals
than expected, which is both a strength (stability) and a weakness (it ignores the contradiction
entirely).

---

## 8. Ideas for Improvement

**1. Add partial credit for musically adjacent genres.**
Right now "rock" and "metal" score the same as "rock" and "classical" — both get zero genre
points. A simple lookup table pairing related genres (rock↔metal, lofi↔ambient, jazz↔blues)
and awarding half a point for a near-match would fix the Iron Tide / Gym Hero problem immediately.

**2. Expand the catalog to at least 5 songs per genre.**
The single biggest improvement would not be to the algorithm at all — it would be to the data.
Most genres have one song. Until there are enough songs per genre to fill a top-5 list with
genuine matches, the recommender will always produce low-quality results for most user types.

**3. Include valence and tempo in the scoring formula.**
Valence (how bright or dark a song feels) and tempo (how fast it moves) are already stored for
every song but ignored during scoring. Adding them with small weights would let the system
distinguish between an intense pop song (high valence) and an intense rock song (low valence),
which is exactly the distinction that makes Gym Hero feel wrong for a happy-pop listener.

---

## 9. Personal Reflection

### Biggest Learning Moment

The biggest learning moment was not about the code — it was about the data. I spent time
designing a careful scoring formula with specific weights, then ran experiments changing those
weights, and every time the fundamental problem stayed the same: most genres in the catalog had
exactly one song. No weight adjustment could make a blues recommendation feel satisfying when
the only blues song in the entire catalog was already ranked first. The algorithm was fine.
The data was the ceiling.

That realization changed how I think about AI systems in general. When a recommendation feels
wrong, the instinct is to blame the algorithm — tweak a weight, change a rule. But often the
real issue is that the data does not represent the world evenly. Fixing the data would have
done more for this recommender than any amount of scoring logic redesign.

---

### How AI Tools Helped — and Where I Had to Verify

AI tools (Claude, Copilot) were genuinely useful at two specific points. First, when designing
the algorithm recipe — having a structured conversation about which features should carry more
weight, and why, produced clearer thinking than staring at a blank file would have. The prompt
"should genre outweigh mood?" forced an answer with a reason attached, which became part of the
actual design documentation.

Second, AI-suggested adversarial profiles were more creative than the ones I would have come up
with alone. The "opposing genre + mood" profile (metal + relaxed) and the "dead-centre energy"
profile revealed real weaknesses in the scoring logic that standard testing would have missed.

Where I had to double-check: any time a formula was suggested, I verified the math manually
before trusting it. The energy-doubling experiment was a good example — the AI confirmed the
new max score was still 4.0, but I re-calculated it by hand (1.0 + 1.0 + 2.0) before updating
the code. AI tools can produce plausible-sounding math that is subtly wrong, especially when
the formula involves multiple interacting parts. Treating suggestions as a first draft to verify,
not a final answer to accept, was the right approach.

---

### What Surprised Me About Simple Algorithms "Feeling" Like Recommendations

The most surprising thing was how much the *explanation* changed the feel of the result more
than the result itself. When a song appeared at the top of the list with no context, it could
feel arbitrary. When the same song appeared with "genre match (+1.0); mood match (+1.0); energy
0.35 near target 0.38 (+1.94)," it suddenly felt *reasoned* — even though the underlying math
was just three additions.

Real recommenders never show you this. Spotify does not say "you got this song because 47,000
people with your listening history also listened to it on Tuesday afternoons." VibeMatch does
say that, in a simpler form, and it turns out transparency alone makes a system feel more
trustworthy — even when the algorithm behind it is less sophisticated.

The other surprise was how quickly results started feeling like *character*. The lofi profile
always returned calm, textured songs. The rock profile always opened with Storm Runner. Running
different profiles felt like watching different people browse different sections of a record
store. That personality emerged entirely from three rules and a sort — no machine learning,
no neural network, no training data. Just arithmetic on labeled spreadsheet rows.

---

### What I Would Try Next

**Give related genres partial credit.** A rock listener getting zero genre points for a metal
song feels like the most fixable bug in the current system. A small lookup table mapping sonic
neighbors (rock ↔ metal, lofi ↔ ambient, jazz ↔ blues) and awarding 0.5 points for a near-match
would immediately produce more musically intuitive results, especially for genres with only one
song in the catalog.

**Add a second user preference: tempo.** Energy and tempo are related but not the same —
a 60 BPM ambient track and a 60 BPM slow jazz ballad have similar energy levels but feel
completely different. Tempo is already stored for every song. Adding it as a fourth scoring
rule with a small weight would let the system separate "slow and heavy" from "slow and delicate,"
which is a distinction real listeners care about.

**Try building the collaborative side.** This entire project was content-based — it never
looked at what other people listened to. The next interesting step would be simulating a small
set of users with known listening histories and seeing if "people who liked Library Rain also
liked Spacewalk Thoughts" produces different (and better) results than pure feature matching.
Even with 18 songs and 5 fake users, the contrast between the two approaches would be instructive.
