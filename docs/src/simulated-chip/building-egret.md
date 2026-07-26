# Building Egret in Verilator

Building a chip sounds like it should involve a fab. Luckily not the case when doing simulation!
Simulation takes the Verilog that describes Egret and turns it into a program that behaves exactly
like the chip would.

## From RTL to a running model

The build has two halves that Bazel stitches together. The first half is the
hardware. FuseSOC reads Egret's core description, follows its dependencies to
collect every RTL file the design pulls in, and hands the whole set to
Verilator. Verilator translates that synthesizable Verilog into C++ and compiles
it into a single executable, `Vchip_sim_tb`, the cycle-accurate model of the
entire chip. Bazel exposes it as the `//hw:verilator` target.

The second half is the software. The RISC-V toolchain compiles the C you want to
run, `hello_world.c` to start, into an ELF, then converts that ELF into a flash
image in the form the chip expects. This image is one of three images the
chip needs in place before its first clock edge, the next section covers
where the other two come from.

## The four memories, and the three you fill

Egret has four kinds of memory, knowing what each contains is necessary
to get to a properly booting chip.

- **ROM**: 32 KiB of memory based at `0x8000`, holds the first code the core executes. In
  simulation this is the test ROM, whose only job is to bring the chip up and jump to flash.
- **Flash**: two 512 KiB banks based at `0x20000000`, holds our applications. The
  `hello_world` image lives here.
- **OTP**: 2 KiB of one-time-programmable memory, holds no executable code at all.
  It carries root secrets, configuration, and the life cycle state.
- **SRAM**: 128 KiB based at `0x10000000`, is working memory, populated at runtime
  rather than pre-loaded.

At reset the chip needs images for the three non-volatile memories and fills
SRAM as it runs. ROM code is what runs first, flash is what it hands off to, and OTP
is the configuration both of them read. When a run starts, `opentitantool` spawns
the chip model with exactly those three, as `--meminit=rom0,...`,
`--meminit=flash0,...` and `--meminit=otp,...`. The trailing digit on the first
two is a slot number, since ROM and flash can each be loaded in more than one
piece.

Interestingly, the ROM image is scrambled before it is loaded, and its words are 39 bits wide
rather than 32. Those extra seven bits are ECC (error correction code). Egret's `rom_ctrl` descrambles
and integrity-checks every fetch on the fly, so the image on disk is already in
the form the hardware expects to see, which is why the file is named something
like `test_rom_sim_verilator.39.scr.vmem`. The top eight words of ROM are not
code either. They hold the expected 256-bit digest of everything below them, and
at power-on `rom_ctrl` hashes the ROM and compares. You met the consequence of
that check in [the front matter](../what-is-a-root-of-trust.md): the digest it
computes is forwarded to `keymgr`.
The ROM image is not just the first code to run, it is an input to the chip's
identity. See `rom_ctrl`'s
[theory of operation](https://docs.pavona.org/book/hw/ip/rom_ctrl/doc/theory_of_operation.html)
for the scrambling scheme, the 39-bit word format, and the digest-to-`keymgr`
handoff.

The OTP image is the default `img_rma`, which puts the chip in the RMA life
cycle state. RMA leaves debug features enabled, including JTAG access to the
main processor, which is exactly what you want while learning (and exactly what a
production device must NOT allow). Pavona's threat model lists test and debug
interfaces as an attack surface in their own right, so keep in mind that the
chip you are booting is deliberately in its most open configuration for now.

## Building the Hello World image

The example is at `sw/device/examples/hello_world/` in the Pavona repo, three files: the `BUILD`
target, a `README.md`, and `hello_world.c`. A single Bazel invocation compiles it:

```sh
./bazelisk.sh build sw/device/examples/hello_world:hello_world
```

> [!NOTE]
> The extra colon between the directory and the target name is Bazel's label syntax, not a typo.

The build produces a set of files under `bazel-bin/sw/device/examples/hello_world/`, each named for its execution environment:

```sh
hello_world_sim_verilator.elf      # the linked RISC-V binary
hello_world_sim_verilator.dis      # its disassembly, human-readable
hello_world_sim_verilator.map      # the linker map
hello_world_sim_verilator.64.vmem  # the flash image the model loads
```

The `sim_verilator` in every name is the execution environment:
a program declares which environments it supports, Pavona then builds one variant per environment,
named `<program>_<environment>`. `hello_world` declares two, `sim_verilator` and
`sim_dv`. Larger tests such as `sw/device/tests:aes_smoketest` declare a dozen,
including FPGA boards and real silicon, from the same C source. The bare label
`:hello_world` is a suite over those variants rather than a binary itself, which
is why building it produces the `sim_verilator` files above.

> [!TIP]
> Alongside `sim_verilator`, Egret
> defines `sim_verilator_rom_with_fake_keys`, which is the same simulated chip
> booting the real `sw/device/silicon_creator/rom` instead of the test ROM, with
> development signing keys. That is the environment the secure boot tests under
> `sw/device/silicon_creator/rom/e2e` run in, and it is where the next part starts.
> Everything in this part deliberately stays simple and on the test ROM.

A just have a compiled `hello_world_sim_verilator` target in `bazel-bin/`, with its ELF,
disassembly, map, and vmem image, and a Verilator model that is built and
cached. The next chapter goes over actually running all of this.
