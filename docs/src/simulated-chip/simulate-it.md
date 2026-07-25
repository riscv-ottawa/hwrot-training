# Simulate it

You've read how to set up the environment, build Egret, boot it, read its memory
map, and where DV fits. Now do it. Every command in this section is something you
can run against your own Pavona checkout, not just read about.

## Try it yourself

The full walkthrough lives in
[`tutorials/simulated-chip/`](https://github.com/riscv-ottawa/hwrot-training/tree/main/tutorials/simulated-chip)
in this repository (`tutorials/simulated-chip/README.md` if you have cloned it
locally). It takes you from an empty machine to a green boot: build Pavona's
container, build `sw/device/examples/hello_world`, run it on the Verilator model,
confirm the simulated UART prints `Hello World!` and `PASS!`, then open the
disassembly next to `hw/top_egret/doc/memory_map.md` and find where your
`LOG_INFO` calls land in `uart0`'s address range.

The same directory holds `run.sh`, which does the build and the boot end to end,
fails loudly if the chip never prints `PASS!`, and collects the boot log, the
build artifacts, the instruction trace and the waveform into one directory. Do
the steps by hand first, then use the script to prove the whole thing re-runs
from a clean tree. That reproducibility is the quiet claim underneath the rest of
the book: every later Part asserts that something happens in simulation, and the
assertion is only worth something if you can get from an empty machine to the
same result.

The rest of this page works through the two things the tutorial captures but does
not have room to explain: what is actually in the instruction trace, and what the
waveform tells you about simulated time.

## Reading the handoff out of the trace

The boot log summarises the most important moment of the run in one line, `Test
ROM complete, jumping to flash (addr: 20000480)!`. In the instruction trace that
moment is not a message at all. It is a program counter crossing from the ROM
region at `0x8000` into the flash region at `0x20000000`, which is all a boot
handoff has ever been.

Each row of `trace_core_00000000.log` is one retired instruction, whitespace
separated: simulation time, cycle count, program counter, the instruction word,
its disassembly, and then the registers read and written plus, for loads and
stores, the address touched and the data moved. Print the transition and the
instruction that led to it:

```shell
$ awk '$3 ~ /^20/ { print prev; print; exit } { prev = $0 }' trace_core_00000000.log
```

The first row is the last instruction the test ROM executed; the second is the
first instruction executed out of flash, at `0x20000480`. The second column of
that row is the cycle count, so it also tells you how many cycles the chip spent
in ROM before handing over.

That number is worth writing down. It is how long a boot takes when the ROM
verifies nothing at all, and the Secure boot Part measures the same thing again
with the real `silicon_creator` ROM in place, which hashes and checks a signature
before it will jump anywhere. The difference between those two numbers is the
cost of the guarantee, in cycles.

## What the waveform says about simulated time

Capture an FST trace, open it in GTKWave, and find the UART transmit signal
carrying the first character of `Hello World!`. Measure one bit and the period
comes out at about 139 microseconds of simulated time, which is 7200 baud, not
the 115200 you would expect from a serial console.

The reason is in `sw/device/lib/arch/device_sim_verilator.c`, and it is worth
following, because it is the clearest statement in the tree of what a simulation
is and is not. Under the `sim_verilator` execution environment the software is
told the core runs at 500 kHz and the peripheral clock at 125 kHz. Egret in
silicon runs its core at 100 MHz and its peripherals at 24 MHz. The model is
cycle-accurate, meaning every clock edge of the real RTL is evaluated in order.
It is not silicon-accurate in frequency, because simulated cycles cost wall-clock
time, and a boot has to finish while you are still watching.

The baud rate falls out of that choice rather than being picked freely. Pavona
programs the UART through a numerically controlled oscillator, and
`CALCULATE_UART_NCO` in `sw/device/lib/arch/device.h` computes it as
`(baud << 20) / peripheral_clock`, with any result of `0x10000` or more treated
as invalid. That ceiling is the UART's sixteen-times oversampling showing
through: the baud rate can never exceed a sixteenth of the peripheral clock. At
125 kHz that caps you at 7812.5 baud, so 7200 is very nearly the fastest legal
choice, and it yields an NCO of 60397.

Now the arithmetic that explains your wall-clock wait. One bit is 139
microseconds of simulated time, so a ten-bit character frame is about 1.4
milliseconds, or roughly 694 cycles of the 500 kHz core. The boot log you watched
is a few hundred characters, which is a few hundred thousand simulated cycles
spent doing nothing but shifting bits out of a serial port. Printing is by far
the most expensive thing a simulated chip can do, and knowing that changes how
you instrument later exercises: when a chapter needs evidence, a waveform or a
trace costs you nothing at runtime, while another `LOG_INFO` costs you a
thousand cycles.

## Where the verdict comes from

One last thing to notice while you are here. The harness has no privileged view
inside the chip. It decides pass or fail by matching text on the UART:
`PASS.*\n` for success, and `(FAIL|FAULT).*\n` or `BFV:[0-9a-f]{8}` for failure.
Those patterns are `OTTF_SUCCESS_MSG` and `OTTF_FAILURE_MSG` in
`rules/pavona/defs.bzl`, wired into Egret's execution environments in
`hw/top_egret/BUILD`. A test that hangs prints nothing and fails on a timeout
instead. The last of those patterns, the boot fault value, comes from the real
secure boot ROM rather than the test ROM, so you cannot produce one yet. Keep the
shape of it in mind; the next Part is where it starts appearing.
