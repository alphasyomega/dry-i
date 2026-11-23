# Dry_I — the inspector who makes every guard prove itself

> **He lines your guards up and asks each one to show it still works — today, not the day you wrote it.** *A guard you have not seen fail is a guard you cannot trust.*

| | |
|---|---|
| **What it needs** | Guards written as scripts that can answer a test flag (`--selftest`). Python 3, standard library only. |
| **Where it runs** | Anywhere Python runs. |
| **What it does not cover** | Guards that CHANGE things (see Scope). And it does not read logs: it asks your guards to prove themselves NOW, not to account for what they did last month. |

---

## 🕵️ What he is for

**You install a guard and feel covered.** A guard you tested once by hand, the day you wrote it,
has **no proof left** — that test walked out with the conversation.

Dry_I asks every guard, right now, to show that it still works. **It runs them. It does not read
their source and guess.**

| | |
|---|---|
| ✅ **Use him on** | guards that only LOOK and report — checkers, watchers, linters, hooks that warn |
| 🚫 **Not for** | guards that CHANGE things. Running one to test it would do its real job, at a time nobody chose |


## 🛠️ What to do

### ✍️ Give each guard a way to prove itself

A log tells you what your guard did in the past. This asks it to show, right now, that it
still works. **A guard you tested once by hand, the day you wrote it, has no proof left: that test
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

### 💡 Where this earns its place

- **A startup check.** `--brief` at the top of a session: one line that says the guards ran and
  how many passed, or names the one that did not.
- **A pre-commit or pre-push hook you have never seen fire.** Give it a test flag and let this run
  it; a hook that cannot answer today's question may have been dead for weeks.
- **A CI gate that always passes.** Same question: passing, or not running?

## 📏 Limits and scope — reporters, not changers

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

## ⚠️ Warnings — read before you run him

> 🔴 **HE RUNS YOUR GUARDS. POINT HIM ONLY AT GUARDS YOU WOULD RUN YOURSELF.**
> Testing a script means starting it. A script that ignores the flag simply does its normal job.

🕵️ **A script that ignores the flag runs its normal job, twice.** Each run is bounded by a
timeout, stdin closed, a throwaway working directory and `python -I`. **It is not bounded against
a guard that writes to an absolute path.**

📏 **What he does not cover, said plainly:**

- 🔁 **Guards that change things.** Deleting, moving, sending, overwriting — those are run by a
  person, on purpose. See the scope above.
- 📜 **He does not read logs.** He asks your guards to prove themselves **now**, not to account
  for what they did last month.
- 🎯 **He answers one question:** *does this guard still work today?* Not whether it is the right
  guard, not whether it covers what you think it covers.

*He is only as safe as the guards you point him at.*

## 🙏 Where this came from

**Anthropic's *Building strong safety evaluations* (13 November 2026)** gave the method: a grader
must fail loudly rather than drop cases silently, and a guard is not trusted until it has been seen
to fail on purpose. https://www.anthropic.com/research/building-strong-safety-evaluations

*No count is printed here on purpose. A number in a README is true the day it is written and
quietly false afterwards — and this tool exists so you can read your own, today, instead of
trusting someone else's.*

**And it can now prove itself:** `python prove_your_guards.py --selftest` builds throwaway guards
(one that passes, one that fails, one that says both, one that stays silent, one that crashes,
argparse, one that ignores the flag, one that only mentions the marker) and checks each lands in
the right bucket. It prints `selftest: pass` alone on its line, once, so it passes its own gate.

**Honest limits:** `prove_your_guards.py` was run against a folder of real pieces and against fake
guards built to pass, to fail, and to have no test at all — each outcome checked, including the exit
codes. It runs guards, so it is only as safe as the guards you point it at.

---

*With love, for Love.*
