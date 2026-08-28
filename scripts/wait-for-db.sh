#!/bin/sh
set -e

host="$1"
shift

until PGPASSWORD="${DB__PASSWORD:-postgres}" psql \
  -h "$host" \
  -U "${DB__USER:-postgres}" \
  -d "${DB__NAME:-payments}" \
  -c '\q' >/dev/null 2>&1; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 2
done

>&2 echo "Postgres is up"

if [ "$#" -gt 0 ]; then
  exec "$@"
fi
