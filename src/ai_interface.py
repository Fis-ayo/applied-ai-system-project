"""
ai_interface.py
Gemini-powered RAG layer for the music recommender.

Flow:
  1. knowledge_base.retrieve_context — retrieves relevant domain knowledge (second data source)
  2. interpret_query                 — Gemini maps natural language + context to structured prefs
  3. recommend_songs                 — rule-based scorer retrieves top candidates from songs.csv
  4. explain_recommendations         — Gemini writes a natural language response
"""

import json
import logging
import os

from google import genai
from google.genai import types

try:
    from src.recommender import recommend_songs
    from src.knowledge_base import retrieve_context
except ModuleNotFoundError:
    from recommender import recommend_songs
    from knowledge_base import retrieve_context

logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = "gemini-2.5-flash"


def _build_interpret_system(songs: list[dict], context: str = "") -> str:
    genres = ", ".join(sorted({s["genre"] for s in songs}))
    system = f"""You are a music preference interpreter. Convert a natural language request into structured JSON.

Return ONLY valid JSON with exactly these fields:
{{
  "genre": "<one genre from the available list>",
  "mood": "<one of: euphoric, happy, romantic, angry, intense, melancholic, chill, energetic, focused>",
  "target_energy": <float between 0.0 and 1.0>,
  "reasoning": "<one sentence explaining your choices>",
  "confidence": <float between 0.0 and 1.0 — how confident you are in this interpretation>
}}

Available genres: {genres}

Guidelines:
- target_energy: 0.0 = very calm/quiet, 0.5 = moderate, 1.0 = extremely loud/intense
- Pick the single closest genre from the available list
- If the request mentions an activity (studying, gym, sleep), infer the appropriate mood and energy"""

    if context:
        system += f"\n\nRelevant domain knowledge for this request:\n{context}"

    return system


def _strip_fences(text: str) -> str:
    """Remove markdown code fences that the model sometimes wraps JSON in."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def interpret_query(query: str, songs: list[dict], use_context: bool = True) -> dict:
    """
    Ask Gemini to extract structured music preferences from a natural language query.
    When use_context=True, relevant domain knowledge is retrieved and injected into the prompt.
    """
    context = retrieve_context(query) if use_context else ""
    if context:
        logger.info("Injecting knowledge base context into prompt")
    else:
        logger.info("No knowledge base context matched — interpreting from query alone")

    logger.info("Interpreting query: %r (context=%s)", query, bool(context))
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=_build_interpret_system(songs, context),
                max_output_tokens=300,
            ),
        )
        text = _strip_fences(response.text)
        prefs = json.loads(text)
        prefs["context_used"] = bool(context)
        logger.info("Interpreted preferences: %s", prefs)
        return prefs
    except json.JSONDecodeError as e:
        logger.warning("Gemini returned invalid JSON (%s) — using fallback prefs", e)
        return {"genre": "pop", "mood": "happy", "target_energy": 0.5,
                "reasoning": "fallback", "confidence": 0.0, "context_used": False}
    except Exception as e:
        logger.error("Gemini API error during interpretation: %s", e)
        raise


def explain_recommendations(query: str, prefs: dict, recommendations: list) -> str:
    """Ask Gemini to write a friendly explanation of the retrieved recommendations."""
    songs_text = "\n".join(
        f'{i+1}. "{song["title"]}" by {song["artist"]} '
        f'(genre: {song["genre"]}, mood: {song["mood"]}, energy: {song["energy"]:.2f})'
        for i, (song, score, _) in enumerate(recommendations)
    )
    prompt = (
        f'A user asked for: "{query}"\n\n'
        f"I found these matches:\n{songs_text}\n\n"
        "Write a warm, 2-3 sentence response explaining why these songs fit their request. "
        "Mention 1-2 specific songs by name."
    )
    logger.info("Generating explanation for %d recommendations", len(recommendations))
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=250),
        )
        return response.text.strip()
    except Exception as e:
        logger.error("Gemini API error during explanation: %s", e)
        return "Here are your top song recommendations based on your request."


def get_recommendations(
    query: str,
    songs: list[dict],
    k: int = 5,
    mode: str = "balanced",
    use_context: bool = True,
) -> dict:
    """
    Full RAG pipeline: retrieve domain knowledge → interpret query → score catalog → explain.

    Data sources:
      1. data/music_knowledge.json  — activity/mood domain knowledge (context injection)
      2. data/songs.csv             — 3,420 songs across 114 genres (candidate retrieval)

    Returns a dict with keys:
      query, interpreted_prefs, recommendations (list of (song, score, reasons)), explanation
    """
    prefs = interpret_query(query, songs, use_context=use_context)
    recommendations = recommend_songs(prefs, songs, k=k, mode=mode)
    explanation = explain_recommendations(query, prefs, recommendations)
    return {
        "query": query,
        "interpreted_prefs": prefs,
        "recommendations": recommendations,
        "explanation": explanation,
    }
