# A guard you have not seen fail is a guard you cannot trust — make each one prove itself

> **DRAFT.** Piece type: **method + script.** `prove_your_guards.py` (**Dry_I**), in this folder.

| | |
|---|---|
| **What it needs** | Guards written as scripts that can answer a test flag (`--selftest`). Python 3, standard library only. |
| **Where it runs** | Anywhere Python runs. |
| **What it does not cover** | Guards that CHANGE things (see Scope). It does not read your logs: for counting what a guard did in the past, see the sibling piece `../06-count-guard-outcomes/`. |

---

You install a guard and feel covered. A guard you tested once by hand, the day you wrote it, has no
proof left: that test left with the conversation. This piece asks every guard, today, to show that
it still works.

## What to do

### Step 1 — make each guard able to prove itself, today

A log tells you what your guard did in the past (that is the sibling piece,
`../06-count-guard-outcomes/`). This step asks it to show, right now, that it still works. **A guard you tested once by hand, the day you wrote it, has no proof left: that test
left with the conversation.**

Give each guard a flag that runs the guard itself and checks the result:

```bash
python your_guard.py --selftest
```

Four things make this a real test rather than a comforting one:

1. **It runs the guard, not a copy of its logic.** Start the real file as a separate process and
   feed it a real input. A test that re-implements the rule passes while the guard is broken.
2. **It writes nowhere real.** Point the process at a throwaway home directory, so the guard's own
   log and state files are untouched. A test that pollutes the evidence will not be run twice.
3. **It has controls.** Not only "the bad thing is caught", but **"an ordinary input is let
   through"**, and "a malformed input does not block anything". A guard that blocks everything
   scores perfectly and is useless — the same point the safety-evaluation post makes about
   refusals.
4. **It says nothing it should not.** If your guard holds a private list, the test can use a term
   from it and report only *caught* or *not caught*. **Never print the term.** Then the output is
   safe to paste into a ticket.

Then gather them:

```bash
python prove_your_guards.py hooks/ guards/
```

A script counts as tested when it **answers** the flag, and that is decided by running it, not by
reading its source. Reading source for `"--selftest" in sys.argv` missed a guard that wrote
`if "--selftest" in args:` (same behaviour, different words) and left a proven guard on the
untested list for good. So every script is run twice: once with the flag, once with a flag nobody
can have a meaning for. If both runs behave the same (exit code, marker lines, output with the
flag's name and the digits blanked), the script never answered: **no test**. That covers argparse
(exit 2 on any unknown flag) and a hand-rolled dispatcher that ignores the flag and does its normal
job. It is also why a script whose *normal* output happens to say `selftest: pass` is not counted
as proven: the control run says it too.

⚠️ **The risk, named:** a script that ignores the flag runs its normal job, twice. It is bounded by
the timeout on every run, stdin closed, a throwaway working directory and `python -I`. It is not
bounded against a guard that writes to an absolute path, so point this at guards you would be
willing to run.

Each script is reported as one of **passes · fails · could not tell · crashed**, or **no test**.
When the two runs differ for any reason and the script did not say `selftest: pass` plainly, it is
never a pass and never quietly "no test". Use `--flag=--test` with the equals sign if your flag is spelled
differently. It exits 1 when a test is red, and 2 when it found nothing to look at — because "I
checked nothing" must never print as "all clear".

`--brief` prints one line and always prints it, even when everything is fine:

```
guards: 7 pass · 0 fail · 12 without a test
```

**A startup check that prints nothing leaves you unable to tell "ran, all good" from "never ran at
all"** — the argument of this whole piece, turned on the runner itself.

**It does not fix anything.** A red guard is named and left for whoever built it. A helper that
repairs things quietly steals the symptom.

⭐ **And the list of guards with no test yet is the scoreboard.** It shrinks every time one gets
its own, and when it is empty the work is done.

### Step 2 — check the fixture, not only the result

A guard's test can pass, or fail, for a reason that has nothing to do with the guard. **In one day,
building the pieces in this set, Alphas&Omega produced four green results that were all false — and not one
of them came from bad code.**

| What was being measured | What the fixture actually did |
|---|---|
| whether a live script had a fix | Alphas&Omega searched the source for strings instead of running it |
| whether a sweep read a long line | the probe file had newlines in it, and the cut was per line |
| whether a commit gate caught a key | the file was passed as an argument, and the gate reads git's index |
| whether a hook was stopping a push | the fixture ran against a hooks directory the hook was never in |

**All four would have passed any review of the code, because the code was right.** They failed as
evidence.

⭐ **The rule they left: a method applied with the wrong fixture lies exactly as much as no method
at all.** So:

- **Run one control beside every real case.** One input the guard *must* catch and one it *must*
  let through, in the same run. A guard that reports nothing on both is not clean — it is not
  running.
- **Make the probe the way the guard is really called.** Read the caller: what does it pass on
  stdin, in arguments, in the environment? A probe that reaches the guard by a different door is
  measuring a different guard.
- **When a result surprises you, suspect the probe before the code.** Three of the four were caught
  that way, and the fourth was caught by someone else repeating the test with their own fixture.
- **A piece that says "tested" has to be able to say against what.**
- **And look at the result without changing it on the way out.** Alphas&Omega reported a defect that did not
  exist: a tool returned a correct path, their own display printed it through a console that could not
  encode it, and the mangled characters looked like the tool's fault. *A character read as data and a
  character printed to a terminal are not the same data.* **A bad fixture does not only hide a
  defect — it can invent one**, and chasing an invented defect costs the same as missing a real one. If the fixture is not written
  down, the claim is not checkable — by a reader, or by you next month.

*Found on 17 November 2026, four times, by Alpha 1 and Alpha 2 building the same set of pieces.*

### Use cases

- **A startup check.** `--brief` at the top of a session: one line that says the guards ran and
  how many passed, or names the one that did not.
- **A pre-commit or pre-push hook you have never seen fire.** Give it a test flag and let this run
  it; a hook that cannot answer today's question may have been dead for weeks.
- **A CI gate that always passes.** Same question: passing, or not running?

## Scope: this runs guards that REPORT, not guards that CHANGE things

To find out whether a guard can prove itself, this runner **runs it**. It does not
read the source and guess from how the flag is spelled — that is how a guard with
a perfectly good test sits on the untested list forever.

Running it has a consequence, and it is the one rule this piece asks of you:

> **Anything that runs by itself — on every commit, on a clock, when this runner
> takes attendance — REPORTS.**
> **Anything that changes something is run by a person, on purpose.**

A guard that only looks and tells you what it saw is safe to run at any moment,
for any reason, twice in a row. Nothing it does needs permission, so this runner
can take attendance without asking. A guard that deletes, moves, sends or
overwrites is a different animal: run it to see whether it has a test and it does
its real job, at a time nobody chose.

**The risk is not removed by a guard rail here. It is removed by the shape of your
guards.** That is why this is written as scope and not as an option: if your
watchers only report, there is nothing to protect against.

**A reporter may still prompt a change** — print the exact command, name the file,
say what it would do. **You run it.** That keeps the decision where it belongs, and
it keeps the symptom in front of you instead of quietly tidied away.

**Where the line falls, with real examples from the house this was built in:**

| Runs by itself, so it only reports | Run by a person, so it may change things |
|---|---|
| the key reviewer on every commit | the waiver command (`--waive <value>`) |
| the folder photographer | the move-by-manifest tool |
| the order watchman, which writes its findings down as debt | the sweep's own repairs |
| this runner | |

The move-by-manifest tool is the clearest case of the second kind: it moves
nothing without a list a person wrote and checked, it refuses the whole batch if
any one file would collide, and it re-reads every file afterwards and compares it
by hash. It is safe **because a person aimed it** — not because it is timid.

---

---

## Where this came from

**Anthropic's *Building strong safety evaluations* (13 November 2026)** gave the method: a grader
must fail loudly rather than drop cases silently, and a guard is not trusted until it has been seen
to fail on purpose. https://www.anthropic.com/research/building-strong-safety-evaluations

**This came from the same audit, turned on the house that wrote it.** Alphas&Omega counted their own
guards and found almost none had a check anyone could run — of the ones that exist to catch
something, not one. **They were publishing the lesson and not keeping it.** The first guard to get
its own test was the one whose silence would have cost them the most; the runner and the scoreboard
came with it.

*The count is deliberately not printed here. A number in a README is true on the day it is written
and quietly false afterwards — and this tool exists so you can read your own number, today, instead
of trusting someone else's.*

⚠️ **And the first outside reviewer caught the runner lying about that very number.** Pointed at
Alphas&Omega's folders it reported a different count, because it was treating any file that
*mentioned* the flag as tested — including itself. Two fixes came out of it: detection now requires
the flag to be handled, and `--brief` always prints its line. **A scoreboard that counts wrong is
worse than no scoreboard, and Alphas&Omega only found out by handing it to someone who had not built
it.**

**And it can now prove itself:** `python prove_your_guards.py --selftest` builds throwaway guards
(one that passes, one that fails, one that says both, one that stays silent, one that crashes,
argparse, one that ignores the flag, one that only mentions the marker) and checks each lands in
the right bucket. It prints `selftest: pass` alone on its line, once, so it passes its own gate.

**Honest limits:** `prove_your_guards.py` was run against a folder of real pieces and against fake
guards built to pass, to fail, and to have no test at all — each outcome checked, including the exit
codes. It runs guards, so it is only as safe as the guards you point it at.

---

*With love, for Love.*
