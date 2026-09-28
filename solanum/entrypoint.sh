#!/bin/sh
# librb sizes its fd tables from RLIMIT_NOFILE and walks all of them, so
# under a huge Docker default limit (1073741816 on some hosts) every
# solanum process (ircd, authd, ssld, bandb, ...) spins at 100% CPU and
# never answers a client. Cap it here so the image works without
# `--ulimit` / a compose `ulimits:`.
ulimit -n 4096 || exit 1
exec /opt/solanum/bin/solanum -foreground "$@"
