#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prove_your_guards.py — runs every guard's own test, and names the ones with none.

This asks every guard to prove, right now, that it still works.

    python prove_your_guards.py hooks/ guards/
    python prove_your_guards.py . --flag=--check
    python prove_your_guards.py hooks/ --brief
    python prove_your_guards.py --selftest

It looks in the folders you name and runs every script in its own process with
a test flag (`--selftest` by default). Whether a script HAS a test is decided by
what it did when it ran, never by how its source is spelled. Each guard knows how
to test itself; this only gathers them and counts.

⭐ THE LIST OF THE ONES WITH NO TEST IS THE SCOREBOARD. It gets shorter every
time one gets its own, and when it is empty the work is done.

🔑 IT REPORTS, IT DOES NOT FIX. If a guard fails, it says so and stops there:
what broke and why belongs to whoever built that piece. A helper that fixes
things quietly steals the symptom from you.

OUTCOMES, the ones you should ask of any guard:
    passes · fails · could not tell (it hung, or said nothing) · crashed
plus one for a script that never answered the flag: no test.

Exit code: 1 if any test failed, 0 otherwise. A missing test is not a failure —
it is a line on the scoreboard. Standard library only.
"""
import re
import os
import sys
import argparse
import subprocess
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ME = os.path.basename(os.path.abspath(__file__))


# Directories that never hold a guard. Walking into them only counts files that
# are somebody else's code, or copies of ours.
PRUNED = (".git", "__pycache__", "node_modules", ".venv", "venv", "site-packages",
          "dist", "build", ".mypy_cache", ".cache")


# Folders are walked recursively (--no-recurse reads only the top level of each
# folder you name), because a guard one folder down is still a guard. The report
# always says how far it looked and what it skipped.
def scripts_in(folders, missing, stats, recurse=True):
    """Yields .py paths. stats gets 'folders' and 'files' counts and a 'pruned' set."""
    for folder in folders:
        if not os.path.isdir(folder):
            # A folder you named and I could not read is not a folder with
            # nothing in it. Printing it and carrying on let a mistyped path
            # produce a green run over an inventory that was never looked at.
            missing.append(folder)
            continue
        for root, dirs, files in os.walk(folder):
            stats["folders"] += 1
            if recurse:
                for d in dirs:
                    if d in PRUNED:
                        stats["pruned"].add(d)
                dirs[:] = sorted(d for d in dirs if d not in PRUNED)
            else:
                dirs[:] = []
            for name in sorted(files):
                if not name.endswith(".py") or name == ME:
                    continue
                path = os.path.join(root, name)
                if os.path.isfile(path):
                    stats["files"] += 1
                    yield path


def looked_line(stats):
    return "looked in %d folder%s, %d file%s considered" % (
        stats["folders"], "" if stats["folders"] == 1 else "s",
        stats["files"], "" if stats["files"] == 1 else "s")


def pruned_line(stats):
    if not stats["pruned"]:
        return ""
    return "skipped by name: %s" % ", ".join(sorted(stats["pruned"]))


# THE ONE LINE A SELF TEST MUST PRINT.
#
# Reading the source to decide whether a script has a test is guessing, and
# guessing certified a script that only mentioned the flag. So the test says so
# itself, in its own words, on its own line:
#
#     selftest: pass        or        selftest: fail
#
# Alone on its line, and exactly once. A line with anything else on it does not
# count, and two marker lines mean the guard did not say one thing.
#
# Anything else — no line, an exit code with no line, a crash — is "could not
# tell", and that is NOT a pass. A guard cannot be green because a runner
# squinted at its source code.
# The marker must be the WHOLE line (matched with fullmatch, below), not a
# substring found anywhere. Spacing around the colon and around the line is free;
# any other character on the line disqualifies it.
MARKER = re.compile(r"\s*selftest\s*:\s*(pass|fail)\s*", re.I)


def marker_lines(*streams):
    """Every line, across all the streams together, that is only the marker."""
    found = []
    for text in streams:
        for line in text.splitlines():
            m = MARKER.fullmatch(line)
            if m:
                found.append(m.group(1).lower())
    return found


# HOW "NO TEST" IS TOLD APART FROM "A TEST THAT SAID NOTHING", BY RUNNING.
#
# Every script is run twice: once with the test flag, once with a control flag
# that no script can have a meaning for. If the two runs behave the same (same
# exit code, same marker lines, same output once the flag's own name and the
# digits are blanked out) the script did not answer the flag: it has no test.
# That covers argparse (exit 2 on any unknown flag) and a hand-rolled dispatcher
# that ignores what it does not know and does its normal job. The control is also
# what stops a script whose NORMAL job prints `selftest: pass` from being
# counted as proven: the control run prints it too, so it was not a response.
#
# The risk accepted, named: a script that ignores the flag runs its normal job,
# twice. Bounded by: the timeout on every run, stdin closed (a hook waiting for
# input gets end-of-file, not a hang), a fresh throwaway working directory per run (relative
# writes land there), and python -I. Absolute paths a guard writes to are not
# contained. Run this on guards you would be willing to run.
#
# Fail closed: when the two runs differ for any reason, the script is treated as
# having answered, and unless it said `selftest: pass` plainly it is "could not
# tell" or "crashed", never a pass and never quietly "no test".
CONTROL = "--prove-your-guards-control"
NO_TEST = "no test"


def _once(path, arg, timeout, cwd):
    """(rc, stdout, stderr), or the string 'timeout' / 'crash: ...'. Never raises."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    try:
        p = subprocess.run([sys.executable, "-I", os.path.abspath(path), arg],
                           capture_output=True, timeout=timeout, cwd=cwd,
                           stdin=subprocess.DEVNULL, env=env)
    except subprocess.TimeoutExpired:
        return "timeout"
    except Exception as e:
        return "crash: %s: %s" % (e.__class__.__name__, e)
    return (p.returncode,
            (p.stdout or b"").decode("utf-8", "replace"),
            (p.stderr or b"").decode("utf-8", "replace"))


def _shape(res, arg, cwd, other):
    """What a run looked like, with its own flag name and its own scratch dir
    blanked. Digits are NOT blanked: 'mode 1' and 'mode 2' are different answers,
    and when in doubt the runs count as different (fail closed -> never 'no test')."""
    rc, out, err = res
    def blank(t):
        for spelling in {cwd, cwd.replace("\\", "/"), os.path.realpath(cwd)}:
            t = t.replace(spelling, "<CWD>")
        return t.replace(arg, "<ARG>").replace(other, "<ARG>").strip()
    return rc, marker_lines(out, err), blank(out), blank(err)


def run(path, flag, timeout):
    """(outcome, detail). It never raises: a runner that crashes reports nothing."""
    # Each run gets its own fresh directory: a normal job that creates state
    # ("created", then "already exists") must not look like an answer to the flag.
    with tempfile.TemporaryDirectory() as scratch:
        res = _once(path, flag, timeout, scratch)
    if res == "timeout":
        # Hung on the flag. A control run would hang too and tell us nothing.
        return "could not tell", "did not finish in %d seconds" % timeout
    if isinstance(res, str):
        return "crashed", res[7:]
    with tempfile.TemporaryDirectory() as scratch2:
        ctl = _once(path, CONTROL, timeout, scratch2)
    if isinstance(ctl, str):
        # The comparison that decides "no test" could not be made. Fail closed:
        # never a pass, never quietly "no test".
        return "could not tell", ("control run (unknown flag) did not give a clean "
                                  "result: %s" % ctl)
    rc, out, err = res
    said = marker_lines(out, err)

    # Did the script answer the flag? Only an unknown control run can say.
    if _shape(res, flag, scratch, CONTROL) == _shape(ctl, CONTROL, scratch2, flag):
        return NO_TEST, "behaves the same with an unknown flag (exit %d)" % rc

    lines = out.strip().splitlines()
    last = lines[-1].strip() if lines else ""
    if not said:
        if rc != 0:
            return "crashed", ("exited %d and never printed `selftest: pass` "
                               "or `selftest: fail` alone on a line" % rc)
        return "could not tell", ("exited 0 and never printed `selftest: pass` "
                                  "or `selftest: fail` alone on a line")
    # A guard that says two things has not reported a result; do not pick one.
    if len(said) > 1:
        return "fails", ("printed %d marker lines: %s"
                         % (len(said), ", ".join(said)))[:70]
    if said[0] == "fail":
        return "fails", (last or "said selftest: fail")[:70]
    if rc != 0:
        return "fails", ("said selftest: pass but exited %d" % rc)
    return "passes", last[:70]


# THE RUNNER'S OWN TEST. A piece that says "every guard must be able to prove
# itself today" has to be able to. What it proves is the one thing that matters
# here: that it CLASSIFIES correctly. It builds throwaway guards in a temp
# directory, runs the real classifier (run()) over each, and checks each one
# lands in the right bucket. Each fixture is a tiny script, so the whole test
# takes a couple of seconds: a self-test nobody runs because it is slow is a
# self-test that does not exist.
_ARGV = "import sys\nflag = '--selftest' in sys.argv[1:]\n"
FIXTURES = [
    ("said pass", _ARGV + "print('selftest: pass') if flag else print('job')\n",
     "passes"),
    ("said fail", _ARGV + "print('selftest: fail') if flag else print('job')\n",
     "fails"),
    ("said both", _ARGV + "if flag:\n    print('selftest: pass')\n"
                  "    print('selftest: fail')\nelse:\n    print('job')\n",
     "fails"),
    ("pass, exit 1", _ARGV + "if flag:\n    print('selftest: pass')\n"
                     "    sys.exit(1)\nprint('job')\n",
     "fails"),
    ("accepted, silent", _ARGV + "if not flag:\n    print('job')\n",
     "could not tell"),
    ("crashes on flag", _ARGV + "if flag:\n    raise RuntimeError('boom')\n"
                        "print('job')\n",
     "crashed"),
    ("argparse", "import argparse\nargparse.ArgumentParser().parse_args()\n"
                 "print('job')\n",
     NO_TEST),
    ("ignores the flag", "print('job')\n",
     NO_TEST),
    ("only mentions it", _ARGV + "if flag:\n"
                         "    print('a good test would print selftest: pass here')\n"
                         "else:\n    print('job')\n",
     "could not tell"),
    ("normal job says it", "print('selftest: pass')\n",
     NO_TEST),
]


def selftest():
    """Prints `selftest: pass` or `selftest: fail`, alone on its line, once."""
    problems = []
    try:
        with tempfile.TemporaryDirectory() as tmp:
            for i, (label, source, expected) in enumerate(FIXTURES):
                path = os.path.join(tmp, "guard_%d.py" % i)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(source)
                got, detail = run(path, "--selftest", 30)
                mark = "ok " if got == expected else "BAD"
                print("  %s %-18s -> %-15s (wanted %s)" % (mark, label, got, expected))
                if got != expected:
                    problems.append(label)
    except Exception as e:
        problems.append("the self-test itself crashed: %s: %s"
                        % (e.__class__.__name__, e))
    if problems:
        print("  misclassified: %s" % "; ".join(problems))
        print("selftest: fail")
        return 1
    print("selftest: pass")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("folders", nargs="*", help="folders holding your guards")
    p.add_argument("--selftest", action="store_true",
                   help="prove this runner classifies correctly, and nothing else")
    # Write it as --flag=--test, with the equals sign: a value that starts with
    # a dash looks like another option otherwise.
    p.add_argument("--flag", default="--selftest",
                   help="the test flag, written as --flag=--test (default --selftest)")
    p.add_argument("--timeout", type=int, default=180, help="seconds per guard (default 180)")
    p.add_argument("--brief", action="store_true", help="one line, for a startup check")
    p.add_argument("--no-recurse", action="store_true",
                   help="look only at the top level of each folder you name "
                        "(use it when a folder holds sub-projects or vendored code "
                        "whose guards are not yours to prove)")
    p.add_argument("--allow-untested", action="store_true",
                   help="exit 0 even when some guards have no test (scoreboard view)")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    if not a.folders:
        p.error("the following arguments are required: folders")

    missing, paths = [], []
    stats = {"folders": 0, "files": 0, "pruned": set()}
    paths = list(scripts_in(a.folders, missing, stats, not a.no_recurse))

    # Nothing found is NOT "all clear". Saying "they all pass" after looking at
    # zero files is the same silence this piece is about.
    if not paths:
        print("\n  COULD NOT LOOK: no .py files in %s" % ", ".join(a.folders))
        print("  (%s%s)\n" % (looked_line(stats),
                              "; " + pruned_line(stats) if stats["pruned"] else ""))
        return 2

    results = [(x,) + run(x, a.flag, a.timeout) for x in paths]
    without = [r[0] for r in results if r[1] == NO_TEST]
    with_test = [r for r in results if r[1] != NO_TEST]
    rows = [(os.path.basename(r[0]), r[1], r[2]) for r in with_test]
    # Four outcomes means FOUR. Putting "could not tell" in the same bucket as
    # "fails" throws away the very distinction this piece exists to name.
    failing = [r for r in rows if r[1] == "fails"]
    unclear = [r for r in rows if r[1] in ("could not tell", "crashed")]

    # Three ways to end badly, and they are not the same thing:
    #   2 · I could not look — a folder you named is not there, or nothing is tested
    #   1 · I looked and something failed
    #   0 · I looked and everything I could test passed
    # A guard with no test is not a pass. --allow-untested turns that into a
    # scoreboard instead of a gate, on purpose and by your choice, never mine.
    blind = (bool(missing) or bool(unclear) or (not with_test)
             or (without and not a.allow_untested))

    if a.brief:
        # One line, always, even when everything is fine. A startup check that
        # prints nothing leaves you unable to tell "ran, all good" from "never
        # ran at all" — which is the whole argument of this piece, turned on
        # the runner itself.
        print("guards: %d pass · %d fail · %d cannot tell · %d without a test · %s%s%s"
              % (len(rows) - len(failing) - len(unclear), len(failing),
                 len(unclear), len(without), looked_line(stats),
                 ("  · %d folder(s) not found" % len(missing)) if missing else "",
                 ("  → " + ", ".join(r[0] for r in failing)) if failing else ""))
        return 1 if failing else (2 if blind else 0)

    width = max([len(r[0]) for r in rows] + [20])
    print()
    print("  GUARDS — their own test, actually run")
    print()
    for name, outcome, detail in rows:
        print("  %-*s  %-16s %s" % (width, name, outcome, detail))
    if not rows:
        print("  (none of them has a test yet)")

    print()
    print("  %d with a test, %d with none yet." % (len(with_test), len(without)))
    print("  %s." % looked_line(stats))
    if pruned_line(stats):
        print("  %s." % pruned_line(stats))
    if missing:
        print()
        print("  COULD NOT LOOK — you named %d folder(s) that are not there:"
              % len(missing))
        for folder in missing:
            print("    - %s" % folder.replace("\\", "/"))
        print("  A path you mistyped is not an inventory that came back clean.")
    if without:
        print()
        print("  These are the scoreboard. It gets shorter on its own.")
        for path in without:
            print("    - %s" % path.replace("\\", "/"))
    print()
    if failing:
        print("  %d with a red test. This runner does not fix that:" % len(failing))
        print("  it says so, and whoever built the piece looks at it.")
        print()
        return 1
    if blind:
        print("  Everything with a test passed — and that is not the same as")
        print("  everything being tested. Pass --allow-untested when you want")
        print("  this as a scoreboard instead of a gate.")
        print()
        return 2
    if without:
        print("  Everything with a test passed. %d still have none, and you asked"
              % len(without))
        print("  for a scoreboard rather than a gate, so this is not a failure.")
    else:
        print("  Every guard here has a test, and every test passed.")
    print()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("\n  the runner crashed (%s: %s) and needs a look by hand.\n"
              % (e.__class__.__name__, e))
        sys.exit(3)
