# Hello, World!

Everything so far has been preparation. This is the moment the chip comes alive:
one command boots the model, runs your software, and prints back over a simulated
serial port.

## Turning the key

```shell
$ ./bazelisk.sh test sw/device/examples/hello_world:hello_world_sim_verilator --test_output=streamed
```

The target name is the program with the `_sim_verilator` execution environment
appended, and because it is a `test` target Bazel treats a successful run as a
passing test. Behind that one line, Bazel builds the Verilator model if it is not
already cached (the ten-minute step), then hands off to opentitantool, which
spawns the model with the three memory images and connects to its simulated
UART. The `--test_output=streamed` flag is what makes the chip's output appear on
your terminal in real time instead of being captured silently.

The run itself takes about a minute once the model is built. What you are
watching is the simulated chip executing one clock edge at a time, faithfully
enough that the UART bytes it emits are the bytes real silicon would send.

The clocks, on the other hand, are not silicon's. Under this execution
environment the software is told the core runs at 500 kHz and the peripherals at
125 kHz, with the UART at 7200 baud, which you can read for yourself in
`sw/device/lib/arch/device_sim_verilator.c`. Egret in silicon runs its core at
100 MHz. Cycle-accurate means every clock edge is modelled, not that the clock is
set to the frequency a real chip would use, because simulated cycles cost
wall-clock time and a boot has to finish while you are still watching.

## Reading the boot log

A successful run prints something close to this:

```
I00001 test_rom.c:193] kChipInfo: scm_revision=54697461
I00002 test_rom.c:270] Test ROM complete, jumping to flash (addr: 20000480)!
I00000 hello_world.c:37] Hello World!
I00001 hello_world.c:40] Built at: Mar 01 2026, 12:34:56
I00002 hello_world.c:44] PASS!
```

Your run will differ in the details. The revision number, the build timestamp,
and the source line numbers all track whatever Pavona commit you checked out, so
treat the line numbers as pointers to find rather than values to match. The
shape is fixed, and small as it is, this log is the entire run in miniature.

The first two lines come from `test_rom.c`, the code in ROM that runs before
anything else. It reports the chip's revision and then announces that it is
finished and jumping to flash, at `0x20000480` here, just past the base of the
flash region you met in the last chapter. Those two log calls are easy to find in
the source, and reading the code around them is more informative than the log
line itself.

The next three lines come from `hello_world.c` running out of flash. Each is one
`LOG_INFO` call in the source, and the annotations point back at the lines that
emitted them. `PASS!` is not decoration. Pavona's test harness watches the UART
stream and decides the verdict from it, matching `PASS.*\n` for success and
`(FAIL|FAULT).*\n` or `BFV:[0-9a-f]{8}` for failure. A run that came up, printed
happily and never said `PASS!` is a failing test, exactly as intended. That last
failure pattern, the boot fault value, comes from the real secure boot ROM rather
than the test ROM, and you will meet it in the next Part.

## What that log does not prove

Take the win first. A cycle-accurate model of a secure microcontroller booted on
your laptop, ran your code and talked back. That is a real artifact.

Then read the log honestly. The ROM in this run is the test ROM, and Pavona's own
`sw/device/lib/testing/test_rom/README.md` opens by calling it a testing-only
device image, pointing at `sw/device/silicon_creator/rom` as the reference
implementation of the secure boot specification. The test ROM has two jobs:
bootstrap code if asked, then jump to flash. It checks no signature and verifies
no manifest. Nothing in the five lines above tested whether Egret would refuse to
run code an attacker planted, because nothing in this run ever asked.

This is the difference between a chip that runs and a root of trust that
guarantees something, and it is worth holding on to. Egret does have the real
thing, and Pavona wires it up as a separate execution environment,
`sim_verilator_rom_with_fake_keys`, which boots the silicon creator ROM with
development keys. Swapping that in is where the Secure boot Part begins.

## Running it again

Ask Bazel to run the same test a second time and you will likely see it report
`(cached) PASSED` almost instantly. Bazel caches test results and will not re-run
a test whose inputs have not changed. That is usually what you want, but when you
are iterating on the chip or the software and need to force a real run, disable
it:

```shell
$ ./bazelisk.sh test sw/device/examples/hello_world:hello_world_sim_verilator \
    --test_output=streamed --cache_test_results=false
```

## Seeing more than the UART

The UART is a keyhole. The simulation will show you the whole room, and this is
the point in the book where you should turn that on, because every later Part
uses it.

Ibex logs every instruction it retires. The trace lands in
`trace_core_00000000.log` inside Bazel's cache, one tab-separated row per
instruction: simulation time, cycle count, program counter, the instruction
word, its disassembly, then the registers it read and wrote and, for loads and
stores, the address it touched and the data it moved. Bazel's cache buries it, so
go looking:

```shell
$ find ~/.cache/bazel -name "trace_core_00000000.log"
```

That file is the complete execution history of the boot you just watched, from
the first instruction out of reset to the last. The jump from ROM to flash that
the log announced in one line is in there as an actual control transfer you can
find by address.

For hardware state rather than software state, Verilator can dump an FST
waveform. Tracing costs roughly a factor of a thousand in speed, so the test
timeout needs raising to match:

```shell
$ ./bazelisk.sh test sw/device/examples/hello_world:hello_world_sim_verilator \
    --test_output=streamed \
    --test_timeout=1000 \
    --test_arg=--verilator-args=--trace=/tmp/sim.fst
$ gtkwave /tmp/sim.fst
```

The simulation also prints its own process ID at startup and offers a trick
worth remembering: sending it `SIGUSR1` toggles tracing while it runs. On a long
simulation you can leave tracing off, wait for the interesting moment, and
capture only the window you care about instead of gigabytes of boot. When a
later chapter watches the key manager advance through its states, this is the
mechanism doing the watching.

## What you should have at the end

A green `hello_world_sim_verilator` run with `Hello World!` and `PASS!` on your
screen, an understanding of which lines came from ROM and which from your flash
application, and a clear sense of what the run did not check. This is the
artifact the rest of the book builds on: a real, reproducible boot of a secure
microcontroller, running on your laptop, with the instruments attached. Change
the string in `hello_world.c`, rebuild, and watch your own words come back over
the UART, then move on to mapping the chip you just booted.
