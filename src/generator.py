"""
generator.py - Procedural song generation rules (100% pure Python).
"""

import random
from typing import Optional
from core import QUALITIES, infer_root


def detect_chord_root(pcs: set[int]) -> int:
    """Guess the root of a chord using tertian interval scoring."""
    return infer_root(pcs)


def rule_tritone_subs(vamp: list[set[int]]) -> list[set[int]]:
    """Substitute dominant/cadential chords (or alternating bars) with their tritone substitution."""
    new_vamp = []
    for i, pcs in enumerate(vamp):
        # Substitute every second chord (or all if single-chord vamp) so harmonic contrast is preserved
        if len(vamp) == 1 or i % 2 == 1:
            new_pcs = set((p + 6) % 12 for p in pcs)
            new_vamp.append(new_pcs)
        else:
            new_vamp.append(set(pcs))
    return new_vamp


def rule_relative_key(vamp: list[set[int]]) -> list[set[int]]:
    """Shift the harmony to the relative major/minor (up or down 3 semitones)."""
    shift = 3 if random.random() > 0.5 else -3
    return [set((p + shift) % 12 for p in pcs) for pcs in vamp]


def rule_modal_mixture(vamp: list[set[int]]) -> list[set[int]]:
    """Borrow chords from parallel key by inflecting the 3rd between major and minor."""
    new_vamp = []
    for pcs in vamp:
        root = detect_chord_root(pcs)
        rel = set((p - root) % 12 for p in pcs)
        if 4 in rel:
            rel.remove(4)
            rel.add(3)
        elif 3 in rel:
            rel.remove(3)
            rel.add(4)
        new_vamp.append(set((r + root) % 12 for r in rel))
    return new_vamp


def rule_pedal_point(vamp: list[set[int]]) -> list[set[int]]:
    """Force the first chord's root to be present across all chords."""
    if not vamp:
        return []
    pedal = detect_chord_root(vamp[0])
    new_vamp = []
    for pcs in vamp:
        new_pcs = set(pcs)
        new_pcs.add(pedal)
        new_vamp.append(new_pcs)
    return new_vamp


def rule_secondary_dominants(vamp: list[set[int]]) -> list[set[int]]:
    """Replace weak-beat chords with the secondary dominant (V7) of the following chord."""
    if len(vamp) < 2:
        return list(vamp)
    new_vamp = []
    n = len(vamp)
    for i, pcs in enumerate(vamp):
        if i % 2 == 1:
            target_pcs = vamp[(i + 1) % n]
            target_root = detect_chord_root(target_pcs)
            dom_root = (target_root + 7) % 12
            dom_pcs = set((dom_root + iv) % 12 for iv in QUALITIES["7"])
            new_vamp.append(dom_pcs)
        else:
            new_vamp.append(set(pcs))
    return new_vamp


def rule_chromatic_passing(vamp: list[set[int]]) -> list[set[int]]:
    """Create chromatic planing/passing approach on weak bars toward the next structural chord."""
    if len(vamp) < 2:
        return list(vamp)
    new_vamp = []
    n = len(vamp)
    for i, pcs in enumerate(vamp):
        if i % 2 == 1:
            next_pcs = vamp[(i + 1) % n]
            r_curr = detect_chord_root(pcs)
            r_next = detect_chord_root(next_pcs)
            step = -1 if ((r_next - r_curr) % 12) <= 6 else 1
            passing_pcs = set((p + step) % 12 for p in next_pcs)
            new_vamp.append(passing_pcs)
        else:
            new_vamp.append(set(pcs))
    return new_vamp


def rule_backdoor_sub(vamp: list[set[int]]) -> list[set[int]]:
    """Replace cadential/even-numbered bars with bVII7 backdoor dominant chords."""
    new_vamp = []
    n = len(vamp)
    for i, pcs in enumerate(vamp):
        if i % 2 == 1:
            target_root = detect_chord_root(vamp[(i + 1) % n])
            bvii_root = (target_root + 10) % 12
            new_pcs = set((bvii_root + iv) % 12 for iv in QUALITIES["7"])
            new_vamp.append(new_pcs)
        else:
            new_vamp.append(set(pcs))
    return new_vamp


def rule_diminished_approach(vamp: list[set[int]]) -> list[set[int]]:
    """Substitute weak-beat chords with a leading-tone dim7 approach a half-step below the next root."""
    if not vamp:
        return []
    new_vamp = []
    n = len(vamp)
    for i, pcs in enumerate(vamp):
        if len(vamp) == 1 or i % 2 == 1:
            target_root = detect_chord_root(vamp[(i + 1) % n])
            dim_root = (target_root - 1) % 12
            dim_pcs = set((dim_root + iv) % 12 for iv in QUALITIES["dim7"])
            new_vamp.append(dim_pcs)
        else:
            new_vamp.append(set(pcs))
    return new_vamp


def rule_sus_substitution(vamp: list[set[int]]) -> list[set[int]]:
    """Convert major/minor thirds to sus4 voicings."""
    new_vamp = []
    for pcs in vamp:
        root = detect_chord_root(pcs)
        rel = set((p - root) % 12 for p in pcs)
        rel.discard(3)
        rel.discard(4)
        rel.add(5)  # Perfect fourth
        new_vamp.append(set((r + root) % 12 for r in rel))
    return new_vamp


def rule_harmonic_extensions(vamp: list[set[int]]) -> list[set[int]]:
    """Add 9ths (and occasional 11ths/13ths) for extended jazz harmony."""
    new_vamp = []
    for pcs in vamp:
        root = detect_chord_root(pcs)
        new_pcs = set(pcs)
        new_pcs.add((root + 2) % 12)  # 9th
        if random.random() > 0.5:
            new_pcs.add((root + 5) % 12)  # 11th
        new_vamp.append(new_pcs)
    return new_vamp


def rule_coltrane_changes(vamp: list[set[int]]) -> list[set[int]]:
    """Cycle tonic Centers by major thirds (Giant Steps augmented triad axis)."""
    if not vamp:
        return []
    root = detect_chord_root(vamp[0])
    centers = [root, (root + 4) % 12, (root + 8) % 12]
    new_vamp = []
    for i in range(len(vamp)):
        c_root = centers[i % 3]
        new_vamp.append(set((c_root + iv) % 12 for iv in QUALITIES["maj7"]))
    return new_vamp


def rule_neapolitan(vamp: list[set[int]]) -> list[set[int]]:
    """Introduce a Neapolitan (bII major) chord at cadential / turnaround bars."""
    if not vamp:
        return []
    new_vamp = [set(pcs) for pcs in vamp]
    tonic_root = detect_chord_root(vamp[0])
    b2_root = (tonic_root + 1) % 12
    b2_pcs = set((b2_root + iv) % 12 for iv in QUALITIES["maj"])

    # Place Neapolitan on the penultimate bar (or final bar if length <= 2)
    target_idx = max(0, len(new_vamp) - 2) if len(new_vamp) > 2 else len(new_vamp) - 1
    new_vamp[target_idx] = b2_pcs
    return new_vamp


def rule_constant_structure(vamp: list[set[int]]) -> list[set[int]]:
    """Plane a uniform chord quality across all chord roots in the vamp."""
    preferred_qualities = ["maj7", "m7", "7", "m9", "maj9", "7sus4", "m7b5", "quartal4"]
    quality = random.choice(preferred_qualities)
    new_vamp = []
    for pcs in vamp:
        root = detect_chord_root(pcs)
        new_pcs = set((root + iv) % 12 for iv in QUALITIES[quality])
        new_vamp.append(new_pcs)
    return new_vamp


RULES = [
    ("Tritone Subs", rule_tritone_subs),
    ("Relative Key", rule_relative_key),
    ("Modal Mixture", rule_modal_mixture),
    ("Pedal Point", rule_pedal_point),
    ("Secondary Dominants", rule_secondary_dominants),
    ("Chromatic Passing", rule_chromatic_passing),
    ("Backdoor Substitution", rule_backdoor_sub),
    ("Diminished Approach", rule_diminished_approach),
    ("Sus Substitution", rule_sus_substitution),
    ("Harmonic Extensions", rule_harmonic_extensions),
    ("Coltrane Changes", rule_coltrane_changes),
    ("Neapolitan Chord", rule_neapolitan),
    ("Constant Structure", rule_constant_structure),
]


def generate_section(vamp: list[set[int]]) -> tuple[list[set[int]], list[str]]:
    """Pick 2 distinct harmonic rules and apply them sequentially."""
    selected = random.sample(RULES, 2)
    current_vamp = [set(c) for c in vamp]
    applied_names = []
    for name, func in selected:
        current_vamp = func(current_vamp)
        applied_names.append(name)
    return current_vamp, applied_names


def generate_song(vamp: list[set[int]], form: str, seed: Optional[int] = None) -> list[dict]:
    """Generate a full song based on arbitrary section form letters (e.g. ABACABA)."""
    if seed is not None:
        random.seed(seed)

    clean_form = [ch.upper() for ch in form if ch.isalpha()]
    if not clean_form:
        raise ValueError(f"Invalid song form: {form!r}")

    sections = {"A": ([set(c) for c in vamp], ["Original Vamp"])}
    unique_sections = sorted(set(clean_form) - {"A"})
    for s in unique_sections:
        sections[s] = generate_section(vamp)

    song_data = []
    for char in clean_form:
        song_data.append({
            "section": char,
            "vamp": sections[char][0],
            "rules": sections[char][1],
        })
    return song_data
