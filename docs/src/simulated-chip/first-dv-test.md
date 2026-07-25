# Your first DV test

A green boot tells you the chip works. It does not tell you the chip is correct.
Those are different claims, and the gap between them is where design verification
lives.

## What a boot does and does not prove

When `hello_world_sim_verilator` passed, it proved that one path through the
chip, reset, ROM, jump to flash, configure the UART, print, worked for one set of
inputs. That is a real and valuable signal. It is also a single trace through an
enormous space of possible states. It says nothing about what the UART does when
its transmit FIFO overflows, whether a register reads back its specified reset
value after an odd reset sequence, or how a block behaves under inputs no sane
program would produce but an attacker gladly would. Recall the attacker profiles
from [the threat model](../threats-and-trust-boundaries.md): fault injection is
the deliberate business of driving a chip outside its specification. Any argument
that Egret holds up under that has to come from somewhere other than a
well-behaved boot.

Design verification, DV in the project's language, is the discipline that closes
the gap. Instead of running application software and watching for `PASS!`, DV
wraps an individual block in a testbench that drives it directly, with both
hand-written directed tests and randomized stimulus, and checks every response
against a reference model. It measures coverage, so the question "which behaviors
have actually been exercised?" has a numeric answer rather than an optimistic
one. And it runs checks a booting system never would, starting with the most
basic and most frequently violated: that every control and status register comes
out of reset holding the value the specification says it should.

## Why DV needs a different toolchain

Here is the practical catch. Pavona's DV testbenches are written in UVM, a
SystemVerilog framework built on constructs, classes above all, that open-source
simulators do not support. Pavona's
[DV setup guide](https://docs.pavona.org/book/doc/getting_started/setup_dv.html)
is direct about it: the flow fully supports Synopsys VCS, with support for
Cadence Xcelium as well. Verilator, which carried you through every earlier
chapter, cannot run them. This is not a configuration difference, it is a
genuinely separate toolchain, and access to it usually means an EDA license your
workplace or university holds.

If you do have access, the smoke regression Pavona's CI runs against Egret is a
single command:

```shell
$ util/dvsim/dvsim.py hw/top_egret/dv/top_egret_sim_cfgs.hjson -i smoke --fixed-seed=1
```

The `--fixed-seed=1` pins the randomization so the run is reproducible, which is
exactly how a reported CI failure gets reproduced: same seed, same stimulus, same
result. Without a fixed seed, "it passed on my machine" is not a claim about the
same test.

Even if you never run it, read what that one command covers.
`hw/top_egret/dv/top_egret_sim_cfgs.hjson` is a batch of every individual
testbench in the design, and the list is an education in itself. AES appears
twice, masked and unmasked, because the side-channel countermeasure is a distinct
configuration that has to be verified as such. KMAC likewise. `lc_ctrl` appears
four times, across combinations of volatile unlock enabled and disabled and DMI
access. `rom_ctrl` appears in 32 KiB and 64 KiB variants, `acc` in standard and
post-quantum configurations. Under these sit the primitives, `prim_alert`,
`prim_esc`, `prim_lfsr`, `prim_prince`, and above them the chip-level testbench.
The shape of that list is what verifying a security design actually looks like:
not one testbench per block, but one per meaningful configuration of each block.

## If you don't have a commercial simulator

Most readers will not, and that is fine. The goal of this chapter is not to run
UVM, it is to understand what UVM checks that your boot did not, so that when a
later Part says a block is verified you know what the word covered.

Two things are worth doing instead. The first is to read a real testbench.
Pavona's own docs name `hw/ip/uart/dv` as the canonical example, and it is a good
one precisely because you already know what the UART does from the outside. You
watched it print. Reading its testbench shows the same block examined from the
inside, register by register and transaction by transaction, with a scoreboard
deciding whether each response was right.

The second is to notice how much still runs on Verilator. `sw/device/tests` holds
per-block smoke tests that use the same `sim_verilator` execution environment as
`hello_world`, including `aes_smoketest`, `hmac_smoketest`, `kmac_smoketest`,
`csrng_smoketest`, `entropy_src_smoketest`, `otp_ctrl_smoketest` and
`acc_smoketest`. They are software-driven rather than adversarial, so they prove
less than a UVM regression, but they exercise the blocks the rest of this book is
about and they run on your laptop tonight:

```shell
$ ./bazelisk.sh test sw/device/tests:aes_smoketest_sim_verilator --test_output=streamed
```

Run one of the crypto smoke tests with the instruction trace or a waveform
enabled and you are watching a real block do real work, which is the closest
thing to DV available without a license, and better preparation for the rest of
the book than reading about it.

## What you should have at the end

A clear answer to one question: what does a DV test check that a passing
Verilator boot does not? If you have a commercial simulator, a green `smoke`
regression alongside your green boot. If you do not, a read through
`hw/ip/uart/dv` and a second green Verilator test that drives a block you care
about. Either way you now hold both halves of how this design earns confidence,
the boot that shows it runs and the verification that shows it is right, and that
distinction is the foundation the rest of the book stands on.
