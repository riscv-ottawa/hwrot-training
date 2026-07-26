# Why open silicon: OpenTitan and Pavona

In almost every device shipping today, the final turtle is a black box. The
design is secret, the firmware is sealed, and you are asked to trust it because
the vendor says so. That is a strange arrangement for the one component whose
failure nothing else in the system can compensate for. A root of trust asks to
be trusted absolutely, which is precisely why it should be open to inspection.
When the RTL, the boot ROM, and the verification environment are all public, the
security argument can be checked by anyone who cares to, and the design earns
trust by being examined rather than by being hidden.

[OpenTitan](https://opentitan.org/), from the lowRISC project, is where that
changed. It is the original open-source silicon root of trust, open all the way
down to the chip design itself, and it runs on RISC-V. It is also not a paper
design. As of March 2026, OpenTitan silicon fabricated by Nuvoton
[ships in commercially available Chromebooks](https://lowrisc.org/news/opentitan-ships-in-chromebooks-first-production-deployment/),
the project's first production deployment. Its `top_earlgrey`
configuration is the most thoroughly documented, and its `silicon_creator` C
code is the reference implementation of secure boot.

Open here means more than a published block diagram. Both designs in this book
ship their Verilog, their `silicon_creator` C code, their register descriptions,
their design verification testbenches, and their threat model under Apache 2.0.
That is also what makes this book possible at all. You cannot single-step a
proprietary secure element, and you certainly cannot watch its key manager
change state. In simulation, on open RTL, you can watch any signal in the
design.

[Pavona](https://pavona.org/) is the newer design, built in part from OpenTitan
and steered by a foundation hosted by GlobalPlatform with
certification readiness as an explicit goal. It keeps OpenTitan's architecture
and much of its software, and adds the `acc` asymmetric cryptography
coprocessor: a separate processor with its own memories and its own big-number
ISA, running RSA and ECC today and carrying vectorized instructions for the
lattice-based ML-KEM and ML-DSA algorithms. Pavona is the reference we actually
build and run, and the configuration that we focus on is `top_egret`, the
discrete secure microcontroller we will boot, decompose, and break.

Note, the two projects and implementations play slightly different roles in this book.
Egret is what we run. Every command you type, every boot log you read, and
every block you break is Egret in Verilator. Earl Grey is what we read when
Egret's own documentation is unclear or lacking, which it may be, because OpenTitan is older,
more thoroughly written up, and the so-called `silicon_creator` code it has is the canonical
secure-boot implementation. The two are close enough that most of what you learn
about one transfers to the other, and this book says so explicitly each time it
steps from one to another.
