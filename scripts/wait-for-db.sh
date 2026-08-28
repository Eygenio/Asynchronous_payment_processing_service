#!/bin/sh
set -e

host="$1"
shift
cmd="$@"

until PGPASSWORD="${DB__PASSWORD:-postgres}" psql -h "$host" -U "${DB__USER:-postgres}" -d "${DB__NAME:-payments}" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 2
done

>&2 echo "Postgres is up - executing command"
exec $cmd
