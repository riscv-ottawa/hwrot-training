#!/usr/bin/env python3
"""Check that every reference-style link label used in the book has a definition
in src/refs.md.

mdbook resolves `[text][label]` against definitions pulled in by
`{{#include ./refs.md}}` at the bottom of each chapter. An undefined label
renders silently as the literal text `[label]`, so a typo ships as visible
breakage with no build error. lychee does not catch this (it is not a link until
resolved). This script catches it.

Run from the repo root:

    python3 scripts/book/check_refdefs.py

Exits non-zero if any used label is undefined, or if any defined label is never
used (dead entries in refs.md).
"""

import re
import sys
import pathlib

SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("src")
REFS = SRC / "refs.md"

if not REFS.is_file():
    sys.exit(f"refs.md not found at {REFS}")

# Collect defined labels from refs.md. A definition line looks like:
#   [label]: https://example.com/...
defined = []
for line in REFS.read_text().splitlines():
    m = re.match(r"^\[([^\]]+)\]:", line)
    if m:
        defined.append(m.group(1).strip().lower())
defined_set = set(defined)

# Match reference-style link usages.
#   [text][label]   -> label is group 2
#   [label][]       -> label is group 1 (collapsed)
#   [label]         -> label is group 1 (shortcut)
# Inline links [text](url) and images ![alt](url) are stripped first so their
# bracketed text is not mistaken for a label.
USAGE = re.compile(r"\[([^\]]+)\](?:\[([^\]]*)\])?")
INLINE_LINK = re.compile(r"!\[([^\]]*)\]\([^)]*\)|\[([^\]]+)\]\([^)]*\)")
ALERT = re.compile(r"\[![A-Z]+\]")
INLINE_CODE = re.compile(r"`[^`]*`")

used = {}  # label -> list of "file:line" locations


def strip_noise(line: str) -> str:
    line = INLINE_LINK.sub("", line)
    line = ALERT.sub("", line)
    line = INLINE_CODE.sub("", line)
    return line


for md in sorted(SRC.rglob("*.md")):
    if md == REFS:
        continue
    in_fence = False
    for i, raw in enumerate(md.read_text().splitlines(), 1):
        stripped = raw.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("{{#include"):
            continue
        for m in USAGE.finditer(strip_noise(raw)):
            label = m.group(2)
            if label is None or label == "":
                label = m.group(1)
            label = label.strip().lower()
            if not label:
                continue
            used.setdefault(label, []).append(f"{md.relative_to(SRC)}:{i}")

undefined = {l: locs for l, locs in used.items() if l not in defined_set}
unused = [d for d in defined if d not in used]

exit_code = 0
if undefined:
    print(f"Undefined reference labels ({len(undefined)}):")
    for l in sorted(undefined):
        print(f"  [{l}]  used at {', '.join(undefined[l])}")
    print(f"\nAdd definitions to {REFS.relative_to('.')} or fix the typo.")
    exit_code = 1

if unused:
    print(f"Defined-but-unused labels in refs.md ({len(unused)}):")
    for l in sorted(unused):
        print(f"  [{l}]")
    print("\nRemove dead entries, or they drift from what the book actually links.")
    exit_code = 1

if not exit_code:
    print(
        f"OK: {len(used)} labels used across the book, "
        f"{len(defined_set)} defined in {REFS.relative_to('.')}, all resolve."
    )
sys.exit(exit_code)
