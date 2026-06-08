#!/usr/bin/env python3
"""
sandwich.py is a unified CLI for the sandwich toolkit
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
    harm_parser.add_argument("--voicing", choices=["closed", "drop2", "drop3", "smooth"], help="Voicing style")

    # Generate subcommand
    gen_parser = subparsers.add_parser("generate", help="Procedurally generate a song from a vamp")
    gen_parser.add_argument("vamp", help="Vamp chords (separated by | or ,)")
    gen_parser.add_argument("--form", default="ABAB", help="Song form (e.g. ABACADA)")
    gen_parser.add_argument("--voicing", choices=["closed", "drop2", "drop3", "smooth"], help="Voicing style")
    gen_parser.add_argument("--rhythm", choices=["four-on-the-floor", "bossa", "swing", "waltz"], help="Rhythmic pattern")

    # Negative subcommand
    neg_parser = subparsers.add_parser("negative", help="Perform negative harmony transformation")
    neg_parser.add_argument("input", help="Pitches (space or comma separated) or melody text")
    neg_parser.add_argument("--key", required=True, help="Key root (e.g. C, G, Eb)")

    # Modulate subcommand
    mod_parser = subparsers.add_parser("modulate", help="Suggest paths for modulating between keys")
    mod_parser.add_argument("from_key", help="Starting key (e.g. C major)")
    mod_parser.add_argument("to_key", help="Target key (e.g. G major)")

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
        from core import harmonize, generate_voicing, optimize_voice_leading, name_voicing
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
        
        print("# Suggested Harmonization")
        if args.voicing:
            print(f"*Voicing Style:* {args.voicing}")
            print("| Start | Note | Chord | Roman | Voicing |")
            print("|---|---|---|---|---|")
            
            from core import detect_key, get_diatonic_chords
            pcs = [n["pc"] for n in notes]
            best_key = detect_key(pcs)[0]
            diatonic = get_diatonic_chords(best_key["root"], best_key["scale"])
            
            prev_voicing = []
            for i, note in enumerate(notes):
                candidates = [c for c in diatonic if note["pc"] in c["pcs"]]
                chosen = candidates[0] if candidates else diatonic[0]
                
                if args.voicing == "smooth":
                    voicing = optimize_voice_leading(prev_voicing, chosen["pcs"])
                else:
                    voicing = generate_voicing(chosen["pcs"], style=args.voicing)
                
                prev_voicing = voicing
                print(f"| {note['start']:.2f} | {note['name']} | {chosen['name']} | {chosen['roman']} | {name_voicing(voicing)} |")
        else:
            results = harmonize(notes)
            print("| Start | Note | Chord | Roman |")
            print("|---|---|---|---|")
            for r in results:
                print(f"| {r['start']:.2f} | {r['melody_note']} | {r['chord']} | {r['roman']} |")
        return 0

    elif args.command == "generate":
        from core import parse_vamp, name_pitch_set, generate_voicing, optimize_voice_leading, name_voicing, RHYTHMS
        from generator import generate_song
        
        try:
            vamp_pcs = parse_vamp(args.vamp)
            song = generate_song(vamp_pcs, args.form)
            
            print(f"# Generated Song: {args.form}")
            if args.voicing:
                print(f"*Voicing Style:* {args.voicing}")
            if args.rhythm:
                print(f"*Rhythmic Pattern:* {args.rhythm}")
            print()
            
            prev_voicing = []
            for entry in song:
                print(f"## Section {entry['section']}")
                print(f"*Applied Rules:* {', '.join(entry['rules'])}")
                
                cols = ["Bar", "Chords"]
                if args.voicing: cols.append("Voicing")
                if args.rhythm: cols.append("Rhythm (Offsets)")
                
                print(f"| {' | '.join(cols)} |")
                print(f"| {' | '.join(['---']*len(cols))} |")
                
                for i, chord_pcs in enumerate(entry['vamp']):
                    row = [f"{i+1}", name_pitch_set(chord_pcs)]
                    
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
        from core import negative_transform, parse_pitch_class, name_pitch
        try:
            root = parse_pitch_class(args.key)
            raw_pitches = args.input.replace(",", " ").split()
            pcs = [parse_pitch_class(p) for p in raw_pitches]
            
            neg_pcs = negative_transform(pcs, root)
            
            print(f"# Negative Harmony (Key: {args.key})")
            print(f"**Original:** {' '.join(raw_pitches)}")
            print(f"**Negative:** {' '.join(name_pitch(p) for p in neg_pcs)}")
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        return 0

    elif args.command == "modulate":
        from core import detect_key, suggest_modulation, parse_pitch_class
        
        try:
            # Simple key parser: split into root and scale
            def parse_key_str(s):
                parts = s.split()
                root = parse_pitch_class(parts[0])
                scale = parts[1].lower() if len(parts) > 1 else "major"
                return {"root": root, "scale": scale, "name": f"{parts[0]} {scale}"}
            
            k1 = parse_key_str(args.from_key)
            k2 = parse_key_str(args.to_key)
            
            results = suggest_modulation(k1, k2)
            
            print(f"# Modulation: {k1['name']} -> {k2['name']}")
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
            print("## Dominant Approach")
            print(f"Apply the dominant of the target key: **{results['target_v7']['name']}**")
            
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        return 0

if __name__ == "__main__":
    sys.exit(main())
