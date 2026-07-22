# Contributing to hwrot-training

Thanks for helping build this. This is a public mdBook and simulation tutorials that
teaches the hardware root of trust by booting a real open-source design (Pavona
Egret and OpenTitan) in Verilator and pulling it apart subsystem by subsystem.

## Picking up work

Work is tracked as GitHub issues. Assign yourself an issue before starting so two
people do not duplicate. Each issue names the chapter or tutorial it touches and
lists its acceptance criteria; those criteria are the definition of done.

## The accuracy bar

This is security and hardware material for a public audience, so correctness is important
Every technical claim, register name, address, or behavior should trace to a real source file
in the reference repos or to something you actually ran in simulation.
Do not invent or infer hardware details.

The reference repos are read-only ground truth:

* Pavona: https://github.com/pavona/pavona
* OpenTitan: https://github.com/lowRISC/opentitan

Keep the designs distinct. For example, Egret uses `keymgr`, Dragonfly uses `keymgr_dpe`, and Pavona adds the `acc` PQC coprocessor that Earl Grey lacks.
When a Pavona spec is still Pre-RFC, reference back to OpenTitan's  source if it helps and state which design the claim describes.
If a claim cannot be backed by a source or a run, say so rather than filling the gap.

## Writing style

The book prose follows these rules, and so do commits, PRs, and reviews:

- No AI filler.
  - You're welcome to use AI to help you draft writeups and prove out tutorial material, but you MUST review and edit everything yourself before committing.
- Plain, direct language.
- No hype; state facts and give justification where needed.

Teaching mindset: each chapter has one storyline with implicit "why it matters" framing,
annotated code and register or flow diagrams, and ends in a concrete artifact the reader
can show off. Pace a chapter to be roughly only a few hours that can be done in an evening.

## Layout you need to know

`docs/` contains the mdBook.
`docs/src/` is the content and `docs/src/SUMMARY.md` is the source of truth for structure and the table of contents.
Each Part is a directory with an `index.md` whose final chapter is typically `simulate-it.md`.
`tutorials/` at the repo root holds the hands-on lab each `simulate-it.md` sends readers to; see `tutorials/README.md` for that convention.
`docs/build/` is generated output, never hand-edited.

## Build and verify

Build the book from `docs/`:

```
mdbook build      # output to docs/build/
mdbook serve      # live preview
```

`docs/Containerfile` does the same in a container (Ubuntu 24.04 + mdBook v0.5.2):

```
podman build -f docs/Containerfile docs/
```

Before opening a PR, confirm `mdbook build` succeeds and that `docs/src/SUMMARY.md`
matches the chapter map. For the Pavona simulation toolchain, do not write build
commands from memory; The upstream `pavona/doc/getting_started/` is the source of truth.

## Pull requests

Branch off `main`, keep the change focused on one issue, and open a PR that says
which issue it closes. State plainly what you verified: if the book builds, say so;
if a simulation step was run, show the output; if something is drafted but not yet
run, say that. A reviewer should be able to trace every new claim to a source or a
run.
