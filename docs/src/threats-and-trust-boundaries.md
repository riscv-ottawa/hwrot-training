# Threats and trust boundaries

"Secure" is not a property a chip can have on its own. Every security claim is
relative to an attacker with particular capabilities, and to a boundary that
separates who is in charge of what. Pavona documents both, and both are scoped to
Egret (and Dragonfly), so they describe the exact chip we are about to boot:

- The [lightweight threat model](https://docs.pavona.org/book/doc/security/threat_model/index.html)
  says who is attacking and with what.
- The [logical security model](https://docs.pavona.org/book/doc/security/logical_security_model/index.html)
  says who is in charge at each stage of the chip's life.

One tells you who is trying to tip the final turtle over, the other who is
entitled to stand on it. Read them early. Nearly every later chapter is one row
of one of these two documents examined in hardware.

## Who is attacking

The threat model names three attacker profiles:

- **Physical access**, during manufacturing or out in the field.
- **Malicious device owners**, attacking a device they legitimately possess in
  order to develop an attack that works on every other device of the same type.
- **Remote actors**, who can still measure side channels at a distance.

These are each interesting on their own, but let's consider the second one for a second.
A root of trust has to keep secrets from the person holding it, which is obviously harder
than keeping secrets from someone across a network...this will explain some of the design decisions
we'll encounter that might look paranoid, until you accept the threat model that's been chosen.

The attack surface is correspondingly wide: the chip surface itself, open to
inspection, reverse engineering, and physical manipulation; the operating
environment, meaning temperature and power; peripheral interfaces and the APIs
exposed at the device boundary; the test and debug interfaces; the clock, power,
and reset lines. Pretty much everything! It of course even includes the documentation
and design data, which is the whole "open silicon" thing.
But, interestingly, publishing the design is actually covered by the threat model, not a violation of it!
This is because none of the security is meant to rely on obscurity (i.e., the design being secret).

The methods split into three families:

- **Logical.** Software bugs reachable through an interface, compromise of secure
  boot, impersonation of the silicon creator or owner, misuse of test and debug
  functionality, insider compromise of provisioning.
- **Non-volatile memory.** Firmware downgrade, data rollback, command replay.
  These target time rather than secrets, forcing the device back into a state
  that was valid once.
- **Physical.** Passive side channel analysis, extracting a key by watching
  execution time, power draw, or electromagnetic emissions while the device runs
  perfectly normally, and active fault injection, pushing voltage, clock,
  temperature, EM, or a laser outside specification to make the device skip a
  check or corrupt a comparison. Any combination of these are in scopes too.

Due to all of this, it becomes apparent why a large fraction of Egret is not
actually compute or cryptography at all. Instead, as we'll learn, it is redundancy
and integrity checking: dual-core lockstep, bus and register file integrity, shadowed registers,
hardened counters and program counter, alerts that escalate, and more. None of this helps against bad
cryptography. All of it exists because of the rather terrifying number of physical-attack methods.

## Who is in charge

The logical security model draws the other boundary, and it is about entities
rather than adversaries. A Pavona chip deals with up to three over its lifetime:

- **Silicon Creator.** Designs, manufactures, tests, and provisions the chip with
  its first identity, the Creator Identity, which is what proves the chip is
  genuine.
- **Silicon Owner.** Whoever currently owns the device. It validates the Creator
  Identity, provisions a second identity of its own that the creator does not
  know, and supplies the functional software stack.
- **Application Provider.** Supplies the applications running on top of that
  stack, and can derive further identities from the owner's, isolated from each
  other by owner software.

Note that these roles are "logical", meaning they can also collapse. One vertically
integrated company that creates the silicon and provisions all of its software leaves
a single identity rather than two (essentially the TPM model).

The boundary is drawn in software stages, and owning a stage means controlling
the key that signs it. The Silicon Creator owns the ROM, immutable after
manufacture, and the ROM_EXT, a modifiable extension that patches hardware
issues, applies the security settings judged too risky to hard-wire into ROM, and
performs creator identity provisioning. As those stages run they lock out the
parts of the chip that later stages have no business touching, and they do not
execute again until the next reset. Everything after that belongs to the owner.
Because creator code is measured into the Creator Identity, and because it is
open, a prospective owner can inspect exactly what it is inheriting before
accepting a chip.

Taking all of the above sections together, we see how the threat model tells you what
a given mechanism is defending against, defining attacker profiles demonstrates how intense things can get out in the real world,
and the entity model tells you whose key forms the base of trust at each step along the boot chain.
When we trace from the initial ROM all the way up to owner firmware, or watch a device carry two separate identities, or step
through a lifecycle transition, we must keep this model and its boundaries in mind.
