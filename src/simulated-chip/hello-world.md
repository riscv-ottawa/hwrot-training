# Hello, World!

We've prepared everything needed.
One command can now be used to boot the simulated chip/model, run your software,
and print things back over a simulated serial port.

```sh
./bazelisk.sh test sw/device/examples/hello_world:hello_world_sim_verilator --test_output=streamed
```

The target name is the program with the `_sim_verilator` execution environment
appended, and because it is a `test` target Bazel treats a successful run as a
passing test. This one line has Bazel build the Verilator model if it is not
already cached (the long ~10 min initial step), then hand off to `opentitantool`, which
spawns the model with the three memory images and connects to its simulated
UART. The `--test_output=streamed` flag is what makes the chip's output appear on
your terminal in real time instead of being captured silently.

The run itself takes about a minute once the model is built. What you are
watching is the simulated chip executing one clock edge at a time, faithfully
enough that the UART bytes it emits are the bytes real silicon would send. Woohoo!

> [!NOTE]
> Clocks are something that diverge in simulation vs. silicon.
>
> In our execution environment, the software is told the core runs at 500 kHz and the peripherals at
> 125 kHz, with the UART at 7200 baud (you can read for yourself in
> `sw/device/lib/arch/device_sim_verilator.c`). Egret in silicon runs its core at
> 100 MHz. Cycle-accurate means every clock edge is modelled, not that the clock is
> set to the frequency a real chip would use. Each simulated cycle costs
> extra time in simulation, so things are kept lower in sim.

## Reading the boot log

A successful run prints something close to this:

```
I00001 test_rom.c:200] kChipInfo: scm_revision=54697461
I00002 test_rom.c:276] Test ROM complete, jumping to flash (addr: 20000480)!
I00000 hello_world.c:35] Hello World!
I00001 hello_world.c:38] Built at: Jul 25 2026, 22:00:47
I00002 hello_world.c:41] PASS!
```

Your run will differ in some details. For example, the revision number, the build timestamp,
and the source line numbers all track whatever Pavona commit you checked out, so
treat the line numbers as pointers to find rather than values to match.

The first two lines come from `test_rom.c`, the code in ROM that runs before
anything else. It reports the chip's revision and then announces that it is
finished and jumping to flash, at `0x20000480` here, just past the base of the
flash region.

The next three lines come from `hello_world.c` running out of flash. Each is one
`LOG_INFO` call in the source, and the annotations point back at the lines that
emitted them. `PASS!` is Pavona's test harness watching the UART
stream and deciding the verdict from it, matching `PASS` for success.
A run that came up, printed happily and never said `PASS!` is a failing test.

## Running it again

Ask Bazel to run the same test a second time and you will likely see it report
`(cached) PASSED` almost instantly. Bazel caches test results and will not re-run
a test whose inputs have not changed. That is usually what you want, but when you
are iterating on the chip or the software and need to force a real run, disable
it:

```sh
./bazelisk.sh test sw/device/examples/hello_world:hello_world_sim_verilator \
    --test_output=streamed --cache_test_results=false
```

## Seeing more than the UART

There is much more to look at then just the UART output!

Ibex logs every instruction it executes. The trace lands in
`trace_core_00000000.log` inside Bazel's cache, one tab-separated row per
instruction. There is actually a lot more than just the instructions though.
In the log file, you'll find info about simulation time, cycle count, program counter, the instruction
word, its disassembly, then the registers it read and wrote and, for loads and
stores, the address it touched and the data it moved. Wow!

The log file is a bit buried, so to find it...use `find`:

```sh
find ~/.cache/bazel -name "trace_core_00000000.log"
```

That file is the complete software execution history of the boot you just watched, from
the first instruction out of reset to the last.

For hardware state rather than software state, Verilator can dump an FST
waveform.

> [!NOTE]
> Turning on Verilator waveform tracing (`--trace=/tmp/sim.fst`) makes the simulation run WAY
> slower than without tracing, so the test's timeout value needs to be raised proportionally
> or Bazel may kill the test before it finishes.

```sh
./bazelisk.sh test sw/device/examples/hello_world:hello_world_sim_verilator \
    --test_output=streamed \
    --test_timeout=1000 \
    --test_arg=--verilator-args=--trace=$HOME/src/sim.fst
```

> [!NOTE]
> Neither GTKWave nor Surfer is in Pavona's container image.
> If you want to view it, open the file on your host system,
> in whichever waveform viewer you have installed on the host, e.g.,
> GTKWave or [Surfer][surfer].

> [!TIP]
> The simulation also prints its own process ID at startup and there is a trick
> worth noting: sending `SIGUSR1` toggles tracing while it runs. On a long
> simulation you can leave tracing off, wait for the interesting moment, and
> capture only the window you care about instead of gigabytes of boot.

## A good start

Great! We now have a green `hello_world_sim_verilator` run with `Hello World!` and `PASS!` on our
screens, an understanding of which lines came from ROM and which from the flash
application, and a clear sense of what the run did not check.

This starting point is what the rest of the book builds on, let's keep going!

{{#include ../refs.md}}
