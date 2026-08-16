# Owner-stage image for the Part 2 secure boot lab.
#
# Copy this file and owner_hello.c into your Pavona checkout at lab/, so the
# package label is //lab:owner_hello.

# ANCHOR: loads
load("//rules:const.bzl", "CONST", "hex")
load("//rules:manifest.bzl", "manifest")
load("//rules/pavona:defs.bzl", "pavona_binary")
# ANCHOR_END: loads

# ANCHOR: manifest
manifest({
    "name": "owner_manifest",
    "identifier": hex(CONST.OWNER),
})
# ANCHOR_END: manifest

# ANCHOR: binary
pavona_binary(
    name = "owner_hello",
    testonly = True,
    srcs = ["owner_hello.c"],
    ecdsa_key = {
        "//sw/device/silicon_creator/lib/ownership/keys/fake:app_prod_ecdsa": "prod_key_0",
    },
    exec_env = ["//hw/top_egret:sim_verilator_rom_with_fake_keys"],
    linker_script = "//sw/device/lib/testing/test_framework:ottf_ld_silicon_owner_slot_a",
    manifest = ":owner_manifest",
    # Without this the artifacts are named owner_hello_{name}.*, literal braces
    # included: sim_verilator_rom_with_fake_keys never sets its own exec_env
    # string, and the default "{name}" is used unformatted.
    naming_convention = "{name}",
    deps = [
        "//sw/device/lib/runtime:log",
        "//sw/device/lib/testing/test_framework:ottf_main",
    ],
)
# ANCHOR_END: binary
