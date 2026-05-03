#!/usr/bin/env python3
"""
melody_parser.py

parse a melody from plain text, musical instrument digital interface, lilypond,
or music extensible markup language. output a normalized note list with pitch
class, octave, duration (quarter-note units), and cumulative start time.

usage:
  python3 melody_parser.py path/to/file.txt
  python3 melody_parser.py path/to/file.midi
  python3 melody_parser.py path/to/file.ly
  python3 melody_parser.py path/to/file.musicxml
  python3 melody_parser.py --format text "c4q d4q e4q f4q"
  python3 melody_parser.py --format text "c d e f g a b"

format detection:
  by file extension (.txt, .midi/.mid, .ly/.lily/.lilypond, .xml/.musicxml/.mxl).
  override with --format {text, midi, lilypond, musicxml}.

text input syntax (any of these):
  bare pitches:           "c d e f g a b"
  pitches with octave:    "c4 d4 e4 f4 g4"
  with quarter-note tag:  "c4q d4q e4h f4w"  (q=1, h=2, w=4, e=0.5, s=0.25)
  with explicit duration: "c4:1 d4:0.5 e4:0.5 f4:1"
  use 'r' for rests:      "c4 r d4 e4"

output:
  a text table:
    | i | pitch | octave | start (quarter notes) | duration | pitch class |
"""

import argparse
import sys
import os

NAMES_FLAT = ["c", "db", "d", "eb", "e", "f", "gb", "g", "ab", "a", "bb", "b"]
PARSE_MAP = {
    "c": 0, "b#": 0, "dbb": 0,
    "c#": 1, "db": 1,
    "d": 2, "ebb": 2,
    "d#": 3, "eb": 3,
    "e": 4, "fb": 4,
    "f": 5, "e#": 5,
    "f#": 6, "gb": 6,
    "g": 7, "abb": 7,
    "g#": 8, "ab": 8,
    "a": 9, "bbb": 9,
    "a#": 10, "bb": 10,
    "b": 11, "cb": 11,
}
DURATION_TAGS = {"w": 4.0, "h": 2.0, "q": 1.0, "e": 0.5, "s": 0.25, "t": 1.0 / 3}


def parse_text(s: str) -> list[dict]:
    """parse a plain text melody string into a list of note dicts."""
    tokens = s.replace(",", " ").split()
    notes: list[dict] = []
    cursor = 0.0
    for tok in tokens:
        tok = tok.strip().lower()
        if not tok:
            continue
        if tok.startswith("r"):
            # rest
            dur = 1.0
            if ":" in tok:
                dur = float(tok.split(":", 1)[1])
            elif len(tok) > 1 and tok[1] in DURATION_TAGS:
                dur = DURATION_TAGS[tok[1]]
            cursor += dur
            continue
        # split duration if present
        if ":" in tok:
            pitch_part, dur_part = tok.split(":", 1)
            duration = float(dur_part)
        else:
            # check for trailing duration tag
            if tok and tok[-1] in DURATION_TAGS and len(tok) > 1 and tok[-2].isdigit():
                duration = DURATION_TAGS[tok[-1]]
                pitch_part = tok[:-1]
            else:
                duration = 1.0
                pitch_part = tok
        # split pitch and octave
        # find where digits start
        octave = None
        i = 0
        while i < len(pitch_part) and not pitch_part[i].isdigit():
            i += 1
        pitch_token = pitch_part[:i]
        if i < len(pitch_part):
            try:
                octave = int(pitch_part[i:])
            except ValueError:
                pass
        if pitch_token not in PARSE_MAP:
            raise ValueError(f"could not parse pitch: {pitch_part!r}")
        pc = PARSE_MAP[pitch_token]
        notes.append({
            "pc": pc,
            "octave": octave,
            "start": cursor,
            "duration": duration,
            "name": NAMES_FLAT[pc],
        })
        cursor += duration
    return notes


def parse_midi(path: str) -> list[dict]:
    try:
        import mido
    except ImportError:
        raise RuntimeError(
            "musical instrument digital interface parsing requires the mido library. "
            "install with: pip install mido --break-system-packages"
        )
    mid = mido.MidiFile(path)
    ticks_per_beat = mid.ticks_per_beat
    notes: list[dict] = []
    cursor_ticks = 0
    note_starts: dict[int, int] = {}
    # use the first track that contains note_on events
    track = None
    for t in mid.tracks:
        for msg in t:
            if msg.type == "note_on" and msg.velocity > 0:
                track = t
                break
        if track is not None:
            break
    if track is None:
        return notes
    for msg in track:
        cursor_ticks += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            note_starts[msg.note] = cursor_ticks
        elif (msg.type == "note_off") or (msg.type == "note_on" and msg.velocity == 0):
            if msg.note in note_starts:
                start = note_starts.pop(msg.note)
                duration_ticks = cursor_ticks - start
                pc = msg.note % 12
                octave = msg.note // 12 - 1
                notes.append({
                    "pc": pc,
                    "octave": octave,
                    "start": start / ticks_per_beat,
                    "duration": duration_ticks / ticks_per_beat,
                    "name": NAMES_FLAT[pc],
                })
    notes.sort(key=lambda n: n["start"])
    return notes


def parse_lilypond(text: str) -> list[dict]:
    """very basic lilypond note parser. handles c, d, e... with accidentals
    (cis=c#, ces=cb, dis=d#, des=db, etc.), octave marks (c' c'' c, c,,) and
    durations (c4 c8 c16 c2 c1). does not handle tuplets, ties, chords, or
    grace notes - those are skipped or approximated. ignores backslash commands
    like \\relative."""
    import re
    LP_PITCH = {
        "c": 0, "cis": 1, "des": 1, "d": 2, "dis": 3, "ees": 3, "es": 3,
        "e": 4, "fes": 4, "f": 5, "fis": 6, "ges": 6, "g": 7,
        "gis": 8, "aes": 8, "as": 8, "a": 9, "ais": 10, "bes": 10, "b": 11, "ces": 11,
    }
    notes: list[dict] = []
    cursor = 0.0
    # strip comments
    text = re.sub(r"%.*", "", text)
    # if there's a music block, skip everything before the first opening brace
    # (this discards \relative c' style metadata that would otherwise be parsed
    # as notes)
    if "{" in text:
        text = text[text.find("{"):]
    # strip backslash commands: \word
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    # require notes to be preceded by whitespace, start of string, or { | <
    # and followed by whitespace, end, or duration digits/octave marks
    pattern = re.compile(
        r"(?:(?<=\s)|(?<=\{)|(?<=\|)|(?<=<)|^)"
        r"(?P<pitch>[a-h](?:is|es|s)?)"
        r"(?P<oct>[',]*)"
        r"(?P<dur>\d+\.?)?"
        r"(?=\s|$|[\}\|>])"
    )
    for m in pattern.finditer(text):
        pitch_tok = m.group("pitch")
        if pitch_tok not in LP_PITCH:
            continue
        pc = LP_PITCH[pitch_tok]
        octs = m.group("oct") or ""
        # base octave for unmarked pitches is octave 3 in lilypond convention
        octave = 3 + octs.count("'") - octs.count(",")
        dur_tok = m.group("dur") or "4"
        if dur_tok.endswith("."):
            base = int(dur_tok[:-1])
            duration = (4.0 / base) * 1.5
        else:
            base = int(dur_tok)
            duration = 4.0 / base
        notes.append({
            "pc": pc,
            "octave": octave,
            "start": cursor,
            "duration": duration,
            "name": NAMES_FLAT[pc],
        })
        cursor += duration
    return notes


def parse_musicxml(path: str) -> list[dict]:
    import xml.etree.ElementTree as ET
    tree = ET.parse(path)
    root = tree.getroot()
    # find divisions per quarter note (default 1)
    divisions = 1
    div_el = root.find(".//divisions")
    if div_el is not None and div_el.text:
        divisions = int(div_el.text)
    notes: list[dict] = []
    cursor = 0.0
    STEP_TO_PC = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
    for note_el in root.iter("note"):
        is_rest = note_el.find("rest") is not None
        dur_el = note_el.find("duration")
        if dur_el is None or not dur_el.text:
            continue
        duration = int(dur_el.text) / divisions
        if is_rest:
            cursor += duration
            continue
        pitch_el = note_el.find("pitch")
        if pitch_el is None:
            cursor += duration
            continue
        step = pitch_el.findtext("step", default="C").lower()
        alter = int(pitch_el.findtext("alter", default="0"))
        octave = int(pitch_el.findtext("octave", default="4"))
        pc = (STEP_TO_PC.get(step, 0) + alter) % 12
        notes.append({
            "pc": pc,
            "octave": octave,
            "start": cursor,
            "duration": duration,
            "name": NAMES_FLAT[pc],
        })
        cursor += duration
    return notes


def detect_format(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".txt", ".text"):
        return "text"
    if ext in (".midi", ".mid"):
        return "midi"
    if ext in (".ly", ".lily", ".lilypond"):
        return "lilypond"
    if ext in (".xml", ".musicxml", ".mxl"):
        return "musicxml"
    return "text"


def render(notes: list[dict]) -> str:
    lines = ["| i | pitch | octave | start (quarter notes) | duration | pitch class |",
             "|---|---|---|---|---|---|"]
    for i, n in enumerate(notes):
        oct_str = str(n["octave"]) if n["octave"] is not None else "-"
        lines.append(
            f"| {i} | {n['name']} | {oct_str} | {n['start']:.3f} | {n['duration']:.3f} | {n['pc']} |"
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="file path, or quoted text if --format text and not a file")
    ap.add_argument("--format", choices=["text", "midi", "lilypond", "musicxml"], default=None)
    args = ap.parse_args()

    if args.format == "text" and not os.path.exists(args.input):
        # treat the argument as inline text
        try:
            notes = parse_text(args.input)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
    else:
        if not os.path.exists(args.input):
            print(f"error: file not found: {args.input}", file=sys.stderr)
            return 2
        fmt = args.format or detect_format(args.input)
        try:
            if fmt == "text":
                with open(args.input, "r", encoding="utf-8") as f:
                    notes = parse_text(f.read())
            elif fmt == "midi":
                notes = parse_midi(args.input)
            elif fmt == "lilypond":
                with open(args.input, "r", encoding="utf-8") as f:
                    notes = parse_lilypond(f.read())
            elif fmt == "musicxml":
                notes = parse_musicxml(args.input)
            else:
                print(f"error: unknown format {fmt}", file=sys.stderr)
                return 2
        except RuntimeError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        except Exception as e:
            print(f"error parsing {fmt}: {e}", file=sys.stderr)
            return 2

    print(f"# parsed melody")
    print()
    print(f"note count: {len(notes)}")
    if notes:
        total_dur = max(n["start"] + n["duration"] for n in notes)
        print(f"total duration: {total_dur:.3f} quarter notes")
        # pitch class histogram for ostinato derivation
        pc_counts: dict[int, float] = {}
        for n in notes:
            pc_counts[n["pc"]] = pc_counts.get(n["pc"], 0.0) + n["duration"]
        ranked = sorted(pc_counts.items(), key=lambda kv: -kv[1])
        print(f"pitch class weight (by total duration):")
        for pc, w in ranked[:6]:
            print(f"  {NAMES_FLAT[pc]}: {w:.2f}")
    print()
    print(render(notes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
