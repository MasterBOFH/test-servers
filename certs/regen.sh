#!/bin/sh
# Regenerates the test CA and the one server certificate every image uses.
# The certificate covers every server name in this repo
# (<software>.example.irc.com), plus localhost and 127.0.0.1, so a client
# that trusts ca.crt can test real certificate verification against any of
# them. The CA key is thrown away: to issue a new cert, rerun this script,
# which replaces the CA too.
#
# Everything here is public test material — never trust ca.crt outside
# testing.
set -eu
cd "$(dirname "$0")"
days=3650
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

openssl req -x509 -newkey rsa:2048 -nodes -days "$days" \
  -subj "/O=ExampleNet IRC Network/CN=ExampleNet Test CA" \
  -keyout "$tmp/ca.key" -out ca.crt \
  -addext "basicConstraints=critical,CA:TRUE" \
  -addext "keyUsage=critical,keyCertSign,cRLSign"

openssl req -newkey rsa:2048 -nodes \
  -subj "/O=ExampleNet IRC Network/CN=example.irc.com" \
  -keyout server.key -out "$tmp/server.csr"

cat > "$tmp/ext.cnf" <<EOF
basicConstraints=CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth,clientAuth
subjectAltName=DNS:example.irc.com,DNS:*.example.irc.com,DNS:localhost,IP:127.0.0.1
EOF
openssl x509 -req -in "$tmp/server.csr" -days "$days" \
  -CA ca.crt -CAkey "$tmp/ca.key" -CAserial "$tmp/ca.srl" -CAcreateserial \
  -extfile "$tmp/ext.cnf" \
  -out server.crt

# Some ircds want the chain in one file.
cat server.crt ca.crt > server-chain.crt
chmod 644 server.key
openssl verify -CAfile ca.crt server.crt
