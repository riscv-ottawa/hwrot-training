# RISC-V Ottawa: Hardware Root of Trust

A hands-on study of what a hardware root of trust actually is, built entirely in
simulation on your own machine. We take a real open-source root of trust
(OpenTitan, and the newer certification-aligned Pavona), boot it in Verilator,
decompose it subsystem by subsystem until the whole trust chain is understood end
to end, then put it to work the way a product does, as a discrete secure element
that a separate host processor drives, and break the link between them to find out
what it can and cannot guarantee.

No prior hardware-security experience is assumed, though comfort with C, the
command line, and basic cryptography will help.

Read the book here: hwrot.riscvottawa.ca (planned)

## What this covers

- What a root of trust is and why open silicon matters (OpenTitan and Pavona)
- Building and running the Pavona Egret chip in the Verilator simulator
- Secure boot: the ROM to ROM_EXT to owner-firmware chain and signature verification
- Identity and keys: DICE, the OTP root secret, and key derivation
- Attestation: identity certificates and verifying a certificate chain
- Secure storage and lifecycle: scrambling and lifecycle-gated access
- Post-quantum cryptography: the `acc` coprocessor and NIST known-answer tests
- Provisioning and ownership transfer
- Egret as a secure co-processor: driving it from a cv32e40x host over SPI, and breaking the link (replay and tamper)

## Building the book

The website is built using [mdBook](https://github.com/rust-lang/mdBook). The
book lives under [docs](./docs), kept separate from the repo root so the root
can stay focused on [tutorials](./tutorials), the hands-on lab material.

The folder of primary relevance is [docs/src](./docs/src), which holds the book
content in markdown. From `docs/`, build with `mdbook build` (output goes to
`docs/build/`), or `mdbook serve` for a live-reloading local preview. A
`Containerfile` is also provided in `docs/` that builds the book and serves it
with a static web server (build with `docs/` as the context).

## Resources

### Project tooling

- [OpenTitan](https://opentitan.org/)
- [Pavona](https://pavona.org/)
- [Verilator](https://www.veripool.org/verilator/)

### Reference material

The literature review behind this project (secure boot, embedded trust anchors, security surveys, etc)
is tracked in [Hayagriva](https://github.com/typst/hayagriva) format in [`references.yml`](./references.yml).
