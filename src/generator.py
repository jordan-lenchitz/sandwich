"""
generator.py - Procedural song generation rules (100% pure Python).
"""

import random
from core import NAMES_FLAT, QUALITIES, parse_pitch_class, name_pitch, detect_key, get_diatonic_chords

def detect_chord_root(pcs: set[int]) -> int:
    """Guess the root of a chord. For simplicity, assume the lowest PC is the root or use simple heuristic."""
    if not pcs: return 0
    # Heuristic: if it looks like a major or minor triad, find the root
    sorted_pcs = sorted(list(pcs))
    for r in sorted_pcs:
        rel = set((p - r) % 12 for p in pcs)
        # Check if it contains 0 and 7 (root and fifth)
        if 0 in rel and 7 in rel:
            return r
    return min(pcs)

def rule_tritone_subs(vamp: list[set[int]]) -> list[set[int]]:
    """Substitute chords using tritone substitution logic."""
    new_vamp = []
    for pcs in vamp:
        root = detect_chord_root(pcs)
        # Shift root by 6 semitones
        new_root = (root + 6) % 12
        new_pcs = set((p + 6) % 12 for p in pcs)
        new_vamp.append(new_pcs)
    return new_vamp

def rule_relative_key(vamp: list[set[int]]) -> list[set[int]]:
    """Shift the harmony to the relative major/minor (up or down 3 semitones)."""
    shift = 3 if random.random() > 0.5 else -3
    return [set((p + shift) % 12 for p in pcs) for pcs in vamp]

def rule_modal_mixture(vamp: list[set[int]]) -> list[set[int]]:
    """Borrow chords from parallel key by flattening 3rd, 6th, or 7th."""
    new_vamp = []
    for pcs in vamp:
        # Simple heuristic: if it has a 4 (maj 3rd), make it a 3 (min 3rd)
        root = detect_chord_root(pcs)
        rel = set((p - root) % 12 for p in pcs)
        if 4 in rel:
            rel.remove(4)
            rel.add(3)
        new_vamp.append(set((r + root) % 12 for r in rel))
    return new_vamp

def rule_pedal_point(vamp: list[set[int]]) -> list[set[int]]:
    """Force the first chord's root to be the bass for all chords."""
    if not vamp: return []
    pedal = detect_chord_root(vamp[0])
    new_vamp = []
    for pcs in vamp:
        new_pcs = set(pcs)
        new_pcs.add(pedal)
        new_vamp.append(new_pcs)
    return new_vamp

def rule_secondary_dominants(vamp: list[set[int]]) -> list[set[int]]:
    """Insert a V7 chord before every second chord."""
    new_vamp = []
    for i, pcs in enumerate(vamp):
        if i > 0 and i % 2 == 1:
            target_root = detect_chord_root(pcs)
            dom_root = (target_root + 7) % 12
            dom_pcs = set((dom_root + iv) % 12 for iv in QUALITIES["7"])
            new_vamp.append(dom_pcs)
        new_vamp.append(pcs)
    return new_vamp[:len(vamp)] # Keep length same or slightly expanded? Plan said 4-8.

def rule_chromatic_passing(vamp: list[set[int]]) -> list[set[int]]:
    """Insert chromatic passing chords between chords."""
    new_vamp = []
    for i in range(len(vamp) - 1):
        new_vamp.append(vamp[i])
        r1 = detect_chord_root(vamp[i])
        r2 = detect_chord_root(vamp[i+1])
        if abs(r1 - r2) > 1:
            step = 1 if r2 > r1 else -1
            passing_root = (r1 + step) % 12
            passing_pcs = set((p + step) % 12 for p in vamp[i])
            new_vamp.append(passing_pcs)
    new_vamp.append(vamp[-1])
    return new_vamp[:len(vamp)]

def rule_backdoor_sub(vamp: list[set[int]]) -> list[set[int]]:
    """Replace chords with bVII7 chords relative to the guessed key."""
    new_vamp = []
    # Simplified: replace every other chord root with root + 10
    for i, pcs in enumerate(vamp):
        if i % 2 == 1:
            root = detect_chord_root(pcs)
            new_root = (root + 10) % 12
            new_pcs = set((new_root + iv) % 12 for iv in QUALITIES["7"])
            new_vamp.append(new_pcs)
        else:
            new_vamp.append(pcs)
    return new_vamp

def rule_diminished_approach(vamp: list[set[int]]) -> list[set[int]]:
    """Replace chords with diminished chords a half step below."""
    new_vamp = []
    for pcs in vamp:
        root = detect_chord_root(pcs)
        dim_root = (root - 1) % 12
        dim_pcs = set((dim_root + iv) % 12 for iv in QUALITIES["dim7"])
        new_vamp.append(dim_pcs)
    return new_vamp

def rule_sus_substitution(vamp: list[set[int]]) -> list[set[int]]:
    """Convert major/minor triads to sus4."""
    new_vamp = []
    for pcs in vamp:
        root = detect_chord_root(pcs)
        rel = set((p - root) % 12 for p in pcs)
        if 3 in rel: rel.remove(3)
        if 4 in rel: rel.remove(4)
        rel.add(5) # Add perfect fourth
        new_vamp.append(set((r + root) % 12 for r in rel))
    return new_vamp

def rule_harmonic_extensions(vamp: list[set[int]]) -> list[set[int]]:
    """Add 9ths or 11ths."""
    new_vamp = []
    for pcs in vamp:
        root = detect_chord_root(pcs)
        new_pcs = set(pcs)
        new_pcs.add((root + 2) % 12) # 9th
        if random.random() > 0.5:
            new_pcs.add((root + 5) % 12) # 11th
        new_vamp.append(new_pcs)
    return new_vamp

def rule_coltrane_changes(vamp: list[set[int]]) -> list[set[int]]:
    """Insert major thirds cycle (Giant Steps style)."""
    if len(vamp) < 3: return vamp
    root = detect_chord_root(vamp[0])
    # Cycle: Root, Root+4, Root+8
    c1 = set((root + iv) % 12 for iv in QUALITIES["maj7"])
    c2 = set(((root + 4) % 12 + iv) % 12 for iv in QUALITIES["maj7"])
    c3 = set(((root + 8) % 12 + iv) % 12 for iv in QUALITIES["maj7"])
    new_vamp = [c1, c2, c3]
    while len(new_vamp) < len(vamp):
        new_vamp.append(random.choice([c1, c2, c3]))
    return new_vamp

def rule_neapolitan(vamp: list[set[int]]) -> list[set[int]]:
    """Insert bII major chord."""
    new_vamp = []
    for pcs in vamp:
        root = detect_chord_root(pcs)
        b2_root = (root + 1) % 12
        b2_pcs = set((b2_root + iv) % 12 for iv in QUALITIES["maj"])
        new_vamp.append(b2_pcs)
    return new_vamp

def rule_constant_structure(vamp: list[set[int]]) -> list[set[int]]:
    """All chords become the same quality (e.g. m9)."""
    quality = random.choice(list(QUALITIES.keys()))
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
    """Pick 2 random rules and apply them."""
    selected = random.sample(RULES, 2)
    current_vamp = vamp
    applied_names = []
    for name, func in selected:
        current_vamp = func(current_vamp)
        applied_names.append(name)
    return current_vamp, applied_names

def generate_song(vamp: list[set[int]], form: str) -> dict:
    """Generate a full song based on form A, B, C, D, E."""
    sections = {'A': (vamp, ["Original Vamp"])}
    unique_sections = set(form.upper()) - {'A'}
    for s in sorted(list(unique_sections)):
        if s in 'BCDE':
            sections[s] = generate_section(vamp)
    
    song_data = []
    for char in form.upper():
        if char in sections:
            song_data.append({
                "section": char,
                "vamp": sections[char][0],
                "rules": sections[char][1]
            })
    return song_data
