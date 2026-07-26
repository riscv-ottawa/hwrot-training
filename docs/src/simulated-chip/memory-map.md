# Reading the memory map

You have booted a chip. Now you need to be able to find your way around it. A
microcontroller is, from software's point of view, a set of hardware blocks
bolted onto a single address space, and to talk to any block you read from or
write to its addresses. The memory map is the directory of that address space,
and it is the reference you will reach for in every remaining part of this book.

## Where the map comes from

Egret's map is not written by hand, it is generated, and the file says so in its
own first lines:

```
util/topgen.py -t hw/top_egret/data/top_egret.hjson -o hw/top_egret/
```

`top_egret.hjson` is the machine-readable description of how the chip is
assembled, listing every block, its interfaces, and where it lands in the address
space. One topgen run over that description emits the RTL that wires the top
level together, the documentation you are about to read in
`hw/top_egret/doc/memory_map.md`, and the C headers the firmware compiles
against. Open `hw/top_egret/sw/autogen/top_egret_memory.h` and you will find

```c
#define TOP_EGRET_UART0_BASE_ADDR 0x40000000
```

which is the same number, from the same source, as the `uart0` row of the map.
That is why the map can be treated as ground truth rather than documentation.
The address in the document, the address decoded by the bus, and the constant
your C compiles against cannot drift apart, because all three are printed from
one description.

## Walking the address space

Open the map and a structure emerges. Peripherals begin at `0x40000000` with the
four UARTs, then GPIO, SPI, and I2C. `uart0` at `0x40000000` is the one your
`Hello World!` came out of. Higher up sit the blocks that make this a root of
trust rather than a microcontroller:

| Block                   | Base address                | Size                | Its job                                                       |
|-------------------------|-----------------------------|---------------------|---------------------------------------------------------------|
| `otp_ctrl`              | `0x40130000`                | `0x1000`            | one-time-programmable storage: root secrets, life cycle state |
| `lc_ctrl`               | `0x40140000`                | `0x100`             | the life cycle controller: what the chip will and will not do |
| `aes`                   | `0x41100000`                | `0x100`             | symmetric encryption                                          |
| `hmac`                  | `0x41110000`                | `0x2000`            | hashing and message authentication                            |
| `kmac`                  | `0x41120000`                | `0x1000`            | Keccak-based MAC, used in key derivation                      |
| `keymgr`                | `0x41140000`                | `0x100`             | the key manager: derives Egret's identity keys                |
| `csrng` / `entropy_src` | `0x41150000` / `0x41160000` | `0x80` / `0x100`    | random number generation                                      |
| `rom_ctrl`              | `0x411E0000`                | `0x80`              | the ROM controller that checks the boot ROM                   |
| `acc`                   | `0x41300000`                | `0x20000`           | the asymmetric cryptography coprocessor                       |

The sizes are worth a second look, because they say something the base addresses
do not. Most blocks occupy a few hundred bytes: `keymgr`, the block that derives
the device's identity, is a `0x100` window, sixty-four 32-bit registers. `acc` is
`0x20000`, a full 128 KiB. That is not a register file. It is the coprocessor's
own instruction and data memories mapped into the address space, which is what
you would expect from a block that runs its own programs, and it is the first
hint of the security boundary described in the
[ACC documentation](https://docs.pavona.org/book/hw/ip/acc/doc/acc_intro.html):
Ibex loads a program and its inputs, sets a bit, and cannot read that memory back
while ACC is running.

Each row here is a later chapter. `otp_ctrl` and `lc_ctrl` are the Secure storage
and lifecycle part; `keymgr`, `kmac`, and `otp_ctrl` together are the Identity and
keys part; `acc` is the Post-quantum crypto part. The memory map is where those
chapters attach to the running chip, because every one of them is reached through
an address in this table.

Below the peripherals are the memories you loaded images into: ROM at `0x8000`,
main SRAM at `0x10000000`, and flash at `0x20000000`. These are the addresses the
boot log referred to when the test ROM announced it was jumping to flash at
`0x20000480`, just past the base of the flash region.

## Cross-referencing the disassembly

The map becomes real when you hold it against the software you built. Open the
disassembly from two chapters ago:

```shell
less bazel-bin/sw/device/examples/hello_world/hello_world_sim_verilator.dis
```

Follow how `hello_world.c`'s `LOG_INFO` calls turn into UART traffic. The logging
path ends in stores to `uart0`'s registers, and every one of those stores targets
an address inside the `0x40` byte window at `0x40000000`, sixteen 32-bit
registers holding the whole programming interface of the UART. Find one such
store and match its address to the map's `uart0` row. That is the exercise: a
line of C connected to the exact hardware register it drives.

If you captured the instruction trace in the last chapter, do this a second way.
The trace records the address and data of every load and store the core executed,
so the same UART writes appear there as they actually happened, in order, with
cycle counts attached. The disassembly tells you what the program intended; the
trace tells you what the chip did. Reading both against one map is the habit this
part exists to build.

## What you should have at the end

The memory map open next to your disassembly, with at least one `uart0` register
access located and matched, and ideally the same access found in the instruction
trace. More than that, you have the navigation key for the rest of the book. When
a later chapter says "the key manager", you will know it means `0x41140000`, and
you will know how to watch software reach it.
