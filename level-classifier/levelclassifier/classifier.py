"""Detect a module's dance level from its body call text.

Algorithm
---------
For each body line:
  1. Normalize: lowercase, drop parentheticals, split on call separators
     (commas, "then", ";"), collapse whitespace.
  2. For each resulting phrase, slide a window and find the *longest* vocabulary
     phrase that matches, marking those tokens consumed and recording the hit's
     level.
  3. Tokens left unconsumed that are not in NON_CALL_TOKENS are "unknown".

The module level is the max level over all hits (MS < Plus < A1 < A2).

Confidence
----------
  * ``high``  - detection was driven by a recognized Plus/A1/A2 call, OR the
    body was fully recognized (no unknown tokens) and resolves to MS.
  * ``low``   - fell back to MS only because nothing higher was recognized, but
    unknown tokens remain (we could be missing a higher-level call).

Unknown tokens are reported, never used to change a level automatically.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .vocab import (
    INTERLEAVED_CALLS,
    LEVEL_RANK,
    LEVEL_VOCAB,
    NON_CALL_TOKENS,
    RANK_TO_LEVEL,
)

# Build a (level, phrase, token_list) index sorted so we try longer phrases
# first within a single scan.
_INDEX: list[tuple[int, str, list[str]]] = []
for _level, _calls in LEVEL_VOCAB.items():
    _rank = LEVEL_RANK[_level]
    for _phrase in _calls:
        _INDEX.append((_rank, _phrase, _phrase.split()))
# Longest phrase (most tokens) first; ties broken by higher level so a higher
# phrase of equal length is preferred.
_INDEX.sort(key=lambda t: (len(t[2]), t[0]), reverse=True)

_PAREN_RE = re.compile(r"\([^)]*\)")
_SPLIT_RE = re.compile(r"[;,]|\bthen\b")
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9/&'-]*")


@dataclass
class CallHit:
    phrase: str
    level: str


@dataclass
class Classification:
    detected_level: str
    confidence: str                 # "high" | "low"
    hits: list[CallHit] = field(default_factory=list)
    unknown_tokens: list[str] = field(default_factory=list)

    @property
    def deciding_call(self) -> str:
        """The highest-level hit phrase that drove the detected level."""
        best = None
        for h in self.hits:
            if h.level == self.detected_level:
                if best is None:
                    best = h.phrase
        return best or ""


def _tokenize_phrase(phrase: str) -> list[str]:
    phrase = _PAREN_RE.sub(" ", phrase.lower())
    return _TOKEN_RE.findall(phrase)


def _match_phrase(tokens: list[str]) -> tuple[list[CallHit], list[bool]]:
    """Greedy longest-match over a token list.

    Returns (hits, consumed) where ``consumed[i]`` is True if token ``i`` was
    covered by a vocabulary phrase.
    """
    n = len(tokens)
    consumed = [False] * n
    hits: list[CallHit] = []

    i = 0
    while i < n:
        if consumed[i]:
            i += 1
            continue
        matched = False
        # Try index entries (already longest-first). Only consider those whose
        # length fits and whose tokens match starting at i.
        for rank, phrase, ptoks in _INDEX:
            plen = len(ptoks)
            if plen == 0 or i + plen > n:
                continue
            if tokens[i : i + plen] == ptoks:
                for j in range(i, i + plen):
                    consumed[j] = True
                hits.append(CallHit(phrase=phrase, level=RANK_TO_LEVEL[rank]))
                i += plen
                matched = True
                break
        if not matched:
            i += 1

    return hits, consumed


def _match_interleaved(
    tokens: list[str], consumed: list[bool]
) -> list[CallHit]:
    """Match designator-interleaved calls over a whole line's tokens.

    For each entry (part_a, part_b, phrase, level), scan for an unconsumed
    occurrence of part A followed later by part B where every token strictly
    between them is a NON_CALL_TOKEN (so a real call word in the gap breaks the
    match). On success, the part-A and part-B tokens are marked consumed and a
    hit is recorded. Tokens already consumed by a contiguous phrase are skipped,
    so an explicit "Scoot and Dodge" keeps its own "dodge".
    """
    n = len(tokens)
    hits: list[CallHit] = []

    def find_part(part: tuple[str, ...], start: int) -> int:
        plen = len(part)
        i = start
        while i + plen <= n:
            if (
                not any(consumed[i : i + plen])
                and tuple(tokens[i : i + plen]) == part
            ):
                return i
            i += 1
        return -1

    for part_a, part_b, phrase, level in INTERLEAVED_CALLS:
        search_from = 0
        while True:
            a_at = find_part(part_a, search_from)
            if a_at < 0:
                break
            a_end = a_at + len(part_a)
            b_at = find_part(part_b, a_end)
            if b_at < 0:
                break
            # Every token in the gap must be a non-call filler token.
            gap_ok = all(tokens[k] in NON_CALL_TOKENS for k in range(a_end, b_at))
            if gap_ok:
                for k in range(a_at, a_end):
                    consumed[k] = True
                for k in range(b_at, b_at + len(part_b)):
                    consumed[k] = True
                hits.append(CallHit(phrase=phrase, level=level))
                search_from = b_at + len(part_b)
            else:
                # A real call word sits between A and B; this A isn't part of
                # an interleaved call. Advance past it and keep looking.
                search_from = a_end
    return hits


def classify_lines(call_lines: list[str]) -> Classification:
    all_hits: list[CallHit] = []
    all_unknown: list[str] = []

    for line in call_lines:
        # Strip parentheticals at the LINE level first, so a comma inside a
        # parenthetical aside (e.g. "(with each other, i.e. Slither)") does not
        # leak the aside's words into the call stream.
        cleaned = _PAREN_RE.sub(" ", line)

        # Normal contiguous matching runs per call chunk (calls do not span a
        # comma / "then"). We build the line's full token list and a shared
        # consumed-mask by concatenating each chunk's tokens in order.
        line_tokens: list[str] = []
        line_consumed: list[bool] = []
        for chunk in _SPLIT_RE.split(cleaned):
            toks = _tokenize_phrase(chunk)
            if not toks:
                continue
            hits, consumed = _match_phrase(toks)
            all_hits.extend(hits)
            line_tokens.extend(toks)
            line_consumed.extend(consumed)

        # Designator-interleaved calls (e.g. "Boys Walk, Girls Dodge") are
        # matched across chunk boundaries on the whole line, after contiguous
        # phrases have claimed their tokens.
        all_hits.extend(_match_interleaved(line_tokens, line_consumed))

        # Anything still unconsumed and not a filler token is unknown.
        all_unknown.extend(
            tok
            for idx, tok in enumerate(line_tokens)
            if not line_consumed[idx] and tok not in NON_CALL_TOKENS
        )

    if all_hits:
        best_rank = max(LEVEL_RANK[h.level] for h in all_hits)
    else:
        best_rank = LEVEL_RANK["ms"]
    detected = RANK_TO_LEVEL[best_rank]

    # Confidence.
    if best_rank > LEVEL_RANK["ms"]:
        confidence = "high"  # a recognized higher-level call drove it
    elif not all_unknown:
        confidence = "high"  # fully recognized and stays MS
    else:
        confidence = "low"   # MS-by-absence but unrecognized tokens remain

    # De-duplicate unknowns, preserve order.
    seen: set[str] = set()
    unknown_unique: list[str] = []
    for tok in all_unknown:
        if tok not in seen:
            seen.add(tok)
            unknown_unique.append(tok)

    return Classification(
        detected_level=detected,
        confidence=confidence,
        hits=all_hits,
        unknown_tokens=unknown_unique,
    )
