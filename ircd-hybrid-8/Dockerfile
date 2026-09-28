# ircd-hybrid 8.2.x test server, built from a pinned upstream tag.
#
#   docker build -f ircd-hybrid-8/Dockerfile -t ghcr.io/masterbofh/test-servers/ircd-hybrid-8:dev .
#   docker run --rm -p 4442:4442 -p 5552:5552 ghcr.io/masterbofh/test-servers/ircd-hybrid-8:dev
#
# Ports: 4442 plaintext, 5552 TLS (certs/server-chain.crt).

ARG DEBIAN_TAG=trixie-20260918-slim

FROM debian:${DEBIAN_TAG} AS build
ARG HYBRID_TAG=8.2.47
# Commit the tag points at; the build fails if the tag is ever moved.
ARG HYBRID_COMMIT=1ad473137191b1a7e2992145dcf67bf6f44beb7c
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential ca-certificates git libjansson-dev libssl-dev \
 && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch "${HYBRID_TAG}" \
      https://github.com/ircd-hybrid/ircd-hybrid /src \
 && test "$(git -C /src rev-parse HEAD)" = "${HYBRID_COMMIT}"
WORKDIR /src
# configure silently falls back to no TLS if it can't find OpenSSL, so
# assert it was actually found.
RUN ./configure --prefix=/opt/hybrid --with-tls=openssl \
 && grep -q '^#define HAVE_LIBSSL 1' config.h \
 && make -j"$(nproc)" \
 && make install

FROM debian:${DEBIAN_TAG}
ARG HYBRID_TAG=8.2.47
LABEL org.opencontainers.image.source="https://github.com/MasterBOFH/test-servers" \
      org.opencontainers.image.version="${HYBRID_TAG}" \
      org.opencontainers.image.title="ircd-hybrid-8" \
      org.opencontainers.image.description="ircd-hybrid ${HYBRID_TAG} test server"
RUN apt-get update \
 && apt-get install -y --no-install-recommends libjansson4 libssl3t64 \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --system --home-dir /opt/hybrid --shell /usr/sbin/nologin ircd
COPY --from=build /opt/hybrid /opt/hybrid
COPY ircd-hybrid-8/ircd.conf /opt/hybrid/etc/ircd.conf
COPY motd.txt /opt/hybrid/etc/ircd.motd
COPY --chown=ircd:ircd --chmod=600 certs/server.key /opt/hybrid/etc/server.key
COPY certs/server-chain.crt /opt/hybrid/etc/server-chain.crt
# The ircd writes its pid file, logs and k/d/x-line databases under var/.
RUN chown -R ircd:ircd /opt/hybrid/var
USER ircd
WORKDIR /opt/hybrid
EXPOSE 4442 5552
CMD ["/opt/hybrid/bin/ircd", "-foreground"]
