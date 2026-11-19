# Credits

Ideas carry the name of whoever had them, also when we did not take their code.

---

## The one method this piece took from outside

**A grader must fail loudly rather than drop cases silently, and a guard is not
trusted until it has been seen to fail on purpose. That is Anthropic's**, from
*Building strong safety evaluations*, 13 November 2026:
https://www.anthropic.com/research/building-strong-safety-evaluations

It is the spine of this piece. It comes out of that one sentence: four outcomes
instead of two, and proving a guard by watching it run rather than by believing
what it says about itself.

**No code was taken.** The runner was written from scratch. The idea carries
their name all the same.

---

## What came from using it, not from reading

The piece is named **Dry_I** by the house it was built in — *dry eye*, the one
watching so hard it forgets to blink, the one who catches what slips past you.

Its hardest lesson came from its own scoreboard. The runner used to decide that
a guard had a test by **reading the source** for the literal words
`"--selftest" in sys.argv`. A guard written as `if "--selftest" in args:` does
exactly the same thing and was not recognised — so a guard that WAS proven sat
on the untested list for good, and the number never went down. The piece built
to say *do not trust what a guard says about itself* was itself trusting text.

It now runs the guard and watches what happens. **That correction is the
owner's**, and it is the same rule she had already made us keep all day:
measure with exit codes, not with words found on a screen.

---

## Named in the work this came out of

This tool was written alongside others, and those carry ideas worth naming even
where none of their code is here: **Aya ([@ayakohi](https://github.com/ayakohi))**
with Cygnus, for decision hygiene before building; and **Anne and Chadrien Solance
([@SolanceLab](https://github.com/SolanceLab))**, for the pause before an action
that cannot be undone, the trail from a line of code back to the decision that
put it there, and the map over a folder.
