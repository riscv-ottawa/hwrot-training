# Booting a chip on your laptop

The entire Pavona Egret design and source is completely open. You can read, edit,
and create a cycle-accurate model of the whole chip that can run directly on the laptop in front of you.
So, let's get hands-on!.

By the end of this part, you will have compiled the chip into a simulator, booted real software on it,
watched control pass from ROM to flash, printed `Hello World!` over a simulated
UART, and traced those characters back to the exact hardware registers used.

Everything runs in [Verilator](https://www.veripool.org/verilator/), which
magically translates synthesizable Verilog into a C++ program.
This allows you to exercise things one clock edge at a time.
But be warned, this fidelity has some costs, for example, the first build
may take on the order of ten minutes, and booting the thing (which, in real silicon would finish in
milliseconds) takes about a minute. Not that bad though! And what this buys you is visibility no
physical chip can offer. Ibex writes out every instruction executed, and any
signal anywhere in the design can be dumped to a waveform, including signals that
would not reach any pin on real silicon. Clairvoyant!

> [!NOTE]
> Booting a chip and securing a chip are different achievements.
> What we are about to run is the _test ROM_, a
> development image whose own README calls out as testing-only, and it verifies no
> signatures whatsoever. The real secure boot ROM lives in
> `sw/device/silicon_creator/rom` and is subject to later parts. This part
> is just to show the chip coming up, that it runs our code, and how we can watch it happen.

The chapters for this part:

- [Development environment](./dev-environment.md) sets up the toolchain (Bazel,
  fusesoc, Verilator, and the Python tooling).
- [Building Egret in Verilator](./building-egret.md) covers building the chip,
  from RTL through fusesoc to a compiled simulation binary, and the three memory images it boots from.
- [Hello, World!](./hello-world.md) boots real software,
  reads the log line by line, and turns on the instrumentation.
- [Reading the memory map](./memory-map.md) closes the part by mapping the chip
  so you can navigate and locate each block by address.

Every command here is one you run against your own Pavona checkout, and you walk
away with a reproducible green boot you can get back to from a clean tree.
