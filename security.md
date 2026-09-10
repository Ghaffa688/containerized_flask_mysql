# Security Notes

This document records known security findings in the project's
container images, the rationale for each accepted finding, and
the policy CI enforces.

## Threat model

- The web container runs as an unprivileged user (uid 1001)
  with all Linux capabilities dropped and a read-only root
  filesystem.
- The db container runs the official mysql:8.0 image (Oracle
  Linux 9.7 base) and drops privileges to the mysql user via
  gosu at startup.
- Neither container exposes a shell to untrusted users.
- The Flask app receives input only from HTTP clients on the
  local development network.

## Scan summary

| Image | HIGH | CRITICAL | Source |
|-------|------|----------|--------|
| web   | ~58  | ~7       | Debian base packages and libmariadb |
| db    | 30   | 0        | Oracle Linux 9.7 base, gosu, Python deps in mysqlsh |

Scan command:
    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
      aquasec/trivy:latest image --severity HIGH,CRITICAL <image>

## web image findings

### Debian base packages (util-linux, perl-base, ncurses, sqlite, systemd, gzip, libacl1)
These come from the python:3.11-slim base image (Debian 13.6).
Every entry shows an empty "Fixed Version" column, meaning no
patched package exists in Debian yet. The Flask application does
not invoke these libraries directly; they are present for
general-purpose use in the base image. They will be picked up
when the python:3.11-slim maintainers rebuild against a patched
Debian.

### libmariadb3 / libmariadb-dev / mariadb-common (2 CRITICAL, 4 HIGH)
Required to satisfy mysqlclient's link-time dependency on the
MariaDB client library. No patched version is available in
Debian 13.6. A future improvement is to replace mysqlclient
with PyMySQL, a pure-Python driver with no system library
dependency, which would eliminate these six findings.

### setuptools vendored copies (2 HIGH)
setuptools bundles private copies of jaraco.context 5.3.0 and
wheel 0.45.1 inside its _vendor directory. These are executed
only by setuptools during package builds, never by the running
application. They cannot be patched without patching setuptools
upstream.

### Python application dependencies
All direct dependencies (Flask, Werkzeug, mysqlclient,
Flask-MySQLdb) report zero CVEs.

## db image findings

### Oracle Linux 9.7 base packages (curl, glib2, gnutls, krb5-libs, libacl, libcap, sqlite-libs)
These are shipped by the mysql:8.0 official image, which is
currently based on Oracle Linux 9.7. Most show a fixed version
available in the el9_8 channel, meaning the base image is one
minor release behind. They will resolve when Oracle publishes
an updated mysql:8.0 image. The MySQL server daemon does not
call most of these libraries in the project's usage pattern.

### gosu binary (1 CRITICAL, 21 HIGH)
All findings are in the Go standard library compiled statically
into the gosu binary shipped by mysql:8.0. gosu runs once at
container startup, calls setgid, setuid, and exec, then exits.
It never performs TLS, HTTP, URL, XML, MIME, mail, or template
processing, so none of the CVE'd code paths are reachable.
Accepted as non-exploitable.

### mysqlsh Python packages (cryptography, pyOpenSSL, urllib3)
These are part of the MySQL Shell utility bundled in the image.
They are not used by the Flask app or by the mysqld daemon in
this project. Accepted as non-reachable.

## Policy

- CI fails only on CRITICAL findings that have a fixed version
  available.
- HIGH findings with a fix available are fixed when convenient.
- Findings with no fixed version are documented here and
  re-evaluated on every base image update.
- Non-reachable findings are accepted with rationale.
- Scan runs automatically on every tag push in CI.