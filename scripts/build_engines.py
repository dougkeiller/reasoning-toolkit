#!/usr/bin/env python3
"""Build the Markdown copies of the engines that ship inside plugin/.

Anthropic's directory accepts no script files from unverified publishers, so
the plugin carries each engine as a code block in a reference Markdown file.
The .py files in scripts/ stay the source of truth; run this after editing them:

    python3 scripts/build_engines.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "plugin" / "references"

RUN = """## How to run it

{steps}
If nothing can run Python here, fall back to the by-hand method in the skill
and say in the note that the engine was not run.

Each code block below is saved to its own file before running. In Claude Code,
this one-liner saves a block by file name:

```bash
python3 -c "import re,sys;s=open(sys.argv[1]).read();open(sys.argv[2],'w').write(re.search(r'<!-- file: '+re.escape(sys.argv[2])+r' -->\\s*```python\\n(.*?)```',s,re.S).group(1))" ${{CLAUDE_PLUGIN_ROOT}}/references/{ref} FILENAME
```

Anywhere else (claude.ai or Cowork with code execution), read this file and
write the block to that file name with your file tool.
"""

ENGINES = [
    {
        "ref": "sensitivity-engine.md",
        "files": ["sensitivity.py"],
        "title": "Sensitivity engine (decision-matrix)",
        "intro": "The decision-matrix skill's Monte Carlo sensitivity engine. It reads the\n"
                 "spec described in the skill and reports the ranking, weight and score\n"
                 "sensitivity, and how often each option wins under uncertainty.",
        "steps": "1. Save the `sensitivity.py` block below as `sensitivity.py`.\n"
                 "2. Run `python3 sensitivity.py spec.json`. It needs numpy; if that import\n"
                 "   fails, try `pip install numpy` or `uv run --with numpy python sensitivity.py spec.json`.\n",
    },
    {
        "ref": "logic-engine.md",
        "files": ["entail.py", "entail_fallback.py"],
        "title": "Logic engine (formal-logic)",
        "intro": "The formal-logic skill's entailment engine. It checks whether the premises\n"
                 "are consistent, whether they force the conclusion, gives a counterexample\n"
                 "if not, and marks each premise load-bearing or decorative.",
        "steps": "1. Check for the z3 solver: `python3 -c \"import z3\"` (or try `pip install z3-solver`).\n"
                 "2. If z3 is there, save the `entail.py` block and run `python3 entail.py spec.json`.\n"
                 "3. If not, save the `entail_fallback.py` block and run\n"
                 "   `python3 entail_fallback.py spec.json`. It tries every true/false\n"
                 "   combination: exact for yes/no variables, bounded for numbers, and the\n"
                 "   report says which engine ran and what range was checked.\n",
    },
]


def main():
    REF.mkdir(parents=True, exist_ok=True)
    for e in ENGINES:
        md = (f"# {e['title']}\n\n{e['intro']}\n\n"
              + RUN.format(steps=e["steps"], ref=e["ref"])
              + "\nGenerated from `scripts/` in the GitHub repo by `scripts/build_engines.py`;"
                " do not edit by hand.\n")
        for f in e["files"]:
            code = (ROOT / "scripts" / f).read_text().rstrip() + "\n"
            assert "```" not in code, f"{f} contains a Markdown fence"
            md += f"\n## {f}\n\n<!-- file: {f} -->\n```python\n{code}```\n"
        (REF / e["ref"]).write_text(md)
        print("wrote", REF / e["ref"])


if __name__ == "__main__":
    main()
