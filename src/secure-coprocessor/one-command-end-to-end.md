# One command, end to end

> Walk a single request from host to Egret and back: the host sends a command,
> Egret performs a real security operation (recommended: sign a host-supplied
> nonce, or emit an attestation), and the result is verified off-device. This is
> the artifact the part is built to reach. In the committed tier the "host" is a
> lightweight SPI (or UART) model in Egret's own Verilator harness (`spidpi` /
> `uartdpi` in `pavona/hw/top_egret/dv/verilator/chip_sim_tb.sv`; Verilator target
> `pavona/hw/top_egret/chip_egret_verilator.core`), driving Egret's `spi_device`.
> Be explicit that the host is stimulus here, not cv32e40x RTL yet; the real core
> arrives in the next chapter.
