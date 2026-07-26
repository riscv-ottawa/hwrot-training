# Development environment

Before you can build a chip you need the tools that turn its source into
something runnable. Pavona's toolchain is larger than a typical firmware
project's because it spans two worlds at once, hardware and software...and the
same repository builds both. Understanding what each tool does makes the setup
feel less like wizardry and more like a normal down-to-earth toolbox.

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
You rarely call Verilator, fusesoc, or the opentitantool yourself; Bazel orchestrates
them, which is why nearly every command in this part starts with `./bazelisk.sh`.

> [!NOTE]
> Bazel is like `make`...but on steroids. You name a target and it
> works out what to rebuild just like `make`, except Bazel also goes and fetches its own tools
> (Verilator included), runs every step sandboxed so the result does not depend
> on what is lying around your machine, and caches test results and not just
> build outputs.

In the container we're going to use, Verilator is built from source rather
than installed from a package, because distribution packages tend to lag badly
behind. Pavona pins the version in `third_party/verilator/extensions.bzl` (`5.046`
at the time of writing) and Bazel compiles it for you the first time you build a
simulation target. That compile is the bulk of the first ten-minute wait, but it
only happens once. Second, the Python tooling (topgen, regtool, dvsim, and the
scripts that generate register files and documentation) runs in a
project-specific virtual environment, installed from `python-requirements.txt`
with version/hash pinning, so its dependencies never collide with any system Python packages in the container.

There are two options to get your dev environment set up. Pavona's
[getting started guide](https://docs.pavona.org/book/doc/getting_started/index.html)
documents a native one running on a Ubuntu host. It works well
if you already run a supported Ubuntu version. The container path below is the simpler
option and works more broadly, thus it is what the rest of this book assumes.

## Containerized build with Podman or Docker

Pavona provides a container definition at `util/container/Dockerfile`, built on
Ubuntu 22.04, that installs every system dependency the getting started guide
lists. Your locally checked out version of the Pavona repo stays on the
host and is bind-mounted in, so your edits, your Bazel cache, and your git
history live in one place and outlive any container you recycle.

We use [Podman](https://podman.io/) here, but every invocation below is
identical under Docker (substitute `docker` for `podman`, drop the `--userns`
and `--user` flags explained below since Docker does not need them, and note
that Pavona's own instructions run `docker build` under `sudo`).

Build the image once from the top of your Pavona checkout:

```sh
podman build -t pavona -f util/container/Dockerfile .
```

Then start an interactive shell in it, mapping your checkout to `/home/dev/src`
inside the container. The `DEV_UID` and `DEV_GID` variables give the container's
`dev` user your own user and group IDs, so files it creates land back on the
host owned by you rather than by root:

```sh
podman run -it \
  --userns=keep-id \
  --user root:root \
  -v $(pwd):/home/dev/src \
  --env DEV_UID=$(id -u) --env DEV_GID=$(id -g) \
  pavona:latest \
  bash
```

> [!NOTE]
> Rootless Podman gives every container its own private user namespace, so by
> default a process the container thinks is UID 1000 is not the same as UID
> 1000 on your host, it is remapped. Using `--userns=keep-id`
> fixes that by mapping your real host UID into the container as itself, but
> it also makes the container start as that UID instead of root, which breaks
> the `DEV_UID`/`DEV_GID` remap the entrypoint script needs to run as root.
> `--user root:root` puts root back for the entrypoint.

## Ready

You can now open a shell inside the container and run the Bazel wrapper:

```sh
cd ~/src && ./bazelisk.sh
```

With no arguments it fetches the pinned Bazel release and prints Bazel's usage
message. This is enough proof that the wrapper works and the workspace is
is good to go. Onwards!
