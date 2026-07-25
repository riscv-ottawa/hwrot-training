# Building Egret in Verilator

Building a chip sounds like it should involve a fab. In simulation it means
something more approachable: taking the Verilog that describes Egret and turning
it into a program that behaves exactly like the chip would. That program is what
you boot software on.

## From RTL to a running model

The build has two halves that Bazel stitches together. The first half is the
hardware. fusesoc reads Egret's core description, follows its dependencies to
collect every RTL file the design pulls in, and hands the whole tree to
Verilator. Verilator translates that synthesizable Verilog into C++ and compiles
it into a single executable, `Vchip_sim_tb`, the cycle-accurate model of the
entire chip. Bazel exposes it as the `//hw:verilator` target. This step is the
expensive one, on the order of ten minutes the first time, and it only repeats
when the hardware changes.

The second half is the software. The RISC-V toolchain compiles the C you want to
run, `hello_world.c` to start, into an ELF, and then converts that ELF into the
memory images the model loads at reset. Because software changes far more often
than hardware, Bazel caches the compiled model and rebuilds only the software on
later runs, which is why your first boot takes minutes and every one after it
takes seconds.

## The four memories, and the three you fill

Egret has four kinds of memory, and knowing what each holds explains how a bare
model becomes a booting chip.

- ROM, 32 KiB based at `0x8000`, holds the first code the core executes. In
  simulation this is the test ROM, whose only job is to bring the chip up and
  jump to flash.
- Flash, two 512 KiB banks based at `0x20000000`, holds the application. Your
  `hello_world` image lives here.
- OTP, 2 KiB of one-time-programmable memory, holds no executable code at all.
  It carries root secrets, configuration, and the life cycle state.
- SRAM, 128 KiB based at `0x10000000`, is working memory, populated at runtime
  rather than pre-loaded.

At reset the model needs images for the three non-volatile memories and fills
SRAM as it runs. That is not a simulation shortcut, it is the real boot
dependency: ROM code is what runs first, flash is what it hands off to, and OTP
is the configuration both of them read. When a run starts, opentitantool spawns
the model with exactly those three, as `--meminit=rom,...`, `--meminit=flash,...`
and `--meminit=otp,...`.

The images are more interesting than "a file per memory" suggests, and two
details pay off later.

The ROM image is scrambled before it is loaded, and its words are 39 bits wide
rather than 32. Those extra seven bits are ECC. Egret's `rom_ctrl` descrambles
and integrity-checks every fetch on the fly, so the image on disk is already in
the form the hardware expects to see, which is why the file is named something
like `test_rom_sim_verilator.39.scr.vmem`. The top eight words of ROM are not
code either. They hold the expected 256-bit digest of everything below them, and
at power-on `rom_ctrl` hashes the ROM and compares. You met the consequence of
that check in [the front matter](../what-is-a-root-of-trust.md): the digest it
computes is forwarded to `keymgr` and folded into the device's `CreatorRootKey`.
The ROM image is not just the first code to run, it is an input to the chip's
identity.

The OTP image is the default `img_rma`, which puts the chip in the RMA life
cycle state. RMA leaves debug features enabled, including JTAG access to the
main processor, which is exactly what you want while learning and exactly what a
production device must not allow. Pavona's threat model lists test and debug
interfaces as an attack surface in their own right, so keep in mind that the
chip you are booting is deliberately in its most open configuration. The
Secure storage and lifecycle Part is where that stops being a convenience and
starts being the subject.

## Building the Hello World image

The example lives at `sw/device/examples/hello_world/`, three files: the `BUILD`
target, a `README.md`, and `hello_world.c`. One Bazel invocation compiles it:

```shell
$ ./bazelisk.sh build sw/device/examples/hello_world:hello_world
```

The extra colon between the directory and the target name is Bazel's label
syntax, not a typo. The build produces a set of files under
`bazel-bin/sw/device/examples/hello_world/`, each named for its execution
environment:

```
hello_world_sim_verilator.elf      # the linked RISC-V binary
hello_world_sim_verilator.dis      # its disassembly, human-readable
hello_world_sim_verilator.map      # the linker map
hello_world_sim_verilator.64.vmem  # the flash image the model loads
```

The `sim_verilator` in every name is the execution environment, and it is worth
understanding because it is how this repository stays honest about the
difference between designs and targets. A program declares which environments it
supports; Pavona then builds one variant per environment, named
`<program>_<environment>`. `hello_world` declares two, `sim_verilator` and
`sim_dv`. Larger tests such as `sw/device/tests:aes_smoketest` declare a dozen,
including FPGA boards and real silicon, from the same C source. The bare label
`:hello_world` is a suite over those variants rather than a binary itself, which
is why building it produces the `sim_verilator` files above.

One environment deserves an early mention. Alongside `sim_verilator`, Egret
defines `sim_verilator_rom_with_fake_keys`, which is the same simulated chip
booting the real `sw/device/silicon_creator/rom` instead of the test ROM, with
development signing keys. That is the environment the secure boot tests under
`sw/device/silicon_creator/rom/e2e` run in, and it is where the next Part picks
up. Everything in this Part deliberately stays on the test ROM so that the
difference between "it boots" and "it verifies what it boots" stays visible.

You have not run anything yet. You have compiled the chip and the software that
will boot on it. The `.dis` file is worth opening now, because you will hold it
next to the memory map two chapters from now to see exactly where its
instructions touch hardware.

## What you should have at the end

A compiled `hello_world_sim_verilator` target in `bazel-bin/`, with its ELF,
disassembly, map, and vmem image, and a Verilator model that is built and
cached. The next chapter turns the key.
