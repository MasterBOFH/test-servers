# Developing

## Layout

Each image is one directory: a `Dockerfile` plus the server's config (and,
for a few, a small source patch). Every image builds with the **repo root**
as context, so it can use the shared `certs/` and `motd.txt`:

```sh
docker build -f solanum/Dockerfile -t ghcr.io/masterbofh/test-servers/solanum:dev .
docker run --rm -p 127.0.0.1:4447:4447 -p 127.0.0.1:5557:5557 ghcr.io/masterbofh/test-servers/solanum:dev
python3 smoke/check.py --plain 4447 --tls 5557
```

All images build on the same pinned Debian (`ARG DEBIAN_TAG`), except
InspIRCd and Ergo, which extend their official images pinned by tag and
digest.

## Updating a server's version

Each Dockerfile pins its upstream in an `ARG` near the top: a release tag
(with the commit it must resolve to), a tarball version plus its sha256,
or, for projects that don't tag releases, a commit. To update:

1. Change the `ARG`s, recomputing the sha256 or commit.
2. Build, run, and run `smoke/check.py` as above.
3. Update `org.opencontainers.image.version` (it becomes the published
   tag) and the version in the README table.

## Why whole config files, not diffs

irccom's images built each config by applying a diff to the upstream
example config, so they kept working as upstream changed its examples
while the images tracked the latest source. These images pin exact
versions instead, so a whole config file is written once per version, is
easier to read, and states every non-default setting with a comment
saying why. When bumping a version, check the upstream changelog for
config changes; `smoke/check.py` and the build's config test (where the
ircd has one) catch most breakage.

## Source patches

A few ircds have no config switch for something the tests need, so their
Dockerfile patches the source at build time (for example, skipping reverse
DNS on clients). Each patch is guarded with a `grep` or `git apply`, so the
build fails loudly if a version bump moves the patched code.

## Why reverse DNS, ident and throttling are off

Tests normally reach a container through Docker's port mapping, so the
server sees every client as the bridge gateway. Connect-backs to that
address (ident, proxy scans) and PTR lookups for it are commonly dropped
or never answered, and each one then waits out its full timeout before
the client can register. One gateway address for every client would also
trip any per-IP throttle.

## TLS

`certs/regen.sh` recreates the test CA and the server certificate. The CA
key is discarded, so the whole set is replaced together. The private key
is public on purpose: these are test servers.

## Publishing

`.github/workflows/images.yml` builds every image on each push and pull
request, runs `smoke/check.py` against it, and on `master` pushes it to
`ghcr.io/<owner>/test-servers/<image>` as `:latest` and
`:<org.opencontainers.image.version>`. A newly published package starts
out private on GitHub; make it public once in the package's settings.

## Contributions

Welcome. By contributing you agree to [CLA.md](CLA.md).
