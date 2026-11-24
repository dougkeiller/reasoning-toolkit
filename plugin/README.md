# Reasoning Toolkit

Eight decision and reasoning methods for Claude Code, packaged as skills. You don't need to name them: say "poke holes in this", "which of these should we pick", or "I'm stuck", and Claude reaches for the right one.

These aren't prompt templates. Where a method needs independent perspectives, each one runs as a separate subagent that can't see the others. Where it needs arithmetic or logic, it runs real code. And every run writes a dated working note, so a skipped step is visible.

## The eight

**Pressure-test a decision**

| Skill | What it does |
| --- | --- |
| Decision Matrix | Weighted scoring against a do-nothing baseline, then real sensitivity analysis: drop-one checks, weight-flip thresholds and a 20,000-draw Monte Carlo. Tells you whether the winner survives different priorities. |
| Devil's Advocate | Six independent adversaries plus a Klein pre-mortem, looking for the failure that optimism is hiding. |
| Formal Logic | Runs the Z3 solver on an argument. When it fails, you get a concrete counterexample. |
| Hindsight | A post-mortem in which a cold reader judges the decision without being told the outcome, to separate a bad call from bad luck. |

**Break a stuck loop**

| Skill | What it does |
| --- | --- |
| Structured Reflection | Asks questions instead of giving answers until the problem gets reframed. |
| Chain of Thought | Each step must quote the previous step's output, so no leap is silently bridged. |
| Graph of Thought | Branches into genuinely different approaches, scores them on a rubric fixed in advance, and merges the best parts. |
| Context Switcher | Each stakeholder's view, developed by a separate agent that can't see the others. |

## Install

```bash
claude plugin marketplace add dougkeiller/reasoning-toolkit
claude plugin install reasoning-toolkit@reasoning-toolkit
```

## Requirements

Decision Matrix needs `numpy` and Formal Logic needs `z3-solver`. The skills install them on first use if missing, or you can run `uv run --with numpy` / `pip install numpy z3-solver`. Everything else runs anywhere. If subagents aren't available, the multi-perspective methods say so and flag lower confidence rather than faking independence.

## Working notes

Each run writes `reasoning-notes/YYYY-MM-DD-<subject>-<tool>.md` in the folder of the project the question is about, with YAML frontmatter. Existing notes are never overwritten; a clash becomes `-v2`. If the right folder is unclear, the skill asks.

`examples/` has two worked runs and a sample decision-matrix spec.

## Version

0.3.0 (2026-11-10). Decision Matrix now requires a baseline option (set `"baseline": null` to opt out; older specs without the key are refused), anchors each scale before weights are set, screens must-haves first, and adds an equal-weights check.

## Origin

Modelled on the eight tools at reasoning.services, rebuilt as local skills. The companion [research-toolkit](https://github.com/dougkeiller/research-toolkit) uses Decision Matrix for its shortlist cut.

## Engines without script files

Anthropic's plugin directory accepts script files only from verified publishers, so the plugin carries no scripts. The decision-matrix and formal-logic engines ship as code inside `references/sensitivity-engine.md` and `references/logic-engine.md`; Claude saves and runs them wherever it can run Python, with the same results as the source scripts in `scripts/` (tested 2026-11-24: byte-identical code and identical output). If no Python is available, the skills fall back to a by-hand method and say so.

Without the z3 solver installed, formal-logic uses a brute-force fallback: exact for yes/no variables, bounded for numbers, and the report says which engine ran.
