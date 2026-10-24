"""Curated evidence-to-action research cards for an ORIGINAL local music partner.

These are compact interpretations of user-supplied deep research, never
album transcriptions or model training data. Historical propositions,
researcher design hypotheses, and unresolved uncertainty are separate.
All evidence URLs are offline metadata: no requests are made at show time.
"""
from __future__ import annotations

import re

# Verified source attributions in the research dossier. A source supports
# the *historical_claim*, not the suggested MIDI or arrangement parameters.
CARDS = (
    {
        "id": "illmatic-1994-gap-reply",
        "album": "illmatic-1994",
        "source": {"author": "Jeff 'Chairman' Mao / Large Professor",
                   "title": "Interview: Hip Hop Great Large Professor",
                   "date": "2015-02-24", "kind": "firsthand_interview",
                   "url": "https://daily.redbullmusicacademy.com/2015/02/large-professor-interview/"},
        "historical_claim": "Large Professor describes connecting producers with different beats and approaches around Nas.",
        "action": "When Suzy ends a dense vocal phrase, generate 1-3 original notes inside the following rest; suppress notes during the verse.",
        "role": "vocal_reply",
        "controls": ("lead_active", "rest_beats", "note_events"),
        "hypothetical": {"max_notes": 3, "rest_guard_beats": 0.5},
        "tags": ("illmatic", "nas", "boom bap", "queensbridge", "dj premier", "voice", "vocal", "space"),
        "uncertainty": "Vocal-density thresholds are original controls, not album measurements.",
    },
    {
        "id": "illmatic-1994-producer-contrast",
        "album": "illmatic-1994",
        "source": {"author": "Jeff 'Chairman' Mao / Large Professor",
                   "title": "Interview: Hip Hop Great Large Professor",
                   "date": "2015-02-24", "kind": "firsthand_interview",
                   "url": "https://daily.redbullmusicacademy.com/2015/02/large-professor-interview/"},
        "historical_claim": "Illmatic was built across several producers with differing musical approaches.",
        "action": "Preserve Suzy's harmonic framework while changing only one ORIGINAL response role at a section boundary: bass, keys or vocal answer.",
        "role": "section_orchestrator",
        "controls": ("section_index", "active_role", "layer_count"),
        "hypothetical": {"max_simultaneous_response_roles": 1},
        "tags": ("illmatic", "nas", "large professor", "producer", "section", "contrast", "arrangement"),
        "uncertainty": "The role sequence is an invention, not an Illmatic track sequence.",
    },
    {
        "id": "baduizm-1997-call-space",
        "album": "baduizm-1997",
        "source": {"author": "Erykah Badu / Eothen Alapatt",
                   "title": "Erykah Badu: Red Bull Music Academy Lecture",
                   "date": "2011", "kind": "firsthand_interview",
                   "url": "https://www.redbullmusicacademy.com/lectures/erykah-badu-frother-of-the-month/"},
        "historical_claim": "Badu describes early underground hip-hop roots, her Philadelphia work with the Roots, and their jazz/Tribe connection.",
        "action": "Wait for a detected gap in Suzy's lead; compose a short new answer or one harmonic extension, never an imitation of Badu's melody.",
        "role": "vocal_reply",
        "controls": ("rest_beats", "lead_active", "harmonic_context"),
        "hypothetical": {"max_notes": 3, "rest_guard_beats": 0.5},
        "tags": ("baduizm", "erykah badu", "rnb", "neo soul", "jazz", "vocal", "roots", "call response", "space"),
        "uncertainty": "Exact Baduizm call-and-response timing is not established by the interview.",
    },
    {
        "id": "baduizm-1997-philly-boundary",
        "album": "baduizm-1997",
        "source": {"author": "Erykah Badu / Eothen Alapatt",
                   "title": "Erykah Badu: Red Bull Music Academy Lecture",
                   "date": "2011", "kind": "firsthand_interview",
                   "url": "https://www.redbullmusicacademy.com/lectures/erykah-badu-frother-of-the-month/"},
        "historical_claim": "Badu places Otherside of the Game and Sometimes in the Baduizm-era Roots work but the all-in-one-room Poyser/Palladino story mainly with Mama's Gun (2000).",
        "action": "For Suzy's own live-looping arrangement, use an original bass/keys handoff rather than claiming to recreate Baduizm session technique.",
        "role": "bass_keys_handoff",
        "controls": ("bass_onsets", "key_onsets", "lead_active"),
        "hypothetical": {"max_simultaneous_response_roles": 1},
        "tags": ("baduizm", "erykah", "mamas gun", "questlove", "poyser", "palladino", "roots", "rhodes"),
        "uncertainty": "Do not attribute Mama's Gun recording method to all Baduizm tracks.",
    },
    {
        "id": "low-end-1991-bass-center",
        "album": "low-end-theory-1991",
        "source": {"author": "Eddie Houghton / Bob Power",
                   "title": "How Bob Power Put The Low End in The Low End Theory",
                   "date": "2021-09-24", "kind": "producer_interview",
                   "url": "https://www.okayplayer.com/how-bob-power-put-the-low-end-in-a-tribe-called-quests-the-low-end-theory/453108"},
        "historical_claim": "Engineer Bob Power discusses a bass-centered approach to the record's production.",
        "action": "Compose one new bass-support note idea; reduce competing upper-register events around Suzy's voice.",
        "role": "bass_anchor",
        "controls": ("bass_register", "upper_density", "lead_active"),
        "hypothetical": {"max_upper_notes_per_bar": 1},
        "tags": ("low end theory", "tribe", "q tip", "jazz rap", "bass", "minimal", "mix"),
        "uncertainty": "No track bassline, sampled note, or precise mix value is asserted.",
    },
    {
        "id": "low-end-1991-register-budget",
        "album": "low-end-theory-1991",
        "source": {"author": "Q-Tip",
                   "title": "Q-Tip: Red Bull Music Academy Lecture",
                   "date": "2013", "kind": "firsthand_interview",
                   "url": "https://www.redbullmusicacademy.com/lectures/q-tip/"},
        "historical_claim": "Q-Tip discusses Tribe and Native Tongues collaboration and music-making.",
        "action": "Give bass, lead voice and AI answer separate registers; keep the AI answer short and quiet when Suzy is singing.",
        "role": "register_allocator",
        "controls": ("lead_register", "response_register", "bass_register"),
        "hypothetical": {"max_notes": 3},
        "tags": ("tribe", "low end theory", "native tongues", "q tip", "jazz", "register", "vocal"),
        "uncertainty": "These register allocations are experimental, not measured Tribe arrangements.",
    },
    {
        "id": "brown-sugar-1995-keys-core",
        "album": "brown-sugar-1995",
        "source": {"author": "D'Angelo / Nelson George",
                   "title": "D'Angelo: Red Bull Music Academy Lecture",
                   "date": "2014", "kind": "firsthand_interview",
                   "url": "https://www.redbullmusicacademy.com/lectures/dangelo/"},
        "historical_claim": "D'Angelo says much of Brown Sugar grew from his bedroom demos and that he sought Bob Power because he admired Tribe's sound.",
        "action": "Build one original keyboard answer from Suzy's supplied chord; keep common tones and minimize unnecessary chord motion.",
        "role": "keys_harmony",
        "controls": ("supplied_chord", "common_tones", "voice_leading"),
        "hypothetical": {"max_notes": 4},
        "tags": ("brown sugar", "dangelo", "rnb", "soul", "keys", "chords", "bob power", "tribe"),
        "uncertainty": "Do not assign Voodoo/Questlove off-grid timing to Brown Sugar.",
    },
    {
        "id": "brown-sugar-1995-vocal-space",
        "album": "brown-sugar-1995",
        "source": {"author": "Jeff 'Chairman' Mao / Bob Power",
                   "title": "Interview: Bob Power on D'Angelo, Tribe Called Quest and De La Soul",
                   "date": "2014-07-08", "kind": "producer_interview",
                   "url": "https://daily.redbullmusicacademy.com/2014/07/bob-power-interview/"},
        "historical_claim": "Power describes D'Angelo's detailed personal authorship of his arrangement and production ideas.",
        "action": "Treat Suzy's existing vocal and keys as the anchor; add at most one quiet original support phrase after a held note.",
        "role": "vocal_support",
        "controls": ("lead_hold", "rest_beats", "layer_count"),
        "hypothetical": {"max_notes": 2},
        "tags": ("brown sugar", "dangelo", "vocal", "harmony", "rnb", "keys", "support"),
        "uncertainty": "The proposed note count is ours; no historical recording was analyzed.",
    },
    {
        "id": "miseducation-1998-rap-sing-switch",
        "album": "miseducation-1998",
        "source": {"author": "Recording Academy",
                   "title": "The Miseducation of Lauryn Hill: 25 Facts",
                   "date": "2023-08-25", "kind": "institutional_retrospective",
                   "url": "https://www.grammy.com/news/the-miseducation-of-lauryn-hill-facts-cover-controversy-records-anniversary-tour/"},
        "historical_claim": "Hill's album combines singing, rapping, musicians and programmed production; its live feel was discussed by participants.",
        "action": "When Suzy sings dense syllables, reduce AI note density; when she sustains, allow one longer original harmony note.",
        "role": "mode_sensitive",
        "controls": ("lead_onset_density", "lead_sustain", "response_density"),
        "hypothetical": {"max_notes": 2},
        "tags": ("miseducation", "lauryn hill", "rap", "sing", "rnb", "vocal", "live"),
        "uncertainty": "No exact syllable threshold or timing jitter is sourced.",
    },
    {
        "id": "miseducation-1998-preserve-human",
        "album": "miseducation-1998",
        "source": {"author": "Laura Checkoway",
                   "title": "Inside The Miseducation of Lauryn Hill",
                   "date": "2008-08-26", "kind": "participant_reporting",
                   "url": "https://www.rollingstone.com/music/music-news/inside-the-miseducation-of-lauryn-hill-252219/"},
        "historical_claim": "Participant reporting discusses live musical texture and disputes surrounding contributions and production credit.",
        "action": "Keep Suzy's actual recorded note timing unchanged; vary only original AI notes, never rewrite her recorded performance.",
        "role": "preserve_human_timing",
        "controls": ("lead_timing", "response_timing", "timing_guard"),
        "hypothetical": {"max_notes": 3},
        "tags": ("miseducation", "lauryn hill", "live", "human", "timing", "authorship"),
        "uncertainty": "Official credits and later New Ark disputes are separate claims, not automatically reconciled.",
    },
    {
        "id": "cash-crop-1997-role-rotation",
        "album": "cash-crop-1997",
        "source": {"author": "Yasmine Shemesh / Red1 and DJ Kemo",
                   "title": "Vancity calling: how Rascalz made history",
                   "date": "2023-06-05", "kind": "firsthand_interview",
                   "url": "https://www.straight.com/music/vancity-calling-how-rascalz-made-history"},
        "historical_claim": "Rascalz developed within an existing Vancouver network of MCs, DJs, broadcasts, skaters and hip-hop events.",
        "action": "Rotate only one original support role per four-bar section: bass note, sparse key reply or simple texture transition; protect Suzy's next vocal entry.",
        "role": "section_orchestrator",
        "controls": ("section_index", "active_role", "lead_active"),
        "hypothetical": {"max_simultaneous_response_roles": 1},
        "tags": ("rascalz", "cash crop", "vancouver", "red1", "kemo", "dj", "mc", "canada", "role"),
        "uncertainty": "The role rotation is a new exercise, not a documented Cash Crop production pattern.",
    },
    {
        "id": "cash-crop-1997-cypher-space",
        "album": "cash-crop-1997",
        "source": {"author": "Dalton Higgins / JUNO Awards",
                   "title": "Rap's Rocky Road",
                   "date": "undated", "kind": "institutional_history",
                   "url": "https://junoawards.ca/blog/raps-rocky-road/"},
        "historical_claim": "Rascalz declined their 1998 JUNO for Cash Crop to protest exclusion of rap from the main televised awards.",
        "action": "Treat every expected new Suzy verse as a handoff: finish the AI phrase early and keep a clean entry gap; never create a Rascalz riff.",
        "role": "vocal_reentry_guard",
        "controls": ("next_lead_entry", "ai_note_end", "rest_beats"),
        "hypothetical": {"rest_guard_beats": 0.5},
        "tags": ("rascalz", "cash crop", "vancouver", "cypher", "mc", "hip hop", "space", "juno"),
        "uncertainty": "The 'cypher handoff' is a creative analogy; the award protest is cultural history, not a timing instruction.",
    },
)


def _terms(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.casefold())) - {
        "and", "the", "for", "and", "that", "with", "into", "your", "from",
    }


def validate_cards(cards=CARDS) -> None:
    """Fail clearly on malformed, unprovenanced or copyright-risk cards."""
    ids = set()
    for card in cards:
        if not isinstance(card, dict) or set(card) != {
                "id", "album", "source", "historical_claim", "action", "role",
                "controls", "hypothetical", "tags", "uncertainty"}:
            raise ValueError("invalid research-card fields")
        card_id = card["id"]
        if not isinstance(card_id, str) or not re.fullmatch(r"[a-z0-9-]{8,90}", card_id) or card_id in ids:
            raise ValueError("invalid or duplicate research card ID")
        ids.add(card_id)
        src = card["source"]
        if not isinstance(src, dict) or set(src) != {"author", "title", "date", "kind", "url"}:
            raise ValueError("invalid card attribution")
        if not isinstance(src["url"], str) or not src["url"].startswith("https://"):
            raise ValueError("research evidence must cite HTTPS source")
        if any(not isinstance(src[k], str) or not src[k].strip() for k in ("author", "title", "date", "kind")):
            raise ValueError("incomplete research attribution")
        if any(not isinstance(card[k], str) or not card[k].strip() for k in
               ("album", "historical_claim", "action", "role", "uncertainty")):
            raise ValueError("incomplete research card")
        if not isinstance(card["tags"], tuple) or not card["tags"]:
            raise ValueError("missing retrieval tags")
        if not isinstance(card["controls"], tuple) or not card["controls"]:
            raise ValueError("missing executable control vocabulary")
        if not isinstance(card["hypothetical"], dict) or not card["hypothetical"]:
            raise ValueError("missing original experiment constraints")


def research_brief(query: str, *, limit: int = 2, catalog=CARDS,
                   omit_album: str | None = None) -> list[dict]:
    """Retrieve compact, attributed ideas for Qwen; never modify model weights.

    The returned 'reference' ID identifies the individual research CARD,
    unlike the older pack-level references. Public cards are NEVER promoted
    to Suzy's approved private 'live_use' teaching store.
    """
    if not isinstance(query, str) or len(query) > 300:
        raise ValueError("query must be a short string")
    if type(limit) is not int or not 1 <= limit <= 3:
        raise ValueError("only 1-3 research cards can enter local inference")
    if omit_album is not None and (not isinstance(omit_album, str) or not omit_album):
        raise ValueError("invalid excluded reference")
    validate_cards(catalog)
    words = _terms(query)
    if not words:
        return []
    ranked = []
    for position, card in enumerate(catalog):
        if card["album"] == omit_album:
            continue
        name = _terms(card["album"])
        tags = _terms(" ".join(card["tags"]))
        score = 3*len(words & name) + len(words & tags)
        if score:
            ranked.append((-score, position, card))
    ranked.sort()
    return [{
        "reference": card["id"],
        "reference_album": card["album"],
        "cue": card["role"],
        "proposed_action": card["action"][:200],
        "source_label": card["source"]["title"][:90],
        "source_url": card["source"]["url"],
        "source_kind": card["source"]["kind"],
        "source_supports": card["historical_claim"][:180],
        "note": "ORIGINAL musical exercise, NOT album transcription; unverified timings.",
    } for _, _, card in ranked[:limit]]
