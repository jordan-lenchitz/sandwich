import unittest
from tritone_subs import infer_root, generate_candidates, rank_candidates

class TestTritoneSubs(unittest.TestCase):
    def test_infer_root_dominant7(self):
        # C7: C E G Bb -> 0 4 7 10
        pcs = {0, 4, 7, 10}
        self.assertEqual(infer_root(pcs), 0)

    def test_infer_root_min7(self):
        # Am7: A C E G -> 9 0 4 7
        pcs = {9, 0, 4, 7}
        self.assertEqual(infer_root(pcs), 9)

    def test_generate_candidates_c7(self):
        # C7
        pcs = {0, 4, 7, 10}
        cands = generate_candidates(pcs, "C7")
        # Gb7 should be in there
        labels = [c['label'] for c in cands]
        self.assertTrue(any('gb' in l.lower() for l in labels))
        
        # Check if gb7 is ranked highly
        ranked = rank_candidates(cands)
        top_labels = [c['label'] for c in ranked[:3]]
        # Gb7 preserves the tritone (4, 10) -> (4, 10) or (10, 4)
        # Gb7: Gb Bb Db Fb -> 6 10 1 4. Contains 4 and 10.
        self.assertTrue(any('gb7' in l.lower() for l in top_labels), f"Gb7 not in top 3: {top_labels}")

if __name__ == '__main__':
    unittest.main()
