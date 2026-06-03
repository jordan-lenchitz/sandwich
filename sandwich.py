#!/usr/bin/env python3
"""
sandwich.py - Unified CLI for the sandwich music theory toolkit.
"""

import argparse
import sys
import os
import melody_parser
import section_grid
import tritone_subs

def main():
    parser = argparse.ArgumentParser(
        description="sandwich: music theory toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Parse subcommand
    parse_parser = subparsers.add_parser("parse", help="Parse a melody file or string")
    parse_parser.add_argument("input", help="File path or quoted text")
    parse_parser.add_argument("--format", choices=["text", "midi", "lilypond", "musicxml"])

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

    # Key subcommand
    key_parser = subparsers.add_parser("key", help="Detect key/scale from pitches")
    key_parser.add_argument("pitches", help="Pitches (space or comma separated)")

    # Harmonize subcommand
    harm_parser = subparsers.add_parser("harmonize", help="Suggest chords for a melody")
    harm_parser.add_argument("input", help="File path or quoted text")
    harm_parser.add_argument("--format", choices=["text", "midi", "lilypond", "musicxml"])

    # Generate subcommand
    gen_parser = subparsers.add_parser("generate", help="Procedurally generate a song from a vamp")
    gen_parser.add_argument("vamp", help="Vamp chords (separated by | or ,)")
    gen_parser.add_argument("--form", default="ABAB", help="Song form (e.g. ABACADA)")

    args = parser.parse_args()

    if args.command == "parse":
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        return melody_parser.main()
    
    elif args.command == "grid":
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        return section_grid.main()
    
    elif args.command == "subs":
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        return tritone_subs.main()

    elif args.command == "key":
        from core import detect_key, parse_pitch_class
        try:
            raw_pitches = args.pitches.replace(",", " ").split()
            pcs = [parse_pitch_class(p) for p in raw_pitches]
            results = detect_key(pcs)
            print("# Key Detection Results")
            print("| Key/Scale | Score |")
            print("|---|---|")
            for r in results[:10]:
                print(f"| {r['name']} | {r['score']:.2f} |")
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        return 0

    elif args.command == "harmonize":
        from core import harmonize
        from melody_parser import parse_text, detect_format, parse_midi, parse_lilypond, parse_musicxml
        
        notes = []
        if args.format == "text" and not os.path.exists(args.input):
            notes = parse_text(args.input)
        else:
            if not os.path.exists(args.input):
                print(f"error: file not found: {args.input}", file=sys.stderr)
                return 2
            fmt = args.format or detect_format(args.input)
            if fmt == "text":
                with open(args.input, "r") as f: notes = parse_text(f.read())
            elif fmt == "midi": notes = parse_midi(args.input)
            elif fmt == "lilypond":
                with open(args.input, "r") as f: notes = parse_lilypond(f.read())
            elif fmt == "musicxml": notes = parse_musicxml(args.input)
        
        if not notes:
            print("error: no notes found to harmonize", file=sys.stderr)
            return 2
        
        results = harmonize(notes)
        print("# Suggested Harmonization")
        print("| Start | Note | Chord | Roman |")
        print("|---|---|---|---|")
        for r in results:
            print(f"| {r['start']:.2f} | {r['melody_note']} | {r['chord']} | {r['roman']} |")
        return 0

    elif args.command == "generate":
        from core import parse_vamp, name_pitch_set
        from generator import generate_song
        
        try:
            vamp_pcs = parse_vamp(args.vamp)
            song = generate_song(vamp_pcs, args.form)
            
            print(f"# Generated Song: {args.form}")
            print()
            for entry in song:
                print(f"## Section {entry['section']}")
                print(f"*Applied Rules:* {', '.join(entry['rules'])}")
                print("| Bar | Chords |")
                print("|---|---|")
                for i, chord_pcs in enumerate(entry['vamp']):
                    print(f"| {i+1} | {name_pitch_set(chord_pcs)} |")
                print()
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        return 0

if __name__ == "__main__":
    sys.exit(main())
