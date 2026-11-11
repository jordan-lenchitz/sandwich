"""
core.py - Shared music theory primitives for the sandwich project.
"""

from typing import Optional

# Standard pitch class names
NAMES_FLAT = ["c", "db", "d", "eb", "e", "f", "gb", "g", "ab", "a", "bb", "b"]
NAMES_SHARP = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]

# Mapping of various pitch names to their pitch class (0-11)
PARSE_MAP = {
    "c": 0, "b#": 0, "dbb": 0,
    "c#": 1, "db": 1,
    "d": 2, "ebb": 2, "cx": 2,
    "d#": 3, "eb": 3, "fbb": 3,
    "e": 4, "fb": 4, "dx": 4,
    "f": 5, "e#": 5, "gbb": 5,
    "f#": 6, "gb": 6, "ex": 6,
    "g": 7, "abb": 7, "fx": 7,
    "g#": 8, "ab": 8,
    "a": 9, "bbb": 9, "gx": 9,
    "a#": 10, "bb": 10, "cbb": 10,
    "b": 11, "cb": 11, "ax": 11,
}

# Chord quality library: intervals from root in semitones.
QUALITIES = {
    "maj":      (0, 4, 7),
    "min":      (0, 3, 7),
    "dim":      (0, 3, 6),
    "aug":      (0, 4, 8),
    "sus2":     (0, 2, 7),
    "sus4":     (0, 5, 7),
    "maj7":     (0, 4, 7, 11),
    "m7":       (0, 3, 7, 10),
    "7":        (0, 4, 7, 10),
    "m7b5":     (0, 3, 6, 10),
    "dim7":     (0, 3, 6, 9),
    "mmaj7":    (0, 3, 7, 11),
    "augmaj7":  (0, 4, 8, 11),
    "aug7":     (0, 4, 8, 10),
    "7sus4":    (0, 5, 7, 10),
    "6":        (0, 4, 7, 9),
    "m6":       (0, 3, 7, 9),
    "9":        (0, 4, 7, 10, 2),
    "m9":       (0, 3, 7, 10, 2),
    "maj9":     (0, 4, 7, 11, 2),
    "quartal3": (0, 5, 10),
    "quartal4": (0, 5, 10, 15 % 12),
}

QUALITY_DEGREES = {
    "maj": (0, 2, 4),
    "min": (0, 2, 4),
    "dim": (0, 2, 4),
    "aug": (0, 2, 4),
    "sus2": (0, 1, 4),
    "sus4": (0, 3, 4),
    "maj7": (0, 2, 4, 6),
    "m7": (0, 2, 4, 6),
    "7": (0, 2, 4, 6),
    "m7b5": (0, 2, 4, 6),
    "dim7": (0, 2, 4, 6),
    "mmaj7": (0, 2, 4, 6),
    "augmaj7": (0, 2, 4, 6),
    "aug7": (0, 2, 4, 6),
    "7sus4": (0, 3, 4, 6),
    "6": (0, 2, 4, 5),
    "m6": (0, 2, 4, 5),
    "9": (0, 2, 4, 6, 1),
    "m9": (0, 2, 4, 6, 1),
    "maj9": (0, 2, 4, 6, 1),
    "quartal3": (0, 3, 6),
    "quartal4": (0, 3, 6, 2),
}

# Scale library: intervals from root
SCALES = {
    "major":            (0, 2, 4, 5, 7, 9, 11),
    "natural_minor":    (0, 2, 3, 5, 7, 8, 10),
    "harmonic_minor":   (0, 2, 3, 5, 7, 8, 11),
    "melodic_minor":    (0, 2, 3, 5, 7, 9, 11),
    "dorian":           (0, 2, 3, 5, 7, 9, 10),
    "phrygian":         (0, 1, 3, 5, 7, 8, 10),
    "lydian":           (0, 2, 4, 6, 7, 9, 11),
    "mixolydian":       (0, 2, 4, 5, 7, 9, 10),
    "locrian":          (0, 1, 3, 5, 6, 8, 10),
    "pentatonic_maj":   (0, 2, 4, 7, 9),
    "pentatonic_min":   (0, 3, 5, 7, 10),
    "blues":            (0, 3, 5, 6, 7, 10),
    "whole_tone":       (0, 2, 4, 6, 8, 10),
}

SCALE_ALIASES = {
    "maj": "major",
    "ionian": "major",
    "m": "natural_minor",
    "min": "natural_minor",
    "minor": "natural_minor",
    "aeolian": "natural_minor",
    "natural-minor": "natural_minor",
    "harmonic-minor": "harmonic_minor",
    "harm_minor": "harmonic_minor",
    "melodic-minor": "melodic_minor",
    "mel_minor": "melodic_minor",
    "pentatonic_major": "pentatonic_maj",
    "maj_pentatonic": "pentatonic_maj",
    "pentatonic_minor": "pentatonic_min",
    "min_pentatonic": "pentatonic_min",
    "whole-tone": "whole_tone",
}

# Rhythmic patterns: list of (offset, duration) in quarter notes
RHYTHMS = {
    "four-on-the-floor": [(0, 1), (1, 1), (2, 1), (3, 1)],
    "bossa": [(0, 1.5), (1.5, 1.5), (3, 1)],
    "swing": [(0, 1.5), (1.5, 0.5), (2, 1.5), (3.5, 0.5)],
    "waltz": [(0, 1), (1, 1), (2, 1)],  # 3/4
}


def normalize_scale_name(scale: str) -> str:
    """Normalize user-supplied scale names (e.g. 'minor' -> 'natural_minor')."""
    s = scale.strip().lower().replace(" ", "_")
    s = SCALE_ALIASES.get(s, s)
    if s not in SCALES:
        raise ValueError(f"Unknown scale: {scale!r}. Available: {', '.join(SCALES.keys())}")
    return s


def parse_pitch_class(token: str) -> int:
    """Parse a pitch name (e.g., 'C#', 'Bb', or 'c4') into a pitch class (0-11)."""
    t = token.strip().lower()
    if t in PARSE_MAP:
        return PARSE_MAP[t]
    # Also support stripping trailing octave/duration if passed a note token like 'c#4'
    i = 0
    while i < len(t) and not t[i].isdigit() and t[i] != ":":
        i += 1
    if 0 < i < len(t):
        prefix = t[:i]
        rest = t[i:]
        if prefix in PARSE_MAP and (rest[0].isdigit() or rest[0] == ":"):
            return PARSE_MAP[prefix]
    raise ValueError(f"Could not parse pitch class: {token!r}")


def parse_key_string(s: str) -> dict:
    """
    Parse a key string such as 'C major', 'g# minor', 'f#m', 'Eb', 'Bb dorian'
    into {'root': int, 'scale': str, 'name': str, 'root_name': str}.
    """
    raw = s.strip()
    if not raw:
        raise ValueError("Empty key string")
    parts = raw.split()
    if len(parts) == 1:
        tok = parts[0]
        # Handle compact minor/major notation like 'f#m', 'cm', 'AbM'
        if len(tok) > 1 and tok.endswith("m") and tok[:-1].lower() in PARSE_MAP:
            root_tok = tok[:-1]
            scale = "natural_minor"
        elif len(tok) > 1 and tok.endswith("M") and tok[:-1].lower() in PARSE_MAP:
            root_tok = tok[:-1]
            scale = "major"
        else:
            root_tok = tok
            scale = "major"
    else:
        root_tok = parts[0]
        scale = normalize_scale_name(" ".join(parts[1:]))

    root = parse_pitch_class(root_tok)
    display_scale = "minor" if scale == "natural_minor" else scale
    return {
        "root": root,
        "root_name": root_tok.lower(),
        "scale": scale,
        "name": f"{root_tok} {display_scale}",
    }


def name_pitch(pc: int, prefer_sharps: bool = False) -> str:
    """Return the name of a pitch class."""
    return NAMES_SHARP[pc % 12] if prefer_sharps else NAMES_FLAT[pc % 12]


def name_pitch_with_octave(midi_pitch: int, prefer_sharps: bool = False) -> str:
    """Return the name of a MIDI pitch with octave (e.g., C4)."""
    pc = midi_pitch % 12
    octave = (midi_pitch // 12) - 1
    return f"{name_pitch(pc, prefer_sharps)}{octave}"


def name_voicing(voicing: list[int], prefer_sharps: bool = False) -> str:
    """Return a string naming all pitches in a voicing."""
    return " ".join(name_pitch_with_octave(p, prefer_sharps) for p in voicing)


def get_spelled_pitch(root_name: str, degree_offset: int, target_pc: int) -> str:
    """Determine the correct tertian spelling for a pitch based on root and degree."""
    letters = ["c", "d", "e", "f", "g", "a", "b"]
    natural_pcs = [0, 2, 4, 5, 7, 9, 11]

    root_letter = root_name[0].lower()
    root_letter_idx = letters.index(root_letter)

    target_letter_idx = (root_letter_idx + degree_offset) % 7
    target_letter = letters[target_letter_idx]
    target_natural_pc = natural_pcs[target_letter_idx]

    diff = (target_pc - target_natural_pc) % 12
    if diff > 6:
        diff -= 12

    if diff == 0:
        return target_letter
    if diff == 1:
        return target_letter + "#"
    if diff == 2:
        return target_letter + "x"
    if diff == -1:
        return target_letter + "b"
    if diff == -2:
        return target_letter + "bb"
    return target_letter + ("?" * abs(diff))


def spell_chord(root_name: str, quality: str, pcs: set[int]) -> str:
    """Spell a chord correctly using its quality's tertian structure."""
    if quality not in QUALITY_DEGREES or quality not in QUALITIES:
        return " ".join(NAMES_FLAT[p] for p in sorted(pcs))

    degrees = QUALITY_DEGREES[quality]
    intervals = QUALITIES[quality]
    root_pc = parse_pitch_class(root_name)

    spelled = []
    for i in range(len(degrees)):
        target_pc = (root_pc + intervals[i]) % 12
        spelled.append(get_spelled_pitch(root_name, degrees[i], target_pc))
    return " ".join(spelled)


def infer_root(pcs: set[int]) -> int:
    """Guess the root of a pitch class set using tertian heuristics."""
    if not pcs:
        return 0
    scores = {}
    for r in pcs:
        intervals = {(p - r) % 12 for p in pcs}
        score = 0
        if 7 in intervals:
            score += 10  # Perfect fifth
        if 4 in intervals:
            score += 5   # Major third
        if 3 in intervals:
            score += 5   # Minor third
        if 10 in intervals:
            score += 3   # Minor seventh
        if 11 in intervals:
            score += 3   # Major seventh
        if 2 in intervals:
            score += 1   # Ninth
        if 5 in intervals:
            score += 1   # Fourth/Eleventh
        if 9 in intervals:
            score += 1   # Sixth/Thirteenth
        scores[r] = score
    return max(sorted(scores.keys()), key=lambda k: scores[k])


def format_chord_symbol(root_pc: int, quality: str, prefer_sharps: bool = False) -> str:
    """Format a compact chord symbol (e.g., c, cm, g7, abmaj7)."""
    r_name = name_pitch(root_pc, prefer_sharps=prefer_sharps)
    if quality == "maj":
        return r_name
    if quality == "min":
        return f"{r_name}m"
    return f"{r_name}{quality}"


def identify_chord(pcs: set[int], preferred_root: Optional[int] = None) -> dict:
    """
    Identify a pitch-class set as a named chord (root, quality, symbol, spelling).
    Falls back to inferred root + extension description if not an exact library match.
    """
    if not pcs:
        return {"root": 0, "quality": "maj", "symbol": "n.c.", "spelling": ""}

    norm_pcs = {p % 12 for p in pcs}
    inferred = preferred_root if preferred_root is not None else infer_root(norm_pcs)

    # Check exact quality match on inferred root first, then other roots in pcs
    roots_to_try = [inferred] + [r for r in sorted(norm_pcs) if r != inferred]
    for r in roots_to_try:
        rel = {(p - r) % 12 for p in norm_pcs}
        for q_name, intervals in QUALITIES.items():
            if rel == {iv % 12 for iv in intervals}:
                r_name = NAMES_FLAT[r]
                return {
                    "root": r,
                    "quality": q_name,
                    "symbol": format_chord_symbol(r, q_name),
                    "spelling": spell_chord(r_name, q_name, norm_pcs),
                }

    # Fallback: identify core triad/seventh on inferred root
    rel = {(p - inferred) % 12 for p in norm_pcs}
    base_q = "maj"
    if 3 in rel and 4 not in rel:
        base_q = "m7" if 10 in rel else ("dim7" if 9 in rel and 6 in rel else ("dim" if 6 in rel else "min"))
    elif 4 in rel:
        base_q = "maj7" if 11 in rel else ("7" if 10 in rel else "maj")
    elif 5 in rel:
        base_q = "7sus4" if 10 in rel else "sus4"

    symbol = format_chord_symbol(inferred, base_q)
    return {
        "root": inferred,
        "quality": base_q,
        "symbol": symbol,
        "spelling": " ".join(NAMES_FLAT[p] for p in sorted(norm_pcs)),
    }


def parse_chord(s: str) -> set[int]:
    """Parse a space or comma separated chord string into a set of pitch classes."""
    if "," in s:
        tokens = [t for t in s.split(",") if t.strip()]
    else:
        tokens = s.split()
    return set(parse_pitch_class(t) for t in tokens)


def parse_vamp(s: str) -> list[set[int]]:
    """Parse a vamp string (chords separated by '|') into a list of pitch class sets."""
    if "|" in s:
        chunks = s.split("|")
    else:
        chunks = s.split(",")
    vamp = [parse_chord(c.strip()) for c in chunks if c.strip()]
    if not vamp:
        raise ValueError("No chords found in vamp input")
    return vamp


def name_pitch_set(pcs: set[int], root_name: Optional[str] = None, quality: Optional[str] = None) -> str:
    """Return a spelled or flat-spelled, sorted string of pitch class names."""
    if root_name and quality:
        return spell_chord(root_name, quality, pcs)
    return " ".join(NAMES_FLAT[p % 12] for p in sorted(pcs))


def detect_key(pitches: list[int]) -> list[dict]:
    """
    Detect the most likely key/scale based on a list of pitches.
    Scores candidates by pitch coverage, scale utilization, tonic triad presence,
    and boundary (first/last) pitch weighting.
    """
    if not pitches:
        return []

    norm_pitches = [p % 12 for p in pitches]
    unique_pcs = set(norm_pitches)
    first_pc = norm_pitches[0]
    last_pc = norm_pitches[-1]
    results = []

    for root in range(12):
        for scale_name, intervals in SCALES.items():
            scale_pcs = set((root + iv) % 12 for iv in intervals)
            matches = unique_pcs.intersection(scale_pcs)

            # Primary metric: proportion of unique input pitches that fit the scale
            in_scale_ratio = len(matches) / len(unique_pcs) if unique_pcs else 0.0

            # Secondary metric: how much of the scale is utilized by the input
            scale_coverage = len(matches) / len(scale_pcs) if scale_pcs else 0.0

            # Small tie-breaking musical weights so 3-note triads don't score 1.00 across 20 scales
            bonus = 0.0
            if scale_name in ("major", "natural_minor"):
                bonus += 0.04
            elif len(intervals) == 7:
                bonus += 0.02
            if root in unique_pcs:
                bonus += 0.015
            if root == first_pc:
                bonus += 0.015
            if root == last_pc:
                bonus += 0.015
            # Check tonic triad presence
            third_pc = (root + (4 if 4 in intervals else 3)) % 12
            fifth_pc = (root + 7) % 12
            if {root, third_pc, fifth_pc}.issubset(unique_pcs):
                bonus += 0.02

            score = (0.90 * in_scale_ratio) + (0.10 * scale_coverage) + bonus
            results.append({
                "root": root,
                "scale": scale_name,
                "score": score,
                "in_scale_ratio": in_scale_ratio,
                "name": f"{name_pitch(root)} {scale_name}",
            })

    return sorted(results, key=lambda x: (-x["score"], x["root"]))


def get_diatonic_chords(root: int, scale_name: str, include_secondary: bool = False) -> list[dict]:
    """
    Return basic diatonic triads for a given key/scale.
    Supports major, natural_minor, harmonic_minor, melodic_minor, and church modes.
    If include_secondary is True, also adds V7/x chords.
    """
    try:
        scale_name = normalize_scale_name(scale_name)
    except ValueError:
        return []

    intervals = SCALES[scale_name]
    if len(intervals) != 7:
        return []

    chords = []
    roman_base = ["I", "II", "III", "IV", "V", "VI", "VII"]
    major_iv = SCALES["major"]

    for i in range(7):
        chord_root = (root + intervals[i]) % 12
        third_pc = (root + intervals[(i + 2) % 7]) % 12
        fifth_pc = (root + intervals[(i + 4) % 7]) % 12
        pcs = {chord_root, third_pc, fifth_pc}

        third_iv = (third_pc - chord_root) % 12
        fifth_iv = (fifth_pc - chord_root) % 12

        if third_iv == 4 and fifth_iv == 7:
            quality = "maj"
        elif third_iv == 3 and fifth_iv == 7:
            quality = "min"
        elif third_iv == 3 and fifth_iv == 6:
            quality = "dim"
        elif third_iv == 4 and fifth_iv == 8:
            quality = "aug"
        else:
            quality = "maj"

        # Accidental prefix relative to major scale (except standard natural_minor convention)
        prefix = ""
        if scale_name not in ("major", "natural_minor"):
            diff = intervals[i] - major_iv[i]
            if diff == -1:
                prefix = "b"
            elif diff == 1:
                prefix = "#"

        r_num = roman_base[i]
        if quality in ("min", "dim"):
            r_num = r_num.lower()
        if quality == "dim":
            r_num += "°"
        elif quality == "aug":
            r_num += "+"

        label = prefix + r_num
        chords.append({
            "roman": label,
            "degree": i + 1,
            "root": chord_root,
            "quality": quality,
            "name": f"{name_pitch(chord_root)}{quality if quality != 'maj' else ''}",
            "pcs": pcs,
        })

    if include_secondary:
        for i in range(1, len(chords)):
            if chords[i]["quality"] in ("dim", "aug"):
                continue
            target_root = chords[i]["root"]
            dom_root = (target_root + 7) % 12
            chords.append({
                "roman": f"V7/{chords[i]['roman']}",
                "degree": i + 1,
                "root": dom_root,
                "quality": "7",
                "name": f"{name_pitch(dom_root)}7",
                "pcs": set((dom_root + iv) % 12 for iv in QUALITIES["7"]),
            })

    return chords


# Harmonic function profiles per scale degree (0-indexed) based on Lenchitz (2017)
DEGREE_FUNCTIONS_MAJOR = [
    ("T", "T"),       # 1
    ("P", "P"),       # 2
    ("T", "T"),       # 3
    ("P", "P"),       # 4
    ("D", "D [T]"),   # 5
    ("P", "P [T]"),   # 6
    ("D", "D"),       # 7
]

DEGREE_FUNCTIONS_MINOR = [
    ("T", "T"),       # 1
    ("P", "P"),       # 2
    ("T", "T [D]"),   # b3
    ("P", "P [T]"),   # 4
    ("D", "D [T]"),   # 5
    ("P", "P [T]"),   # b6
    ("D", "D [P]"),   # b7
]


def _get_pitch_function_map(root: int, scale_name: str) -> dict[int, dict]:
    """Map each pitch class in a 7-note key to its scale degree and harmonic function (T, P, D)."""
    scale_name = normalize_scale_name(scale_name)
    intervals = SCALES.get(scale_name, SCALES["major"])
    if len(intervals) != 7:
        intervals = SCALES["major"]

    is_minor = 3 in intervals
    func_table = DEGREE_FUNCTIONS_MINOR if is_minor else DEGREE_FUNCTIONS_MAJOR
    out = {}
    for deg_idx, iv in enumerate(intervals):
        pc = (root + iv) % 12
        primary, detailed = func_table[deg_idx]
        out[pc] = {
            "degree": deg_idx + 1,
            "primary": primary,
            "detailed": detailed,
        }
    return out


def suggest_modulation(start_key: dict, end_key: dict) -> dict:
    """
    Suggest paths for modulating between two keys:
    - Diatonic pivot chords
    - Dominant (V7) and Tritone-Sub (bII7) approaches
    - Functional voice-leading across common tones (T / P / D exchange, per Lenchitz 2017)
    """
    s_scale = normalize_scale_name(start_key.get("scale", "major"))
    e_scale = normalize_scale_name(end_key.get("scale", "major"))
    s_root = start_key["root"] % 12
    e_root = end_key["root"] % 12

    start_chords = get_diatonic_chords(s_root, s_scale)
    end_chords = get_diatonic_chords(e_root, e_scale)

    pivots = []
    for sc in start_chords:
        for ec in end_chords:
            if sc["pcs"] == ec["pcs"]:
                pivots.append({
                    "name": sc["name"],
                    "roman_start": sc["roman"],
                    "roman_end": ec["roman"],
                })

    target_v7_root = (e_root + 7) % 12
    target_v7_pcs = set((target_v7_root + iv) % 12 for iv in QUALITIES["7"])

    tritone_sub_root = (target_v7_root + 6) % 12
    tritone_sub_pcs = set((tritone_sub_root + iv) % 12 for iv in QUALITIES["7"])

    # Functional voice-leading of shared diatonic pitches
    s_funcs = _get_pitch_function_map(s_root, s_scale)
    e_funcs = _get_pitch_function_map(e_root, e_scale)
    shared_pcs = sorted(set(s_funcs.keys()) & set(e_funcs.keys()))

    common_tones = []
    preserved_count = 0
    for pc in shared_pcs:
        sf = s_funcs[pc]
        ef = e_funcs[pc]
        same_func = sf["primary"] == ef["primary"]
        if same_func:
            preserved_count += 1
        common_tones.append({
            "pc": pc,
            "pitch": name_pitch(pc).upper(),
            "degree_start": sf["degree"],
            "degree_end": ef["degree"],
            "func_start": sf["detailed"],
            "func_end": ef["detailed"],
            "shift": f"{sf['primary']} -> {ef['primary']}",
            "preserved": same_func,
        })

    if len(shared_pcs) >= 6:
        smoothness = "maximally smooth (closely related / relative collection)"
    elif len(shared_pcs) >= 4:
        smoothness = "moderately smooth"
    elif len(shared_pcs) <= 2 and preserved_count == 0:
        smoothness = "minimally smooth (Kapustin-style functional exchange)"
    else:
        smoothness = "distant / chromatic (low diatonic overlap)"

    return {
        "pivots": pivots,
        "target_v7": {
            "name": f"{name_pitch(target_v7_root)}7",
            "pcs": target_v7_pcs,
        },
        "tritone_sub_v7": {
            "name": f"{name_pitch(tritone_sub_root)}7",
            "pcs": tritone_sub_pcs,
        },
        "common_tones": common_tones,
        "smoothness": smoothness,
    }


def _chord_function_group(degree: int) -> str:
    """Classify scale degree (1-7) into T, P, or D harmonic function."""
    if degree in (1, 3, 6):
        return "T"
    if degree in (2, 4):
        return "P"
    return "D"


def harmonize(melody_notes: list[dict], voicing_style: Optional[str] = None) -> list[dict]:
    """
    Suggest a functional harmonization for a melody.
    Identifies the key, then selects diatonic chords containing each melody note
    using functional progression syntax, cadential weighting, and chord variety.
    """
    if not melody_notes:
        return []

    pcs = [n["pc"] for n in melody_notes]
    best_keys = detect_key(pcs)
    if not best_keys:
        return []

    # Pick top major or minor scale that has diatonic triads
    best_key = next(
        (k for k in best_keys if len(SCALES.get(k["scale"], ())) == 7),
        best_keys[0],
    )
    diatonic = get_diatonic_chords(best_key["root"], best_key["scale"])
    if not diatonic:
        diatonic = get_diatonic_chords(best_key["root"], "major")

    harmonization = []
    prev_chord = None
    prev_voicing: list[int] = []
    total_notes = len(melody_notes)

    for idx, note in enumerate(melody_notes):
        npc = note["pc"] % 12
        candidates = [c for c in diatonic if npc in c["pcs"]]
        if not candidates:
            candidates = diatonic

        def score_candidate(c: dict) -> float:
            s = 0.0
            deg = c["degree"]
            func = _chord_function_group(deg)

            # 1. Position / cadential preferences
            if idx == 0:
                if deg == 1:
                    s += 4.0
                elif deg in (5, 6):
                    s += 1.5
            elif idx == total_notes - 1 and total_notes > 1:
                if deg == 1:
                    s += 4.5
                elif deg == 6:
                    s += 2.0
                elif deg == 5:
                    s += 1.5
            elif idx == total_notes - 2 and total_notes > 2:
                if deg == 5:
                    s += 3.0
                elif deg in (2, 4):
                    s += 2.0

            # 2. Melody note role in chord (root or 3rd preferred over 5th)
            rel_iv = (npc - c["root"]) % 12
            if rel_iv == 0:
                s += 1.2
            elif rel_iv in (3, 4):
                s += 1.0
            else:
                s += 0.6

            # 3. Prefer primary harmonies slightly over vii°
            if deg in (1, 4, 5):
                s += 0.8
            elif deg in (2, 6):
                s += 0.6
            elif deg == 3:
                s += 0.3

            # 4. Transition from previous chord
            if prev_chord is not None:
                prev_deg = prev_chord["degree"]
                prev_func = _chord_function_group(prev_deg)
                if prev_deg == deg:
                    # Discourage repeating the exact same chord on consecutive notes
                    s -= 2.5
                else:
                    # Reward standard functional syntax: T -> P -> D -> T
                    if (prev_func, func) in (("T", "P"), ("P", "D"), ("D", "T"), ("T", "D")):
                        s += 1.8
                    # Reward root motion by descending 5th (e.g. vi->ii, ii->V, V->I)
                    root_motion = (c["root"] - prev_chord["root"]) % 12
                    if root_motion == 5:
                        s += 1.5
                    elif root_motion in (2, 9, 8):
                        s += 0.8

            return s

        chosen = max(candidates, key=score_candidate)
        prev_chord = chosen

        entry = {
            "start": note["start"],
            "duration": note["duration"],
            "melody_note": note.get("name") or name_pitch(npc),
            "chord": chosen["name"],
            "roman": chosen["roman"],
            "pcs": chosen["pcs"],
            "key": best_key["name"],
        }

        if voicing_style:
            if voicing_style == "smooth":
                voicing = optimize_voice_leading(prev_voicing, chosen["pcs"])
            else:
                voicing = generate_voicing(chosen["pcs"], style=voicing_style)
            prev_voicing = voicing
            entry["voicing"] = voicing
            entry["voicing_name"] = name_voicing(voicing)

        harmonization.append(entry)

    return harmonization


def format_duration(sec: float) -> str:
    """Format seconds into M:SS."""
    m = int(sec // 60)
    s = sec % 60
    return f"{m}:{s:05.2f}" if s % 1 else f"{m}:{int(s):02d}"


def negative_transform(pitches: list[int], key_root: int) -> list[int]:
    """
    Perform negative harmony transformation (reflection across the axis
    between the minor and major third of the key).
    Reflection axis is (key_root + 3.5).
    Reflected PC = (2 * axis - PC) % 12 = (2 * key_root + 7 - PC) % 12.
    """
    axis_x2 = 2 * key_root + 7
    return [(axis_x2 - p) % 12 for p in pitches]


def generate_voicing(pcs: set[int], style: str = "closed", base_octave: int = 4) -> list[int]:
    """
    Generate a voicing (MIDI pitches) for a set of pitch classes.
    Styles: closed, drop2, drop3.
    """
    sorted_pcs = sorted(list(pcs))
    if not sorted_pcs:
        return []

    closed = [p + 12 * base_octave for p in sorted_pcs]

    if style == "closed" or len(closed) < 2:
        return closed

    if style == "drop2":
        if len(closed) >= 2:
            closed[-2] -= 12
    elif style == "drop3":
        if len(closed) >= 3:
            closed[-3] -= 12

    return sorted(closed)


def optimize_voice_leading(prev_voicing: list[int], next_pcs: set[int]) -> list[int]:
    """
    Find a voicing for next_pcs that minimizes the distance from prev_voicing.
    """
    if not prev_voicing or not next_pcs:
        return generate_voicing(next_pcs)

    avg_prev = sum(prev_voicing) / len(prev_voicing)
    best_voicing = []
    min_dist = float("inf")

    pcs_list = sorted(list(next_pcs))
    n = len(pcs_list)

    base_center = int(avg_prev // 12)
    for base_octave in range(base_center - 1, base_center + 2):
        for i in range(n):
            inversion = []
            for j in range(n):
                pc = pcs_list[(i + j) % n]
                octave = base_octave + (1 if (i + j) >= n else 0)
                inversion.append(pc + 12 * octave)

            sorted_prev = sorted(prev_voicing)
            sorted_inv = sorted(inversion)

            dist = 0
            for k in range(min(len(sorted_prev), len(sorted_inv))):
                dist += (sorted_prev[k] - sorted_inv[k]) ** 2

            if dist < min_dist:
                min_dist = dist
                best_voicing = sorted_inv

    return best_voicing
