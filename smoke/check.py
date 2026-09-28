#!/usr/bin/env python3
"""Smoke-test one of this repo's ircd images against its conventions.

    smoke/check.py --plain 4447 --tls 5557

Checks, on a running container:
  - a client registers on the plaintext port within --max-reg seconds
    (answering the server's PING cookie if it sends one);
  - a channel's first joiner gets ops and can KICK a second client;
  - OPER alice / OPER daniel with password "password" both get 381;
  - with --tls, a client registers over TLS with the certificate verified
    against certs/ca.crt (hostname 127.0.0.1 is in the cert).
Waits up to --wait seconds for the server to start accepting. Exits
non-zero on the first failed check.
"""
import argparse, os, socket, ssl, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))


class Fail(Exception):
    pass


class Client:
    def __init__(self, host, port, nick, tls_ctx=None, timeout=15):
        raw = socket.create_connection((host, port), timeout=timeout)
        self.s = tls_ctx.wrap_socket(raw, server_hostname=host) if tls_ctx else raw
        self.s.settimeout(timeout)
        self.nick, self.buf = nick, b""

    def send(self, line):
        self.s.sendall((line + "\r\n").encode())

    def lines(self):
        while True:
            while b"\n" in self.buf:
                raw, self.buf = self.buf.split(b"\n", 1)
                line = raw.decode(errors="replace").rstrip("\r")
                parts = line.split()
                if parts and parts[0] == "PING":
                    self.send("PONG " + " ".join(parts[1:]))
                    continue
                yield line
            data = self.s.recv(4096)
            if not data:
                raise Fail("%s: connection closed" % self.nick)
            self.buf += data

    def until(self, pred, secs, what):
        deadline = time.monotonic() + secs
        self.s.settimeout(secs)
        try:
            for line in self.lines():
                if pred(line):
                    return line
                if time.monotonic() > deadline:
                    break
        except socket.timeout:
            pass
        raise Fail("%s: timed out waiting for %s" % (self.nick, what))

    def register(self, secs):
        t0 = time.monotonic()
        self.send("NICK " + self.nick)
        self.send("USER %s 0 * :smoke test" % self.nick.lower())
        seen = {}
        while True:
            line = self.until(lambda l: len(l.split()) > 1, secs, "registration")
            code = line.split()[1]
            if code in ("001", "002", "004"):
                seen[code] = line
                if code == "001":
                    seen["t"] = time.monotonic() - t0
            elif code in ("432", "433", "465", "ERROR") or line.startswith("ERROR"):
                raise Fail("%s: registration refused: %s" % (self.nick, line))
            if code in ("376", "422"):
                return seen

    def close(self):
        try:
            self.send("QUIT :smoke done")
        except OSError:
            pass
        self.s.close()


def wait_for(host, port, secs):
    deadline = time.monotonic() + secs
    while True:
        try:
            socket.create_connection((host, port), timeout=2).close()
            return
        except OSError:
            if time.monotonic() > deadline:
                raise Fail("port %d never accepted a connection" % port)
            time.sleep(1)


def check(args):
    tag = "s%d" % (os.getpid() % 10000)
    wait_for(args.host, args.plain, args.wait)
    # Some servers accept before they are ready to register; retry once.
    for attempt in (1, 2):
        try:
            a = Client(args.host, args.plain, tag + "a")
            reg = a.register(args.max_reg + 10)
            break
        except (Fail, OSError):
            if attempt == 2:
                raise
            time.sleep(5)
    print("002:", reg.get("002"))
    print("004:", reg.get("004"))
    print("plaintext registration: %.2fs" % reg["t"])
    if reg["t"] > args.max_reg:
        raise Fail("registration took %.2fs (limit %.1fs)" % (reg["t"], args.max_reg))

    chan = "#smoke" + tag
    a.send("JOIN " + chan)
    names = a.until(lambda l: " 353 " in l, 10, "NAMES after JOIN")
    if ("@" + a.nick) not in names.split(":", 2)[-1].split():
        raise Fail("first joiner did not get ops: %s" % names)
    b = Client(args.host, args.plain, tag + "b")
    b.register(args.max_reg + 10)
    b.send("JOIN " + chan)
    a.until(lambda l: l.startswith(":" + b.nick) and " JOIN " in l, 10, "B's JOIN")
    a.send("KICK %s %s :smoke" % (chan, b.nick))
    got = b.until(lambda l: " KICK " in l or " 482 " in l, 10, "KICK")
    if " KICK " not in got:
        raise Fail("KICK refused: %s" % got)
    print("ops + kick: ok")

    for c, oper in ((a, "alice"), (b, "daniel")):
        c.send("OPER %s password" % oper)
        got = c.until(lambda l: len(l.split()) > 1 and l.split()[1] in
                      ("381", "464", "491", "481", "461"), 10, "OPER %s reply" % oper)
        if got.split()[1] != "381":
            raise Fail("OPER %s refused: %s" % (oper, got))
    print("oper alice + daniel: ok")
    a.close()
    b.close()

    if args.tls:
        ctx = ssl.create_default_context(cafile=args.ca)
        wait_for(args.host, args.tls, args.wait)
        t = Client(args.host, args.tls, tag + "t", tls_ctx=ctx)
        reg = t.register(args.max_reg + 10)
        print("TLS registration (verified): %.2fs, %s" % (reg["t"], t.s.version()))
        t.close()


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--plain", type=int, required=True)
    p.add_argument("--tls", type=int)
    p.add_argument("--ca", default=os.path.join(HERE, "..", "certs", "ca.crt"))
    p.add_argument("--wait", type=float, default=90)
    p.add_argument("--max-reg", type=float, default=3.0)
    args = p.parse_args()
    try:
        check(args)
    except (Fail, OSError, ssl.SSLError) as e:
        print("FAIL:", e)
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
