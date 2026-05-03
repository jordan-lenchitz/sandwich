#!/usr/bin/env python3
"""
tritone_subs.py

given a chord (as a list of pitch class names), output candidate tritone
substitution chords ranked by common tones with the original. used by the
tritone-vamp-arranger logic in step 7 of the process.

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

# pitch class names. flats preferred for output spelling, but parsing accepts
# both flats and sharps.
NAMES_FLAT = ["c", "db", "d", "eb", "e", "f", "gb", "g", "ab", "a", "bb", "b"]
NAMES_SHARP = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]

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

# chord quality library: intervals from root in semitones.
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
    t = token.strip().lower()
    if t in PARSE_MAP:
        return PARSE_MAP[t]
    raise ValueError(f"could not parse pitch class: {token!r}")


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


def name_pitch_set(pcs: set[int]) -> str:
    # output flat-spelled, sorted by pitch class.
    return " ".join(NAMES_FLAT[p] for p in sorted(pcs))


def generate_candidates(orig_pcs: set[int], orig_label: str) -> list[dict]:
    """
    enumerate candidate substitutions.
    for each chord quality, build that quality on every root, then filter:
    - exclude the literal original pitch set
    - require a tritone relation with the original (at least one pitch pair
      a tritone apart between sets)
    """
    candidates = []
    seen_keys = set()
    for q_name, intervals in QUALITIES.items():
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
            candidates.append({
                "label": f"{NAMES_FLAT[r]}{q_name if q_name not in ('maj','min') else ('' if q_name=='maj' else 'm')}",
                "root": r,
                "quality": q_name,
                "pcs": set(pcs),
                "common_tones": ct,
            })
    return candidates


def rank_candidates(cands: list[dict]) -> list[dict]:
    # primary sort: common tones desc; secondary: prefer chord types with both
    # third and seventh (more harmonic substance); tertiary: alphabetical quality.
    quality_priority = {
        "7": 0, "m7": 1, "m7b5": 2, "dim7": 3, "maj7": 4, "mmaj7": 5,
        "9": 6, "m9": 7, "maj9": 8, "augmaj7": 9, "aug7": 10, "7sus4": 11,
        "6": 12, "m6": 13, "maj": 14, "min": 15, "dim": 16, "aug": 17,
        "sus2": 18, "sus4": 19, "quartal3": 20, "quartal4": 21,
    }
    return sorted(
        cands,
        key=lambda c: (
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
        if c["common_tones"] >= 3:
            notes.append("smooth")
        elif c["common_tones"] == 2:
            notes.append("classic chromatic")
        elif c["common_tones"] == 1:
            notes.append("strict tritone feel")
        else:
            notes.append("jarring; structural use")
        # check direct tritone transpose of original root: not always known here;
        # we can flag candidates whose root is exactly six semitones from any
        # original pitch as a tritone-related root.
        tritone_root = any(((c["root"] - p) % 12) == 6 or ((p - c["root"]) % 12) == 6
                           for p in orig_pcs)
        if tritone_root:
            notes.append("tritone-related root")
        lines.append(
            f"| {c['label']} | {name_pitch_set(c['pcs'])} | {c['common_tones']} | {'; '.join(notes)} |"
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
