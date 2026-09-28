# IRCd test servers

Docker images of the major IRC servers, each built from a pinned upstream
release and configured to be easy to test against: IRC clients, bots,
bouncers, bridges, and documentation of how servers actually behave.

Forked from [irccom/test-servers](https://github.com/irccom/test-servers)
(last updated 2020), rebuilt on current releases and published to the
GitHub Container Registry.

**These images are not secure and not meant to run a real network.** They
use hardcoded oper passwords, a published TLS key, and have every
anti-abuse limit turned off.

## Servers

| Image | Software | Version | Plaintext | TLS |
|---|---|---|---|---|
| `ircd-irc2` | IRCnet ircd | 2.11.3 | 4440 | — ¹ |
| `unrealircd-6` | UnrealIRCd | 6.2.7 | 4441 | 5551 |
| `ircd-hybrid-8` | ircd-hybrid | 8.2.47 | 4442 | 5552 |
| `ircu2` | ircu (Undernet) | u2.10.12.19 | 4443 | — ¹ |
| `bahamut` | Bahamut (DALnet) | 2.2.4 | 4444 | 5554 |
| `ngircd` | ngIRCd | 28 ³ | 4445 | 5555 |
| `ircd-ratbox` | ircd-ratbox | 3.0.10 | 4446 | 5556 |
| `solanum` | Solanum (Libera.Chat) | `03503ff` ² | 4447 | 5557 |
| `inspircd-4` | InspIRCd | 4.12.1 | 4448 | 5558 |
| `ergo` | Ergo | 2.19.1 | 4449 | 5559 |

¹ No native TLS in this version.
² Solanum doesn't tag releases; the image pins a commit on its default branch.
³ Nicks are limited to 9 characters (the RFC default), shorter than on the other servers.

Images are `ghcr.io/masterbofh/test-servers/<image>`, tagged `:latest` and
with the upstream version (e.g. `ghcr.io/masterbofh/test-servers/solanum:03503ff…`).
Every image is multi-arch — `linux/amd64` and `linux/arm64` — so the same
tags run natively on Apple Silicon Macs and ARM servers.

## Running

One server:

```sh
docker run --rm -p 127.0.0.1:4447:4447 -p 127.0.0.1:5557:5557 ghcr.io/masterbofh/test-servers/solanum:latest
```

All of them, from a checkout of this repo:

```sh
docker compose pull && docker compose up -d   # prebuilt images
docker compose up -d --build                  # or build locally
docker compose down
```

The compose file publishes ports on 127.0.0.1 only; change that to test
from another machine.

## What every image has in common

- Server name `<software>.example.irc.com` (e.g. `solanum.example.irc.com`),
  network `ExampleNet`.
- Two opers: `alice` / `password` and `daniel` / `password`.
- MOTD: "This is the MOTD".
- Port 44xx is plaintext, 55xx is TLS.
- TLS uses the certificate in [`certs/`](certs): one cert for
  `*.example.irc.com`, `localhost` and `127.0.0.1`, signed by a test CA.
  Trust `certs/ca.crt` in your client to test real certificate
  verification.
- No ident, DNSBL or proxy checks and no reverse-DNS lookups: tests usually
  connect through Docker's port mapping, so the server sees the bridge
  gateway as the client, and connect-backs or PTR lookups for it tend to
  hang until their timeouts. A client registers in well under a second.
- Throttling and connection limits are off: many connections from one
  address, reconnecting freely, and no flood kills at normal test rates.
  (ircu2 keeps its default 1024-byte `CLIENT_FLOOD`, so client-side flood
  pacing can be tested against it.)
- A channel's first joiner gets ops.

## Testing an image

[`smoke/check.py`](smoke/check.py) checks a running server against those
conventions — registration time, ops and KICK, both opers, and verified
TLS:

```sh
python3 smoke/check.py --plain 4447 --tls 5557
```

CI runs it against every image on each push and pull request before
anything is published.

See [DEVELOPING.md](DEVELOPING.md) for how the images are built and how to
update a version.
