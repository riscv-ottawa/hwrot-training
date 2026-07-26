# Contributing to hwrot-training

Thanks for helping build this. This is a public mdBook that teaches the hardware
root of trust by booting a real open-source design (Pavona Egret and OpenTitan)
in Verilator and pulling it apart subsystem by subsystem.

## Picking up work

Work is tracked as GitHub issues. Assign yourself an issue before starting so two
people do not duplicate. Each issue names the chapters it touches and lists its
acceptance criteria; those criteria are the definition of done.

## Write accurately

This is security and hardware material for a public audience, so correctness
matters. Every technical claim, register name, address, or behavior should
trace to a real source file in the reference repos or to something you actually
ran in simulation. Cite the file path (e.g. `pavona/hw/top_egret/doc/datasheet.md`)
so a reviewer can follow it. Do not invent or infer hardware details.

The reference repos are read-only ground truth:

* Pavona: https://github.com/pavona/pavona
* OpenTitan: https://github.com/lowRISC/opentitan

Keep the designs distinct. Egret uses `keymgr`, Dragonfly uses `keymgr_dpe`, and
Pavona adds the `acc` PQC coprocessor that Earl Grey lacks. When a Pavona spec
is still Pre-RFC, fall back to OpenTitan's `silicon_creator` source and state
which design the claim describes. If a claim cannot be backed by a source or a
run, say so rather than filling the gap.

Do not paste register tables, lifecycle tables, or full threat models into a
chapter. Link to the spec section and summarize only what the narrative needs.

## Links and references

External links are written reference-style: `[OpenTitan][opentitan]`,
with the URL defined once in `src/refs.md` as `[opentitan]: https://opentitan.org/`.
`src/refs.md` is pure definitions, so including it renders nothing visible. Each
chapter that uses a label ends with an include so mdBook can resolve it:

```
{{#include ./refs.md}}        # from src/*.md
{{#include ../refs.md}}       # from src/<part>/*.md
```

Add a new external link by appending a `[label]: url` line to `src/refs.md` and
using `[text][label]` in the chapter. Reuse an existing label rather than
defining a duplicate. An undefined label renders silently as the literal text
`[label]` with no build error, so run the checker (below) before opening a PR.

Prior art (papers, specs, surveys) is cited the same way. The full citation
lives in the `src/references.md` page, and a matching `[label]: url` line in
`src/refs.md` lets a chapter cite it inline, e.g., as `[TyTAN][brasser2015]`. To add a
source, write the entry into `src/references.md` and append its `[label]: url`
to `src/refs.md`.

## Writing style

The book prose follows these rules, and so do commits, PRs, and reviews:

- No AI filler.
  - You're welcome to use AI to help you draft writeups and prove out lab material, but you MUST review and edit everything yourself before committing.
- Plain, direct language.
- No hype; state facts and give justification where needed.

Teaching mindset: each chapter has one storyline with implicit "why it matters" framing,
annotated code and register or flow diagrams, and ends in a concrete artifact the reader
can show off. Pace a chapter to roughly one evening session.

## Repo layout

The mdBook lives at the repo root.
`src/` is the content and `src/SUMMARY.md` is the source of truth for structure and the table of contents.
Each part is a directory with an `index.md` and kebab-case chapter files.
There is no mandatory final chapter: a part ends on whichever chapter best closes it,
and whether it sets a closing challenge is up to whoever writes it.
The hands-on material goes into the chapters themselves. `scripts/` is a shared
dir for helper scripts a contributor found useful while working on content
here or while driving the Pavona repo; book- and writing-related scripts go under
`scripts/book/` (e.g. `check_refdefs.py`). A chapter may reference one when the
reader needs to run it, but short snippets can and should stay inline in the chapters themselves.
`book/` is generated output, never hand-edited.

## Build and verify

Build the book from the repo root:

```
mdbook build      # output to book/
mdbook serve      # live preview
```

`Containerfile` does the same in a container (Ubuntu 24.04 + mdBook v0.5.2):

```
podman build .
```

Before opening a PR, run all three verification steps locally, matching what CI
in `.github/workflows/book.yml` does:

```
mdbook build
lychee --config lychee.toml 'src/**/*.md'
python3 scripts/book/check_refdefs.py
```

The build fails on any error, including a chapter referenced from
`src/SUMMARY.md` but missing as a file (`create-missing = false`), a broken
relative link, or a dead image reference. `check_refdefs.py` catches
reference-style link labels that have no definition (or definitions nothing
uses). For the Pavona simulation toolchain, do not write build commands from
memory; the upstream `pavona/doc/getting_started/` is the source of truth.

## Definition of done

A chapter is ready to merge when:

- `mdbook build`, `lychee`, and `check_refdefs.py` all pass.
- Every technical claim traces to a source file path or to a simulation run.
- The chapter follows the upstream spec and ends in things the reader can actually run.
- The chapter is wired into `src/SUMMARY.md` with a real link.
- New external links are added to `src/refs.md` and the chapter includes it.

## Pull requests

Branch off `main`, keep the change focused on one issue, and open a PR that says
which issue it closes. State plainly what you verified: if the book builds, say so;
if a simulation step was run, show the output; if something is drafted but not yet
run, say that. A reviewer should be able to trace every new claim to a source or a
run.
