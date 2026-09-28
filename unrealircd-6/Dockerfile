# UnrealIRCd 6, built from the pinned official release tarball.
# Plaintext clients on 4441, TLS on 5551 (the repo's shared certificate).
#
#   docker build -f unrealircd-6/Dockerfile -t ghcr.io/masterbofh/test-servers/unrealircd-6:dev .
#   docker run --rm -p 4441:4441 -p 5551:5551 ghcr.io/masterbofh/test-servers/unrealircd-6:dev
#
# The build context is the repository root (for certs/ and motd.txt).

ARG DEBIAN_IMAGE=debian:trixie-20260918-slim

FROM ${DEBIAN_IMAGE} AS build

# UnrealIRCd doesn't publish git tags; this is the release tarball from
# unrealircd.org. SHA256 matches the one published on
# https://www.unrealircd.org/download/6.0/6.2.7/src (the tarball's .asc GPG
# signature also verifies against the UnrealIRCd release key).
ARG VERSION=6.2.7
ARG SHA256=e075375f469309bf1d54134bc914ec50a4ae3b09da6d2db2c11f9fa88d649370

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential pkg-config ca-certificates curl \
      libssl-dev libpcre2-dev libargon2-dev libsodium-dev libc-ares-dev libjansson-dev \
 && rm -rf /var/lib/apt/lists/*

# UnrealIRCd refuses to build or run as root.
RUN useradd --create-home --home-dir /home/ircd --uid 10001 --shell /bin/sh ircd
USER ircd
WORKDIR /home/ircd

RUN curl -fsSL -o unrealircd.tar.gz "https://www.unrealircd.org/downloads/unrealircd-${VERSION}.tar.gz" \
 && echo "${SHA256}  unrealircd.tar.gz" | sha256sum -c - \
 && tar -xzf unrealircd.tar.gz \
 && rm unrealircd.tar.gz

WORKDIR /home/ircd/unrealircd-${VERSION}
# ./Config is interactive; `-quick` skips every question and runs
# ./configure straight from the answers in config.settings.
COPY --chown=ircd:ircd unrealircd-6/config.settings ./config.settings
RUN ./Config -quick \
 && make -j"$(nproc)" \
 && make install
# Fail the build unless UnrealIRCd links Debian's libargon2 (see
# config.settings): the bundled one is tuned to the build machine's CPU.
RUN ldd /home/ircd/unrealircd/bin/unrealircd | grep -q '^\s*libargon2\.so\.1 => /lib/' \
 && ! ls /home/ircd/unrealircd/lib | grep -q argon2

# Shared test certificate (leaf + CA chain, so clients can verify against
# certs/ca.crt), at the paths set::tls in unrealircd.conf points to.
COPY --chown=ircd:ircd certs/server-chain.crt /home/ircd/unrealircd/conf/tls/server-chain.crt
COPY --chown=ircd:ircd certs/server.key /home/ircd/unrealircd/conf/tls/server.key
COPY --chown=ircd:ircd motd.txt /home/ircd/unrealircd/conf/ircd.motd
COPY --chown=ircd:ircd unrealircd-6/unrealircd.conf /home/ircd/unrealircd/conf/unrealircd.conf
# The key is public test material, but keep the file private anyway; and
# fail the build on a bad config rather than at container start.
RUN chmod 600 /home/ircd/unrealircd/conf/tls/server.key \
 && /home/ircd/unrealircd/unrealircd configtest

FROM ${DEBIAN_IMAGE}

ARG VERSION=6.2.7
LABEL org.opencontainers.image.source="https://github.com/MasterBOFH/test-servers" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.title="unrealircd-6" \
      org.opencontainers.image.description="UnrealIRCd ${VERSION} test server"

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libssl3t64 libpcre2-8-0 libargon2-1 libsodium23 libc-ares2 libjansson4 \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --home-dir /home/ircd --uid 10001 --shell /bin/sh ircd

# Same absolute path as the build stage: paths (and the private lib rpath)
# are compiled in.
COPY --from=build --chown=ircd:ircd /home/ircd/unrealircd /home/ircd/unrealircd

USER ircd
EXPOSE 4441 5551
# -F: stay in the foreground as PID 1; logs go to stderr (docker logs).
ENTRYPOINT ["/home/ircd/unrealircd/bin/unrealircd", "-F"]
