"""
Unit tests for the music recommender.

Run from the project root:
    pytest
"""

import pytest
from src.recommender import Song, UserProfile, Recommender, score_song, recommend_songs, SCORING_MODES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_song(id=1, title="Test Song", artist="Test Artist",
              genre="pop", mood="happy", energy=0.8,
              tempo_bpm=120.0, valence=0.8, danceability=0.7, acousticness=0.2):
    return Song(id=id, title=title, artist=artist, genre=genre, mood=mood,
                energy=energy, tempo_bpm=tempo_bpm, valence=valence,
                danceability=danceability, acousticness=acousticness)


def make_song_dict(id=1, genre="pop", mood="happy", energy=0.8):
    return {"id": id, "title": f"Song {id}", "artist": "Artist",
            "genre": genre, "mood": mood, "energy": energy,
            "tempo_bpm": 120.0, "valence": 0.7, "danceability": 0.7, "acousticness": 0.2}


# ---------------------------------------------------------------------------
# score_song — unit tests
# ---------------------------------------------------------------------------

def test_score_song_perfect_match_returns_max_score():
    """Exact genre + mood match with perfect energy should return the maximum score."""
    user = {"genre": "pop", "mood": "happy", "target_energy": 0.8}
    song = {"genre": "pop", "mood": "happy", "energy": 0.8}
    score, _ = score_song(user, song)
    assert score == SCORING_MODES["balanced"].max_score


def test_score_song_no_categorical_match_only_energy():
    """When genre and mood both miss, only energy points contribute."""
    user = {"genre": "pop", "mood": "happy", "target_energy": 0.5}
    song = {"genre": "rock", "mood": "angry", "energy": 0.5}
    score, reasons = score_song(user, song)
    # balanced energy_max=2.0, perfect energy match → score=2.0
    assert score == 2.0
    assert not any("genre match" in r for r in reasons)
    assert not any("mood match" in r for r in reasons)


def test_score_song_maximum_energy_mismatch_gives_zero_energy_points():
    """Energy 1.0 vs target 0.0 should contribute 0 energy points."""
    user = {"genre": "rock", "mood": "angry", "target_energy": 0.0}
    song = {"genre": "rock", "mood": "angry", "energy": 1.0}
    score, _ = score_song(user, song)
    # genre(1.0) + mood(1.0) + energy(0.0) = 2.0
    assert score == 2.0


def test_score_song_genre_first_mode_weights_genre_heavily():
    """genre_first mode should award 2.5 pts for a genre match."""
    user = {"genre": "jazz", "mood": "chill", "target_energy": 0.4}
    song = {"genre": "jazz", "mood": "intense", "energy": 0.4}
    score, _ = score_song(user, song, weights=SCORING_MODES["genre_first"])
    # genre(2.5) + mood(0) + energy(1.0 * 1.0) = 3.5
    assert score == 3.5


def test_score_song_mood_first_mode_weights_mood_heavily():
    """mood_first mode should award 2.5 pts for a mood match."""
    user = {"genre": "rock", "mood": "melancholic", "target_energy": 0.4}
    song = {"genre": "jazz", "mood": "melancholic", "energy": 0.4}
    score, _ = score_song(user, song, weights=SCORING_MODES["mood_first"])
    # genre(0) + mood(2.5) + energy(1.0 * 1.0) = 3.5
    assert score == 3.5


def test_score_song_reasons_list_genre_and_mood_when_matched():
    """Reason strings should mention genre and mood when they both match."""
    user = {"genre": "pop", "mood": "happy", "target_energy": 0.5}
    song = {"genre": "pop", "mood": "happy", "energy": 0.5}
    _, reasons = score_song(user, song)
    assert any("genre match" in r for r in reasons)
    assert any("mood match" in r for r in reasons)


def test_score_song_score_is_non_negative():
    """Score should never be negative regardless of inputs."""
    user = {"genre": "pop", "mood": "happy", "target_energy": 0.0}
    song = {"genre": "rock", "mood": "angry", "energy": 1.0}
    score, _ = score_song(user, song)
    assert score >= 0.0


# ---------------------------------------------------------------------------
# recommend_songs — unit tests
# ---------------------------------------------------------------------------

def test_recommend_songs_returns_k_results():
    songs = [make_song_dict(i, genre="pop", mood="happy", energy=0.8) for i in range(10)]
    user = {"genre": "pop", "mood": "happy", "target_energy": 0.8}
    results = recommend_songs(user, songs, k=3)
    assert len(results) == 3


def test_recommend_songs_sorted_by_score_descending():
    """Top result should have the highest score."""
    songs = [
        make_song_dict(1, genre="pop",  mood="happy",   energy=0.8),
        make_song_dict(2, genre="rock", mood="angry",   energy=0.1),
        make_song_dict(3, genre="jazz", mood="focused", energy=0.5),
    ]
    user = {"genre": "pop", "mood": "happy", "target_energy": 0.8}
    results = recommend_songs(user, songs, k=3)
    scores = [score for _, score, _ in results]
    assert scores == sorted(scores, reverse=True)


def test_recommend_songs_k_larger_than_catalog_returns_all():
    """Asking for more songs than exist should return the full catalog."""
    songs = [make_song_dict(i) for i in range(3)]
    user = {"genre": "pop", "mood": "happy", "target_energy": 0.8}
    results = recommend_songs(user, songs, k=100)
    assert len(results) == 3


def test_recommend_songs_top_result_is_best_match():
    """A perfect-match song should rank first even in a mixed catalog."""
    songs = [
        make_song_dict(1, genre="blues", mood="melancholic", energy=0.2),
        make_song_dict(2, genre="pop",   mood="happy",       energy=0.8),
        make_song_dict(3, genre="metal", mood="angry",       energy=0.95),
    ]
    user = {"genre": "pop", "mood": "happy", "target_energy": 0.8}
    results = recommend_songs(user, songs, k=3)
    top_song = results[0][0]
    assert top_song["genre"] == "pop"
    assert top_song["mood"] == "happy"


# ---------------------------------------------------------------------------
# Recommender class — unit tests
# ---------------------------------------------------------------------------

def make_small_recommender():
    return Recommender([
        make_song(id=1, genre="pop",  mood="happy",   energy=0.8),
        make_song(id=2, genre="jazz", mood="focused", energy=0.4),
    ])


def test_recommender_recommend_returns_correct_count():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)
    assert len(results) == 2


def test_recommender_recommend_best_match_ranks_first():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_recommender_explain_returns_non_empty_string():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    rec = make_small_recommender()
    explanation = rec.explain_recommendation(user, rec.songs[0])
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


def test_recommender_explain_mentions_song_title():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    rec = make_small_recommender()
    song = rec.songs[0]
    explanation = rec.explain_recommendation(user, song)
    assert song.title in explanation


def test_recommender_k_larger_than_catalog_returns_all():
    rec = make_small_recommender()
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    results = rec.recommend(user, k=100)
    assert len(results) == len(rec.songs)
