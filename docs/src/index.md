<center>
<h1>
    Hardware Root of Trust<br/>
    <span style="color: #d9a18d">Exploring OpenTitan and Pavona</span><br/>
</h1>
</center>

## Overview

This material is provided by [RISC-V Ottawa](https://riscvottawa.ca) as a
hands-on study of the hardware root of trust (HWRoT): a small, trusted core that
everything else in a secure system depends on.

Rather than reading about it in the abstract, we take a real open-source root of trust implementation, boot it in a simulator on a laptop, and pull it apart subsystem by subsystem until the whole chain of trust is understood end to end.

The final goal is to get to the point where we can use a HWRoT in the same way a real product would. For this, we'll focus on the discrete secure element use case, where a separate host processor communicates to the HWRoT over SPI.

The two open implementations we study are [OpenTitan](https://opentitan.org/), the open silicon
root of trust from lowRISC, and [Pavona](https://pavona.org/), the newer,
certification-aligned design derived from it that adds a post-quantum crypto
stack. Everything here runs in simulation using
[Verilator](https://www.veripool.org/verilator/), so you need no special hardware,
only a machine with enough memory to build it.

No prior hardware-security experience is assumed, though comfort with C, the
command line, and the basics of public-key cryptography will help.

## How the book is organized

The point of this book is not to rehash the already stellar documentation provided by OpenTitan and Pavona. Instead, it is to get you to look, understand, simulate, integrate, simulate again, break, and teach. It opens with the ideas, what a root of trust is, why open silicon matters, and which threats it is built against.

The chapters after that each take one subsystem of the chip (secure boot, secure storage and lifecycle, identity and keys, attestation, post-quantum crypto, provisioning and ownership) and follow it from the specification down through to the RTL and the firmware that drives it, ending in an exercise you perform yourself.

The final part is the most exciting, since this is where we stop treating the chip as a lab specimen and instead use it as a real component: a secure co-processor serving a host that has to trust its answers.

Don't jump to the end though! Because every chapter ends in something you can simulate yourself and show off, e.g., a waveform, a boot log, a certificate chain that validates, or a run that correctly refuses to proceed.

As mentioned, the reference documentation from OpenTitan and Pavona is excellent and we link to it constantly rather than restating it; what this book adds is the narrative thread through it, a live simulation on your own machine, and a view of the internal state running in your own simulation environment.

## What will you learn?

By the end you should be able to:

- Explain what a hardware root of trust is and how it is built from open silicon
- Build and run a real root-of-trust chip entirely in simulation
- Trace the secure boot chain from immutable ROM up to owner firmware
- Follow a device identity from an OTP root secret through key derivation to an
  attestation certificate that a remote service can verify
- Reason about secure storage, lifecycle states, and post-quantum cryptography
- Provision a blank simulated chip and hand ownership of it to someone else
- Utilize the chip from a host processor as a secure co-processor, and understand the attack surface between them and what defenses are provided

The goal is to gain fundamental and transferable knowledge on what it takes to have trust rooted in hardware.
