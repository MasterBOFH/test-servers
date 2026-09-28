# InspIRCd 4: the official image, pinned by tag and digest, with our own
# whole config instead of the image's environment-generated one.
# Plaintext clients on 4448, TLS on 5558 (the repo's shared certificate).
#
#   docker build -f inspircd-4/Dockerfile -t ghcr.io/masterbofh/test-servers/inspircd-4:dev .
#   docker run --rm -p 4448:4448 -p 5558:5558 ghcr.io/masterbofh/test-servers/inspircd-4:dev
#
# The build context is the repository root (for certs/ and motd.txt).
FROM inspircd/inspircd-docker:4.12.1@sha256:932f9d6de542e8084cdfd62e28a80c329d402a88d46dfdaf2ee95c841d747540

LABEL org.opencontainers.image.source="https://github.com/MasterBOFH/test-servers" \
      org.opencontainers.image.version="4.12.1" \
      org.opencontainers.image.title="inspircd-4" \
      org.opencontainers.image.description="InspIRCd 4.12.1 test server"

# The image already runs as the unprivileged user "inspircd" (uid 10000).
COPY --chown=inspircd:inspircd inspircd-4/inspircd.conf /inspircd/conf/inspircd.conf
COPY --chown=inspircd:inspircd motd.txt /inspircd/conf/motd.txt
COPY --chown=inspircd:inspircd certs/server-chain.crt /inspircd/conf/server-chain.crt
COPY --chown=inspircd:inspircd certs/server.key /inspircd/conf/server.key
# DH parameters once, at build time: the official entrypoint generates them
# (and a self-signed cert) at every container start, which takes seconds.
# The key is public test material, but keep the file private anyway.
RUN /usr/bin/certtool --generate-dh-params --sec-param normal --outfile /inspircd/conf/dhparams.pem \
 && chmod 600 /inspircd/conf/server.key

# Bypass the official entrypoint (config copying, cert and DH generation):
# everything it would create is already in /inspircd/conf.
WORKDIR /inspircd
EXPOSE 4448 5558
HEALTHCHECK --interval=60s --timeout=3s --start-period=10s CMD /usr/bin/nc -z localhost 4448
# --nofork: stay in the foreground as PID 1.
ENTRYPOINT ["/inspircd/bin/inspircd", "--nofork"]
