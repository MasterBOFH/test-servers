# ircu2 (Undernet's ircd), built from a pinned upstream tag.
# Build from the repo root:
#   docker build -f ircu2/Dockerfile -t ghcr.io/masterbofh/test-servers/ircu2:dev .
ARG DEBIAN_TAG=trixie-20260918-slim

FROM debian:${DEBIAN_TAG} AS build
ARG IRCU_TAG=u2.10.12.19
ARG IRCU_COMMIT=08df0f21fa4086ce98a3e9b415b5afbe78872bff
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates git build-essential flex bison autotools-dev \
 && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch "${IRCU_TAG}" https://github.com/UndernetIRC/ircu2 /src \
 && test "$(git -C /src rev-parse HEAD)" = "${IRCU_COMMIT}"
WORKDIR /src
# The shipped config.guess/config.sub predate aarch64 (pre-2012), so
# configure can't identify an arm64 build machine. Replace them with
# Debian's current copies, as Debian's own packaging does.
RUN find . -name config.guess -exec cp /usr/share/misc/config.guess {} \; \
 && find . -name config.sub -exec cp /usr/share/misc/config.sub {} \; \
 && test -n "$(find . -name config.guess)" \
 && for g in $(find . -name config.guess); do sh "$g" >/dev/null; done
# --with-maxcon: configure otherwise takes `ulimit -Hn` of the build
#   container (~1e9 under Docker) and sizes its connection tables by it.
# --with-domain: else read from the build host's resolv.conf (not
#   reproducible).
RUN ./configure --prefix=/opt/ircu --with-dpath=/opt/ircu/lib \
      --with-maxcon=1024 --with-domain=example.irc.com \
 && make \
 && install -D -m 755 ircd/ircd /opt/ircu/bin/ircd

FROM debian:${DEBIAN_TAG}
ARG IRCU_TAG=u2.10.12.19
LABEL org.opencontainers.image.source="https://github.com/MasterBOFH/test-servers" \
      org.opencontainers.image.version="${IRCU_TAG}" \
      org.opencontainers.image.title="ircu2" \
      org.opencontainers.image.description="ircu ${IRCU_TAG} test server"
RUN useradd --system --home-dir /opt/ircu/lib --shell /usr/sbin/nologin ircd
COPY --from=build /opt/ircu/bin/ircd /opt/ircu/bin/ircd
COPY ircu2/ircd.conf /opt/ircu/lib/ircd.conf
COPY motd.txt /opt/ircu/lib/ircd.motd
# ircd writes its pid and log files into its data dir.
RUN chown -R ircd:ircd /opt/ircu/lib
USER ircd
WORKDIR /opt/ircu/lib
EXPOSE 4443
# -n: stay in the foreground as the container's main process.
CMD ["/opt/ircu/bin/ircd", "-n", "-f", "/opt/ircu/lib/ircd.conf"]
