#!/usr/bin/env python3
"""Formal Logic engine, no-dependency fallback for when z3 is not installed.

Same spec and same report shape as entail.py, but it checks worlds by brute
force instead of with a solver:

- bool variables: every combination is tried, so verdicts are exact
  (up to 20 bool variables, about a million worlds).
- int / real variables: only a bounded set of candidate values is tried
  (every number that appears in the expressions, plus and minus one, and 0).
  A counterexample it finds is real. "Entailed" is only proven inside that
  range, and the report says so.

Usage: python3 entail_fallback.py spec.json
"""
import itertools
import json
import re
import sys


class Bad(Exception):
    pass


def And(*xs):
    return all(xs)


def Or(*xs):
    return any(xs)


def Not(x):
    return not x


def Implies(a, b):
    return (not a) or b


def Xor(a, b):
    return bool(a) != bool(b)


def If(c, a, b):
    return a if c else b


def Distinct(*xs):
    return len(set(xs)) == len(xs)


SAFE = {"And": And, "Or": Or, "Not": Not, "Implies": Implies, "Xor": Xor,
        "If": If, "Distinct": Distinct, "True": True, "False": False}
MAX_WORLDS = 2_000_000


def candidates(kind, exprs):
    if kind in ("bool", "boolean"):
        return [False, True]
    nums = set()
    for e in exprs:
        for m in re.findall(r"(?<![A-Za-z_])-?\d+(?:\.\d+)?", e):
            v = float(m) if "." in m else int(m)
            nums.update({v - 1, v, v + 1})
    nums.add(0)
    if kind in ("real", "float"):
        extra = {x + 0.5 for x in nums}
        nums |= extra
    return sorted(nums)


def evaluate(expr, world):
    env = dict(SAFE)
    env.update(world)
    return bool(eval(expr, {"__builtins__": {}}, env))  # noqa: S307 - local spec


def render(world, labels):
    rows = []
    for name in sorted(world):
        v = world[name]
        label = labels.get(name, name)
        if isinstance(v, bool):
            rows.append(f"    {'TRUE ' if v else 'FALSE'}  {label}")
        else:
            rows.append(f"    {v:>7}  {label}")
    return "\n".join(rows) if rows else "    (no variables to report)"


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: entail_fallback.py <spec.json>")
    spec = json.load(open(sys.argv[1]))
    vars_spec = spec.get("vars", {})
    labels = spec.get("labels", {})
    premises = spec.get("premises", [])
    conclusion = spec.get("conclusion")

    missing = [v for v in vars_spec if v not in labels]
    if missing:
        raise SystemExit(
            "Every variable needs a plain-English label so the translation can "
            f"be checked by a human. Missing: {', '.join(missing)}")
    if not conclusion:
        raise SystemExit("Spec needs a 'conclusion'.")

    prem_ids = [p.get("id") or f"P{i + 1}" for i, p in enumerate(premises)]
    prem_exprs = [p["expr"] for p in premises]
    concl = conclusion["expr"]
    all_exprs = prem_exprs + [concl]

    names = list(vars_spec)
    kinds = [vars_spec[n].strip().lower() for n in names]
    for n, k in zip(names, kinds):
        if k not in ("bool", "boolean", "int", "integer", "real", "float"):
            raise SystemExit(f"unknown type '{k}' for variable '{n}' (use bool, int, or real)")
    exact = all(k in ("bool", "boolean") for k in kinds)
    domains = [candidates("int" if k == "integer" else k, all_exprs) for k in kinds]
    total = 1
    for d in domains:
        total *= len(d)
    if total > MAX_WORLDS:
        raise SystemExit(f"Too many worlds to check by brute force ({total:,}). "
                         "Install z3 (pip install z3-solver) and use entail.py, "
                         "or reduce the number of variables.")

    worlds = []
    for combo in itertools.product(*domains):
        w = dict(zip(names, combo))
        try:
            pv = [evaluate(e, w) for e in prem_exprs]
            cv = evaluate(concl, w)
        except Exception as e:  # noqa: BLE001
            raise SystemExit(f"Could not evaluate an expression: {type(e).__name__}: {e}")
        worlds.append((w, pv, cv))

    out = []
    add = out.append
    add("=" * 68)
    add("FORMAL LOGIC VERDICT (fallback engine: brute force, no z3)")
    add("=" * 68)
    if spec.get("claim"):
        add(f"Testing: {spec['claim']}")
        add("")
    add("The translation being tested (check this before trusting the verdict):")
    for p, pid in zip(premises, prem_ids):
        add(f"  {pid}. {p.get('text', '(no English given)')}")
        add(f"      {p['expr']}")
    add(f"  C.  {conclusion.get('text', '(no English given)')}")
    add(f"      {conclusion['expr']}")
    add("")
    if not exact:
        add("NOTE: numeric variables were checked only at these values:")
        for n, k, d in zip(names, kinds, domains):
            if k not in ("bool", "boolean"):
                add(f"    {n}: {d}")
        add("A counterexample below is real. 'Entailed' or 'inconsistent' is")
        add("proven only inside this range; confirm with z3 if it matters.")
        add("")

    consistent = [w for w, pv, cv in worlds if all(pv)]
    add("-" * 68)
    add("STEP 1 — Are the premises consistent with each other?")
    if not consistent:
        core = None
        for size in range(1, len(prem_exprs) + 1):
            for idx in itertools.combinations(range(len(prem_exprs)), size):
                if not any(all(pv[i] for i in idx) for _, pv, _ in worlds):
                    core = [prem_ids[i] for i in idx]
                    break
            if core:
                break
        add("  NO. The premises contradict each other.")
        add(f"  Smallest contradicting set: {', '.join(sorted(core or prem_ids))}")
        add("  A contradictory premise set entails ANY conclusion, so the")
        add("  entailment test below would be vacuous. Fix the premises first.")
        add("=" * 68)
        print("\n".join(out))
        return
    add("  YES. There is at least one world where all premises hold.")
    add("  One such world:")
    add(render(consistent[0], labels))
    add("")

    counter = [w for w, pv, cv in worlds if all(pv) and not cv]
    add("-" * 68)
    add("STEP 2 — Do the premises actually force the conclusion?")
    if not counter:
        add("  ENTAILED. No world satisfies the premises while the conclusion")
        add("  is false. The conclusion follows necessarily.")
    else:
        add("  NOT ENTAILED. The conclusion may be true, but these premises do")
        add("  not force it. Here is the counterexample — every premise holds")
        add("  and the conclusion is still false:")
        add("")
        add("  WITNESS:")
        add(render(counter[0], labels))
        add("")
        add("  To make the argument valid you must add a premise that rules")
        add("  this world out.")
    add("")

    if not any(all(pv) and cv for _, pv, cv in worlds):
        add("-" * 68)
        add("  WARNING: the premises entail the NEGATION of the conclusion.")
        add("  The argument establishes the opposite of what it claims.")
        add("")

    if not counter and len(prem_exprs) > 1:
        add("-" * 68)
        add("STEP 3 — Which premises are load-bearing?")
        for i, pid in enumerate(prem_ids):
            breaks = any(all(v for j, v in enumerate(pv) if j != i) and not cv
                         for _, pv, cv in worlds)
            if breaks:
                add(f"  {pid}: LOAD-BEARING — drop it and the argument collapses.")
            else:
                add(f"  {pid}: DECORATIVE — drop it and the conclusion still follows.")
        add("")

    add("=" * 68)
    add("Reminder: this verdict is about the FORMALIZATION above, not about")
    add("the world. A valid argument from false premises proves nothing.")
    add("=" * 68)
    print("\n".join(out))


if __name__ == "__main__":
    main()
