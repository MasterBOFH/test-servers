# ircd-ratbox test server, built from the pinned final upstream release.
#
#   docker build -f ircd-ratbox/Dockerfile -t ghcr.io/masterbofh/test-servers/ircd-ratbox:dev .
#   docker run --rm -p 4446:4446 -p 5556:5556 ghcr.io/masterbofh/test-servers/ircd-ratbox:dev
#
# Ports: 4446 plaintext, 5556 TLS (served by ratbox's ssld helper,
# certs/server-chain.crt).
#
# Source: 3.0.10 (Jan 2016) is the last release on the official download
# site. The github.com/ircd-ratbox/ircd-ratbox repository is empty (no
# commits at all), so there is no git ref to pin instead.

ARG DEBIAN_TAG=trixie-20260918-slim

FROM debian:${DEBIAN_TAG} AS build
ARG RATBOX_VERSION=3.0.10
# Published upstream as ircd-ratbox-3.0.10.tar.bz2.sha256.
ARG RATBOX_SHA256=8d871ab81e8581179c3b831e25bd2f6d4f6dfc77380cb190237221bda247ead4
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential bzip2 ca-certificates curl patch libssl-dev \
 && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL -o /ratbox.tar.bz2 \
      "https://www.ratbox.org/download/ircd-ratbox-${RATBOX_VERSION}.tar.bz2" \
 && echo "${RATBOX_SHA256}  /ratbox.tar.bz2" | sha256sum -c - \
 && mkdir /src && tar -xjf /ratbox.tar.bz2 -C /src --strip-components=1
WORKDIR /src
# ratbox has no config switch to skip reverse DNS of connecting clients (and
# a resolver that never answers PTR queries for the Docker bridge range
# stalls every registration past a client's timeout), so patch it out.
# patch fails the build if a future version moves this code.
COPY ircd-ratbox/no-reverse-dns.patch /
RUN patch -p1 --fuzz=0 < /no-reverse-dns.patch
# ac_cv_func_arc4random=no: glibc >= 2.36 has arc4random() but not
# arc4random_stir(), which libratbox's no-TLS PRNG (nossl.c) calls whenever
# configure finds arc4random. With OpenSSL that file compiles to nothing, so
# this only matters if configure ever falls back to no TLS -- which the grep
# below then fails the build on anyway (configure falls back silently).
RUN ac_cv_func_arc4random=no \
    ./configure --prefix=/opt/ratbox --enable-openssl --disable-zlib \
 && grep -q '^#define HAVE_OPENSSL 1' libratbox/include/libratbox_config.h \
 && make \
 && make install

FROM debian:${DEBIAN_TAG}
ARG RATBOX_VERSION=3.0.10
LABEL org.opencontainers.image.source="https://github.com/MasterBOFH/test-servers" \
      org.opencontainers.image.version="${RATBOX_VERSION}" \
      org.opencontainers.image.title="ircd-ratbox" \
      org.opencontainers.image.description="ircd-ratbox ${RATBOX_VERSION} test server"
# netbase provides /etc/services. ratbox's resolver helper resolves each
# resolv.conf nameserver with getaddrinfo(ns, "domain"); without that file
# every nameserver is silently dropped and no DNS query is ever sent. (Client
# lookups are patched out above; without that patch, this alone made every
# client stall ~30s at "Looking up your hostname".)
RUN apt-get update \
 && apt-get install -y --no-install-recommends libssl3t64 netbase \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --system --home-dir /opt/ratbox --shell /usr/sbin/nologin ircd
COPY --from=build /opt/ratbox /opt/ratbox
COPY ircd-ratbox/ircd.conf /opt/ratbox/etc/ircd.conf
COPY motd.txt /opt/ratbox/etc/ircd.motd
COPY --chown=ircd:ircd --chmod=600 certs/server.key /opt/ratbox/etc/server.key
COPY certs/server-chain.crt /opt/ratbox/etc/server-chain.crt
# The ircd writes its pid file and ban database under etc/, logs under logs/.
RUN mkdir -p /opt/ratbox/logs \
 && chown -R ircd:ircd /opt/ratbox/etc /opt/ratbox/logs
USER ircd
WORKDIR /opt/ratbox
EXPOSE 4446 5556
# libratbox spins at 100% CPU and never answers a client when RLIMIT_NOFILE
# is as huge as Docker's default can be (1073741816), so cap it here rather
# than rely on the runner passing --ulimit. (ssld inherits the limit.)
CMD ["/bin/sh", "-c", "ulimit -n 4096 && exec /opt/ratbox/bin/ircd -foreground"]
