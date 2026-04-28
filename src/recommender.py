import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scoring Strategy — Strategy Pattern
# ---------------------------------------------------------------------------
# Each ScoringWeights instance defines one ranking strategy.
# Swapping the strategy changes what the recommender prioritises without
# touching any other code. All presets sum to 4.0 so scores are comparable.

@dataclass
class ScoringWeights:
    """Holds the point values for each scoring rule under one strategy."""
    genre_pts:  float   # points for an exact genre match
    mood_pts:   float   # points for an exact mood match
    energy_max: float   # maximum points from energy proximity

    @property
    def max_score(self) -> float:
        """Highest possible score under this strategy."""
        return self.genre_pts + self.mood_pts + self.energy_max


# Preset strategies — all max out at 4.0
SCORING_MODES: Dict[str, ScoringWeights] = {
    # Genre drives everything; mood and energy are tiebreakers
    "genre_first":    ScoringWeights(genre_pts=2.5, mood_pts=0.5, energy_max=1.0),

    # Emotional state drives everything; genre is secondary
    "mood_first":     ScoringWeights(genre_pts=0.5, mood_pts=2.5, energy_max=1.0),

    # How the music physically feels matters most; labels are hints only
    "energy_focused": ScoringWeights(genre_pts=0.5, mood_pts=0.5, energy_max=3.0),

    # Equal categorical weight, energy doubled — current experimental default
    "balanced":       ScoringWeights(genre_pts=1.0, mood_pts=1.0, energy_max=2.0),
}

DEFAULT_MODE = "balanced"


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k Song objects ranked by score against the given UserProfile."""
        user_prefs = {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "target_energy": user.target_energy,
        }
        scored = []
        for song in self.songs:
            song_dict = {"genre": song.genre, "mood": song.mood, "energy": song.energy}
            score, _ = score_song(user_prefs, song_dict)
            scored.append((song, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        results = [s for s, _ in scored[:k]]
        logger.debug("Recommender returned %d songs for genre=%s mood=%s", len(results), user.favorite_genre, user.favorite_mood)
        return results

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a plain-language string describing why a Song matches a UserProfile."""
        reasons = []
        if song.genre == user.favorite_genre:
            reasons.append(f"matches your preferred genre ({song.genre})")
        if song.mood == user.favorite_mood:
            reasons.append(f"matches your preferred mood ({song.mood})")
        energy_diff = abs(song.energy - user.target_energy)
        if energy_diff <= 0.15:
            reasons.append(f"energy level ({song.energy:.2f}) is close to your target ({user.target_energy:.2f})")
        if not reasons:
            reasons.append("best available match given your preferences")
        return f'"{song.title}" by {song.artist}: ' + "; ".join(reasons) + "."

def score_song(
    user_prefs: Dict,
    song: Dict,
    weights: Optional[ScoringWeights] = None,
) -> Tuple[float, List[str]]:
    """Score one song against user preferences using the given ScoringWeights strategy."""
    if weights is None:
        weights = SCORING_MODES[DEFAULT_MODE]

    score = 0.0
    reasons = []

    # Rule 1 — Genre match
    if song["genre"] == user_prefs.get("genre", ""):
        score += weights.genre_pts
        reasons.append(f"genre match (+{weights.genre_pts})")

    # Rule 2 — Mood match
    if song["mood"] == user_prefs.get("mood", ""):
        score += weights.mood_pts
        reasons.append(f"mood match (+{weights.mood_pts})")

    # Rule 3 — Energy proximity: energy_max × (1.0 - |song - target|)
    # Perfect match → energy_max pts.  Worst mismatch → 0 pts.
    target_energy = user_prefs.get("target_energy", 0.5)
    energy_points = round(weights.energy_max * (1.0 - abs(song["energy"] - target_energy)), 2)
    score += energy_points
    reasons.append(f"energy {song['energy']} vs target {target_energy} (+{energy_points})")

    return round(score, 2), reasons


def load_songs(csv_path: str) -> List[Dict]:
    """Parse a CSV file of songs and return a list of dicts with typed numeric fields."""
    import csv
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id":           int(row["id"]),
                "title":        row["title"],
                "artist":       row["artist"],
                "genre":        row["genre"],
                "mood":         row["mood"],
                "energy":       float(row["energy"]),
                "tempo_bpm":    float(row["tempo_bpm"]),
                "valence":      float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })
    return songs

def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    mode: str = DEFAULT_MODE,
) -> List[Tuple[Dict, float, str]]:
    """Score every song using the named mode, sort descending, return top k as (song, score, explanation) tuples."""
    weights = SCORING_MODES.get(mode, SCORING_MODES[DEFAULT_MODE])

    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, weights)
        scored.append((song, score, "; ".join(reasons)))

    return sorted(scored, key=lambda item: item[1], reverse=True)[:k]
