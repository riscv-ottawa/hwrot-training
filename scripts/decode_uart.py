#!/usr/bin/env python3
"""Decode UART bytes straight out of an FST waveform.

Surfer has no built-in protocol decoder: its translator plugin API (both the
Rust/WASM kind and the Python kind) hands you one bit-vector value at a time
with no view of neighboring samples, so it cannot reconstruct a byte from a
serial line sampled over time. This script does the reconstruction outside
Surfer, against the FST file directly, using the same `wellen` waveform
reader Surfer itself is built on (via its Python binding, `pywellen`).

Requires: pip install pywellen

Usage:
  ./decode_uart.py sim.fst
  ./decode_uart.py sim.fst --signal 'TOP.chip_sim_tb.cio_uart_tx_d2p' --baud 7200

The default signal path is Egret's UART0 TX pin as wired in
hw/top_egret/dv/verilator/chip_sim_tb.sv (the `cio_uart_tx_d2p` net driven by
`u_dut`, read by the `uartdpi` model). The default baud rate matches that same
file's `uartdpi #(.BAUD('d7_200), ...)` instantiation. If your signal path
differs (a different top module, a renamed instance), pass --signal; the
script lists every variable with "uart" in its name to help you find it.
"""
import argparse
import sys


def decode(signal, transitions, bit_period_ticks):
    """Yield (start_time, byte) for each complete UART frame in transitions."""
    # transitions[0] is the trace's initial value at t=0 (VCD/FST always record
    # one), not a real edge, so it can never be a start bit on its own; start
    # the scan at index 1 and require an actual high-to-low transition.
    i, n = 1, len(transitions)
    while i < n:
        t, v = transitions[i]
        prev_v = transitions[i - 1][1]
        if prev_v != 1 or v != 0:
            i += 1
            continue

        # falling edge from idle high: the start of a start bit.
        bits = []
        for k in range(1, 9):  # 8 data bits, LSB first
            sample_t = t + round((k + 0.5) * bit_period_ticks)
            bits.append(signal.value_at(sample_t))
        stop_t = t + round((9 + 0.5) * bit_period_ticks)
        stop = signal.value_at(stop_t)

        if None in bits or stop != 1:
            print(f"[t={t}] incomplete or misframed byte, skipping", file=sys.stderr)
        else:
            byte = sum(b << k for k, b in enumerate(bits))
            yield t, byte

        # Skip past every transition inside the frame we just consumed.
        i += 1
        while i < n and transitions[i][0] < stop_t:
            i += 1


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("fst", help="path to the FST waveform (e.g. sim.fst)")
    parser.add_argument(
        "--signal",
        default="TOP.chip_sim_tb.cio_uart_tx_d2p",
        help="hierarchical path to the UART TX pin (default: %(default)s)",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=7200,
        help="baud rate, matches uartdpi's BAUD parameter (default: %(default)s)",
    )
    args = parser.parse_args()

    try:
        from pywellen import Waveform
    except ImportError:
        sys.exit("pywellen is not installed; run: pip install pywellen")

    wave = Waveform(args.fst)

    try:
        var = wave[args.signal]
    except KeyError:
        candidates = sorted(
            v.full_name for v in wave.all_vars() if "uart" in v.full_name.lower()
        )
        sys.exit(
            f"'{args.signal}' not found in {args.fst}.\n"
            "Signals with 'uart' in the name:\n  "
            + "\n  ".join(candidates or ["(none found)"])
        )

    if not var.is_1bit:
        sys.exit(f"'{args.signal}' is not a 1-bit signal (width={var.bitwidth}); wrong pin?")

    ts = wave.timescale
    seconds_per_tick = ts.factor * (10 ** ts.unit.to_exponent())
    bit_period_ticks = (1.0 / args.baud) / seconds_per_tick

    signal = var.signal
    transitions = list(signal)  # [(time, value), ...]
    if not transitions:
        sys.exit(f"'{args.signal}' never changes in this trace")

    found = False
    for t, byte in decode(signal, transitions, bit_period_ticks):
        found = True
        ch = chr(byte) if 32 <= byte < 127 else f"\\x{byte:02x}"
        print(f"t={t:<12} 0x{byte:02x} {ch!r}")

    if not found:
        print("no complete UART frames found; check --signal and --baud", file=sys.stderr)


if __name__ == "__main__":
    main()
