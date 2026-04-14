"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    from src.recommender import load_songs, recommend_songs
except ModuleNotFoundError:
    from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # -----------------------------------------------------------------------
    # Taste profiles — swap ACTIVE_PROFILE to test different listeners
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # Taste profiles — swap ACTIVE_PROFILE to test different listeners
    # -----------------------------------------------------------------------

    # Profile A: Pop/happy listener — upbeat, high energy, radio-friendly
    profile_pop = {
        "genre":         "pop",
        "mood":          "happy",
        "target_energy": 0.80,
    }

    # Profile B: Chill lofi listener — studying, low stimulation, acoustic texture
    profile_lofi = {
        "genre":         "lofi",
        "mood":          "chill",
        "target_energy": 0.38,
    }

    # Profile C: Intense rock listener — high activation, raw energy, electric
    profile_rock = {
        "genre":         "rock",
        "mood":          "intense",
        "target_energy": 0.90,
    }

    # Profile D: Focused work listener — productive but not distracting
    profile_focus = {
        "genre":         "lofi",
        "mood":          "focused",
        "target_energy": 0.42,
    }

    # Set which profile to run
    ACTIVE_PROFILE = profile_pop
    user_prefs = ACTIVE_PROFILE

    recommendations = recommend_songs(user_prefs, songs, k=5)

    # -----------------------------------------------------------------------
    # Output formatting
    # -----------------------------------------------------------------------
    width = 60
    genre  = user_prefs.get("genre", "?")
    mood   = user_prefs.get("mood", "?")
    energy = user_prefs.get("target_energy", "?")

    print()
    print("=" * width)
    print(f"  Recommendations for: genre={genre} | mood={mood} | energy={energy}")
    print("=" * width)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n  #{rank}  {song['title']} — {song['artist']}")
        print(f"       Score  : {score} / 4.0")
        print(f"       Why    : {explanation}")

    print()
    print("=" * width)


if __name__ == "__main__":
    main()
