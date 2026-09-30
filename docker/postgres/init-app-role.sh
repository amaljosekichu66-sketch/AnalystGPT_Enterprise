#!/bin/sh
# Create the least-privilege role the API connects as (L19).
#
# Run once by the postgres image, from /docker-entrypoint-initdb.d, when the
# data volume is first initialised. The API used to connect as the `postgres`
# superuser, so any SQL it could be made to run had full control of the
# cluster. This role can log in and use this database only: no SUPERUSER,
# CREATEDB or CREATEROLE. It owns the tables because the API creates its own
# schema at startup.
#
# An EXISTING volume does not re-run init scripts: run this file once by hand
# (docker compose exec postgres sh /docker-entrypoint-initdb.d/10-app-role.sh).
set -eu

: "${APP_DB_USER:?APP_DB_USER must be set}"
: "${APP_DB_PASSWORD:?APP_DB_PASSWORD must be set}"

psql -v ON_ERROR_STOP=1 \
    -v app_user="$APP_DB_USER" \
    -v app_password="$APP_DB_PASSWORD" \
    -v db_name="$POSTGRES_DB" \
    --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'EOSQL'
SELECT format('CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L', :'app_user', :'app_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'app_user') \gexec
REVOKE ALL ON DATABASE :"db_name" FROM PUBLIC;
GRANT CONNECT, TEMPORARY ON DATABASE :"db_name" TO :"app_user";
GRANT USAGE, CREATE ON SCHEMA public TO :"app_user";
EOSQL
