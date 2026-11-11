import unittest
from core import (
    RHYTHMS,
    detect_key,
    format_duration,
    generate_voicing,
    harmonize,
    identify_chord,
    name_pitch,
    negative_transform,
    parse_key_string,
    parse_pitch_class,
    suggest_modulation,
)
from generator import RULES, generate_song
from melody_parser import load_melody, parse_lilypond, parse_text
from sandwich import execute_command
from section_grid import assign_bars, build_tree, parse_kv_csv


class TestCore(unittest.TestCase):
    def test_parse_pitch_class(self):
        self.assertEqual(parse_pitch_class("C"), 0)
        self.assertEqual(parse_pitch_class("C#"), 1)
        self.assertEqual(parse_pitch_class("Db"), 1)
        self.assertEqual(parse_pitch_class("B"), 11)
        self.assertEqual(parse_pitch_class("Cb"), 11)
        self.assertEqual(parse_pitch_class("c4"), 0)
        with self.assertRaises(ValueError):
            parse_pitch_class("H")

    def test_name_pitch(self):
        self.assertEqual(name_pitch(0), "c")
        self.assertEqual(name_pitch(1), "db")
        self.assertEqual(name_pitch(1, prefer_sharps=True), "c#")

    def test_format_duration(self):
        self.assertEqual(format_duration(60), "1:00")
        self.assertEqual(format_duration(65), "1:05")
        self.assertEqual(format_duration(120.5), "2:00.50")

    def test_negative_transform(self):
        self.assertEqual(negative_transform([0, 4, 7], 0), [7, 3, 0])
        self.assertEqual(negative_transform([7, 11, 2], 7), [2, 10, 7])

    def test_generate_voicing(self):
        pcs = {0, 4, 7}  # C major
        closed = generate_voicing(pcs, style="closed", base_octave=4)
        self.assertEqual(closed, [48, 52, 55])

        drop2 = generate_voicing(pcs, style="drop2", base_octave=4)
        self.assertEqual(drop2, [40, 48, 55])

    def test_suggest_modulation(self):
        k1 = {"root": 0, "scale": "major"}  # C major
        k2 = {"root": 7, "scale": "major"}  # G major
        results = suggest_modulation(k1, k2)
        pivots = [p["name"] for p in results["pivots"]]
        self.assertIn("c", pivots)
        self.assertIn("emin", pivots)
        self.assertIn("g", pivots)
        self.assertIn("amin", pivots)
        self.assertEqual(results["target_v7"]["name"], "d7")
        self.assertEqual(results["tritone_sub_v7"]["name"], "ab7")

    def test_suggest_modulation_minor_and_kapustin(self):
        k1 = parse_key_string("C major")
        k2 = parse_key_string("A minor")
        rel = suggest_modulation(k1, k2)
        self.assertEqual(len(rel["pivots"]), 7)

        # Kapustin Op. 82 No. 1 -> No. 2 (C major -> g# minor)
        k_gsharp = parse_key_string("g# minor")
        kap = suggest_modulation(k1, k_gsharp)
        self.assertEqual(len(kap["common_tones"]), 2)
        shifts = {ct["pitch"]: ct["shift"] for ct in kap["common_tones"]}
        self.assertEqual(shifts["E"], "T -> P")
        self.assertEqual(shifts["B"], "D -> T")
        self.assertIn("minimally smooth", kap["smoothness"])

    def test_harmonize_uses_functional_variety(self):
        notes = parse_text("c4 d4 e4 f4 g4 a4 b4 c5")
        harm = harmonize(notes, voicing_style="smooth")
        romans = [h["roman"] for h in harm]
        # Should start and end on I and use IV, V, or vi rather than only I/ii/iii
        self.assertEqual(romans[0], "I")
        self.assertEqual(romans[-1], "I")
        self.assertTrue(any(r in ("IV", "V", "vi") for r in romans))
        self.assertTrue(all("voicing_name" in h for h in harm))

    def test_identify_chord(self):
        info = identify_chord({8, 0, 3, 7})  # Abmaj7
        self.assertEqual(info["symbol"], "abmaj7")

    def test_detect_key_triad_ranking(self):
        res = detect_key([0, 4, 7])
        self.assertEqual(res[0]["name"], "c major")

    def test_rhythms(self):
        self.assertIn("bossa", RHYTHMS)
        self.assertEqual(RHYTHMS["four-on-the-floor"][0], (0, 1))

    def test_melody_parser_inline_without_format_flag(self):
        notes = load_melody("c4q d4e e4e f4h")
        self.assertEqual(len(notes), 4)
        self.assertAlmostEqual(notes[-1]["start"], 2.0)
        self.assertAlmostEqual(notes[-1]["duration"], 2.0)

        ly_notes = parse_lilypond(r"\relative c' { c4 d8 e8 f2 }")
        self.assertEqual(len(ly_notes), 4)

    def test_section_grid_readme_example(self):
        subs = parse_kv_csv("A=aaba,B=aabc,C=aabc")
        root = build_tree("ABACABA", subs)
        actual_bars, mismatch = assign_bars(root, total_bars=80, ostinato_bars=4)
        self.assertEqual(actual_bars, 80)
        self.assertEqual(mismatch, 0)

    def test_generator_rules_and_forms(self):
        vamp = [{0, 4, 7, 11}, {2, 5, 9, 0}, {7, 11, 2, 5}, {0, 4, 7, 11}]
        for name, rule_fn in RULES:
            out = rule_fn(vamp)
            self.assertEqual(len(out), len(vamp), f"Rule {name} changed vamp length")
            self.assertTrue(all(len(c) > 0 for c in out))

        song = generate_song(vamp, "ABCDEF", seed=7)
        self.assertEqual([s["section"] for s in song], ["A", "B", "C", "D", "E", "F"])

    def test_cli_execute_command_and_web_app(self):
        for cmd in [
            'parse "c4 d4 e4 f4"',
            'grid --length-sec 240 --tempo 80 --meter 4/4 --top ABACABA --sub "A=aaba,B=aabc,C=aabc"',
            'subs "c e g bb"',
            'key "c d e f g a b"',
            'harmonize "c4 e4 g4 a4" --voicing drop2',
            'generate "ab c eb g | ab c d f" --form ABA --seed 1',
            'negative "c4 e4 g4" --key C',
            'modulate "C minor" "Eb major"',
        ]:
            code, stdout, stderr = execute_command(cmd)
            self.assertEqual(code, 0, f"Command failed: {cmd} -> {stderr}")
            self.assertTrue(len(stdout) > 0)

        from main import _render_page, render_markdown_to_html
        html_out = render_markdown_to_html("# Heading\n| A | B |\n|---|---|\n| 1 | 2 |")
        self.assertIn("<table", html_out)
        page = _render_page(command='key "c e g"', stdout="# Key\n", stderr="<script>alert(1)</script>")
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("&lt;script&gt;", page)


if __name__ == "__main__":
    unittest.main()
