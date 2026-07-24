# How a chip trusts its own code

Primary reference: https://docs.pavona.org/book/doc/security/specs/secure_boot/index.html

> Part intro: why a chip refuses to run unsigned code, and the chain that enforces it.

TODO: build a terminology on-ramp before the ROM_EXT/ePMP specifics, integrity
via hashing vs. authenticity via signatures/HMAC, chain of trust, per feedback
on the 2021 CCSL talk (`ccsl-presentation-2021-03-12/feedback.md`): don't
assume the reader already knows how a binary is measured, verified, and
chained. Add a figure for the hashing/measurement explanation specifically
(what's hashed, how a running digest accumulates), the same feedback flagged
that as missing last time.
