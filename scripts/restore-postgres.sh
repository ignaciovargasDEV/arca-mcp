#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 backups/arca_mcp_YYYYmmddTHHMMSSZ.sql.gz" >&2
  exit 1
fi

backup_file="$1"
compose_dir="${COMPOSE_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

cd "$compose_dir"
set -a
source .env
set +a

gzip -dc "$backup_file" | docker compose exec -T postgres-main \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
