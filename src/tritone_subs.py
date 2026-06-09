#!/usr/bin/env python3
"""
tritone_subs.py

input a chord 
output candidate tritone substitution chords ranked by common tones with the original

usage:
  python3 tritone_subs.py "ab c eb g"
  python3 tritone_subs.py --pitches "ab,c,eb,g"
  python3 tritone_subs.py --root ab --quality maj7
  python3 tritone_subs.py --pitches "ab,c,eb,g" --top 5

output:
  a text-style table of candidates with pitch class set, common-tone count,
  tritone-relation note, and a brief comment.
"""

import argparse
import sys

from core import NAMES_FLAT, NAMES_SHARP, PARSE_MAP, QUALITIES, parse_pitch_class


def parse_pitches(s: str) -> list[int]:
    # accept comma or space separated.
    if "," in s:
        toks = [t for t in s.split(",") if t.strip()]
    else:
        toks = s.split()
    return [parse_pitch_class(t) for t in toks]


def chord_pitches(root: int, quality: str) -> tuple[int, ...]:
    if quality not in QUALITIES:
        raise ValueError(f"unknown quality: {quality}")
    return tuple(sorted({(root + iv) % 12 for iv in QUALITIES[quality]}))


def common_tones(a: set[int], b: set[int]) -> int:
    return len(a & b)


def has_tritone_relation(orig: set[int], cand: set[int]) -> bool:
    # at least one pair (p in orig, q in cand) with (q - p) % 12 == 6 and p != q.
    for p in orig:
        if ((p + 6) % 12) in cand:
            return True
    return False


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


def get_spelled_pitch(root_name: str, degree_offset: int, target_pc: int) -> str:
    """Determine the correct spelling for a pitch based on root and degree."""
    letters = ["c", "d", "e", "f", "g", "a", "b"]
    natural_pcs = [0, 2, 4, 5, 7, 9, 11]
    
    root_letter = root_name[0].lower()
    root_letter_idx = letters.index(root_letter)
    
    target_letter_idx = (root_letter_idx + degree_offset) % 7
    target_letter = letters[target_letter_idx]
    target_natural_pc = natural_pcs[target_letter_idx]
    
    # Calculate accidental difference
    diff = (target_pc - target_natural_pc) % 12
    if diff > 6: diff -= 12
    
    if diff == 0: return target_letter
    if diff == 1: return target_letter + "#"
    if diff == 2: return target_letter + "x"
    if diff == -1: return target_letter + "b"
    if diff == -2: return target_letter + "bb"
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


def name_pitch_set(pcs: set[int], root_name: str = None, quality: str = None) -> str:
    # output flat-spelled, sorted by pitch class.
    if root_name and quality:
        return spell_chord(root_name, quality, pcs)
    return " ".join(NAMES_FLAT[p] for p in sorted(pcs))


def infer_root(pcs: set[int]) -> int:
    """Guess the root of a pitch class set using tertian heuristics."""
    if not pcs:
        return 0
    scores = {}
    for r in pcs:
        intervals = {(p - r) % 12 for p in pcs}
        score = 0
        if 7 in intervals: score += 10 # Perfect fifth
        if 4 in intervals: score += 5  # Major third
        if 3 in intervals: score += 5  # Minor third
        if 10 in intervals: score += 3 # Minor seventh
        if 11 in intervals: score += 3 # Major seventh
        if 2 in intervals: score += 1  # Ninth
        if 5 in intervals: score += 1  # Fourth/Eleventh
        if 9 in intervals: score += 1  # Sixth/Thirteenth
        scores[r] = score
    # Return the pitch with the highest score; tie-break by lower pitch class
    return max(sorted(scores.keys()), key=lambda k: scores[k])


def get_internal_tritones(pcs: set[int]) -> set[frozenset[int]]:
    """Find all pairs of pitches in the set that are a tritone apart."""
    tritones = set()
    pcs_list = list(pcs)
    for i in range(len(pcs_list)):
        for j in range(i + 1, len(pcs_list)):
            if (pcs_list[i] - pcs_list[j]) % 12 == 6:
                tritones.add(frozenset([pcs_list[i], pcs_list[j]]))
    return tritones


def generate_candidates(orig_pcs: set[int], orig_label: str, orig_root: int = None) -> list[dict]:
    """
    enumerate candidate substitutions.
    for each chord quality, build that quality on every root, then filter:
    - exclude the literal original pitch set
    - require a tritone relation with the original
    """
    candidates = []
    seen_keys = set()
    orig_tritones = get_internal_tritones(orig_pcs)
    
    actual_root = orig_root if orig_root is not None else infer_root(orig_pcs)
    tritone_of_root = (actual_root + 6) % 12
    tritone_of_fifth = (actual_root + 7 + 6) % 12

    for q_name, intervals in QUALITIES.items():
        if len(intervals) != 4:
            continue
        for r in range(12):
            pcs = frozenset((r + iv) % 12 for iv in intervals)
            if pcs == frozenset(orig_pcs):
                continue
            if not has_tritone_relation(orig_pcs, set(pcs)):
                continue
            key = (q_name, frozenset(pcs))
            if key in seen_keys:
                continue
            seen_keys.add(key)
            
            ct = common_tones(set(orig_pcs), set(pcs))
            cand_tritones = get_internal_tritones(set(pcs))
            preserved = len(orig_tritones & cand_tritones)
            
            # root importance: 2 for tritone of root, 1 for tritone of fifth
            root_priority = 0
            if r == tritone_of_root:
                root_priority = 2
            elif r == tritone_of_fifth:
                root_priority = 1
                
            # tritone of input chord member: root is 6 semitones from any original pitch
            tritone_root = any(((r - p) % 12) == 6 for p in orig_pcs)

            root_name = NAMES_FLAT[r]
            candidates.append({
                "label": f"{root_name}{q_name if q_name not in ('maj','min') else ('' if q_name=='maj' else 'm')}",
                "spelling": spell_chord(root_name, q_name, set(pcs)),
                "root": r,
                "quality": q_name,
                "pcs": set(pcs),
                "common_tones": ct,
                "preserved_tritones": preserved,
                "tritone_root": tritone_root,
                "root_priority": root_priority,
            })
    return candidates


def rank_candidates(cands: list[dict]) -> list[dict]:
    # primary sort: preserved tritones desc; 
    # secondary: root priority (tritone of root then tritone of fifth);
    # tertiary: any tritone of input chord member;
    # fourth: common tones desc; 
    # fifth: prefer chord types with both third and seventh.
    quality_priority = {
        "7": 0, "m7": 1, "m7b5": 2, "dim7": 3, "maj7": 4, "mmaj7": 5,
        "9": 6, "m9": 7, "maj9": 8, "augmaj7": 9, "aug7": 10, "7sus4": 11,
        "6": 12, "m6": 13, "maj": 14, "min": 15, "dim": 16, "aug": 17,
        "sus2": 18, "sus4": 19, "quartal3": 20, "quartal4": 21,
    }
    return sorted(
        cands,
        key=lambda c: (
            -c["preserved_tritones"],
            -c["root_priority"],
            -int(c["tritone_root"]),
            -c["common_tones"],
            quality_priority.get(c["quality"], 99),
            c["root"],
        ),
    )


def render_table(orig_label: str, orig_pcs: set[int], cands: list[dict], top_n: int) -> str:
    lines = []
    lines.append(f"# tritone substitution candidates for {orig_label}")
    lines.append("")
    lines.append(f"original pitch classes: {name_pitch_set(orig_pcs)}")
    lines.append("")
    lines.append("| candidate | pitches | common tones | notes |")
    lines.append("|---|---|---|---|")
    for c in cands[:top_n]:
        notes = []
        if c["preserved_tritones"] > 0:
            notes.append("preserves tritone")
        
        if c["root_priority"] == 2:
            notes.append("tritone of root")
        elif c["root_priority"] == 1:
            notes.append("tritone of fifth")
        elif c["tritone_root"]:
            notes.append("tritone of input chord member")

        if c["common_tones"] >= 3:
            notes.append("smooth")
        elif c["common_tones"] == 2:
            notes.append("classic chromatic")
        elif c["common_tones"] == 1:
            notes.append("strict tritone feel")
        else:
            notes.append("jarring; structural use")
        
        lines.append(
            f"| {c['label']} | {c.get('spelling') or name_pitch_set(c['pcs'])} | {c['common_tones']} | {'; '.join(notes)} |"
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pitches_pos", nargs="?", help="positional pitches, space or comma separated")
    ap.add_argument("--pitches", help="comma or space separated pitch class names")
    ap.add_argument("--root", help="root pitch class name (used with --quality)")
    ap.add_argument("--quality", help="chord quality from the library (e.g. maj7, m7, 7, m7b5, dim7)")
    ap.add_argument("--label", default=None, help="optional human label for the original chord")
    ap.add_argument("--top", type=int, default=10, help="how many candidates to return (default 10)")
    args = ap.parse_args()

    if args.root and args.quality:
        try:
            r = parse_pitch_class(args.root)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        pcs = set(chord_pitches(r, args.quality))
        label = args.label or f"{args.root.lower()}{args.quality}"
        cands = generate_candidates(pcs, label, orig_root=r)
    else:
        raw = args.pitches or args.pitches_pos
        if not raw:
            ap.print_help()
            return 2
        try:
            pcs_list = parse_pitches(raw)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        pcs = set(pcs_list)
        label = args.label or " ".join(NAMES_FLAT[p] for p in sorted(pcs))
        cands = generate_candidates(pcs, label)

    cands = rank_candidates(cands)
    print(render_table(label, pcs, cands, args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
