# RISC-V Ottawa: Hardware Root of Trust

This material is provided by [RISC-V Ottawa](https://riscvottawa.ca) as a hands-on study of the hardware root of trust (HWRoT): a small, trusted core that everything else in a secure system depends on.

Rather than reading about it in the abstract, we take a real open-source root of trust implementation, boot it in a simulator on a laptop, and pull it apart subsystem by subsystem until the whole chain of trust is understood end to end.

The final goal is to get to the point where we can use a HWRoT in the same way a real product would. For this, we'll focus on the discrete secure element use case, where a separate host processor communicates to the HWRoT over SPI.

No prior hardware-security experience is assumed, though comfort with C, the
command line, and basic cryptography will help.

Read the book here: [hwrot.riscvottawa.ca](https://hwrot.riscvottawa.ca/)

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

The website is built using [mdBook](https://github.com/rust-lang/mdBook).

The folder of primary relevance is [src](./src), which holds the book content in
markdown. Build with `mdbook build` (output goes to `book/`), or `mdbook serve`
for a live-reloading local preview. A `Containerfile` is also provided that
builds the book and serves it with a static web server.

## Resources

### Project tooling

- [OpenTitan](https://opentitan.org/)
- [Pavona](https://pavona.org/)
- [Verilator](https://www.veripool.org/verilator/)

### Reference material

The literature review behind this project (secure boot, embedded trust anchors, security surveys, etc)
is tracked in [Hayagriva](https://github.com/typst/hayagriva) format in [`references.yml`](./references.yml).
