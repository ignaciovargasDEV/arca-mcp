#!/usr/bin/env bash
set -euo pipefail

compose_dir="${COMPOSE_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
backup_dir="${BACKUP_DIR:-$compose_dir/backups}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "$backup_dir"

cd "$compose_dir"
set -a
source .env
set +a

docker compose exec -T postgres-main \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists \
  | gzip > "$backup_dir/${POSTGRES_DB}_${timestamp}.sql.gz"

echo "$backup_dir/${POSTGRES_DB}_${timestamp}.sql.gz"
