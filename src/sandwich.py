#!/usr/bin/env python3
"""
sandwich.py is a unified CLI for the sandwich toolkit
"""

import argparse
import contextlib
import io
import shlex
import sys
from typing import Optional, Union

import melody_parser
import section_grid
import tritone_subs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sandwich.py",
        description="sandwich: music theory toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Parse subcommand
    parse_parser = subparsers.add_parser("parse", help="Parse a melody file or string")
    parse_parser.add_argument("input", help="File path or quoted text")
    parse_parser.add_argument("--format", choices=["text", "midi", "lilypond", "musicxml"], default=None)

    # Grid subcommand
    grid_parser = subparsers.add_parser("grid", help="Generate a song structure grid")
    grid_parser.add_argument("--length-sec", type=float, required=True)
    grid_parser.add_argument("--tempo", type=float, required=True)
    grid_parser.add_argument("--meter", required=True)
    grid_parser.add_argument("--ostinato-bars", type=int, default=4)
    grid_parser.add_argument("--top", required=True)
    grid_parser.add_argument("--sub", default="")
    grid_parser.add_argument("--subsub", default="")
    grid_parser.add_argument("--sub3", default="")

    # Subs subcommand
    subs_parser = subparsers.add_parser("subs", help="Find tritone substitutions")
    subs_parser.add_argument("pitches_pos", nargs="?", help="Pitches (space or comma separated)")
    subs_parser.add_argument("--pitches", help="Pitches")
    subs_parser.add_argument("--root", help="Root pitch class")
    subs_parser.add_argument("--quality", help="Chord quality")
    subs_parser.add_argument("--label", help="Optional label")
    subs_parser.add_argument("--top", type=int, default=10, help="Number of candidates")
    subs_parser.add_argument("--all-qualities", action="store_true", help="Include triads, 7ths, and 9ths")

    # Key subcommand
    key_parser = subparsers.add_parser("key", help="Detect key/scale from pitches")
    key_parser.add_argument("pitches", help="Pitches (space or comma separated)")

    # Harmonize subcommand
    harm_parser = subparsers.add_parser("harmonize", help="Suggest chords for a melody")
    harm_parser.add_argument("input", help="File path or quoted text")
    harm_parser.add_argument("--format", choices=["text", "midi", "lilypond", "musicxml"], default=None)
    harm_parser.add_argument("--voicing", choices=["closed", "drop2", "drop3", "smooth"], help="Voicing style")

    # Generate subcommand
    gen_parser = subparsers.add_parser("generate", help="Procedurally generate a song from a vamp")
    gen_parser.add_argument("vamp", help="Vamp chords (separated by | or ,)")
    gen_parser.add_argument("--form", default="ABAB", help="Song form (e.g. ABACADA)")
    gen_parser.add_argument("--voicing", choices=["closed", "drop2", "drop3", "smooth"], help="Voicing style")
    gen_parser.add_argument("--rhythm", choices=["four-on-the-floor", "bossa", "swing", "waltz"], help="Rhythmic pattern")
    gen_parser.add_argument("--seed", type=int, default=None, help="Optional random seed for reproducible output")

    # Negative subcommand
    neg_parser = subparsers.add_parser("negative", help="Perform negative harmony transformation")
    neg_parser.add_argument("input", help="Pitches (space or comma separated) or melody text")
    neg_parser.add_argument("--key", required=True, help="Key root (e.g. C, G, Eb)")

    # Modulate subcommand
    mod_parser = subparsers.add_parser("modulate", help="Suggest paths for modulating between keys")
    mod_parser.add_argument("from_key", help="Starting key (e.g. C major, g# minor)")
    mod_parser.add_argument("to_key", help="Target key (e.g. G major, f#m)")

    return parser


def dispatch(args: argparse.Namespace) -> int:
    if args.command == "parse":
        return melody_parser.run_from_args(args)

    elif args.command == "grid":
        return section_grid.run_from_args(args)

    elif args.command == "subs":
        return tritone_subs.run_from_args(args)

    elif args.command == "key":
        from core import detect_key, parse_pitch_class
        try:
            raw_pitches = args.pitches.replace(",", " ").split()
            if not raw_pitches:
                raise ValueError("no pitches provided")
            pcs = [parse_pitch_class(p) for p in raw_pitches]
            results = detect_key(pcs)
            print("# Key Detection Results")
            print("| Key/Scale | Score | In-Scale Fit |")
            print("|---|---|---|")
            for r in results[:10]:
                fit_pct = f"{r['in_scale_ratio'] * 100:.0f}%"
                print(f"| {r['name']} | {r['score']:.2f} | {fit_pct} |")
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        return 0

    elif args.command == "harmonize":
        from core import harmonize
        try:
            notes = melody_parser.load_melody(args.input, args.format)
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            return 2

        if not notes:
            print("error: no notes found to harmonize", file=sys.stderr)
            return 2

        results = harmonize(notes, voicing_style=args.voicing)
        detected_key = results[0].get("key", "unknown") if results else "unknown"
        print("# Suggested Harmonization")
        print(f"*Detected Key:* {detected_key}")
        if args.voicing:
            print(f"*Voicing Style:* {args.voicing}")
            print()
            print("| Start | Note | Chord | Roman | Voicing |")
            print("|---|---|---|---|---|")
            for r in results:
                print(f"| {r['start']:.2f} | {r['melody_note']} | {r['chord']} | {r['roman']} | {r['voicing_name']} |")
        else:
            print()
            print("| Start | Note | Chord | Roman |")
            print("|---|---|---|---|")
            for r in results:
                print(f"| {r['start']:.2f} | {r['melody_note']} | {r['chord']} | {r['roman']} |")
        return 0

    elif args.command == "generate":
        from core import (
            RHYTHMS,
            generate_voicing,
            identify_chord,
            name_pitch_set,
            name_voicing,
            optimize_voice_leading,
            parse_vamp,
        )
        from generator import generate_song

        try:
            vamp_pcs = parse_vamp(args.vamp)
            song = generate_song(vamp_pcs, args.form, seed=args.seed)

            print(f"# Generated Song: {args.form.upper()}")
            if args.voicing:
                print(f"*Voicing Style:* {args.voicing}")
            if args.rhythm:
                print(f"*Rhythmic Pattern:* {args.rhythm}")
            print()

            prev_voicing: list[int] = []
            for entry in song:
                print(f"## Section {entry['section']}")
                print(f"*Applied Rules:* {', '.join(entry['rules'])}")

                cols = ["Bar", "Chord", "Pitches"]
                if args.voicing:
                    cols.append("Voicing")
                if args.rhythm:
                    cols.append("Rhythm (Offsets)")

                print(f"| {' | '.join(cols)} |")
                print(f"| {' | '.join(['---'] * len(cols))} |")

                for i, chord_pcs in enumerate(entry["vamp"]):
                    info = identify_chord(chord_pcs)
                    row = [f"{i + 1}", info["symbol"], name_pitch_set(chord_pcs)]

                    if args.voicing == "smooth":
                        voicing = optimize_voice_leading(prev_voicing, chord_pcs)
                    elif args.voicing:
                        voicing = generate_voicing(chord_pcs, style=args.voicing)
                    else:
                        voicing = None

                    if voicing:
                        prev_voicing = voicing
                        row.append(name_voicing(voicing))

                    if args.rhythm:
                        pattern = RHYTHMS[args.rhythm]
                        row.append(", ".join(str(p[0]) for p in pattern))

                    print(f"| {' | '.join(row)} |")
                print()
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        return 0

    elif args.command == "negative":
        from core import identify_chord, name_pitch, negative_transform, parse_pitch_class
        try:
            root = parse_pitch_class(args.key)
            notes = melody_parser.parse_text(args.input)
            if not notes:
                raise ValueError("no pitches found in input")

            pcs = [n["pc"] for n in notes]
            neg_pcs = negative_transform(pcs, root)

            has_octaves = any(n["octave"] is not None for n in notes)
            orig_tokens = []
            neg_tokens = []
            for n, npc in zip(notes, neg_pcs):
                if has_octaves and n["octave"] is not None:
                    orig_tokens.append(f"{n['name']}{n['octave']}")
                    neg_tokens.append(f"{name_pitch(npc)}{n['octave']}")
                else:
                    orig_tokens.append(n["name"])
                    neg_tokens.append(name_pitch(npc))

            orig_chord = identify_chord(set(pcs))
            neg_chord = identify_chord(set(neg_pcs))

            print(f"# Negative Harmony (Key: {args.key})")
            print(f"**Original:** {' '.join(orig_tokens)} ({orig_chord['symbol']})")
            print(f"**Negative:** {' '.join(neg_tokens)} ({neg_chord['symbol']})")
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        return 0

    elif args.command == "modulate":
        from core import name_pitch_set, parse_key_string, suggest_modulation

        try:
            k1 = parse_key_string(args.from_key)
            k2 = parse_key_string(args.to_key)

            results = suggest_modulation(k1, k2)

            print(f"# Modulation: {k1['name']} -> {k2['name']}")
            print(f"*Voice-Leading Profile:* {results['smoothness']}")
            print()
            print("## Pivot Chords")
            if results["pivots"]:
                print("| Chord | Function in Start Key | Function in Target Key |")
                print("|---|---|---|")
                for p in results["pivots"]:
                    print(f"| {p['name']} | {p['roman_start']} | {p['roman_end']} |")
            else:
                print("No direct diatonic pivot chords found.")

            print()
            print("## Dominant & Tritone-Sub Approaches")
            v7 = results["target_v7"]
            tt = results["tritone_sub_v7"]
            print(f"- **Secondary Dominant (V7):** `{v7['name']}` ({name_pitch_set(v7['pcs'])})")
            print(f"- **Tritone Substitution (bII7):** `{tt['name']}` ({name_pitch_set(tt['pcs'])})")

            if results.get("common_tones"):
                print()
                print("## Common-Tone Functional Voice-Leading")
                print("| Pitch | Degree (Start -> Target) | Function (Start) | Function (Target) | Shift |")
                print("|---|---|---|---|---|")
                for ct in results["common_tones"]:
                    deg_str = f"^{ct['degree_start']} -> ^{ct['degree_end']}"
                    print(f"| {ct['pitch']} | {deg_str} | {ct['func_start']} | {ct['func_end']} | {ct['shift']} |")

        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        return 0

    return 2


ALLOWED_SUBCOMMANDS = ("parse", "grid", "subs", "key", "harmonize", "generate", "negative", "modulate")


def normalize_cli_string(command_str: str) -> list[str]:
    """Normalize a user CLI string into an argv list, stripping optional leading 'python3 sandwich.py'."""
    cmd = command_str.strip()
    for prefix in ("python3 sandwich.py", "python sandwich.py", "./sandwich.py", "sandwich.py"):
        if cmd.startswith(prefix):
            cmd = cmd[len(prefix):].strip()
            break
    return shlex.split(cmd)


def execute_command(command: Union[str, list[str]]) -> tuple[int, str, str]:
    """
    Execute a sandwich CLI command in-process and capture (exit_code, stdout, stderr).
    Safe for web requests without spawning subprocesses.
    """
    try:
        parts = normalize_cli_string(command) if isinstance(command, str) else list(command)
    except Exception as e:
        return 2, "", f"Error parsing command: {e}"

    if not parts or parts[0] not in ALLOWED_SUBCOMMANDS:
        return (
            2,
            "",
            f"Error: Invalid or disallowed command. Available: {', '.join(ALLOWED_SUBCOMMANDS)}",
        )

    parser = build_parser()
    out_buf = io.StringIO()
    err_buf = io.StringIO()

    with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
        try:
            args = parser.parse_args(parts)
            code = dispatch(args)
        except SystemExit as exc:
            code = int(exc.code) if isinstance(exc.code, int) else 2
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            code = 2

    return code, out_buf.getvalue(), err_buf.getvalue()


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
