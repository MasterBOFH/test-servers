# Solanum (Libera.Chat's ircd, successor of charybdis) test server.
#
#   docker build -f solanum/Dockerfile -t ghcr.io/masterbofh/test-servers/solanum:dev .
#   docker run --rm -p 4447:4447 -p 5557:5557 ghcr.io/masterbofh/test-servers/solanum:dev
#
# Ports: 4447 plaintext, 5557 TLS (certs/server-chain.crt).
#
# Solanum publishes no tags or releases, so this pins a commit on the
# default branch (its head on 2026-09-22), fetched as GitHub's source
# tarball for that commit and checked against a sha256 computed from it.

ARG DEBIAN_TAG=trixie-20260918-slim

FROM debian:${DEBIAN_TAG} AS build
ARG SOLANUM_COMMIT=03503ff488ea5757a0fdfd62b7509b02b41904ab
ARG SOLANUM_SHA256=8a02793a99625ad014680bc05188027bd1a6332e367870b85b026d371e8eb526

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential pkg-config meson ninja-build flex bison \
      libsqlite3-dev libltdl-dev libssl-dev ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL -o /solanum.tar.gz \
      "https://github.com/solanum-ircd/solanum/archive/${SOLANUM_COMMIT}.tar.gz" \
 && echo "${SOLANUM_SHA256}  /solanum.tar.gz" | sha256sum -c - \
 && mkdir /src && tar -xzf /solanum.tar.gz -C /src --strip-components=1
WORKDIR /src

# The one source change: authd never loads its reverse-DNS provider, so
# clients register immediately with their IP as host. Solanum has no config
# switch for rDNS, and a resolver that never answers PTR queries for the
# Docker bridge range stalls every registration ~6s (the lowest configurable
# timeout, connect_timeout = 1, still costs 1-2s). authd then logs one
# harmless "BUG: handle_options got a bad option type rdns_timeout" at
# startup: the ircd still sends that setting.
# grep -q fails the build if a future pin moves this line.
RUN grep -q '^\s*load_provider(&rdns_provider);' authd/provider.c \
 && sed -i '/^\s*load_provider(&rdns_provider);/d' authd/provider.c

# OpenSSL backend for ssld (the TLS port). It's also the only option that
# builds at all: librb's no-TLS backend (nossl.c) calls arc4random_stir,
# which current glibc doesn't provide.
RUN meson setup build --prefix=/opt/solanum --optimization=2 \
      -Dopenssl=enabled -Dmbedtls=disabled -Dgnutls=disabled \
 && meson compile -C build \
 && meson install -C build


FROM debian:${DEBIAN_TAG}
ARG SOLANUM_COMMIT=03503ff488ea5757a0fdfd62b7509b02b41904ab
LABEL org.opencontainers.image.source="https://github.com/MasterBOFH/test-servers" \
      org.opencontainers.image.version="${SOLANUM_COMMIT}" \
      org.opencontainers.image.title="solanum" \
      org.opencontainers.image.description="Solanum ${SOLANUM_COMMIT} test server"

# netbase provides /etc/services: authd's resolver looks up the "domain"
# service by name, and without it finds no nameservers and exits in a loop.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libsqlite3-0 libltdl7 libssl3t64 netbase \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --system --home-dir /opt/solanum --shell /usr/sbin/nologin ircd

COPY --from=build /opt/solanum /opt/solanum
COPY solanum/ircd.conf /opt/solanum/etc/ircd.conf
COPY motd.txt /opt/solanum/etc/ircd.motd
COPY --chown=ircd:ircd --chmod=600 certs/server.key /opt/solanum/etc/server.key
COPY certs/server-chain.crt /opt/solanum/etc/server-chain.crt
COPY solanum/entrypoint.sh /entrypoint.sh

# The ircd writes its pid file and ban database under etc/ and var/, and
# its log under logs/.
RUN mkdir -p /opt/solanum/logs /opt/solanum/var \
 && chown -R ircd:ircd /opt/solanum/etc /opt/solanum/var /opt/solanum/logs

USER ircd
WORKDIR /opt/solanum
EXPOSE 4447 5557
ENTRYPOINT ["/entrypoint.sh"]
