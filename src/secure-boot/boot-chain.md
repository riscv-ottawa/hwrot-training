# The chain of trust

In [part 1](../simulated-chip/hello-world.md) we booted Egret and printed
`Hello, World!`, but at no point did the chip check anything. The test ROM
jumped into whatever happened to be sitting in flash.  This is actually what most microcontrollers do...but that's not good enough for a security focused chip.
Let's dive into how we can do better.

## Single address space, oh my!

Putting Egret to the side for a second. In general, a typical microcontroller (MCU) device only has a single physical address space, with some
vendor-provided immutable (ROM) code at the bottom that runs first, sometimes a bootloader right above that, then a kernel or an operating system (e.g., RTOS), then applications. Everything here shares that single
address space, and everything below the applications runs privileged (actually, many times the applications run as privileged themselves if the underlying hardware or OS don't provide much for separation). A device
like this has no virtual memory to hide behind (unless it's the [Baochip][baochip]!) and sometimes no hardware-backed memory protection
at all ([Haj-Yahya et al.][hajyahya2019]).

Now suppose an attacker gets code into the bootloader through some bug in a
layer above it. They do not just control the bootloader; they control every
stage that runs after it, because each stage is loaded and started by the one
below. Worse, if the compromise is written back into flash, it is still there
after a power cycle!

So the boot process is asked to do two separate things, and it is easy to
conflate them. It can *measure*: hash each stage as it goes and keep a record of
what ran, without ever refusing anything. Or it can *enforce*: check each stage
before running it and stop if the check fails. The literature calls the first
trusted or authenticated boot and the second secure boot, and the difference is
entirely in what happens on a mismatch ([Parno et al.][parno2010]). Egret does
both, but this part is about the second: a stage that fails its check does not
get to run.

The mechanism is a chain. Each stage verifies the next one before handing over
control, so trust propagates upward one hop at a time:

<center>
    <figure>
        <img src="/img/diagrams/generic-boot-chain.png" alt="A generic three-stage boot chain, drawn three times as verification spreads upward" width="90%">
        <figcaption>A generic MCU device, drawn three times as the chain
        builds. Green is verified, the thick black lines are memory protection,
        and the attacker sits up among the applications.</figcaption>
    </figure>
</center>

Read it left to right. In the first panel only the ROM is green, and everything
above it is unverified. In the second the ROM has checked the bootloader, so the
bootloader is green too. In the third the bootloader has checked the kernel, and
the whole privileged stack is verified. The keys drawn inside the ROM and the
bootloader are what each stage checks the next one against, and the thick black
lines are another part of the story, which we will get to shortly.

Egret's chain has the same shape with different names. Its three stages are
ROM, ROM_EXT, and the owner image, and the rest of this chapter is that picture
redrawn one stage at a time with Egret's memory map on it.

## Verify first, then hand over

Two rules make this so-called "chain of trust" to work:

The first is the obvious one: no stage runs until the stage before it has
checked a signature over it. What "checked" means concretely is a hash (e.g., SHA-256) digest for integrity and a signature (e.g., ECDSA P-256) over that digest for authenticity.

The second rule is about what happens *after* the check passes. Namely, booting should be one-way.
Pavona's [logical security model][pavona-logical-security] states it in capital
letters: from ROM through every software stage, execution is ONE WAY, and each
stage completes its task and irreversibly jumps to the next. Once ROM has jumped, nothing later has any legitimate reason to read ROM's memory, so ROM can lock itself away on the way out and never need it back. This applies to later stages as well.
Those thick black lines in the diagram above denote that closing-off, and on Egret this is achieved by something called (e)PMP, which [has its own chapter](./epmp.md). For now, just note that every arrow in the diagrams below is doing two things at once: verifying, and isolating.

## Where the chain is anchored

Every stage in this chapter checks a signature against a key the previous stage
handed it. So the chain has to start somewhere, and the first stage has no
earlier stage to hand it anything. There is no signature to check ROM against,
because there is nothing before ROM to sign it.

Since this is a physical chip, the anchor has to be the hardware itself, and on
Egret that hardware is `rom_ctrl`. It runs before the CPU executes a single ROM
instruction (see the [ROM controller theory of operation][rom-ctrl-theory] for
the details).

On reset, `rom_ctrl` streams the entire contents of ROM through a `cSHAKE256`
operation via the KMAC (Keccak [message authentication code][mac]) hardware
block, then compares the resulting digest against a 256-bit hash stored in the
top eight words of ROM itself. The FSM ([finite-state machine][fsm]) that drives
this reads that expected digest straight from the ROM bus and wires the result
to both the power manager and the key manager:

Pavona `hw/ip/rom_ctrl/rtl/rom_ctrl_fsm.sv:282-292`
```
assign exp_digest_o = rom_data_i;
assign exp_digest_vld_o = reading_top;
assign exp_digest_idx_o = rel_addr;

// The 'done' signal for pwrmgr is asserted once we get into the Done state. The 'good' signal
// comes directly from the checker.
assign pwrmgr_data_o = '{done: in_state_done, good: checker_good};

// Pass the digest all-at-once to the keymgr. The loose check means that glitches will add
// spurious edges to the valid signal that can be caught at the other end.
assign keymgr_data_o = '{data: digest_i, valid: mubi4_test_true_loose(in_state_done)};
```

Two different things happen with that result. The power manager gets a pass/fail
bit it can use to decide whether to let the chip boot at all, and the key manager
gets the raw digest, forwarded unconditionally, whether or not it matched. That
raw digest becomes the first material for something called the `CreatorRootKey`.
As a result, a ROM that an attacker has modified does not
merely fail to boot, it produces the *wrong* root key, so every identity and
every key derived from it downstream becomes wrong too. This is the hardware
we root trust in!

<center>
    <figure>
        <img src="/img/diagrams/egret-boot-chain.1.svg" alt="Egret's boot stages with only ROM verified" width="90%">
        <figcaption>Egret at the moment the CPU starts. <code>rom_ctrl</code>
        has already checked ROM; the two flash stages are still just unverified bytes.
        </figcaption>
    </figure>
</center>

## Hop 1: ROM verifies ROM_EXT

From here the same steps repeat for every remaining stage, Pavona's
[secure boot spec][pavona-secure-boot] explains it in detail. In summary: load the next stage's
manifest, hash its contents together with a set of usage constraints, and check
the manifest's signature against that digest and a public key already baked into
the current stage. For ROM, that means computing
`SHA256(usage_constraints || rom_ext_contents)` and verifying it against a
Silicon Creator public key baked into ROM itself
(see upstream `sw/device/silicon_creator/lib/manifest.h:203-235`).

Note, Egret keeps two ROM_EXT slots, and ROM tries the candidate with the higher `security_version` first, breaking ties in favor of the higher major version and then the higher minor version (`sw/device/silicon_creator/rom/boot_policy.c:18-34`). That ordering only decides what to
verify first; every attempted candidate must meet the device's stored minimum and pass verification.
For simplicity this lab only ever populates slot A, so you will not see that fallback.

<center>
    <figure>
        <img src="/img/upstream/flash_layout.svg" title="Original source: https://docs.pavona.org/book/doc/security/specs/secure_boot/index.html#memory-layout" alt="Flash layout" width="70%">
        <figcaption>The real chip's flash: two banks, each holding a ROM_EXT
        slot and an owner slot.</figcaption>
    </figure>
</center>

Those slots are real addresses (see `hw/top_egret/doc/memory_map.md`, or `EGRET_SLOTS`
in `hw/top_egret/defs.bzl`). The lab we'll do later uses `opentitantool image assemble` to build one simplified image reusing the same slot offsets without the full two-bank
layout.

Once the signature is verified, ROM unlocks flash execution over the ROM_EXT
region and jumps to it. This covered both rules we mentioned above: the
signature decided that ROM_EXT may run, and an ePMP configuration decided what it may
reach.

<center>
    <figure>
        <img src="/img/diagrams/egret-boot-chain.2.svg" alt="Egret's boot stages with ROM and ROM_EXT verified" width="90%">
        <figcaption>Hop one. An attacker who rewrote ROM_EXT in flash gets
        caught here, because the signature no longer matches the
        contents.</figcaption>
    </figure>
</center>

## Hop 2: ROM_EXT verifies the owner image

ROM_EXT repeats the same as above with one thing changed: it verifies against a
Silicon Owner public key instead of a Silicon Creator one.
This acts as the handoff from creator-controlled trust to owner-controlled trust, which is the boundary [the front matter](../threats-and-trust-boundaries.md) drew between the two entities, now happening as one concrete key lookup in the middle of a boot. The spec calls this stage's target `BL0`, but we'll call it the owner image going forward.

`rom_ext.c`'s `rom_ext_boot()` measures the owner block and derives DICE
attestation keys for it before verifying and jumping
(see `sw/device/silicon_creator/rom_ext/rom_ext.c:227-318`). We'll take about DICE derivation later in this book (Part 4).

> [!NOTE]
> "The owner" just means whoever's key ROM_EXT is currently configured to
> accept. What ownership is and how it changes hands is covered in Part 7.
> Here it matters only because we'll soon start working with a blank device, which, on first
> boot, has no owner configured yet. The  `sku_creator_owner_init` method
> (`sw/device/silicon_creator/lib/ownership/test_owner.c:98`) writes a default
> owner page carrying the `APP_PROD_ECDSA_P256` key and continues the boot
> process. So we'll see the owner image signed with `app_prod_ecdsa`,
> it's the key ROM_EXT just gave itself permission to trust.

<center>
    <figure>
        <img src="/img/diagrams/egret-boot-chain.3.svg" alt="Egret's boot stages with all three verified" width="90%">
        <figcaption>Hop two, and the chain is complete.</figcaption>
    </figure>
</center>

## What happens when verification fails

Everything so far describes the boot chain's happy path. A secure boot design also has
to decide what it does when a check fails. Halting outright is the simplest option, but a bad one for a device in the field...since recovering it then needs physical access and likely a trip back to the manufacturer.
Entering some defined failure logic that reports the
problem is definitely better...but only if there is anyone around to hear it.
A third option is to recover: keep a known-good image in memory the boot code alone can reach, and restore from it when a check fails (see [Dave et al.][dave2021]).

Egret's different stages recover in different ways.
If the first ROM_EXT candidate fails verification, ROM tries the other slot.
If boot still cannot continue, ROM follows its own shutdown path.
Moving up, an owner image that fails ROM_EXT's check leads into a rescue protocol instead, ROM_EXT's route to being handed a replacement image rather than simply refusing to continue. We'll look at both of these cases in [reading the boot log](./boot-log.md).

## Watching it happen

A fully successful boot prints about thirty lines,
[reading the boot log](./boot-log.md) goes through all of them, but here's a snippet:

```
 OpenTitan:4001-0002-01
ROM_EXT:0.110
verify: key=2;P256;prod
entry: 0x20010480
```

The first two lines are ROM and ROM_EXT announcing themselves, which means hop one is
already finished by the time the second line prints. `verify: key=2;P256;prod`
is ROM_EXT naming the exact key slot, algorithm and role it is about to check
the owner image against, which shows us hop two happening at this one line of output.
`entry: 0x20010480` is the jump address, and everything the chip prints after it is
running with control handed all the way up to code an owner signed.

Next, [signing and verifying an image](./signature-verification.md) opens up the
step this chapter drew as an arrow: what the signature actually covers, which
key gets picked out of which set, and,briefly, the coprocessor that does the arithmetic.

{{#include ../refs.md}}
