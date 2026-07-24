# Simulate it

> Hands-on walkthrough outlined in tutorials/secure-coprocessor/ (real content
> pending Phase 8): drive Egret's `spi_device` from a host model via the
> cryptotest/ujson service, have Egret sign a fresh host nonce, verify it
> off-device, then run the bus-level replay/tamper attack and watch freshness and
> signing defeat it.
>
> Challenge: get Egret to sign a fresh host nonce over SPI and verify it
> off-device. Stretch challenge: replace the DPI host with a real cv32e40x SoC.
