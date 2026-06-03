# sandwich 🥪

a music theory cli with an emphasis on tritone subs and algorithmic forms :)

### how to use it

* `sandwich.py parse`: reads melodies from midi, lilypond, musicxml, or just plain text
* `sandwich.py grid`: builds song structures based on recursion; preserves "shapes" across sections
* `sandwich.py subs`: finds tritone substitutions for any chord ranked by common tones
* `sandwich.py key`: guesses the scale/key based on notes you provide
* `sandwich.py harmonize`: suggests some chords based on melody you provide

### examples
```bash
# 1. parse a melody (gives you a note list table)
python3 sandwich.py parse "c4 d4 e4 f4 g4" --format text

# 2. build a song grid (recursive structure)
python3 sandwich.py grid --length-sec 240 --tempo 80 --meter 4/4 --top ABACABA --sub "A=aaba,B=aabc,C=aabc"

# 3. guess a key
python3 sandwich.py key "c d e f g a b"

# 4. get chords for a melody (auto-harmonization)
python3 sandwich.py harmonize "c4 d4 e4 f4 g4" --format text

# 5. find tritone substitutions
python3 sandwich.py subs "c e g bb"
```

### why?
read the pdf (`april-2017-paper-final.pdf`) for the deep theory behind it

all python because let's keep it weird! :0
