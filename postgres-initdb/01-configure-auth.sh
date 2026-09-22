#!/bin/bash
# Runs ONCE on first PostgreSQL data directory initialization.
# Sets md5 auth for all TCP connections so that psycopg2 clients
# from Docker host (published port) and other containers both work.
set -e

PG_HBA="$PGDATA/pg_hba.conf"

# Replace default scram-sha-256 catch-all with md5
sed -i 's/^host all all all scram-sha-256/host all all all md5/' "$PG_HBA"

# Also replace loopback trust rules with md5 (required on Docker Desktop for Windows
# where Docker-published port connections arrive via the bridge gateway, not 127.0.0.1)
sed -i 's|host    all             all             127.0.0.1/32            trust|host    all             all             127.0.0.1/32            md5|' "$PG_HBA"
sed -i 's|host    all             all             ::1/128                 trust|host    all             all             ::1/128                 md5|' "$PG_HBA"

# Set the server-level password_encryption to md5 so ALTER USER stores an md5 hash
# that is compatible with all auth methods (md5, password)
echo "password_encryption = md5" >> "$PGDATA/postgresql.conf"

echo "[initdb] pg_hba.conf updated: all TCP connections use md5 auth"
echo "[initdb] postgresql.conf: password_encryption set to md5"
