# Driving the root of trust from a host

Primary reference: `pavona/hw/top_egret/doc/datasheet.md` (host-facing peripherals)
and `pavona/hw/ip/spi_device/doc/theory_of_operation.md`.

> Part intro (post-decision-date capstone): the payoff of the whole project.
> Everything up to here studied Egret from the inside. This Part uses it from the
> outside, the way a product does: a separate application processor (an OpenHW
> cv32e40x host) treats Egret as a discrete secure element and offloads its
> security operations to it over a bus.
>
> TODO before writing: this is the heaviest Part. Pace it as more than one ~3-hour
> session. It replaces the earlier "Breaking it" Part; the single break-it
> exercise is `breaking-the-link.md` (a bus-level replay/tamper on the
> host<->Egret SPI link), which lands harder here because the reader has just
> built the very link being attacked.
>
> Accuracy anchors (verify against the repos, do not restate the specs):
> - Host channel: Egret exposes `spi_device` (fixed IO; TPM, generic/firmware,
>   flash, and passthrough modes) as the primary way an off-chip host drives it
>   (`pavona/hw/top_egret/doc/datasheet.md`,
>   `pavona/hw/ip/spi_device/doc/theory_of_operation.md`). UART is the secondary
>   console channel.
> - Egret has no mailbox IP. The on-die mailbox model belongs to the integrated
>   `top_dragonfly`, not the discrete Egret; keep that distinction sharp.
> - This is chip-to-chip over a bus, not a core swap, and not the cv32e40x XIF
>   extension interface. XIF is an on-die, pipeline-coupled coprocessor interface,
>   the wrong model for an off-chip secure element.
