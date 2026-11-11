# sandwich 🥪
a music theory toolkit with an emphasis on tritone subs, functional voice-leading, and recursion

### howto

* `sandwich.py parse` reads melodies from midi, lilypond, musicxml, or inline plain text
* `sandwich.py grid` builds song structures based on recursion and preserves "shapes" across sections
* `sandwich.py subs` finds tritone substitutions for any chord ranked by tritone preservation and common tones
* `sandwich.py key` guesses the scale/key given some notes
* `sandwich.py harmonize` suggests functional diatonic chords and voice-leadings given a melody
* `sandwich.py generate` builds an entire song from a vamp of chords that you supply
* `sandwich.py negative` reflects pitches or melodies across the major/minor third axis of a key
* `sandwich.py modulate` finds pivot chords, dominant/tritone-sub approaches, and common-tone functional voice-leading between keys

### examples
```bash
# parse a melody into a note list table
python3 src/sandwich.py parse "c4q d4e e4e f4q g4h"

# build a song grid with recursive structure
python3 src/sandwich.py grid --length-sec 240 --tempo 80 --meter 4/4 --top ABACABA --sub "A=aaba,B=aabc,C=aabc"

# guess a key
python3 src/sandwich.py key "c d e f g a b"

# get chords and smooth voice-leading for a melody
python3 src/sandwich.py harmonize "c4 d4 e4 f4 g4 a4 b4 c5" --voicing smooth

# find tritone subs
python3 src/sandwich.py subs "c e g bb"

# generate a song from a vamp using pure python inference
python3 src/sandwich.py generate "ab c eb g | ab c d f | ab c eb g | ab c db f" --form ABACADAEADACABA --voicing drop2 --rhythm bossa

# transform a melody or chord using negative harmony
python3 src/sandwich.py negative "c4 e4 g4 b4" --key C

# analyze modulation paths and functional voice-leading (Kapustin Op. 82 style)
python3 src/sandwich.py modulate "C major" "g# minor"
```

### why?
read the pdf (`april-2017-paper-final.pdf`) if you are curious about the state of music theory back in 2017!

100% python because let's keep it weird :0
