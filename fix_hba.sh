#!/bin/bash
# Write a completely new pg_hba.conf that uses 'password' method for all TCP connections.
# 'password' sends the password in clear over the wire — acceptable for local dev only.
cat > /var/lib/postgresql/data/pg_hba.conf << 'HBAEOF'
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             0.0.0.0/0               password
host    all             all             ::/0                    password
local   replication     all                                     trust
host    replication     all             127.0.0.1/32            trust
host    replication     all             ::1/128                 trust
HBAEOF
echo "pg_hba.conf rewritten"
