# Deploy Y Operación

## Levantar Con Docker Compose

```bash
cp .env.example .env
mkdir -p certs backups
docker compose up -d --build
```

Ver estado:

```bash
docker compose ps
```

Ver logs:

```bash
docker compose logs -f arca-mcp
docker compose logs -f postgres-main
```

## Puertos

Por defecto:

- MCP: `127.0.0.1:8000`
- PostgreSQL: `127.0.0.1:5432`

Esto significa que no quedan expuestos públicamente.

## Actualizar

```bash
git pull
docker compose up -d --build
```

Si hay migraciones nuevas y la base ya existía, aplicalas manualmente antes de reiniciar el MCP. Ejemplo:

```bash
docker compose exec -T postgres-main psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < migrations/002_factura_e_exportacion.sql
```

Si tu shell no tiene cargadas las variables de `.env`, ejecutalo dentro del contenedor:

```bash
docker compose exec -T postgres-main sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < migrations/002_factura_e_exportacion.sql
```

Si solo cambiaste `.env`:

```bash
docker compose up -d arca-mcp
```

## Backup

Crear backup:

```bash
./scripts/backup-postgres.sh
```

El archivo queda en `backups/` con timestamp UTC.

## Restore

Restaurar un backup:

```bash
./scripts/restore-postgres.sh backups/arca_mcp_YYYYmmddTHHMMSSZ.sql.gz
```

Hacelo con cuidado: el script ejecuta el SQL contra la base configurada en `.env`.

## Cron

El proyecto no necesita cron propio para mandar reportes al contador si usás Hermes scheduler. El cron del sistema queda recomendado solo para backups.

Ejemplo de backup diario a las 03:15 UTC:

```cron
15 3 * * * cd /opt/arca-mcp && ./scripts/backup-postgres.sh >> /var/log/arca-mcp-backup.log 2>&1
```

## Túnel SSH

Desde tu máquina:

```bash
ssh -L 8000:127.0.0.1:8000 usuario@tu-vps
```

Tu cliente MCP usa:

```txt
http://127.0.0.1:8000/mcp
```

## Checklist De Producción

- `docker compose ps` muestra ambos contenedores arriba.
- `config_status` devuelve `database=true`.
- `config_status` devuelve `afip_access_token=true`.
- En producción, `cert_file_readable=true` y `key_file_readable=true`.
- `AFIP_PUNTO_VENTA` corresponde al punto de venta WSFE que creaste para Factura C.
- Si usás Factura E, `AFIP_PUNTO_VENTA_EXPORTACION` corresponde al punto de venta WSFEX.
- Si usás Factura E, `parametros_factura_e(catalogo="puntos_venta")` muestra el punto esperado y no está bloqueado.
- Si usás Factura E, el certificado está asociado a WSFEX.
- Si usás email, SMTP está configurado y probado con `enviar_reporte_contador`.
- Tenés backup configurado.
