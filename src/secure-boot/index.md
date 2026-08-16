# How a chip trusts its own code

In part 1, we booted the Pavona Egret chip (in simulation)...but we didn't
talk much about security and, more specifically, what it takes to boot the
chip in a secure way. The test ROM you ran got Egret to `Hello World!` by
jumping straight into whatever sat in flash, with no checks along the way.
That's not good enough for a root of trust!

In this part, we'll be booting Egret a few more times, this time through the
real secure boot ROM instead of the test ROM. We'll watch it refuse to run code that
fails verification, and learn what happens in this scenario.
The upstream Pavona [secure boot spec][pavona-secure-boot] docs are the primary reference for this entire part,
but along the way we'll look at specific source and driver code as well so we can get a much deeper technical understanding.

Boot-up will become a two-hop chain: ROM verifies and jumps to a ROM_EXT image, which
verifies and jumps to an owner image. Each stage only progresses after a set of checks pass.
Checks are to validate integrity and authenticity.
Integrity checks whether the image has unexpectedly changed in anyway, and is done via a SHA-256 digest.
Authenticity checks whether the images has been produced by a trusted entity, done by an ECDSA P-256 signature over the image digest using a public key baked into the verifying stage.
Repeating this at every hop is what establishes trust, starting at the root and propagating forward.

> [!NOTE]
> This part runs Egret against development signing keys, not real
> manufacturing keys. The execution environment `sim_verilator_rom_with_fake_keys`
> (`hw/top_egret/BUILD`) boots the real secure boot ROM at
> `sw/device/silicon_creator/rom` with fake keys in place of the test ROM, regardless,
> the verification path is real even though the keys are just examples.

The chapters for this part:

- [The chain of trust](./boot-chain.md) starts by discussing what secure boot is for
  in general, then looks at Egret's boot chain hop by hop, from the `rom_ctrl` hash
  that anchors the root through the ROM_EXT and owner handoffs.
- [Signing and verifying an image](./signature-verification.md) examines one
  of the steps each hop shares, covering the signature process and the fancy
  coprocessor that backs it.
- [Building and running a signed chain](./lab.md) is the hands-on lab,
  where we build and sign an owner image, assemble it into flash next
  to a signed ROM_EXT, and boot both hops using Verilator.
- [ePMP memory protection](./epmp.md) is a hardware feature that covers what a valid signature does not, and is
  what that stops each stage from touching memory it should not.
- [Reading the boot log](./boot-log.md) closes the part by running the same
  boot with one bit flipped and looking at what happens when verification fails.

Every command we show is, again, ones you can run yourself against the Pavona repo.

{{#include ../refs.md}}
