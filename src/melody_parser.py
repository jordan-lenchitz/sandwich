#!/usr/bin/env python3
"""
melody_parser.py

parse a melody
output a normalized note list with pitch class, octave, duration (quarter-note units), and cumulative start time

usage:
  python3 melody_parser.py path/to/file.txt
  python3 melody_parser.py path/to/file.midi
  python3 melody_parser.py path/to/file.ly
  python3 melody_parser.py path/to/file.musicxml
  python3 melody_parser.py --format text "c4q d4q e4q f4q"
  python3 melody_parser.py "c4 d4 e4 f4 g4"

format detection:
  by file extension (.txt, .midi/.mid, .ly/.lily/.lilypond, .xml/.musicxml/.mxl).
  if input is not an existing file path, inline text/lilypond/xml is parsed automatically.
  override with --format {text, midi, lilypond, musicxml}.
"""

import argparse
import os
import sys
from typing import Optional

from core import NAMES_FLAT, PARSE_MAP, format_duration

DURATION_TAGS = {"w": 4.0, "h": 2.0, "q": 1.0, "e": 0.5, "s": 0.25, "t": 1.0 / 3}
FILE_EXTENSIONS = {".txt", ".text", ".midi", ".mid", ".ly", ".lily", ".lilypond", ".xml", ".musicxml", ".mxl"}


def parse_text(s: str) -> list[dict]:
    """parse a plain text melody string into a list of note dicts."""
    tokens = s.replace(",", " ").split()
    notes: list[dict] = []
    cursor = 0.0
    for tok in tokens:
        tok = tok.strip().lower()
        if not tok:
            continue
        if tok.startswith("r") and (len(tok) == 1 or tok[1] in DURATION_TAGS or tok[1] == ":" or tok[1:].isdigit()):
            dur = 1.0
            if ":" in tok:
                dur = float(tok.split(":", 1)[1])
            elif len(tok) > 1 and tok[1] in DURATION_TAGS:
                dur = DURATION_TAGS[tok[1]]
            cursor += dur
            continue
        if ":" in tok:
            pitch_part, dur_part = tok.split(":", 1)
            duration = float(dur_part)
        else:
            if tok and tok[-1] in DURATION_TAGS and len(tok) > 1 and (tok[-2].isdigit() or tok[:-1] in PARSE_MAP):
                # Disambiguate pitch names ending in 'e' or 'b' (none in DURATION_TAGS: w, h, q, e, s, t)
                # Wait: 'e' is both pitch E and eighth-note tag!
                # Only treat trailing 'e' as eighth-note if preceded by a digit (e.g. c4e, e4e) or if pitch_part without it is valid and tok not in PARSE_MAP
                if tok in PARSE_MAP:
                    duration = 1.0
                    pitch_part = tok
                elif tok[-2].isdigit() or (tok[-1] != "e" and tok[:-1] in PARSE_MAP):
                    duration = DURATION_TAGS[tok[-1]]
                    pitch_part = tok[:-1]
                else:
                    duration = 1.0
                    pitch_part = tok
            else:
                duration = 1.0
                pitch_part = tok

        octave = None
        i = 0
        while i < len(pitch_part) and not pitch_part[i].isdigit() and pitch_part[i] != "-":
            i += 1
        pitch_token = pitch_part[:i]
        if i < len(pitch_part):
            try:
                octave = int(pitch_part[i:])
            except ValueError as exc:
                raise ValueError(f"could not parse octave in pitch: {pitch_part!r}") from exc
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
    except ImportError as exc:
        raise RuntimeError(
            "musical instrument digital interface parsing requires the mido library. "
            "install with: pip install mido"
        ) from exc
    mid = mido.MidiFile(path)
    ticks_per_beat = mid.ticks_per_beat
    notes: list[dict] = []
    cursor_ticks = 0
    note_starts: dict[int, int] = {}
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
    """basic lilypond note parser."""
    import re
    LP_PITCH = {
        "c": 0, "cis": 1, "des": 1, "d": 2, "dis": 3, "ees": 3, "es": 3,
        "e": 4, "fes": 4, "f": 5, "fis": 6, "ges": 6, "g": 7,
        "gis": 8, "aes": 8, "as": 8, "a": 9, "ais": 10, "bes": 10, "b": 11, "ces": 11,
    }
    notes: list[dict] = []
    cursor = 0.0
    text = re.sub(r"%.*", "", text)
    if "{" in text:
        text = text[text.find("{"):]
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
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


def parse_musicxml(path_or_xml: str, is_inline: bool = False) -> list[dict]:
    import xml.etree.ElementTree as ET
    if is_inline:
        root = ET.fromstring(path_or_xml)
    else:
        tree = ET.parse(path_or_xml)
        root = tree.getroot()
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


def _looks_like_filepath(s: str) -> bool:
    ext = os.path.splitext(s.strip())[1].lower()
    return ext in FILE_EXTENSIONS or "/" in s or "\\" in s


def load_melody(input_arg: str, fmt: Optional[str] = None) -> list[dict]:
    """
    Load and parse a melody from either a file path or an inline string.
    Automatically handles inline text (e.g. 'c4 d4 e4 f4') even when --format is omitted.
    """
    if os.path.exists(input_arg):
        resolved_fmt = fmt or detect_format(input_arg)
        if resolved_fmt == "text":
            with open(input_arg, "r", encoding="utf-8") as f:
                return parse_text(f.read())
        elif resolved_fmt == "midi":
            return parse_midi(input_arg)
        elif resolved_fmt == "lilypond":
            with open(input_arg, "r", encoding="utf-8") as f:
                return parse_lilypond(f.read())
        elif resolved_fmt == "musicxml":
            return parse_musicxml(input_arg)
        else:
            raise ValueError(f"unknown format {resolved_fmt}")

    # Not an existing file on disk: check if it looks like a missing file path vs inline content
    if fmt == "midi" or (fmt is None and _looks_like_filepath(input_arg)):
        raise FileNotFoundError(f"file not found: {input_arg}")

    resolved_fmt = fmt or "text"
    if resolved_fmt == "text":
        return parse_text(input_arg)
    elif resolved_fmt == "lilypond":
        return parse_lilypond(input_arg)
    elif resolved_fmt == "musicxml":
        if input_arg.strip().startswith("<"):
            return parse_musicxml(input_arg, is_inline=True)
        raise FileNotFoundError(f"file not found: {input_arg}")
    else:
        raise FileNotFoundError(f"file not found: {input_arg}")


def render(notes: list[dict]) -> str:
    lines = [
        "| i | pitch | octave | start (quarter notes) | duration | pitch class |",
        "|---|---|---|---|---|---|",
    ]
    for i, n in enumerate(notes):
        oct_str = str(n["octave"]) if n["octave"] is not None else "-"
        lines.append(
            f"| {i} | {n['name']} | {oct_str} | {n['start']:.3f} | {n['duration']:.3f} | {n['pc']} |"
        )
    return "\n".join(lines)


def format_parsed_melody(notes: list[dict]) -> str:
    lines = ["# parsed melody", "", f"note count: {len(notes)}"]
    if notes:
        total_dur = max(n["start"] + n["duration"] for n in notes)
        lines.append(f"total duration: {total_dur:.3f} quarter notes")
        pc_counts: dict[int, float] = {}
        for n in notes:
            pc_counts[n["pc"]] = pc_counts.get(n["pc"], 0.0) + n["duration"]
        ranked = sorted(pc_counts.items(), key=lambda kv: -kv[1])
        lines.append("pitch class weight (by total duration):")
        for pc, w in ranked[:6]:
            lines.append(f"  {NAMES_FLAT[pc]}: {w:.2f}")
    lines.append("")
    lines.append(render(notes))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="file path, or inline melody text")
    ap.add_argument("--format", choices=["text", "midi", "lilypond", "musicxml"], default=None)
    return ap


def run_from_args(args: argparse.Namespace) -> int:
    try:
        notes = load_melody(args.input, args.format)
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"error parsing {args.format or 'input'}: {e}", file=sys.stderr)
        return 2

    print(format_parsed_melody(notes))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    return run_from_args(args)


if __name__ == "__main__":
    raise SystemExit(main())
