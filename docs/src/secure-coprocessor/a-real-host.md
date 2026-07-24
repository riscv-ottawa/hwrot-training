# Building a real host

> The stretch: replace the host stimulus with an actual cv32e40x SoC so
> "cv32e40x uses Egret" is literally true. cv32e40x is only a core (two OBI buses
> plus the XIF extension interface, no SPI, no RAM, no SoC;
> `cv32e40x/rtl/cv32e40x_core.sv`), so a minimal host needs the core, an
> OBI-attached RAM/ROM, a small custom OBI SPI-master, and firmware speaking the
> same command protocol against Egret. Explain why the tiny custom SPI-master
> beats adapting OpenTitan's TL-UL `spi_host` (which drags in the `tlul` and
> `prim` libraries and an OBI-to-TL-UL bridge), and why XIF is the wrong tool
> here: it couples a coprocessor into the pipeline on-die at instruction
> granularity, not a separate chip over a bus. Frame this chapter as post-gate
> stretch work.
