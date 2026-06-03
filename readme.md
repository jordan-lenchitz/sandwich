# sandwich 🥪
a music theory toolkit with an emphasis on tritone subs and recursion

### howto

* `sandwich.py parse` reads melodies from midi, lilypond, musicxml, or just plain text
* `sandwich.py grid` builds song structures based on recursion and preserves "shapes" across sections
* `sandwich.py subs` finds tritone substitutions for any chord ranked by common tones
* `sandwich.py key` guesses the scale/key given some notes
* `sandwich.py harmonize` suggests some diatonic chords given a melody
* `sandwich.py generate` builds an entire song from a vamp of 4 to 8 chords that you supply

### examples
```bash
# parse a melody into a note list table
python3 sandwich.py parse "c4 d4 e4 f4 g4" --format text

# build a song grid with recursive structure
python3 sandwich.py grid --length-sec 240 --tempo 80 --meter 4/4 --top ABACABA --sub "A=aaba,B=aabc,C=aabc"

# guess a key
python3 sandwich.py key "c d e f g a b"

# get chords for a melody 
python3 sandwich.py harmonize "c4 e4 g4 a4" --format text

# find tritone subs
python3 sandwich.py subs "c e g bb"

# generate a song from a vamp using pure python inference
python3 sandwich.py generate "ab c eb g | ab c d f | ab c eb g | ab c db f" --form ABACADAEADACABA
```

### why?
read the pdf (`april-2017-paper-final.pdf`) if you are curious about the state of music theory back in 2017!

100% python because let's keep it weird :0
