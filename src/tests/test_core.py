import unittest
from core import parse_pitch_class, name_pitch, format_duration

class TestCore(unittest.TestCase):
    def test_parse_pitch_class(self):
        self.assertEqual(parse_pitch_class("C"), 0)
        self.assertEqual(parse_pitch_class("C#"), 1)
        self.assertEqual(parse_pitch_class("Db"), 1)
        self.assertEqual(parse_pitch_class("B"), 11)
        self.assertEqual(parse_pitch_class("Cb"), 11)
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
        from core import negative_transform
        # Key of C (root 0): axis is 3.5. 2*3.5 = 7.
        # C (0) -> (7-0) = 7 (G)
        # E (4) -> (7-4) = 3 (Eb)
        # G (7) -> (7-7) = 0 (C)
        self.assertEqual(negative_transform([0, 4, 7], 0), [7, 3, 0])
        
        # Key of G (root 7): axis is 7 + 3.5 = 10.5. 2*10.5 = 21.
        # G (7) -> (21-7) % 12 = 14 % 12 = 2 (D)
        # B (11) -> (21-11) % 12 = 10 (Bb)
        # D (2) -> (21-2) % 12 = 19 % 12 = 7 (G)
        self.assertEqual(negative_transform([7, 11, 2], 7), [2, 10, 7])

    def test_generate_voicing(self):
        from core import generate_voicing
        pcs = {0, 4, 7} # C major
        closed = generate_voicing(pcs, style="closed", base_octave=4)
        self.assertEqual(closed, [48, 52, 55]) # C4, E4, G4
        
        drop2 = generate_voicing(pcs, style="drop2", base_octave=4)
        # Closed: [48, 52, 55]. Drop second highest (52) -> 40.
        # Sorted: [40, 48, 55]
        self.assertEqual(drop2, [40, 48, 55])

    def test_suggest_modulation(self):
        from core import suggest_modulation
        k1 = {"root": 0, "scale": "major"} # C major
        k2 = {"root": 7, "scale": "major"} # G major
        results = suggest_modulation(k1, k2)
        # C major and G major share C major, E minor, G major, A minor.
        pivots = [p["name"] for p in results["pivots"]]
        self.assertIn("c", pivots)
        self.assertIn("emin", pivots)
        self.assertIn("g", pivots)
        self.assertIn("amin", pivots)
        self.assertEqual(results["target_v7"]["name"], "d7")

    def test_rhythms(self):
        from core import RHYTHMS
        self.assertIn("bossa", RHYTHMS)
        self.assertEqual(RHYTHMS["four-on-the-floor"][0], (0, 1))

if __name__ == "__main__":
    unittest.main()
