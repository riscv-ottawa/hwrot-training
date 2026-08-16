# Building and running a signed chain

Enough theory, let's get the last two chapters running on our own machine!
In this chapter, we're going to write an silicon-owner program,
have Bazel sign it with an owner key,
assemble it into a flash image alongside a signed ROM_EXT,
and boot it all using Verilator through the real secure boot ROM.

Every command below runs from the root of the upstream Pavona repo, inside the toolchain
container we covered in [part 1](../simulated-chip/dev-environment.md).

This will be a two-hop boot process, but will have _one_ flash image in the end that is itself comprised out two separately signed images (placed at two different memory offsets).
We'll start start by creating our very own owner image, then build it, create a final flash image with a ROM_EXT build from already provided code plus our owner image, and, finally, boot it in Verilator.

## The owner image

Create a directory `lab/` at the top of your Pavona checkout, and put two files
in it. Both files can be downloaded directly here if you prefer: [`owner_hello.c`](./lab/owner_hello.c) and [`BUILD`](./lab/BUILD).

First `lab/owner_hello.c`, which is the program that gets to run only if both
signature checks pass. It uses the OTTF, the on-target test framework Part 1's
`hello_world` also ran under:

```c
{{#include ./lab/owner_hello.c}}
```

Returning `true` from `test_main` is what eventually prints `PASS!` - which will, in this case, also proves that ROM has verified ROM_EXT, and ROM_EXT has verified this image.

Next, `lab/BUILD`, which is shown and described below piece-by-piece.

We start with loads, which pull in the manifest rule and Pavona's own binary rule:

```python
{{#include ./lab/BUILD:loads}}
```

Next, the manifest. This is the 1024-byte header
[the previous chapter](./signature-verification.md) briefly discussed; this is us now declaring one ourselves.
`CONST.OWNER` is `0x3042544f` (`rules/const.bzl:18`), the same
value as `CHIP_BL0_IDENTIFIER`, ROM_EXT will refuse the slot completely if the
identifier does not match (`rom_ext_boot_policy.c:66`):

```python
{{#include ./lab/BUILD:manifest}}
```

Finally the binary itself:

```python
{{#include ./lab/BUILD:binary}}
```

There are 3 attributes we need to focus on.

- `ecdsa_key` names
  `app_prod_ecdsa` as the signing key, which is the one the previous chapter
  explained ROM_EXT will have just written into its own owner page on first boot.
- `exec_env` selects `sim_verilator_rom_with_fake_keys`, the environment that
  boots the real secure boot ROM instead of the test ROM.
- `linker_script` places
  the image at the owner slot A offset, so the address it is linked for matches
  the address you are about to assemble it to.

## Build

Let's build it! Run the following from the **base** of the Pavona repo:

```sh
./bazelisk.sh build --jobs=4 \
  //sw/device/silicon_creator/rom:mask_rom_sim_verilator \
  //sw/device/silicon_creator/rom_ext:rom_ext_dice_x509_slot_a \
  //sw/device/silicon_creator/rom_ext/e2e:otp_img_secret2_locked_rma \
  //hw:verilator //lab:owner_hello //sw/host/opentitantool
```

The above builds the ROM, a signed ROM_EXT, an OTP image, the Verilator model of the
chip, your owner image, and the host tool (phew, that's a lot!).

> [!NOTE]
> The OTP image has to be `otp_img_secret2_locked_rma`, not the `img_rma`
> default that Part 1 used. `img_rma` leaves the SECRET2 partition unlocked, so
> `creator_root_key_valid` stays low, `keymgr_ctrl.sv` stays in
> `StCtrlInvalid`, and ROM_EXT's immutable section trips a `HARDENED_CHECK_EQ`
> in `imm_section.c`.
> If you choose `img_rma`, things will just fall over silently and it's very confusing (spoken from experience). If none of the above made sense, no worries, we'll look more closely at OTP partitions in later parts.

## Find the artifacts

The build we just did puts the final device images under a
configuration transition directory (`bazel-out/k8-fastbuild-ST-<hash>/bin`), while
the OTP image, the Verilator model, and `opentitantool` all land in the default one.
A nightmare to find and stitch all of this together yourself. Luckily, we can just ask Bazel.

Execute the following set of commands to find all the various artifacts we need.
We'll set each to its own variable so we can reference them later.

```sh
BIN=$(./bazelisk.sh info bazel-bin)
EXEC=$(./bazelisk.sh info execution_root)
DEV=$EXEC/$(./bazelisk.sh cquery --output=files //lab:owner_hello 2>/dev/null \
  | grep '/owner_hello\.64\.vmem$' | xargs dirname); DEV=${DEV%/lab}

ROM=$DEV/sw/device/silicon_creator/rom/mask_rom_sim_verilator.39.scr.vmem
ROM_EXT=$DEV/sw/device/silicon_creator/rom_ext/rom_ext_dice_x509_slot_a_sim_verilator.prod_key_0.prod_key_0.signed.bin
OWNER=$DEV/lab/owner_hello.prod_key_0.signed.bin
OTP=$BIN/sw/device/silicon_creator/rom_ext/e2e/otp_img_secret2_locked_rma.24.vmem
VSIM=$BIN/hw/build.verilator_real/lowrisc_dv_top_egret_chip_verilator_sim_0.1/sim-verilator/Vchip_sim_tb
OTT=$BIN/sw/host/opentitantool/opentitantool
```

Before going any further, check everything got located and set properly:

```sh
for v in DEV ROM ROM_EXT OWNER OTP VSIM OTT; do
  printf '%-8s %-7s %s\n' "$v" "$([ -e "${!v}" ] && echo OK || echo MISSING)" "${!v}"
done
```

> [!TIP]
> Signed binaries are not default outputs, which is why `ROM`, `ROM_EXT`, and
> `OWNER` are built by appending a known filename to a directory Bazel does
> report. The above loop ensures that any filename that may have drifted from upstream
> shows up here as `MISSING` rather than as a confusing failure later.

## Assemble one flash image

```sh
"$OTT" --rcfile= image assemble --mirror=false --size=0x80000 \
  --output=twohop.img "$ROM_EXT@0x0" "$OWNER@0x10000"
```

The two `@` offsets are `rom_ext_slot_a` and `owner_slot_a` from `EGRET_SLOTS`
in `hw/top_egret/defs.bzl`, the same slots
[the boot chain chapter](./boot-chain.md) showed in the flash layout diagram.
`--size=0x80000` matches the `flash0` region that `--verilator-flash` needs.

Now convert to the 64-bit-word vmem the simulator will actually load:

```sh
srec_cat twohop.img --binary --offset 0x0 --byte-swap 8 \
  --fill 0xff -within twohop.img -binary -range-pad 8 \
  --output twohop.64.vmem --vmem 64
```

> [!NOTE]
> The commands above may seem random/crazy, but they are actually from Pavona's own
> `convert_to_vmem` rule (`rules/pavona/transform.bzl`). There is also a Bazel rule that does the
> assemble and the conversion in one target, `pavona_binary_assemble` in
> `rules/pavona/cc.bzl`, but those are only usable from the FPGA and silicon environments.
> Doing it by hand is more fun anyways.

## Run it

Run this from a dedicated directory:

```sh
"$OTT" --rcfile= --logging=info --interface=verilator \
  --verilator-bin=$VSIM --verilator-rom=$ROM --verilator-otp=$OTP \
  --verilator-flash=twohop.64.vmem \
  console --non-interactive --timeout=3600s --logfile=console.log \
  --exit-success='PASS.*\n' --exit-failure='(FAIL|FAULT).*\n'
```

The simulator will write `uart0.log` and `trace_core_00000000.log` into its working directory.

The console will show a handful of warnings and one `error:` line about
certificates and ownership. They are expected on a device that has never been
provisioned, and the boot continues through them.
See [reading the boot log](./boot-log.md) for more details.

## Watch it run

You may notice long silent stretches after some initial output on the UART, and it may be are hard to tell the silence apart from a hang.
So, open a second shell in the run directory and start watching. The Verilator model includes Ibex's tracer
(`hw/top_egret/chip_egret_verilator.core`), enabled unless you pass
`+ibex_tracer_enable=0`, and it writes one tab-separated line per retired
instruction: time, cycle, PC, encoding, decoded instruction, and the registers
or memory touched (`hw/vendor/lowrisc_ibex/rtl/ibex_tracer.sv`).

Run the following command to get a live feed of execution:

```sh
tail -f trace_core_00000000.log
```

The output is exactly what we mentioned at the end of
[the boot chain chapter](./boot-chain.md), ending in `entry: 0x20010480` and then your own program printing `"owner_hello: the owner image is running"`.

Keep `twohop.img`, `twohop.64.vmem`, and `console.log`. The next two chapters
use all three: [ePMP memory protection](./epmp.md) reads the region dump in the
middle of that console log, and [reading the boot log](./boot-log.md) has you
corrupt `twohop.img` on purpose and run this same command again.

{{#include ../refs.md}}
