# ngIRCd, built from a pinned upstream release tarball, with TLS.
# Build from the repo root:
#   docker build -f ngircd/Dockerfile -t ghcr.io/masterbofh/test-servers/ngircd:dev .
ARG DEBIAN_TAG=trixie-20260918-slim

FROM debian:${DEBIAN_TAG} AS build
# Release "ngIRCd 28" (tag rel-28). The sha256 is of the release asset
# ngircd-28.tar.gz; the same bytes are served by the GitHub release and
# by https://ngircd.barton.de/pub/ngircd/.
ARG NGIRCD_VERSION=28
ARG NGIRCD_SHA256=d4ae5d4f5f13d136f77e7aaff2cdc80fcd3b9a171ac31c28adbae2f4643c04a8
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates curl build-essential libssl-dev zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL -o /ngircd.tar.gz \
      "https://github.com/ngircd/ngircd/releases/download/rel-${NGIRCD_VERSION}/ngircd-${NGIRCD_VERSION}.tar.gz" \
 && echo "${NGIRCD_SHA256}  /ngircd.tar.gz" | sha256sum -c - \
 && mkdir /src \
 && tar -xzf /ngircd.tar.gz -C /src --strip-components=1
WORKDIR /src
# The release tarball ships a generated configure. Ident and PAM are
# opt-in and left out (see ngircd.conf); --with-openssl for TLS.
RUN ./configure --prefix=/opt/ngircd --sysconfdir=/opt/ngircd/etc \
      --with-openssl \
 && make \
 && make install

FROM debian:${DEBIAN_TAG}
ARG NGIRCD_VERSION=28
LABEL org.opencontainers.image.source="https://github.com/MasterBOFH/test-servers" \
      org.opencontainers.image.version="${NGIRCD_VERSION}" \
      org.opencontainers.image.title="ngircd" \
      org.opencontainers.image.description="ngIRCd ${NGIRCD_VERSION} test server"
RUN apt-get update \
 && apt-get install -y --no-install-recommends libssl3t64 zlib1g \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --system --home-dir /opt/ngircd --shell /usr/sbin/nologin ircd
COPY --from=build /opt/ngircd /opt/ngircd
COPY ngircd/ngircd.conf /opt/ngircd/etc/ngircd.conf
COPY motd.txt /opt/ngircd/etc/ngircd.motd
COPY certs/server-chain.crt /opt/ngircd/etc/ssl/server-chain.crt
COPY --chown=ircd:ircd --chmod=600 certs/server.key /opt/ngircd/etc/ssl/server.key
USER ircd
EXPOSE 4445 5555
# -n: stay in the foreground as the container's main process.
CMD ["/opt/ngircd/sbin/ngircd", "-n", "-f", "/opt/ngircd/etc/ngircd.conf"]
