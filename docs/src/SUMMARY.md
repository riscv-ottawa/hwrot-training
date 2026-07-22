# RISC-V Ottawa: Hardware Root of Trust

[Introduction](./index.md)
[What is a Root of Trust?](./what-is-a-root-of-trust.md)
[Why open silicon: OpenTitan and Pavona](./why-open-silicon.md)

# The simulated chip

* [Booting a chip on your laptop]()
  - [Development environment]()
  - [Building Egret in Verilator]()
  - [Hello, World! on the simulated UART]()
  - [Reading the memory map]()
  - [Your first DV test]()
  - [Simulate it]()
<!--* [Booting a chip on your laptop](./simulated-chip/index.md)
  - [Development environment](./simulated-chip/dev-environment.md)
  - [Building Egret in Verilator](./simulated-chip/building-egret.md)
  - [Hello, World! on the simulated UART](./simulated-chip/hello-world.md)
  - [Reading the memory map](./simulated-chip/memory-map.md)
  - [Your first DV test](./simulated-chip/first-dv-test.md)
  - [Simulate it](./simulated-chip/simulate-it.md)-->

# Secure boot

* [How a chip trusts its own code]()
  - [The boot chain: ROM to ROM_EXT to owner]()
  - [Signature verification]()
  - [ePMP memory protection]()
  - [Reading the boot log]()
  - [Simulate it]()
<!--* [How a chip trusts its own code](./secure-boot/index.md)
  - [The boot chain: ROM to ROM_EXT to owner](./secure-boot/boot-chain.md)
  - [Signature verification](./secure-boot/signature-verification.md)
  - [ePMP memory protection](./secure-boot/epmp.md)
  - [Reading the boot log](./secure-boot/boot-log.md)
  - [Simulate it](./secure-boot/simulate-it.md)-->

# Secure storage and lifecycle

* [Keeping secrets and managing state]()
  - [OTP and flash scrambling]()
  - [Lifecycle states]()
  - [The lifecycle gate]()
  - [Simulate it]()
<!--* [Keeping secrets and managing state](./storage-lifecycle/index.md)
  - [OTP and flash scrambling](./storage-lifecycle/scrambling.md)
  - [Lifecycle states](./storage-lifecycle/lifecycle-states.md)
  - [The lifecycle gate](./storage-lifecycle/lifecycle-gate.md)
  - [Simulate it](./storage-lifecycle/simulate-it.md)-->

# Identity and keys (DICE)

* [Where a chip's identity comes from]()
  - [The OTP root secret]()
  - [Key manager derivation and DICE]()
  - [Software binding and key versioning]()
  - [Simulate it]()
<!--* [Where a chip's identity comes from](./identity-keys/index.md)
  - [The OTP root secret](./identity-keys/otp-root-secret.md)
  - [Key manager derivation and DICE](./identity-keys/keymgr.md)
  - [Software binding and key versioning](./identity-keys/binding-versioning.md)
  - [Simulate it](./identity-keys/simulate-it.md)-->

# Attestation

* [Proving who you are]()
  - [Creator and Owner Identity Certificates]()
  - [The certificate chain]()
  - [Verifying a chain off-device]()
  - [Simulate it]()
<!--* [Proving who you are](./attestation/index.md)
  - [Creator and Owner Identity Certificates](./attestation/identity-certificates.md)
  - [The certificate chain](./attestation/cert-chain.md)
  - [Verifying a chain off-device](./attestation/verifying-offline.md)
  - [Simulate it](./attestation/simulate-it.md)-->

# Post-quantum crypto

* [Cryptography that survives quantum computers]()
  - [The acc coprocessor]()
  - [ML-KEM, ML-DSA, and SPHINCS+]()
  - [NIST known-answer tests]()
  - [PQC-enabled secure boot]()
  - [Simulate it]()
<!--* [Cryptography that survives quantum computers](./pqc/index.md)
  - [The acc coprocessor](./pqc/acc-coprocessor.md)
  - [ML-KEM, ML-DSA, and SPHINCS+](./pqc/ml-kem-dsa-sphincs.md)
  - [NIST known-answer tests](./pqc/nist-kats.md)
  - [PQC-enabled secure boot](./pqc/pqc-secure-boot.md)
  - [Simulate it](./pqc/simulate-it.md)-->

# Provisioning and ownership

* [Birth and handover of a device]()
  - [Personalization]()
  - [ECIES-wrapped secret injection]()
  - [Ownership transfer]()
  - [Simulate it]()
<!--* [Birth and handover of a device](./provisioning/index.md)
  - [Personalization](./provisioning/personalization.md)
  - [ECIES-wrapped secret injection](./provisioning/secret-injection.md)
  - [Ownership transfer](./provisioning/ownership-transfer.md)
  - [Simulate it](./provisioning/simulate-it.md)-->

# Breaking it

* [Make it, then break it]()
  - [Forging certificates]()
  - [Replaying attestation]()
  - [Fault injection]()
  - [The protocol red-team]()
  - [An intro to side-channel thinking]()
  - [Simulate it]()
<!--* [Make it, then break it](./breaking-it/index.md)
  - [Forging certificates](./breaking-it/forging-certificates.md)
  - [Replaying attestation](./breaking-it/replay-attestation.md)
  - [Fault injection](./breaking-it/fault-injection.md)
  - [The protocol red-team](./breaking-it/protocol-red-team.md)
  - [An intro to side-channel thinking](./breaking-it/side-channels.md)
  - [Simulate it](./breaking-it/simulate-it.md)-->
