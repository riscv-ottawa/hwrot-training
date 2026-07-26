# What is a Root of Trust?

There is an [old story about what holds up the world](https://en.wikipedia.org/wiki/Turtles_all_the_way_down). Some ancient cultures
pictured the Earth resting on the back of a giant turtle...which invited the
obvious follow-up question: what holds up that turtle? Answer: another turtle. And under
that one? Another turtle. It is **turtles all the way down**.

Every secure device you rely on, your phone, your car, the servers your bank
runs on, is built the same way. It is layers, and each layer is forced to trust
the layer underneath it. Your operating system trusts the bootloader that
started it; the bootloader trusts the firmware before it; that firmware trusts
the very first instruction the processor ever executes. Turtles, all the way
down. Except a device cannot do this forever. At the very bottom there has to be
one final turtle, and the entire stack is standing on it.

A hardware root of trust is that final turtle: a small, immutable piece of
silicon that holds the device's identity and its secret keys, decides what
software is allowed to run at all, and that nothing else vouches for. Nothing
else can, which is what makes it different in kind from every layer above it. It
also sets a hard constraint. The final turtle has to be small enough to audit
and simple enough to reason about, because a flaw in it cannot be patched by
anything above it. Egret's boot ROM is 32 KiB. The entire security argument of a
device can rest on code that would be a rounding error inside an operating
system kernel.

This chapter builds the mental model the rest of the book depends on: the five
jobs a root of trust has to do, and how the blocks of a real chip map onto them.

## The five jobs

The final turtle does five things. Everything else
in this book is one of these jobs examined up close.

- **Identity.** Something no other device can claim (no matter how hard they try),
  descending from a secret the chip is born with and never reveals. An
  identity is something you can't copy or overwrite.
- **Secure boot.** The process to ensure a system can refuse to run code that is not signed by a trusted authority,
  This is started at the very first instruction, before any mutable code
  gets a chance to lie about itself. A gap at the start of the chain leaves a gap in
  the entire chain of trust.
- **Attestation.** Proves to a remote party what hardware and software the device
  is actually running, in a form that the party can verify independently.
- **Secure storage.** Keep secrets and state confidential and tamper-evident
  against an attacker who physically holds the chip, opens the package, and
  reads the memories directly, which is a threat that the Pavona
  [threat model](./threats-and-trust-boundaries.md) calls out explicitly.
- **Cryptography.** Hashing, signing, key exchange, random number generation,
  and, more recently, post-quantum signatures, provided in hardware so they are
  fast, constant-time, and hard to observe. Protecting against side-channels here is crucial,
  since an algorithm that is mathematically correct but leaks its key
  through timing or power consumption is a broken algorithm.

These five are not separate features bolted together. Identity depends on secure
storage to hold its root secret and on cryptography to derive keys from it;
attestation signs its evidence with those keys; secure boot checks signatures
with the same primitives. Egret wires that dependency directly into the hardware.

## The jobs mapped onto Egret

<center>
    <figure>
        <img src="/img/upstream/top_egret_block_diagram.svg" title="Original source: https://github.com/pavona/pavona/blob/main/hw/top_egret/doc/datasheet.md" alt="Egret diagram" width="70%" >
        <figcaption>Egret (discrete chip)</figcaption>
    </figure>
</center>

Egret is a concrete instance of everything discussed above
The datasheet's top-level block diagram given above shows the
Ibex RISC-V core, the memories, and the peripherals on one bus.
Read against the five jobs, that diagram sorts into five groups.

| Job            | Egret blocks that do it                                                                                                                                                    |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Identity       | Key manager (with DICE support), OTP memory (holds the root secret), KMAC (performs the key derivation)                                                                    |
| Secure boot    | ROM (verified on boot), the Ibex core's ePMP (isolates each boot stage), asymmetric cypto and the boot ROM software (verify the next stage's signature)                    |
| Attestation    | Key manager (derives the identity keys that sign the evidence), asymmetric crypto (does the public-key signing)                                                            |
| Secure storage | OTP and flash (which has access control plus memory scrambling), the ROM and SRAM controllers (scrambling), and life cycle controller (gates what the chip will do at all) |
| Cryptography   | AES, HMAC, KMAC, asymmetric crypto (RSA, ECC, and the lattice-based post-quantum algorithms), CSRNG with entropy source (randomness)                                       |

Several blocks appear in more than one row, this overlap is on purpose.
When later chapters zoom into one of these blocks, you can refer back to this
table to see how it connects back to the whole.

The rest of the book is, in a sense, a slow walk through these table rows, one
block at a time, first to understand what each one guarantees and then, in the
final part, to integrate this within a larger system to find out what it does, and does not, do.
