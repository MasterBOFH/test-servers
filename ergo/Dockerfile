# Ergo: the official image, pinned by tag and digest, with our own config.
# Plaintext clients on 4449, TLS on 5559 (the repo's shared certificate).
#
#   docker build -f ergo/Dockerfile -t ghcr.io/masterbofh/test-servers/ergo:dev .
#   docker run --rm -p 4449:4449 -p 5559:5559 ghcr.io/masterbofh/test-servers/ergo:dev
#
# The build context is the repository root (for certs/ and motd.txt).
FROM ghcr.io/ergochat/ergo:v2.19.1@sha256:ef885e44f7fa19101bbbc41baef11dc280dc8107465dccaf6f0860f41b48a682

LABEL org.opencontainers.image.source="https://github.com/MasterBOFH/test-servers" \
      org.opencontainers.image.version="2.19.1" \
      org.opencontainers.image.title="ergo" \
      org.opencontainers.image.description="Ergo 2.19.1 test server"

# The official image runs as root and keeps its config, certs and database
# in /ircd, which it declares a VOLUME. Everything here lives outside it
# instead: config in /etc/ergo, the database in /var/lib/ergo. (Compose
# reuses a container's anonymous volumes when recreating it, so a config
# in /ircd would go stale across image updates.)
RUN adduser -D -H -u 10001 -s /sbin/nologin ergo \
 && mkdir -p /etc/ergo /var/lib/ergo \
 && chown ergo:ergo /var/lib/ergo
COPY ergo/ircd.yaml /etc/ergo/ircd.yaml
COPY motd.txt /etc/ergo/ergo.motd
COPY certs/server-chain.crt /etc/ergo/server-chain.crt
# The key is public test material, but keep the file private anyway.
COPY --chown=ergo:ergo --chmod=600 certs/server.key /etc/ergo/server.key

USER ergo
WORKDIR /var/lib/ergo
# Create the database at build time, which also fails the build on a bad
# config rather than at container start.
RUN /ircd-bin/ergo initdb --conf /etc/ergo/ircd.yaml

EXPOSE 4449 5559
# Bypass the official run.sh (config templating, self-signed cert).
ENTRYPOINT ["/ircd-bin/ergo", "run", "--conf", "/etc/ergo/ircd.yaml"]
