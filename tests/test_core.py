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

if __name__ == "__main__":
    unittest.main()
