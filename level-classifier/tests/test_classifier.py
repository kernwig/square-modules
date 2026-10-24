"""Classification behavior over representative module bodies."""
from __future__ import annotations

from levelclassifier.classifier import classify_lines


def test_pure_mainstream_singing_figure_stays_ms_high_confidence():
    lines = [
        "Heads Square Thru 4,",
        "Dosado,",
        "Swing Thru,",
        "Boys Run Right,",
        "Ferris Wheel,",
        "Centers Pass Thru,",
        "Touch 1/4,",
        "Scoot Back,",
        "Single Hinge,",
        "Swing & Promenade",
    ]
    c = classify_lines(lines)
    assert c.detected_level == "ms"
    assert c.confidence == "high"
    assert c.unknown_tokens == []


def test_spin_the_top_remains_mainstream():
    # Spin the Top is MS (#34); must NOT be confused with Spin Chain Thru.
    c = classify_lines(["Spin The Top,", "Right & Left Thru"])
    assert c.detected_level == "ms"


def test_removed_call_eight_chain_thru_flips_to_plus():
    c = classify_lines(["Heads Eight Chain Thru,", "Swing & Promenade"])
    assert c.detected_level == "plus"
    assert c.confidence == "high"
    assert "eight chain thru" in c.deciding_call


def test_denylist_calls_detected_as_plus():
    for call in [
        "Turn Thru", "Spin Chain Thru", "Walk And Dodge", "Dixie Style",
        "Do Paso", "See Saw", "Cloverleaf", "Pass To The Center",
        "Walk Around The Corner", "Fan The Top",
    ]:
        c = classify_lines([call])
        assert c.detected_level == "plus", f"{call} -> {c.detected_level}"


def test_walk_and_dodge_designator_variants_are_plus():
    # Real phrasings from the vault: space-joined, comma-separated, "&"-joined,
    # singular designators, and "backward" interleaved. All are Plus.
    for call in [
        "Boys Walk Girls Dodge",
        "Girls Walk Boys Dodge",
        "Boys Walk, Girls Dodge,",
        "Girls Walk, Boys Dodge,",
        "Boys Walk & Girls Dodge,",
        "Girls Walk & Boys Dodge",
        "Boy Walk, Girl Dodge,",
        "Girl Walk, Boy Dodge,",
        "Same 4 Girls Walk, Boys Dodge,",
        "Boys Backward Walk & Girls Dodge,",
    ]:
        c = classify_lines([call])
        assert c.detected_level == "plus", f"{call} -> {c.detected_level}"
        assert c.confidence == "high"
        assert "walk" not in c.unknown_tokens and "dodge" not in c.unknown_tokens


def test_plain_walk_and_dodge_still_plus():
    c = classify_lines(["Walk and Dodge"])
    assert c.detected_level == "plus"
    assert c.confidence == "high"


def test_interleaved_walk_dodge_not_triggered_by_unrelated_dodge_call():
    # "Scoot and Dodge" is its own Plus call; a "walk" elsewhere on the line
    # must NOT be joined to its "dodge" to fabricate a Walk & Dodge.
    c = classify_lines(["Boys Walk, Scoot and Dodge"])
    assert c.detected_level == "plus"
    assert "scoot and dodge" in [h.phrase for h in c.hits]
    assert "walk & dodge" not in [h.phrase for h in c.hits]
    # The orphan "walk" (no dodge partner) is surfaced, not silently absorbed.
    assert "walk" in c.unknown_tokens


def test_interleaved_gap_broken_by_real_call_word():
    # A real call word between walk and dodge breaks the interleaved match.
    c = classify_lines(["Girls Walk, Boys Run, Scoot and Dodge"])
    assert "walk & dodge" not in [h.phrase for h in c.hits]


def test_see_saw_not_matched_by_sashay_or_dosado():
    c = classify_lines(["Heads Half Sashay,", "Dosado"])
    assert c.detected_level == "ms"


def test_circle_to_a_line_is_plus_but_circle_left_is_ms():
    assert classify_lines(["Heads Lead Right, Circle To A Line"]).detected_level == "plus"
    assert classify_lines(["Circle Left"]).detected_level == "ms"


def test_a1_call_lockit_detected():
    c = classify_lines(["Step To A Wave,", "Lockit,", "Recycle"])
    assert c.detected_level == "a1"
    assert c.deciding_call == "lockit"


def test_a2_call_motivate_detected():
    c = classify_lines(["Swing Thru,", "Motivate,", "Boys Run"])
    assert c.detected_level == "a2"


def test_highest_level_wins():
    # Contains MS, Plus and A1 calls -> A1.
    c = classify_lines(["Square Thru 4,", "Spin Chain Thru,", "Lockit"])
    assert c.detected_level == "a1"


def test_unknown_token_lowers_confidence_for_ms():
    c = classify_lines(["Heads Frobnicate The Gizmo"])
    assert c.detected_level == "ms"
    assert c.confidence == "low"
    assert "frobnicate" in c.unknown_tokens


def test_eight_chain_down_the_line_is_not_the_plus_call():
    # "Center Eight Chain Down The Line & Backaway" must NOT match the Plus
    # call "Eight Chain Thru".
    c = classify_lines(["Center Eight Chain Down The Line & Backaway,", "Others Bend The Line"])
    assert c.detected_level == "ms"


def test_eight_chain_thru_and_numbered_forms_are_plus():
    assert classify_lines(["Heads Eight Chain Thru"]).detected_level == "plus"
    assert classify_lines(["Heads Eight Chain 4"]).detected_level == "plus"


def test_slither_inside_parenthetical_aside_is_ignored():
    # A2 call name appearing only inside an explanatory parenthetical with an
    # internal comma must not flip the module.
    c = classify_lines(
        ["3/4 Dosado, Boys Half Sashay (with each other.  i.e., Slither),", "Wheel & Deal"]
    )
    assert c.detected_level == "ms"


def test_genuine_partner_hinge_is_plus():
    c = classify_lines(["Pass Thru,", "Partner Hinge,", "Girls Trade,", "Recycle"])
    assert c.detected_level == "plus"
    assert c.deciding_call == "partner hinge"
