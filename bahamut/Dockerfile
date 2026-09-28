# Bahamut (DALnet's ircd), built from a pinned upstream tag, with TLS.
# Build from the repo root:
#   docker build -f bahamut/Dockerfile -t ghcr.io/masterbofh/test-servers/bahamut:dev .
ARG DEBIAN_TAG=trixie-20260918-slim
# Upstream release; the git tag is v<version>. Also the image's version label.
ARG BAHAMUT_VERSION=2.2.4

FROM debian:${DEBIAN_TAG} AS build
ARG BAHAMUT_VERSION
ARG BAHAMUT_COMMIT=d81d8aac53ede1a3fbbeb68b1759822e36a2e42b
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates git gcc libc6-dev make autoconf automake \
      zlib1g-dev libssl-dev \
 && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch "v${BAHAMUT_VERSION}" https://github.com/DALnet/bahamut /src \
 && test "$(git -C /src rev-parse HEAD)" = "${BAHAMUT_COMMIT}"
WORKDIR /src

# The one source change: compile out connection throttling (and with it
# per-IP clone limiting, which the same define gates). Every test client
# comes from one address (the Docker bridge gateway), and the throttle
# fires at accept time -- 3 connections in 15s earns a 2-minute, then
# escalating, z:line -- before the allow block's T flag can exempt
# anyone. There is no config-file switch for it, only this compile-time
# define in config.h or an oper's runtime SET THROTTLE.
# grep -q fails the build if a future tag moves this line.
RUN grep -q '^#define THROTTLE_ENABLE' include/config.h \
 && sed -i 's/^#define THROTTLE_ENABLE/#undef THROTTLE_ENABLE/' include/config.h

# The repo ships only configure.in, so generate include/setup.h.in and
# configure first (with automake's copies of the auxiliary scripts
# configure expects alongside).
# --with-maxconnections: MAXCONNECTIONS is compile-time and sizes static
# arrays; left on "auto" it is probed from the *build* container's
# RLIMIT_NOFILE (~1e9 under Docker). At runtime the ircd lowers its own
# soft limit to exactly this value, so no entrypoint ulimit is needed.
# --enable-openssl: TLS listener on 5554. The grep fails the build if
# configure silently fell back to no encryption.
RUN for f in install-sh config.guess config.sub; do \
      cp /usr/share/automake-*/$f .; \
    done \
 && autoheader \
 && autoconf \
 && ./configure --prefix=/opt/bahamut --with-maxconnections=1024 --enable-openssl \
 && grep -q '^#define HAVE_ENCRYPTION_ON' include/setup.h \
 && make \
 && make install


FROM debian:${DEBIAN_TAG}
ARG BAHAMUT_VERSION
LABEL org.opencontainers.image.source="https://github.com/MasterBOFH/test-servers" \
      org.opencontainers.image.version="${BAHAMUT_VERSION}" \
      org.opencontainers.image.title="bahamut" \
      org.opencontainers.image.description="Bahamut ${BAHAMUT_VERSION} test server"

RUN apt-get update \
 && apt-get install -y --no-install-recommends zlib1g libssl3t64 \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --system --home-dir /opt/bahamut --shell /usr/sbin/nologin ircd

COPY --from=build /opt/bahamut /opt/bahamut
COPY bahamut/ircd.conf /opt/bahamut/ircd.conf
COPY motd.txt /opt/bahamut/ircd.motd
# Bahamut loads ircd.crt with SSL_CTX_use_certificate_chain_file, so
# give it leaf+CA; clients can then verify against certs/ca.crt alone.
COPY certs/server-chain.crt /opt/bahamut/ircd.crt
COPY certs/server.key /opt/bahamut/ircd.key

# The ircd writes its pid file, .maxclients and k-line journal next to
# ircd.conf.
RUN chown -R ircd:ircd /opt/bahamut \
 && chmod 600 /opt/bahamut/ircd.key

USER ircd
WORKDIR /opt/bahamut
EXPOSE 4444 5554
# -t: stay in the foreground (don't fork/detach) as the main process.
ENTRYPOINT ["/opt/bahamut/ircd", "-t"]
