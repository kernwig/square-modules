"""Call vocabulary per dance level, used by the level classifier.

Each level introduces a set of calls. A module's level is the *highest* level
of any call appearing in its body (MS < Plus < A1 < A2). The vocabulary is
transcribed from the authoritative CALLERLAB lists effective 2026-09-01:

  * MS   -> New-Mainstream-Program-List-2026-09-01.pdf
  * Plus -> New-Plus-Program-Teaching-Order.pdf
  * A1/A2-> New-Advanced-List-2026-09-01.pdf (page 1)

Matching strategy (see :mod:`levelclassifier.classifier`):
  * Each entry is a lowercase phrase. A body line is normalized (designators,
    fractions, directions stripped) and scanned for the *longest* phrase match.
  * ``LEVEL_RANK`` orders the levels; the classifier takes the max rank hit.

Only MS/Plus/A1/A2 are modeled. Calls above A2 (C-programs) are out of scope
and surface as unknown tokens in the report.
"""
from __future__ import annotations

# Ordering of the levels we classify.
LEVEL_RANK = {"ms": 0, "plus": 1, "a1": 2, "a2": 3}
RANK_TO_LEVEL = {v: k for k, v in LEVEL_RANK.items()}


# ---------------------------------------------------------------------------
# Mainstream (new, 2026). Phrases are lowercase; variants/synonyms included.
# These are the calls that KEEP a module at Mainstream.
# ---------------------------------------------------------------------------
MS_CALLS: set[str] = {
    # 1. Arm Turn Family
    "arm turn", "right arm turn", "left arm turn", "allemande left", "allemande right",
    # 2-6
    "bend the line", "box the gnat", "california twirl", "cast off 3/4", "cast off",
    "centers in",
    # 7. Circle Family (note: "Circle to a Line" is NOT MS -> see PLUS_CALLS)
    "circle left", "circle right", "single circle", "circle of 4",
    # (bare "circle" intentionally omitted; handled with a direction token)
    # 8. Circulate Family
    "circulate", "couples circulate", "all eight circulate", "all 8 circulate",
    "single file circulate", "column circulate", "box circulate", "split circulate",
    # 9-14
    "courtesy turn", "dive thru", "dosado", "do sa do", "double pass thru",
    "extend", "ferris wheel",
    # 15. First/Next couple go left/right
    "first couple go left", "first couple go right", "next couple go left",
    "next couple go right",
    # 16-18
    "flutterwheel", "flutter wheel", "reverse flutterwheel", "reverse flutter wheel",
    "fold", "cross fold", "grand square",
    # 19. Half Sashay Family
    "half sashay", "rollaway", "ladies in men sashay", "ladies in, men sashay",
    # 20. Hinge Family
    "single hinge", "couples hinge", "hinge",
    # 21. Ladies Chain Family
    "ladies chain", "ladies chain 3/4", "four ladies chain", "chain down the line",
    # 22
    "lead right", "lead left",
    # 23. Ocean Wave Family
    "step to a wave", "dosado to a wave", "single circle to a wave", "alamo style",
    "balance",
    # 24-26
    "pass the ocean", "pass thru",
    "couples promenade", "single file promenade", "star promenade",
    "wrong way promenade", "promenade",
    # 27-29
    "recycle", "right and left grand", "weave the ring", "wrong way grand",
    "right and left thru", "right & left thru",
    # 30-33
    "run", "cross run", "scoot back", "separate", "separate around",
    "slide thru",
    # 34-39
    "spin the top", "split two", "square thru", "left square thru",
    "star right", "star left", "star thru", "sweep a quarter", "sweep 1/4",
    # 40-41
    "swing", "swing thru", "left swing thru",
    # 42. Tag the Line Family
    "tag the line", "tag",
    # 43-45
    "touch a quarter", "touch 1/4", "trade", "couples trade", "right hand trade",
    "left hand trade", "partner trade", "trade by",
    # 46. Turn Back Family
    "u-turn back", "u turn back", "backtrack",
    # 47-50
    "veer left", "veer right", "wheel and deal", "wheel & deal",
    "wheel around", "reverse wheel around", "zoom",
    # Common MS-level primitives seen in bodies
    "forward and back", "forward & back",
}


# ---------------------------------------------------------------------------
# Plus (new, 2026). Calls that lift a module to at least Plus.
# Includes the old-Basic/MS calls that moved to Plus (the approved denylist).
# ---------------------------------------------------------------------------
PLUS_CALLS: set[str] = {
    "acey deucey",
    "cloverleaf",
    "ping pong circulate", "ping pong",
    "turn thru",
    "pass to the center",
    "spin chain thru",
    "scoot and dodge", "scoot & dodge",
    "pair off",
    "teacup chain",
    "dixie style to an ocean wave", "dixie style",
    "walk around the corner",
    "see saw", "seesaw",
    "load the boat",
    "1/4 thru", "quarter thru",
    "walk and dodge", "walk & dodge",
    # Designator-interleaved variants ("Boys Walk, Girls Dodge", "Girl Walk &
    # Boy Dodge", etc.) are recognized by a line-level rule in the classifier
    # (_WALK_DODGE_RE), because they span comma-separated call chunks.
    "spin chain the gears",
    "grand swing thru",
    "3/4 thru", "three quarter thru",
    "triple scoot",
    "track 2", "track two",
    "grand 1/4 thru", "grand quarter thru", "grand 3/4 thru",
    "diamond circulate",
    "pass the sea",
    "flip the diamond",
    "follow your neighbor",
    "cut the diamond",
    # Thar family (26-29)
    "allemande thar", "allemande left to an allemande thar", "wrong way thar",
    "slip the clutch",
    "triple trade",
    "shoot the star", "shoot the star full around",
    "peel off",
    "coordinate",
    "spread",
    "fan the top",
    "relay the deucey",
    "partner tag",
    "dixie grand",
    "explode the wave",
    "crossfire",
    "partner hinge",
    "spin chain and exchange the gears", "spin chain & exchange the gears",
    "linear cycle",
    "peel the top",
    "chase right",
    "clover and",
    "circle to a line",
    "trade the wave",
    "eight chain thru", "8 chain thru",
    "eight chain 1", "eight chain 2", "eight chain 3", "eight chain 4",
    "8 chain 1", "8 chain 2", "8 chain 3", "8 chain 4",
    "all 8 spin the top", "all eight spin the top",
    "do paso",
}


# ---------------------------------------------------------------------------
# A1 (new Advanced, 2026 page 1).
# ---------------------------------------------------------------------------
A1_CALLS: set[str] = {
    "any hand",
    "and cross",
    "as couples",
    "belles and beaus",
    "brace thru",
    "cast a shadow",
    "chain reaction",
    "cross clover and",
    "cross over circulate",
    "cross trail thru",
    "cycle and wheel",
    "double star thru", "triple star thru",
    "ends bend",
    "explode and",
    "explode the line",
    "quarter top", "half the top", "three-quarter top", "three quarter top",
    "grand follow your neighbor",
    "horseshoe turn",
    "lockit",
    "mix",
    "pass in", "pass out",
    "quarter in", "quarter out",
    "right roll to a wave", "left roll to a wave", "roll to a wave",
    "six-two acey deucey", "six two acey deucey",
    "split square chain thru",
    "split square thru",
    "square chain thru",
    "step and slide",
    "swap around", "reverse swap around",
    "transfer the column",
    "triple cross", "double cross",
    "turn and deal",
    "wheel thru", "left wheel thru",
}


# ---------------------------------------------------------------------------
# A2 (new Advanced, 2026 page 1).
# ---------------------------------------------------------------------------
A2_CALLS: set[str] = {
    "all 4 couples", "all four couples",
    "all 8 swing thru", "all 8 switch the wave", "all 8 walk and dodge", "all 8 mix",
    "checkmate the column", "checkmate",
    "diamond chain thru",
    "hourglass circulate", "cut the hourglass", "flip the hourglass", "hourglass",
    "in roll circulate", "out roll circulate",
    "mini-busy", "mini busy",
    "motivate",
    "pass and roll", "pass and roll your neighbor",
    "peel and trail",
    "recycle (facing couples)",
    "remake", "grand remake", "remake the thar",
    "scoot and weave",
    "scoot chain thru",
    "single wheel",
    "slither",
    "spin the windmill",
    "split counter rotate", "box counter rotate", "counter rotate",
    "split transfer", "box transfer",
    "swing and mix",
    "switch the wave",
    "switch to a diamond", "switch to an hourglass",
    "trade circulate",
    "trail off",
    "transfer and",
    "zig zag", "zag zig", "zig zig", "zag zag",
}


# ---------------------------------------------------------------------------
# Designator-interleaved calls.
#
# Some calls name the acting dancers inline between the two words of the call,
# e.g. "Boys Walk, Girls Dodge" is the Plus call "Walk & Dodge" with the
# designators woven in. These cannot be matched as a fixed contiguous phrase.
#
# Each entry is (part_a_tokens, part_b_tokens, canonical_phrase, level). A line
# matches when part A appears, then part B appears later, and *every* token in
# the gap between them is a NON_CALL_TOKEN (designator/direction/connector).
# A real call word in the gap (e.g. "scoot" in "Boys Walk, Scoot and Dodge")
# breaks the match, so unrelated calls sharing a line are not mis-joined.
# Matching skips tokens already consumed by a normal contiguous phrase, so an
# explicit "Scoot and Dodge" is claimed by that call first.
# ---------------------------------------------------------------------------
INTERLEAVED_CALLS: list[tuple[tuple[str, ...], tuple[str, ...], str, str]] = [
    (("walk",), ("dodge",), "walk & dodge", "plus"),
]


LEVEL_VOCAB: dict[str, set[str]] = {
    "ms": MS_CALLS,
    "plus": PLUS_CALLS,
    "a1": A1_CALLS,
    "a2": A2_CALLS,
}


# ---------------------------------------------------------------------------
# Non-call tokens: dancer designators, fractions, directions, formation words,
# connectors. These are stripped from a body line before call matching so they
# are not reported as "unknown".
# ---------------------------------------------------------------------------
DESIGNATORS = {
    "heads", "sides", "head", "side", "boys", "girls", "men", "ladies", "boy",
    "girl", "man", "lady", "centers", "ends", "center", "end", "leaders",
    "trailers", "leader", "trailer", "everybody", "those", "the",
    "new", "outside", "inside", "outsides", "insides", "very",
    "lonesome", "same", "others", "other", "designated", "beaus", "belles",
    "couple", "couples", "partner", "corner",
}

DIRECTIONS = {
    "left", "right", "in", "out", "back", "forward", "up", "down", "around",
    "home", "across", "apart", "together", "away", "wrong", "way",
}

CONNECTORS = {
    "and", "&", "to", "a", "an", "then", "with", "your", "of", "into", "for",
    "come", "go", "make", "start", "again", "do", "move", "all",
}

FRACTIONS = {
    "1/4", "1/2", "3/4", "full", "once", "twice", "quarter", "half", "three-quarter",
    "1", "2", "3", "4", "5", "6", "7", "8", "0",
}

# Combined set of tokens that are never, on their own, a call.
NON_CALL_TOKENS = DESIGNATORS | DIRECTIONS | CONNECTORS | FRACTIONS
