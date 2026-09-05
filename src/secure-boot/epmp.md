# ePMP memory protection

In the last few sections we have learned about the boot chain and even got the whole chain running ourself.
However, once the upper stages, such as, ROM_EXT, owner code, and further application code start to run and continue to execute...but what is actually stopping an upper stage from from reading and tampering with code and data (e.g., ROM secrets) from the stages below it?
A valid signature says a stage is who it claims to be, but says nothing about what that
stage can touch. [Enhanced Physical Memory Protection (ePMP)][smepmp] is the hardware
that answers this question and the subject of this chapter.

## The end state

If you ran the lab in the last section and stared at the boot logs long enough, you would notice that it contains lines (coming from ROM_EXT) that print the entire ePMP
configuration immediately before jumping to the owner image
(see `dbg_print_epmp()` in `sw/device/silicon_creator/lib/dbg_print.c` and how it's called from `rom_ext.c`):

```
0: 00000000 ----- ---- sz=00000000
1: 00000000 ----- ---- sz=00000000
2: 20010400 ----- ---- sz=00000000
3: 20012148   TOR -X-R sz=00001d48
4: 00000000 ----- ---- sz=00000000
5: 00000000 ----- ---- sz=00000000
6: 00000000 ----- ---- sz=00000000
7: 00000000 ----- ---- sz=00000000
8: 20002e88 ----- ---- sz=00000000
9: 2000b550   TOR -X-R sz=000086c8
10: 00000000 ----- ---- sz=00000000
11: 1001c000   NA4 ---- sz=00000004
12: 20000000 NAPOT ---R sz=00100000
13: 00010000 NAPOT -XWR sz=00001000
14: 40000000 NAPOT --WR sz=10000000
15: 10000000 NAPOT --WR sz=00020000
mseccfg = 00000006
entry: 0x20010480
```

The above lines show the sixteen numbered PMP entries, each showing an address, addressing mode, and a
permission string, then at the bottom we see `mseccfg` ([Machine Security Configuration Register][mseccfg]).
The `epmp_defs.h` file has definitions of what the letters mean: each entry's mode is one of `OFF`,
`TOR` (top-of-range: this entry and the previous one together bound a region), `NA4`,
or `NAPOT` (naturally aligned power of two, decoding address and size together from one register),
and the printed field is in lock/execute/write/read order. A leading `-` means the lock bit is clear,
so every entry above is unlocked.

That matters here. At this handoff the owner starts in machine mode with Machine Mode Lockdown
(`MML`) clear. `MPRV` is also clear, so loads and stores use machine-mode permissions. In that
state, the R/W/X bits of a matching unlocked entry do not restrict the owner; they describe access
for less-privileged code.

Let's take a look at some of the rows:

- **Entry 3** is `20012148 TOR -X-R sz=00001d48`, execute-and-read but not
  write for less-privileged code. In TOR mode it pairs with entry 2, so the region runs from
  `0x20010400` to `0x20012148`, the `0x1d48` bytes the row reports.
  This is the owner image's text region, granted by `rom_ext.c` as the
  last ePMP write before handing off to owner code, which is why the printed
  `entry: 0x20010480` log is an address inside here. Because the entry is unlocked and `MML` is
  clear, however, PMP does not deny a write by the machine-mode owner.
- **Entry 9** is `2000b550 TOR -X-R sz=000086c8` (so paired with entry 8 similar as above),
  covering `0x20002e88` to `0x2000b550`. This is ROM_EXT's mutable code region (see
  `imm_section_epmp.c`). ROM_EXT configures it as locked read-execute, but it appears unlocked here
  because ROM_EXT clears every lock bit before the owner handoff.
- **Entry 12** is `20000000 NAPOT ---R sz=00100000`, which is one megabyte
  of flash starting at `0x20000000`, with read-only permission for less-privileged code.
- **Entry 15** is `10000000 NAPOT --WR sz=00020000`, which is all of main
  RAM left as read-write for less-privileged code. It is off at hardware reset. Once ROM creates it,
  its range, mode, and R/W/X bits remain through the owner handoff, although its L bit is cleared.
- **Entry 13**, is the debug ROM at `00010000`, which is currently left with full `-XWR` full access.
  This particular value depends on the device's lifecycle state (our lab has OTP
  provisioned in the RMA mode, which is why debug access is wide open here);
  lifecycle mechanisms will be covered in a later part.
- `mseccfg = 00000006` sets bits 1 and 2: `MMWP` (Machine-Mode Whitelist
  Policy) and `RLB` (Rule Locking Bypass). `MMWP` denies a machine-mode access when no PMP entry
  matches; it does not make a matching unlocked entry restrict machine mode. `RLB` lets locked PMP
  rules be rewritten. Because every entry in the final dump is unlocked, the owner can rewrite the table.

These are PMP conclusions only; the flash and SRAM controllers impose separate restrictions.

## How it got that way

The table above is the end result of a sequence rather than a
configuration executed by a single stage. The chip does not boot naked and screaming (with all memory
unprotected): hardware reset starts with three active locked mappings for ROM, MMIO, and debug ROM,
and early ROM replaces that state with seven active locked regions. ROM and ROM_EXT then reshape the
map, and ROM_EXT clears the PMP locks before the owner handoff, so each stage does not simply hand over
less than it had.
However, each stage doesn't do much logging as these changes happen in real-time,
so the Ibex instruction trace streamed to a file in [the lab](./lab.md) helps reconstruct them:

```sh
grep -E 'pmpcfg|pmpaddr|mseccfg' trace_core_00000000.log
```

Most of what comes back is the boot code re-reading its own configuration, but there are the writes
hiding in there - let's take a look.

## Three takeaways

At the bottom of this chapter you'll find references to the code that was referenced
in tandem with reading through the trace logs mentioned above.
All-in-all, going through this will reveal that the ePMP register writes fall into eight passes across the two-hop boot sequence.
We'll go over three of the most interesting learning takeaways below.

### Next-stage code is not executable until it has been verified

On start-up each next stage's code region remains readable so that the stage below it can check its
signature, but it is not executable yet. ROM opens ROM_EXT's text read-execute after ROM's check
passes. After verifying the owner, ROM_EXT installs its unlocked read-execute mapping before calling it.
The stuff we covered in [signing and verifying an image](./signature-verification.md)
exists exactly so that the system can verify before these ePMP writes are safe to make.

### Some entries are inherited

Do a global search through the Pavona codebase for the comment
"Reclaim entries 0 ~ 7 from ROM and ROM_EXT IMM_SECTION", and you'll find
our next takeaway.

Before ROM_EXT boots the owner image it clears entries 0 through 7 with a simple loop. Entries 8
through 15 remain configured, and entries 2 and 3 are then reused for the owner's executable region.
The handoff is therefore not a blank slate: some entries are reclaimed while others carry forward.

### The lock bit matters

Next, note how ROM and ROM_EXT install locked executable mappings during creator boot, while RAM is
locked read-write and not executable. Before owner handoff, however, ROM_EXT clears every PMP lock
bit. Because the owner starts in machine mode with `MML` clear, the final unlocked R/W/X bits do not
restrict its machine-mode accesses. At the PMP layer, they therefore do not stop the owner from
writing executable memory or executing writable memory.

### And more

For reference, here all eight passes alluded to earlier, in order:

| Pass                           | Who                                             | What changed                                                                                                                 |
| ------------------------------ | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `rom_epmp_init`                | ROM, hand-crafted assembly before the C runtime | Activates seven locked PMP regions. Leaves ROM_EXT's executable mapping off until its signature has been verified.           |
| `rom_epmp_config_debug_rom`    | ROM                                             | Debug ROM entry (lifecycle state), overriding the assembly's hardcoded default.                                              |
| `rom_epmp_unlock_rom_ext_rx`   | ROM                                             | Opens ROM_EXT as read-execute. Only after the signature check has passed.                                                    |
| `imm_section_epmp_reconfigure` | ROM_EXT                                         | Reconfigures MMIO access, the stack guard, and flash, opens ROM_EXT's own _immutable_ text section, and clears selected old entries. |
| `imm_section_epmp_mutable_rx`  | ROM_EXT                                         | Opens the rest of ROM_EXT's code, past the immutable section.                                                                |
| `rom_ext_init`                 | ROM_EXT                                         | Clears entries 0 through 7. Entries 8 through 15 remain configured.                                                         |
| `epmp_clear_lock_bits`         | ROM_EXT                                         | Unlocks every entry before the owner handoff.                                                                                 |
| `epmp_set_tor(2, ...)`         | ROM_EXT                                         | Adds an unlocked read-execute mapping for the verified owner's text region, sized from the manifest, right before the handoff. |

No write anywhere in the trace touches an address above `0x20010000`, where the
owner image lives. The owner never configures ePMP at all.
That describes what this sample owner does, not what PMP prevents: it starts in machine mode with
every PMP entry unlocked, so it can rewrite the policy.

A compromised or malicious owner image, even one that somehow obtained a valid
signature, could therefore rewrite this PMP policy. `MMWP` denies a machine-mode access when no
entry matches, but it does not make a matching unlocked entry restrict machine mode while `MML` is
clear.

Overall, the signature chain decides who gets to run next; ePMP applies the memory-access policy
configured for that stage. These two mechanisms work together to improve the security guarantees of the overall system.

## RTFM

All of the above can be found in roughly seven files from the Pavona repo:

- The hardware reset map: `hw/top_egret/rtl/ibex_pmp_reset_pkg.sv`
- ROM's initial setup, in assembly: `sw/device/silicon_creator/rom/rom_epmp_init.S`
- ROM's lifecycle fix and the ROM_EXT grant: `sw/device/silicon_creator/rom/rom_epmp.c`
- ROM_EXT's reshuffle and its own code regions: `sw/device/silicon_creator/rom_ext/imm_section/imm_section_epmp.c`
- The reclaim loop and the owner grant: `sw/device/silicon_creator/rom_ext/rom_ext.c`
- The driver all of them call: `sw/device/silicon_creator/lib/drivers/epmp.c`
- The in-memory shadow copy and its check: `sw/device/silicon_creator/lib/epmp_state.c`

Next up we'll take a quick look at the serial boot log output and close off this part.

{{#include ../refs.md}}
