"""Source-backed, offline, opt-in historical references for original R&B/hip-hop arranging.

Historical anchors link to reporting, musician interviews, or cultural archives.
Every 'action' below is OUR musical-design interpretation, not a transcription
of a copyrighted recording, artist voice, drum sample, or actual MIDI data.
No network, external packages, private memory or audio files.
"""
from __future__ import annotations

import re

# Small intentionally reviewed seed corpus; expand through attributed research.
# Each entry has a verifiable historical anchor and a separate ORIGINAL action.
PACKS = (
    {
        "id": "illmatic-1994",
        "title": "Illmatic (1994): East Coast hip-hop",
        "year": 1994,
        "historical_context": (
            "Nas's Queensbridge-rooted debut involved producers DJ Premier, "
            "Large Professor, Pete Rock, Q-Tip and L.E.S.; its lyrics and "
            "jazz-influenced production are tied to the social world it describes."
        ),
        "sources": (
            {"label": "Nas: Time Is Illmatic documentary press kit",
             "url": "https://d13jj08vfqimqg.cloudfront.net/uploads/release/press_kit/95/Nas_TII_PressKit.pdf"},
            {"label": "Library of Congress: Illmatic essay",
             "url": "https://www.loc.gov/static/programs/national-recording-preservation-board/documents/Illmatic_McDuffie.pdf"},
        ),
        "ideas": (
            {"id": "spare-boom-bap", "cue": "Dusty, sparse East Coast boom-bap",
             "action": "Keep a steady kick/snare foundation and leave a whole beat free for the lead phrase; invent an original two-note keyboard answer.",
             "tags": ("illmatic", "boom bap", "hip hop", "groove", "space", "drums"), "source_index": 0},
            {"id": "short-jazz-motif", "cue": "Tightly repeated jazz-influenced motif",
             "action": "Make a new short minor-colour piano or electric-keyboard motif, repeat it with one small interval change, never copy a recorded sample.",
             "tags": ("illmatic", "nas", "jazz", "motif", "piano", "sampling"), "source_index": 1},
        ),
    },
    {
        "id": "baduizm-1997",
        "title": "Baduizm (1997): hip-hop-rooted R&B and jazz",
        "year": 1997,
        "historical_context": (
            "Erykah Badu described early demo production as raw underground "
            "hip-hop and spoke about collaborating with The Roots, Questlove "
            "and James Poyser; the 1997 album bridges hip-hop, jazz and R&B."
        ),
        "sources": (
            {"label": "Essence: Erykah Badu on Baduizm's creation",
             "url": "https://www.essence.com/entertainment/erykah-badu-baduizm-25-years/"},
            {"label": "Red Bull Music Academy: Erykah Badu interview",
             "url": "https://www.redbullmusicacademy.com/lectures/erykah-badu-frother-of-the-month/"},
        ),
        "ideas": (
            {"id": "vocal-conversation", "cue": "Conversational R&B vocal response",
             "action": "Answer only after the singer finishes; compose a new three-note response with two soft notes and one sustained ending.",
             "tags": ("baduizm", "erykah", "badu", "neo soul", "rnb", "vocal", "call response"), "source_index": 0},
            {"id": "laidback-rhodes", "cue": "Jazz-coloured, spacious keys behind a singer",
             "action": "Use an original soft electric-piano voicing or single guide-tone line, avoid doubling every vocal note, and preserve a full rest.",
             "tags": ("baduizm", "neo soul", "jazz", "rhodes", "harmony", "rest"), "source_index": 1},
        ),
    },
    {
        "id": "low-end-theory-1991",
        "title": "The Low End Theory (1991): jazz-rap and bass",
        "year": 1991,
        "historical_context": (
            "A Tribe Called Quest's album is recognized as a major jazz-and-rap "
            "fusion; the Library of Congress essay emphasizes its stripped-back "
            "framework, bass focus, jazz sampling, and ensemble contributions."
        ),
        "sources": (
            {"label": "Library of Congress: The Low End Theory essay",
             "url": "https://lcweb2.loc.gov/static/programs/national-recording-preservation-board/documents/The-Low-End-Theory_Amorosi.pdf"},
        ),
        "ideas": (
            {"id": "bass-as-dialogue", "cue": "Bass-led jazz-rap groove",
             "action": "Generate a simple original bass answer between vocal entries, alternating root and a passing tone, with an intentional rest.",
             "tags": ("tribe", "low end theory", "jazz rap", "bass", "hip hop"), "source_index": 0},
            {"id": "economical-jazz-rap", "cue": "Minimal, spacious jazz-rap instrumentation",
             "action": "Leave the bass and drums as the main groove; answer with a single contrasting note instead of layering another full chord.",
             "tags": ("tribe", "jazz rap", "minimal", "hip hop", "space"), "source_index": 0},
        ),
    },
    {
        "id": "brown-sugar-1995",
        "title": "Brown Sugar (1995): hip-hop-rooted soul",
        "year": 1995,
        "historical_context": (
            "D'Angelo's debut brought soul keyboard playing and singing into "
            "conversation with hip-hop production; this is a research reference, "
            "not permission to reproduce the original record."
        ),
        "sources": (
            {"label": "Jazz musicians discuss Brown Sugar's composition",
             "url": "https://youllhearit.com/episodes/brown-sugar-dangelo/transcript"},
        ),
        "ideas": (
            {"id": "soul-keyboard-reply", "cue": "Warm soul keyboard counterline",
             "action": "After the sung line, introduce an original three-note electric-keyboard phrase with one held chord tone and gentle dynamics.",
             "tags": ("dangelo", "brown sugar", "neo soul", "rnb", "keys", "harmony"), "source_index": 0},
        ),
    },
    {
        "id": "miseducation-1998",
        "title": "The Miseducation of Lauryn Hill (1998): singing and rap",
        "year": 1998,
        "historical_context": (
            "Lauryn Hill combined singing, rapping, live instrumentation "
            "and a strong commitment to preserving human musical texture."
        ),
        "sources": (
            {"label": "1999 Biography Today interview quotations",
             "url": "https://files.eric.ed.gov/fulltext/ED439044.pdf"},
            {"label": "BET: cultural legacy and collaborators",
             "url": "https://www.bet.com/hip-hop-awards/articles/7uq9da/the-miseducation-of-lauryn-hill-turns-25-how-a-classic-debut-galvanized-a-generation-of-black-women-and-changed-hip-hop"},
        ),
        "ideas": (
            {"id": "sing-rap-breath", "cue": "Conversational space for both rapped and sung phrasing",
             "action": "Leave a short breath gap after dense syllabic phrasing; answer with a distinct held melody note rather than competing syllables.",
             "tags": ("lauryn", "miseducation", "rap", "sing", "rnb", "vocal", "space"), "source_index": 0},
        ),
    },
    {
        "id": "cash-crop-1997",
        "title": "Cash Crop (1997): Rascalz, Vancouver hip-hop",
        "year": 1997,
        "historical_context": (
            "Vancouver's Rascalz featured Red1 and Misfit as MCs with DJ Kemo "
            "as producer. Their 1997 Cash Crop album was named Best Rap Recording "
            "at the 1998 Junos; they declined the award to protest Black music "
            "being excluded from the televised ceremony. Their collaborative "
            "single Northern Touch came in 1998 and was only added to LATER "
            "Cash Crop pressings, not the original 1997 album. Accounts by Red1 "
            "and Kemo place their musical development in Vancouver's local "
            "radio, DJ, skateboard and hip-hop communities."
        ),
        "sources": (
            {"label": "Georgia Straight: Red1 and DJ Kemo interview (2023)",
             "url": "https://www.straight.com/music/vancity-calling-how-rascalz-made-history"},
            {"label": "Canada Black Music Archives: Rascalz biography",
             "url": "https://thecbma.com/artists/rascalz/"},
            {"label": "NOW Magazine: Northern Touch and later Cash Crop pressings",
             "url": "https://nowtoronto.com/music/why-northern-touch-still-matters/"},
        ),
        "ideas": (
            {"id": "vancouver-mc-pocket",
             "cue": "Original Vancouver boom-bap with vocal space",
             "action": "Make an original restrained 4-bar drum/bass loop, leaving beat four clear for the human MC or R&B lead; answer only after her line.",
             "tags": ("rascalz", "cash crop", "vancouver", "canadian", "hip hop", "boom bap", "pocket", "vocal", "red1", "misfit"),
             "source_index": 0},
            {"id": "kemo-producer-economy",
             "cue": "Producer-led hip-hop groove and short musical motifs",
             "action": "Develop a new two-note bass or keyboard response against Suzy's own beat, vary one accent per cycle, and preserve the lead's phrasing.",
             "tags": ("rascalz", "cash crop", "dj kemo", "beat", "producer", "bass", "motif", "sample culture"),
             "source_index": 0},
            {"id": "north-coast-call-response",
             "cue": "Canadian cross-scene hip-hop exchange, not a track recreation",
             "action": "Make two original contrasting call-and-response phrases for different vocal or synth tracks, with staggered entrances and silence between them.",
             "tags": ("rascalz", "northern touch", "vancouver", "toronto", "canadian hip hop", "collaboration", "call response"),
             "source_index": 2},
        ),
    },
)


def _terms(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.casefold())) - {
        "and", "with", "the", "for", "that", "this", "from", "like", "more"
    }


def knowledge_brief(query: str, *, limit: int = 3, catalog=PACKS) -> list[dict]:
    """Small auditable context a local text model *could* use when opted in.

    Caller must explicitly request this. Returns provenance and musical
    suggestions; caller should NEVER claim Qwen learned weights from it.
    """
    if not isinstance(query, str) or len(query) > 500:
        raise ValueError("query must be at most 500 characters")
    if type(limit) is not int or not 1 <= limit <= 5:
        raise ValueError("limit must be between one and five")
    words = _terms(query)
    scores = []
    for pack in catalog:
        if not isinstance(pack, dict):
            raise ValueError("invalid catalog pack")
        if set(pack) != {"id", "title", "year", "historical_context", "sources", "ideas"}:
            raise ValueError("invalid knowledge pack fields")
        for idea in pack["ideas"]:
            if set(idea) != {"id", "cue", "action", "tags", "source_index"}:
                raise ValueError("invalid musical idea fields")
            ix = idea["source_index"]
            if type(ix) is not int or not 0 <= ix < len(pack["sources"]):
                raise ValueError("unattributed musical idea")
            source = pack["sources"][ix]
            if not source["url"].startswith("https://"):
                raise ValueError("knowledge pack sources must be HTTPS")
            text = _terms(" ".join((pack["title"], idea["cue"], *idea["tags"])))
            # Multi-term queries rank by overlap, with direct title matches first.
            score = 2 * len(words & _terms(pack["title"])) + len(words & text)
            scores.append((score, pack, idea, source))
    scores.sort(key=lambda entry: -entry[0])
    if words and not scores[0][0]:
        return []
    result = []
    for score, pack, idea, source in scores:
        if words and score == 0:
            break
        result.append({
            "reference": pack["id"], "era_year": pack["year"],
            "idea": idea["id"], "cue": idea["cue"],
            "proposed_action": idea["action"][:210],
            "source_label": source["label"], "source_url": source["url"],
            "note": "Original arrangement idea inspired by source-backed context; NOT a transcription.",
        })
        if len(result) == limit:
            break
    return result
