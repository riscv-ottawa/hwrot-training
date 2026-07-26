# The command channel

> How a host submits a command and reads a response over `spi_device`:
> flash-mode command upload plus the mailbox/read-buffer region, the OTTF console
> (`opentitan/sw/device/lib/testing/test_framework/ottf_console_spi.c`), and the
> ujson serialization layer. Ground it in the ready-made `cryptotest` framework
> (`opentitan/sw/device/tests/crypto/cryptotest/`), whose device firmware already
> runs a command server for AES, HMAC, KMAC, SHA/HASH, DRBG (RNG), ECDSA, RSA,
> Ed25519, and SPHINCS+, with a matching host harness. Explain the request ->
> compute -> response shape without reproducing the spi_device register tables;
> link to the spec for those.
