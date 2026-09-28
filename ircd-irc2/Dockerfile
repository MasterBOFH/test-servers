# ircd-irc2: IRCnet's ircd 2.11, built from a pinned upstream tag.
# Build from the repo root:
#   docker build -f ircd-irc2/Dockerfile -t ghcr.io/masterbofh/test-servers/ircd-irc2:dev .
ARG DEBIAN_TAG=trixie-20260918-slim
# Upstream release; the git tag is v<version>. Also the image's version label.
ARG IRCD_VERSION=2.11.3

FROM debian:${DEBIAN_TAG} AS build
ARG IRCD_VERSION
ARG IRCD_COMMIT=a317efddb208626def36970f280d14276c641362
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates git build-essential autotools-dev \
 && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch "v${IRCD_VERSION}" https://github.com/ircnet/ircd /src \
 && test "$(git -C /src rev-parse HEAD)" = "${IRCD_COMMIT}"
WORKDIR /src
# The shipped config.guess/config.sub predate aarch64 (pre-2012), so
# configure can't identify an arm64 build machine. Replace them with
# Debian's current copies, as Debian's own packaging does.
RUN find . -name config.guess -exec cp /usr/share/misc/config.guess {} \; \
 && find . -name config.sub -exec cp /usr/share/misc/config.sub {} \; \
 && test -n "$(find . -name config.guess)" \
 && for g in $(find . -name config.guess); do sh "$g" >/dev/null; done
# This ircd has no switch for reverse DNS on clients. It is not a
# connect-back, but it still makes each registration wait on the
# host's resolver (seconds when the resolver ignores PTR queries for
# the Docker bridge range). The patch skips the lookup; clients show
# by IP, exactly as on DNS failure. git apply fails the build if the
# patched lines move.
COPY ircd-irc2/no-reverse-dns.patch /tmp/
RUN git apply /tmp/no-reverse-dns.patch
# Compile-time settings (./configure copies config.h.dist to config.h):
#   USE_IAUTH off: no iauth process, so no ident/SOCKS/webproxy/DNSBL.
#   NO_IDENT on: ircd then won't do ident itself either.
#   LISTENER_DELAY off: by default the listener is polled only once a
#     second, so a client connecting just after another waits ~1-2s.
#   CLONE_CHECK off (and DELAY_CLOSE, which requires it): otherwise
#     more than 10 connects in 2s from one IP are refused, and test
#     clients all share the gateway IP.
#   MAXCONNECTIONS 1024 (default 50): room for several test suites.
# The greps fail the build if upstream renamed any of these lines.
RUN sed -i -e 's|^#define USE_IAUTH$|#undef USE_IAUTH|' \
      -e 's|^/\* #undef\tNO_IDENT \*/$|#define NO_IDENT|' \
      -e 's|^#define LISTENER_DELAY 1$|#undef LISTENER_DELAY|' \
      -e 's|^#define\tCLONE_CHECK$|#undef CLONE_CHECK|' \
      -e 's|^#define DELAY_CLOSE .*$|#undef DELAY_CLOSE|' \
      -e 's|^#define MAXCONNECTIONS\t50$|#define MAXCONNECTIONS 1024|' \
      support/config.h.dist \
 && grep -q '^#undef USE_IAUTH$' support/config.h.dist \
 && grep -q '^#define NO_IDENT$' support/config.h.dist \
 && grep -q '^#undef LISTENER_DELAY$' support/config.h.dist \
 && grep -q '^#undef CLONE_CHECK$' support/config.h.dist \
 && grep -q '^#undef DELAY_CLOSE$' support/config.h.dist \
 && grep -q '^#define MAXCONNECTIONS 1024$' support/config.h.dist
RUN ./configure --prefix=/opt/ircd --sysconfdir=/opt/ircd/etc \
      --with-rundir=/opt/ircd/run --with-logdir=/opt/ircd/log \
      --without-zlib \
 && make -C "$(support/config.guess)" ircd \
 && install -D -m 755 "$(support/config.guess)/ircd" /opt/ircd/sbin/ircd

FROM debian:${DEBIAN_TAG}
ARG IRCD_VERSION
LABEL org.opencontainers.image.source="https://github.com/MasterBOFH/test-servers" \
      org.opencontainers.image.version="${IRCD_VERSION}" \
      org.opencontainers.image.title="ircd-irc2" \
      org.opencontainers.image.description="IRCnet ircd ${IRCD_VERSION} test server"
RUN useradd --system --home-dir /opt/ircd --shell /usr/sbin/nologin ircd
COPY --from=build /opt/ircd/sbin/ircd /opt/ircd/sbin/ircd
COPY motd.txt /opt/ircd/etc/ircd.motd
COPY ircd-irc2/ircd.conf /opt/ircd/etc/ircd.conf
# ircd writes its pid/tune file and logs here.
RUN install -d -o ircd -g ircd /opt/ircd/run /opt/ircd/log
USER ircd
EXPOSE 4440
# -t: stay in the foreground as the container's main process.
# -p standalone: a lone server otherwise sits in split mode forever
#   (thresholds are floored at 10 servers / 5000 users at compile
#   time), and in split mode a channel's first joiner gets no ops.
CMD ["/opt/ircd/sbin/ircd", "-t", "-p", "standalone"]
