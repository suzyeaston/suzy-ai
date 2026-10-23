"""Opt-in, bounded cultural context for a live model's musical decisions.

Only explicit live_use=True teachings in the local music domain are eligible.
No private memory search, album reviews by default, external services, audio,
or arbitrary world facts are sent to the local model.
"""
import re

ALLOWED_KINDS = frozenset({"musical_idea"})
EXCERPT_KEYS = ("style", "technique", "production", "mood", "note", "voicing")
MAX_CONTEXT = 3


def clean_text(value, limit=100):
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())[:limit].strip()


def music_culture_brief(query="", *, fetcher=None):
    """Return at most three short, musician-approved musical ideas, with IDs.

    A supplied fetcher is used for offline tests. The regular store is local
    SQLite, loaded on the worker thread only (never the audio callback).
    """
    if fetcher is None:
        from ..world import list_teachings
        fetcher = list_teachings
    try:
        rows = fetcher(domain="music", teaching_kind="musical_idea", limit=100)
    except (OSError, ValueError, RuntimeError):
        # A missing or damaged optional world store must never stop the
        # already-working audio and model path.
        return []
    qwords = set(re.findall(r"[a-z0-9]{3,}", clean_text(query, 250).lower()))
    collected = []
    for position, row in enumerate(rows):
        if not isinstance(row, dict) or row.get("teaching_kind") not in ALLOWED_KINDS:
            continue
        payload = row.get("payload")
        if (not isinstance(payload, dict) or payload.get("live_use") is not True
                or row.get("source") != "human"):
            continue
        label = clean_text(row.get("entity_name"), 72)
        detail = {key: clean_text(payload.get(key), 120)
                  for key in EXCERPT_KEYS if clean_text(payload.get(key), 120)}
        if not label or not detail:
            continue
        identity = row.get("id")
        if not isinstance(identity, str) or not re.fullmatch(r"teach_[0-9a-f]{24}", identity):
            continue
        words = set(re.findall(r"[a-z0-9]{3,}", (label + " " + " ".join(detail.values())).lower()))
        score = len(words & qwords)
        collected.append((-score, position, {
            "teaching_id": identity,
            "idea": label,
            "musical_detail": detail,
        }))
    collected.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in collected[:MAX_CONTEXT]]


# Bounded, musically meaningful *mix choices*. Each choice keeps a headroom
# ceiling in the existing mixer, and adjusts actual PCM rather than only UI copy.
VOCAL_ROLES = {
    "support": (0.65, 0.30),
    "counterpoint": (0.40, 0.70),
    "texture": (0.28, 0.42),
}


def validate_cultural_decision(decision, choices):
    """Require both model choices; never invent a cultural decision on failure."""
    if (not isinstance(decision, dict)
            or set(decision) != {"pattern", "role"}
            or decision["pattern"] not in choices
            or decision["role"] not in VOCAL_ROLES):
        raise ValueError("model did not choose a valid cultural vocal arrangement")
    return decision["pattern"], decision["role"]
