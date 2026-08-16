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
and the permission string is read/write/execute, prefixed with a lock bit (not printed out in the logs).
Let's take a look at some of the rows:

- **Entry 3** is `20012148 TOR -X-R sz=00001d48`, execute-and-read but not
  write. In TOR mode it pairs with entry 2, so the region runs from
  `0x20010400` to `0x20012148`, the `0x1d48` bytes the row reports.
  This is the owner image's text region, granted by `rom_ext.c` as the
  last ePMP write before handing off to owner code, which is why the printed
  `entry: 0x20010480` log is an address inside here. What this means is that the owner code gets to run,
  but is denied by hardware to rewrite its own code (or any other memory outside its predefined regions).
- **Entry 9** is `2000b550 TOR -X-R sz=000086c8` (so paired with entry 8 similar as above),
  covering `0x20002e88` to `0x2000b550`. This is ROM_EXT's own code region (see `imm_section_epmp.c`),
  which is, again, deliberately not writable by ROM_EXT itself or anything else.
- **Entry 12** is `20000000 NAPOT ---R sz=00100000`, which is one megabyte
  of read-only memory starting at the base of flash.
- **Entry 15** is `10000000 NAPOT --WR sz=00020000`, which is all of main
  RAM left as read-write. This is the one entry that never changes for the entire boot process,
  as discussed further below.
- **Entry 13**, is the debug ROM at `00010000`, which is currently left with full `-XWR` full access.
  This particular value depends on the device's lifecycle state (our lab has OTP
  provisioned in the RMA mode, which is why debug access is wide open here);
  lifecycle mechanisms will be covered in a later part.
- `mseccfg = 00000006` sets bits 1 and 2: `MMWP` (Machine-Mode Whitelist
  Policy) and `RLB` (Rule Locking Bypass). `MMWP` is a deny-by-default posture for all
  sixteen entries above: any address these sixteen rules do not explicitly cover is inaccessible, no exceptions (or well, yes exceptions...but only the fault kind IYKWIM).

## How it got that way

The table above is the end result of a sequence rather than a
configuration executed by a single stage. The chip boots naked and screaming (all memory unprotected),
but then every stage that runs hands over less than it had and provides the necessary protection.
However, each stage doesn't do much logging as these changes happen in real-time,
so the only record is the Ibex instruction trace the were streamed to a file in [the lab](./lab.md):

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

### Nothing is executable until it has been verified

On start-up each stage's code region has its addressing mode and permissions cleared which,
when `MMWP` is enabled, means it is completely unreachable. It regions only opens up
once the stage below it has finished checking its signature.
Once verified, then access and execution permissions are granted.
This process is repeated a few times: ROM opens ROM_EXT's text read-execute right after ROM's check passes,
and ROM_EXT opens the owner's text read-execute right before it jumps there.
The stuff we covered in [signing and verifying an image](./signature-verification.md)
exists exactly so that the system can verify before this one write to ePMP is safe to make.

### Nothing is inherited

Do a global search through the Pavona codebase for the comment
"Reclaim entries 0 ~ 7 from ROM and ROM_EXT IMM_SECTION", and you'll find
our next takeaway.

Before ROM_EXT boots the owner image it wipes every region ROM built via a
simple loop over entries 0 through 7. ROM's own text, the flash window ROM
started with, all of it is cleared in ePMP (and thus access restricted).
This shows how trust flows forward up the chain but capability does not.
Each level re-grants from scratch whatever the next level
needs, so a stage's reach is only what the stage below it deliberately handed
over, never something left lying around.

### Code is never writable

Next, note how every code region the chain grants comes out read-execute, and RAM stays
read-write and never executable, so nothing that runs can rewrite itself. That
holds for ROM, ROM_EXT, and the owner image alike. The one entry in the final
table with both write and execute is the debug ROM, and that's only because our lab
configured provisioning as RMA, as noted above. RAM is also the single region that
survives the whole boot untouched, being the thing every stage needs and none
of them ever executes from.

### And more

For reference, here all eight passes alluded to earlier, in order:

| Pass                           | Who                                             | What changed                                                                                                                 |
| ------------------------------ | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `rom_epmp_init`                | ROM, hand-crafted assembly before the C runtime | Activates seven PMP regions. Does not include any of ROM_EXT's since it is not verified yet.                                 |
| `rom_epmp_config_debug_rom`    | ROM                                             | Debug ROM entry (lifecycle state), overrides the assembly's hardcoded default when debug is enabled.                         |
| `rom_epmp_unlock_rom_ext_rx`   | ROM                                             | Opens ROM_EXT as read-execute. Only after the signature check has passed.                                                    |
| `imm_section_epmp_reconfigure` | ROM_EXT                                         | Reconfigures MMIO access, the stack guard, and flash, opening ROM_EXT's own _immutable_ text section, and dropping the rest. |
| `imm_section_epmp_mutable_rx`  | ROM_EXT                                         | Opens the rest of ROM_EXT's code, past the immutable section.                                                                |
| `rom_ext_init`                 | ROM_EXT                                         | Clears entries 0 through 7. Everything ROM set is cleared.                                                                   |
| `epmp_clear_lock_bits`         | ROM_EXT                                         | Unlocks every entry so the last pass can rewrite them.                                                                       |
| `epmp_set_tor(2, ...)`         | ROM_EXT                                         | Hands the owner its read-execute region, sized determined by the given manifest, right before the jump.                      |

No write anywhere in the trace touches an address above `0x20010000`, where the
owner image lives. The owner never configures ePMP at all.
It instead just boots inside a locked jail created by the stages before it.

A compromised or malicious owner image, even one that somehow obtained a valid
signature, cannot (over)write its own code, and whatever has not been explicitly granted to access
is denied by `MMWP`.

Overall, the signature chain decides who gets to run next; ePMP decides what they are physically
capable of touching once they do. These two mechanisms work together to improve the security guarantees of the overall system.

## RTFM

All of the above can be found in roughly six files from the Pavona repo:

- ROM's initial setup, in assembly: `sw/device/silicon_creator/rom/rom_epmp_init.S`
- ROM's lifecycle fix and the ROM_EXT grant: `sw/device/silicon_creator/rom/rom_epmp.c`
- ROM_EXT's reshuffle and its own code regions: `sw/device/silicon_creator/rom_ext/imm_section/imm_section_epmp.c`
- The reclaim loop and the owner grant: `sw/device/silicon_creator/rom_ext/rom_ext.c`
- The driver all of them call: `sw/device/silicon_creator/lib/drivers/epmp.c`
- The in-memory shadow copy and its check: `sw/device/silicon_creator/lib/epmp_state.c`

Next up we'll take a quick look at the serial boot log output and close off this part.

{{#include ../refs.md}}
