# Development environment

Before you can build a chip you need the tools that turn its source into
something runnable. Pavona's toolchain is larger than a typical firmware
project's because it spans two worlds at once, hardware and software, and the
same repository builds both. Understanding what each tool does makes the setup
feel less like an incantation and more like assembling a workbench.

At the center is [Bazel](https://bazel.build/), invoked through a wrapper script
called `bazelisk.sh` that fetches the exact Bazel version the project expects.
Bazel is the single entry point for almost everything. It builds the RISC-V
software that runs on the chip, and it also drives the hardware build. When you
ask Bazel for a `sim_verilator` target, it runs
[fusesoc](https://github.com/olofk/fusesoc) to gather the RTL, invokes Verilator
to generate and compile the C++ model, builds the device software, and finally
launches
[opentitantool](https://github.com/lowRISC/opentitan/tree/master/sw/host/opentitantool)
to load the memory images and stream the chip's output back to your terminal.
You rarely call Verilator, fusesoc, or opentitantool yourself; Bazel orchestrates
them, which is why nearly every command in this Part starts with `./bazelisk.sh`.

Two details are worth knowing up front. Verilator is built from source rather
than installed from a package, because distribution packages tend to lag badly
behind. Pavona pins the version in `third_party/verilator/extensions.bzl`, 5.046
at the time of writing, and Bazel compiles it for you the first time you build a
simulation target. That compile is the bulk of the first ten-minute wait, and it
happens once. Second, the Python tooling (topgen, regtool, dvsim, and the
scripts that generate register files and documentation) runs in a
project-specific virtual environment, installed from `python-requirements.txt`
with hash pinning, so its dependencies never collide with your system Python.

Two paths lead to a working workbench. Pavona's
[getting started guide](https://docs.pavona.org/book/doc/getting_started/index.html)
documents the native one: an Ubuntu host, the package list in
`apt-requirements.txt`, and the Python virtual environment above. It works well
if you already run a supported Ubuntu. The container path below is the shorter
route for everyone else, and it is what the rest of this Part assumes.

## Containerized build with Podman or Docker

Pavona provides a container definition at `util/container/Dockerfile`, built on
Ubuntu 22.04, that installs every system dependency the getting started guide
lists. The container holds those dependencies; your Pavona checkout stays on the
host and is bind-mounted in, so your edits, your Bazel cache, and your git
history live in one place and outlive any container you throw away.

We use [Podman](https://podman.io/) here, but every invocation below is
identical under Docker (substitute `docker` for `podman`, and note that Pavona's
own instructions run `docker build` under `sudo`).

Build the image once from the top of your Pavona checkout:

```shell
podman build -t pavona -f util/container/Dockerfile .
```

Then start an interactive shell in it, mapping your checkout to `/home/dev/src`
inside the container. The `DEV_UID` and `DEV_GID` variables give the container's
`dev` user your own user and group IDs, so files it creates land back on the
host owned by you rather than by root:

```shell
podman run -t -i \
  -v $(pwd):/home/dev/src \
  --env DEV_UID=$(id -u) --env DEV_GID=$(id -g) \
  pavona:latest \
  bash
```

`util/container/README.md` documents an optional `USER_CONFIG` variable, a path
to a shell script sourced at startup if you want your own environment set up
inside the container. It is not required. `sudo` works inside the container if
you need to add a package. Once you are at the container's shell, the
`bazelisk.sh` flow is exactly the same as on the native path.

One caveat specific to rootless Podman: the bind-mounted checkout has to be
readable and writable by your user, and the `DEV_UID` and `DEV_GID` mapping
above is what keeps ownership consistent across the boundary. Permission
surprises in the build almost always trace back to that mapping rather than to
anything in Pavona.

## Ready

You can now open a shell inside the container and run the Bazel wrapper:

```shell
cd ~/src && ./bazelisk.sh
```

With no arguments it fetches the pinned Bazel release and prints Bazel's usage
message, which is all you need to see: the wrapper works and the workspace is
recognized. Nothing has been built yet, but the workbench is assembled. The next
chapter puts it to work.
