# Deployment

## Docker Compose

```bash
cp .env.example .env
mkdir -p certs backups
docker compose up -d --build
```

The default Compose file publishes services on localhost only:

- MCP: `127.0.0.1:8000`
- PostgreSQL: `127.0.0.1:5432`

## Updating

```bash
git pull
docker compose up -d --build
```

## Logs

```bash
docker compose logs -f arca-mcp
docker compose logs -f postgres-main
```

## Backups

Create a backup:

```bash
./scripts/backup-postgres.sh
```

Restore a backup:

```bash
./scripts/restore-postgres.sh backups/arca_mcp_YYYYmmddTHHMMSSZ.sql.gz
```

## Cron Example

Daily backup at 03:15 UTC:

```cron
15 3 * * * cd /opt/arca-mcp && ./scripts/backup-postgres.sh >> /var/log/arca-mcp-backup.log 2>&1
```
