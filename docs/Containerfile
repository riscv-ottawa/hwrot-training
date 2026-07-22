FROM ubuntu:24.04 as mdbook

COPY . .

ENV DEBIAN_FRONTEND=noninteractive TZ=UTC
RUN apt-get -y update && \
    apt-get -y --no-install-recommends install ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

ARG MDBOOK_VERSION=v0.5.2
RUN curl -sSL https://github.com/rust-lang/mdBook/releases/download/${MDBOOK_VERSION}/mdbook-${MDBOOK_VERSION}-x86_64-unknown-linux-gnu.tar.gz | tar -xz --directory=/usr/bin/

RUN ["mdbook", "build"]

FROM ghcr.io/static-web-server/static-web-server:2-alpine
ENV SERVER_PORT=8000
ENV SERVER_HEALTH=true
WORKDIR /
COPY --from=mdbook ./book /public

EXPOSE 8000
