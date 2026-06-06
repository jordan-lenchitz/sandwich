"""
core.py - Shared music theory primitives for the sandwich project.
"""

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

def parse_pitch_class(token: str) -> int:
    """Parse a pitch name (e.g., 'C#', 'Bb') into a pitch class (0-11)."""
    t = token.strip().lower()
    if t in PARSE_MAP:
        return PARSE_MAP[t]
    raise ValueError(f"Could not parse pitch class: {token!r}")

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
        # fallback to comma if no pipes
        chunks = s.split(",")
    return [parse_chord(c.strip()) for c in chunks if c.strip()]

def name_pitch_set(pcs: set[int]) -> str:
    """Return a flat-spelled, sorted string of pitch class names."""
    return " ".join(NAMES_FLAT[p] for p in sorted(pcs))

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

# Rhythmic patterns: list of (offset, duration) in quarter notes
RHYTHMS = {
    "four-on-the-floor": [(0, 1), (1, 1), (2, 1), (3, 1)],
    "bossa": [(0, 1.5), (1.5, 1.5), (3, 1)],
    "swing": [(0, 1.5), (1.5, 0.5), (2, 1.5), (3.5, 0.5)],
    "waltz": [(0, 1), (1, 1), (2, 1)], # 3/4
}

def detect_key(pitches: list[int]) -> list[dict]:
    """
    Detect the most likely key/scale based on a list of pitches.
    Returns a ranked list of (root, scale_name, score).
    """
    if not pitches:
        return []
    
    unique_pcs = set(p % 12 for p in pitches)
    results = []
    
    for root in range(12):
        for scale_name, intervals in SCALES.items():
            scale_pcs = set((root + iv) % 12 for iv in intervals)
            # Score based on how many of the unique pitches are in the scale
            matches = unique_pcs.intersection(scale_pcs)
            score = len(matches) / len(unique_pcs) if unique_pcs else 0
            
            # Tie-breaker: prioritize common scales (Major/Minor)
            if scale_name in ("major", "natural_minor"):
                score += 0.01
            
            results.append({
                "root": root,
                "scale": scale_name,
                "score": score,
                "name": f"{name_pitch(root)} {scale_name}"
            })
            
    return sorted(results, key=lambda x: x["score"], reverse=True)

def get_diatonic_chords(root: int, scale_name: str, include_secondary: bool = False) -> list[dict]:
    """
    Return basic diatonic chords for a given key/scale.
    Currently supports major and natural_minor.
    If include_secondary is True, also adds V7/x chords.
    """
    if scale_name not in ("major", "natural_minor"):
        return []
    
    intervals = SCALES[scale_name]
    chords = []
    
    # Roman numeral labels
    if scale_name == "major":
        labels = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]
        qualities = ["maj", "min", "min", "maj", "maj", "min", "dim"]
    else: # natural_minor
        labels = ["i", "ii°", "III", "iv", "v", "VI", "VII"]
        qualities = ["min", "dim", "maj", "min", "min", "maj", "maj"]

    for i in range(len(intervals)):
        chord_root = (root + intervals[i]) % 12
        chords.append({
            "roman": labels[i],
            "root": chord_root,
            "quality": qualities[i],
            "name": f"{name_pitch(chord_root)}{qualities[i] if qualities[i] != 'maj' else ''}",
            "pcs": set((chord_root + iv) % 12 for iv in QUALITIES[qualities[i]])
        })
        
    if include_secondary:
        # Add V7 of each diatonic chord (except I and vii°)
        for i in range(1, len(intervals)):
            if labels[i] in ("vii°", "ii°"): continue
            target_root = (root + intervals[i]) % 12
            dom_root = (target_root + 7) % 12
            chords.append({
                "roman": f"V7/{labels[i]}",
                "root": dom_root,
                "quality": "7",
                "name": f"{name_pitch(dom_root)}7",
                "pcs": set((dom_root + iv) % 12 for iv in QUALITIES["7"])
            })
            
    return chords

def suggest_modulation(start_key: dict, end_key: dict) -> list[dict]:
    """
    Suggest a path for modulating between two keys.
    Uses pivot chords (chords common to both keys).
    """
    start_chords = get_diatonic_chords(start_key["root"], start_key["scale"])
    end_chords = get_diatonic_chords(end_key["root"], end_key["scale"])
    
    pivots = []
    for sc in start_chords:
        for ec in end_chords:
            if sc["pcs"] == ec["pcs"]:
                pivots.append({
                    "name": sc["name"],
                    "roman_start": sc["roman"],
                    "roman_end": ec["roman"]
                })
                
    # Also find secondary dominants of the target key that exist in the start key's orbit
    # (Simplified: just look for the V7 of the target root)
    target_v7_root = (end_key["root"] + 7) % 12
    target_v7_pcs = set((target_v7_root + iv) % 12 for iv in QUALITIES["7"])
    
    return {
        "pivots": pivots,
        "target_v7": {
            "name": f"{name_pitch(target_v7_root)}7",
            "pcs": target_v7_pcs
        }
    }

def harmonize(melody_notes: list[dict]) -> list[dict]:
    """
    Suggest a simple harmonization for a melody.
    Identifies the key, then picks diatonic chords that contain the melody notes.
    """
    if not melody_notes:
        return []
    
    pcs = [n["pc"] for n in melody_notes]
    best_keys = detect_key(pcs)
    if not best_keys:
        return []
    
    best_key = best_keys[0]
    diatonic = get_diatonic_chords(best_key["root"], best_key["scale"])
    
    harmonization = []
    for note in melody_notes:
        # Find chords in the key that contain this pitch class
        candidates = [c for c in diatonic if note["pc"] in c["pcs"]]
        # Default to the tonic if no match found (unlikely for diatonic melody)
        chosen = candidates[0] if candidates else diatonic[0]
        
        harmonization.append({
            "start": note["start"],
            "duration": note["duration"],
            "melody_note": name_pitch(note["pc"]),
            "chord": chosen["name"],
            "roman": chosen["roman"]
        })
    
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
    axis_x2 = (2 * key_root + 7)
    return [(axis_x2 - p) % 12 for p in pitches]

def generate_voicing(pcs: set[int], style: str = "closed", base_octave: int = 4) -> list[int]:
    """
    Generate a voicing (MIDI pitches) for a set of pitch classes.
    Styles: closed, drop2, drop3.
    """
    sorted_pcs = sorted(list(pcs))
    if not sorted_pcs:
        return []
    
    # Start with a closed voicing in the base octave
    closed = [p + 12 * base_octave for p in sorted_pcs]
    
    if style == "closed" or len(closed) < 2:
        return closed
    
    if style == "drop2":
        # Drop the second highest note by an octave
        if len(closed) >= 2:
            closed[-2] -= 12
    elif style == "drop3":
        # Drop the third highest note by an octave
        if len(closed) >= 3:
            closed[-3] -= 12
            
    return sorted(closed)

def optimize_voice_leading(prev_voicing: list[int], next_pcs: set[int]) -> list[int]:
    """
    Find a voicing for next_pcs that minimizes the distance from prev_voicing.
    Brute force approach: try all inversions and octaves within a reasonable range.
    """
    if not prev_voicing or not next_pcs:
        return generate_voicing(next_pcs)
    
    avg_prev = sum(prev_voicing) / len(prev_voicing)
    best_voicing = []
    min_dist = float('inf')
    
    # Try different base octaves for a closed voicing
    pcs_list = sorted(list(next_pcs))
    n = len(pcs_list)
    
    # Try 3 octaves around the average of the previous voicing
    base_center = int(avg_prev // 12)
    for base_octave in range(base_center - 1, base_center + 2):
        # Try all inversions
        for i in range(n):
            # Inversion i: start from the i-th pc
            inversion = []
            for j in range(n):
                pc = pcs_list[(i + j) % n]
                octave = base_octave + (1 if (i + j) >= n else 0)
                inversion.append(pc + 12 * octave)
            
            # Calculate distance (sum of squares of differences)
            # Match notes by proximity
            sorted_prev = sorted(prev_voicing)
            sorted_inv = sorted(inversion)
            
            dist = 0
            # If lengths differ, we'll just compare the common indices
            for k in range(min(len(sorted_prev), len(sorted_inv))):
                dist += (sorted_prev[k] - sorted_inv[k]) ** 2
            
            if dist < min_dist:
                min_dist = dist
                best_voicing = sorted_inv
                
    return best_voicing
