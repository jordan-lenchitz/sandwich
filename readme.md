# sandwich 🥪

a music theory toolkit with an emphasis on tritone subs and algorithmic structure. 

### how to use it
now there's a main entry point called `sandwich.py`. it's way easier.

* `sandwich.py parse`: reads melodies from midi, lilypond, musicxml, or just plain text.
* `sandwich.py grid`: builds song structures based on recursion. preserves "shapes" across sections.
* `sandwich.py subs`: find tritone substitutions for any chord. ranked by common tones.
* `sandwich.py key`: tell it some notes and it'll guess the scale/key.
* `sandwich.py harmonize`: give it a melody and it'll suggest some diatonic chords.

### examples
```bash
# guess a key
python3 sandwich.py key "c d e f g a b"

# get chords for a melody
python3 sandwich.py harmonize "c4 d4 e4 f4 g4" --format text

# still does the tritone stuff
python3 sandwich.py subs "c e g bb"
```

### why?
read the pdf (`april-2017-paper-final.pdf`) for the deep theory behind it. i wrote it in 2017. 

it's all python. keep it weird. :0
