<center>
<h1>
    Hardware Root of Trust<br/>
    <span style="color: #f17232">Exploring OpenTitan and Pavona</span><br/>
</h1>
</center>

## Overview

This material is provided by [RISC-V Ottawa](https://riscvottawa.ca) as a
hands-on study of the hardware root of trust (HWRoT): small, trusted cores that
everything else in a secure system depends on. Rather than reading about it in
the abstract, we take a real open-source root of trust implementation, boot it
in a simulator on a laptop, and pull it apart subsystem by subsystem until the whole chain of trust
is understood end to end. Then we try to break it, to learn the difference between
what it actually guarantees and what one might assume it does.

The two designs we study are [OpenTitan](https://opentitan.org/), the open silicon
root of trust from lowRISC, and [Pavona](https://pavona.org/), the newer,
certification-aligned design derived from it that adds a post-quantum crypto
stack. Everything here runs in simulation using
[Verilator](https://www.veripool.org/verilator/), so you need no special hardware,
only a machine with enough memory to build it.

No prior hardware-security experience is assumed, though comfort with C, the
command line, and the basics of public-key cryptography will help.

<!--The book is published early and grows chapter by chapter. Later parts show in the
table of contents but stay greyed out until their chapter lands, so the full arc
is visible from the start even while the material behind it is still being
written.-->

## What will you learn?

By the end you should be able to:

* Explain what a hardware root of trust is and how it is built from open silicon
* Build and run a real root-of-trust chip entirely in simulation
* Trace the secure boot chain from immutable ROM up to owner firmware
* Follow a device identity from an OTP root secret through key derivation to an
  attestation certificate that a remote service can verify
* Reason about secure storage, lifecycle states, and post-quantum cryptography
* Probe the design's limits: what an attacker can and cannot do against it

The goal is to gain fundamental and transferable knowledge on what it takes to have trust rooted in hardware.
