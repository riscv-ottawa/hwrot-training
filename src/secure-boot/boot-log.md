# Reading the boot log

Before we close this part off, let's take a closer look at the logs our lab
produced, and then go break things on purpose to see what the chip has to say about it.

## The happy path

The happy path is what we saw in [the lab](./lab.md) chapter.
In that chapter we hid some of the logs for brevity, now below here is the full output that you would see if you ran it yourself:

```txt
 OpenTitan:4001-0002-01
ROM_EXT:0.110
IMM_SECTION:0.3-00000000
info: imm_section hash unenforced
warning: corrupted FactoryCerts page
warning: corrupted DiceCerts page
error: UDS certificate not valid
warning: CDI_0 certificate not valid; updating
ownership: \x00\x00\x00\x00
sku_creator_owner_init: saved to flash
info: rescue protocol X
verify: key=2;P256;prod
warning: CDI_1 certificate not valid; updating
[... sixteen ePMP region lines and mseccfg, see epmp.md ...]
entry: 0x20010480
I00001 ottf_main.c:175] Running lab/owner_hello.c
I00002 ottf_main.c:182] Enabling OTTF alert catcher
I00003 owner_hello.c:18] owner_hello: the owner image is running
I00004 ottf_main.c:114] Finished lab/owner_hello.c
I00005 status.c:37] PASS!
```

The first three lines are the stages announcing themselves: ROM, then ROM_EXT,
then ROM_EXT's own immutable section, which runs before the mutable part of
ROM_EXT does.

Then come a handful of lines complaining about certificates, which we can
more-or-less ignore. The device has never been provisioned, so it has no valid
certs to find. Certificates and the DICE identities behind them are covered in a
later part.

Next, `ownership: \x00\x00\x00\x00` and `sku_creator_owner_init: saved to flash`
are ROM_EXT saying that no owner has been configured (hence the four NUL bytes).
ROM_EXT writes itself a default owner and keeps going, which is why we had to
sign with `app_prod_ecdsa` for this lab (it is the key that default owner expects).
Ownership as a concept, and how it changes over time, is covered in a later part too.

The next `info: rescue protocol X` line is not the chip entering rescue. It comes from
`rescue_detect_entry` (`sw/device/silicon_creator/lib/rescue/rescue.c`),
which runs on every single boot to decide whether a rescue was actually
requested/needed, and prints which protocol this build speaks (`X` for [XMODEM][xmodem]).
Our lab example didn't cause any trigger of this, so the boot process carries on normally.

Finally the two lines that belong to the boot chain itself.
`verify: key=2;P256;prod` is the key selection
[the signature chapter](./signature-verification.md) examined, and
`entry: 0x20010480` is the jump into the owner image.
Everything below it is our own owner program running.

Great, now let's break things!

## Making it fail

Recall that the lab's flash image passes through two steps before Verilator ever sees it:
`opentitantool image assemble` stitches the signed ROM_EXT and the signed owner
image into our `twohop.img`, and `srec_cat` converts that to the final `.vmem` the
simulator loads. If we want to emulate an attacker, we can do things to
`twohop.img` and pretend that this is what an attacker with write access _could_ do to flash on an actual running system.

So, let's make a single bit flip somewhere that the digest covers and see what
happens. Each of the two images is a target, at one of these two offsets:

```sh
OFF=2048     # the ROM_EXT image (slot A), mapped at twohop.img@0x0
OFF=69632    # or the owner image, at 0x10000 + 2048
```

The offsets are chosen so the flip lands somewhere that is properly realized;
each image starts with a 1024-byte manifest (`CHIP_MANIFEST_SIZE` in
`sw/device/silicon_creator/lib/base/chip.h`), so byte 2048 is well past the
manifest and its signature field, sitting in the code region the digest actually covers.
The second offset adds that same 2048 offset to `0x10000`, which takes us to the owner slot the lab assembled.

The sections below will take you through both cases, by first doing a new `image assemble`, flipping a bit, doing`srec_cat` again, then running the simulation for each respectively.

## Breaking hop one

Neither of the runs below reads the instruction trace the way
[the ePMP chapter](./epmp.md) did, so we can pass `+ibex_tracer_enable=0` and
save the simulator writing a line per retired instruction.
`--verilator-args` hands anything after it straight to the model
(`sw/host/ot_transports/verilator/src/subprocess.rs`), which is how the plusarg
gets there.

Corrupt the ROM_EXT using the following:

```sh
# Assemble the image again
"$OTT" --rcfile= image assemble --mirror=false --size=0x80000 \
    --output=twohop.img "$ROM_EXT@0x0" "$OWNER@0x10000"
# Corrupt it
OFF=2048
python3 -c "import mmap; f=open('twohop.img','r+b'); m=mmap.mmap(f.fileno(),0); m[$OFF]^=1"
# Generate the simulator vmem image
srec_cat twohop.img --binary --offset 0x0 --byte-swap 8 \
    --fill 0xff -within twohop.img -binary -range-pad 8 \
    --output bad-romext.64.vmem --vmem 64
# Run the simulation
"$OTT" --rcfile= --logging=info --interface=verilator --verilator-bin=$VSIM --verilator-rom=$ROM --verilator-otp=$OTP --verilator-flash=bad-romext.64.vmem --verilator-args=+ibex_tracer_enable=0 console --non-interactive --timeout=900s --logfile=bad-romext.console.log --exit-success='PASS.*\n' --exit-failure='BFV.*\n'
```

The result looks like:

```txt
 OpenTitan:4001-0002-01
BFV:07535603
```

> [!NOTE]
> In the above command, `+ibex_tracer_enable=0` is set to disable instruction trace logs.
> This is just to help speed things up since we're only looking at the console logs.
> If you want to examine the actual instructions executed, just remove the `--verilator-args`.

Bingo! There is no `ROM_EXT:0.110` line at all, meaning ROM rejected the
corrupted ROM_EXT before ever handing it control.

What about `BFV:07535603`? Every `silicon_creator` error is a single 32-bit word
built by the `ERROR_` macro as `(error_id << 24) | (module << 8) | status`.
The module names and per-module error IDs live in `sw/device/silicon_creator/lib/error.h`,
the status codes in `sw/device/lib/base/internal/absl_status.h`.

So split the word into `07`, `5356`, `03` and look each part up: `0x5356` is
ASCII `SV` for `kModuleSigverify`, sigverify error `7` is
`kErrorSigverifyBadEcdsaSignature`, and status `3` is `kInvalidArgument`.
The P-256 signature did not match as expected, which is exactly what a flipped bit should result in!

> [!NOTE]
> The print itself comes from the ROM's `shutdown_report_error`
> (`sw/device/silicon_creator/lib/shutdown.c`), which always emits a `BFV`
> (boot fault value), then an `LCV` (the raw lifecycle state), then a `VER` (the
> chip's SCM revision), in that order. Note that we passed `--exit-failure='BFV.*\n'`,
> so that ends the console the instant the first line matches.

## Breaking hop two

Now the other corruption, with ROM_EXT left untouched (note the fresh
`image assemble`, which recreates the ROM_EXT we just broke above):

```sh
# Assemble the image again
"$OTT" --rcfile= image assemble --mirror=false --size=0x80000 \
    --output=twohop.img "$ROM_EXT@0x0" "$OWNER@0x10000"
# Corrupt it
OFF=69632
python3 -c "import mmap; f=open('twohop.img','r+b'); m=mmap.mmap(f.fileno(),0); m[$OFF]^=1"
# Generate the simulator vmem image
srec_cat twohop.img --binary --offset 0x0 --byte-swap 8 \
    --fill 0xff -within twohop.img -binary -range-pad 8 \
    --output bad-owner.64.vmem --vmem 64
# Run the simulation
"$OTT" --rcfile= --logging=info --interface=verilator --verilator-bin=$VSIM --verilator-rom=$ROM --verilator-otp=$OTP --verilator-flash=bad-owner.64.vmem --verilator-args=+ibex_tracer_enable=0 console --non-interactive --timeout=1800s --logfile=bad-owner.console.log --exit-success='PASS.*\n' --exit-failure='BFV.*\n'
```

This time we get a lot more output:

```txt
 OpenTitan:4001-0002-01
ROM_EXT:0.110
IMM_SECTION:0.3-00000000
info: imm_section hash unenforced
warning: corrupted FactoryCerts page
warning: corrupted DiceCerts page
error: UDS certificate not valid
warning: CDI_0 certificate not valid; updating
ownership: \x00\x00\x00\x00
sku_creator_owner_init: saved to flash
info: rescue protocol X
verify: key=2;P256;prod
BFV:07535603
```

Everything up to `verify: key=2;P256;prod` matches the happy path line for line.
ROM accepted this run's ROM_EXT, and ROM_EXT ran its whole startup, default
owner and all. Only then do things diverge: we see `BFV:07535603` instead of the
normally happy ePMP info followed by the `entry:` line.
This time, the corruption is caught at the owner image's signature check
specifically, not somewhere in ROM_EXT's startup and not by the ROM. Neat!

The code decodes to the same `kErrorSigverifyBadEcdsaSignature`, as expected.
This time though, what print the error log lin was ROM_EXT's own `dbg_printf()`
(see `sw/device/silicon_creator/rom_ext/rom_ext.c`), not the ROM.

This is exact split [the boot chain chapter](./boot-chain.md) covered:
ROM completes execution, hands over to ROM_EXT, then ROM_EXT verifies and catches the bad owner image
(but if you look closer, you'll find it at least offers a way to be given a new valid replacement image later via rescue).

## RTFM

Most of the above findings were gleaned from four main files in the upstream Pavona tree:

- The error encoding, the module list, and the numbered constants:
  `sw/device/silicon_creator/lib/error.h`
- The general status codes comes from:
  `sw/device/lib/base/internal/absl_status.h`
- ROM's shutdown path and the `BFV`/`LCV`/`VER` sequence:
  `sw/device/silicon_creator/lib/shutdown.c`
- ROM_EXT's own failure print and its support for rescue:
  `sw/device/silicon_creator/rom_ext/rom_ext.c`

That wraps up Part 2. Egret verified a real signed boot chain across two hops, isolated
each stage off with ePMP along the way, and refused two different tampered
images (which we could trace back to specific lines of source code because Pavona is open source <3).
Next we'll look at how secrets can be stored in Pavona and how different secrets relate to different
points in the device's lifecycle.

{{#include ../refs.md}}
