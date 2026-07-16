# Seguridad

Este MCP puede emitir comprobantes fiscales reales. Tratá el servicio como infraestructura productiva.

## Defaults Seguros

- Docker Compose publica MCP solo en `127.0.0.1:8000`.
- Docker Compose publica PostgreSQL solo en `127.0.0.1:5432`.
- Producción requiere `PRODUCTION=true`.
- Emitir en producción requiere además `ALLOW_PRODUCTION=true`.
- `emitir_factura_c` requiere un `confirmation_id` generado por `preview_factura_c`.
- `emitir_factura_e` requiere un `confirmation_id` generado por `preview_factura_e`.
- `enviar_reporte_contador` requiere la frase exacta `CONFIRMO ENVIAR EMAIL`.
- Los `confirmation_id` expiran a los 10 minutos.
- Los `confirmation_id` son de un solo uso.
- La frase exacta para producción es `CONFIRMO EMITIR FACTURA REAL`.
- Las llamadas quedan registradas en `mcp_audit_log`.
- El log intenta filtrar claves con nombres sensibles como `token`, `secret`, `password`, `cert` y `key`.

## Archivos Que No Tenés Que Subir

- `.env`
- `certs/`
- `*.key`
- `*.crt`
- `*.csr`
- dumps de base de datos
- backups comprimidos
- `private/`
- PDFs reales de referencia o comprobantes reales

Ya están ignorados en `.gitignore` y `.dockerignore`, pero revisá igual antes de publicar.

## Acceso Recomendado

Para uso personal en un VPS sin dominio, usá túnel SSH:

```bash
ssh -L 8000:127.0.0.1:8000 usuario@tu-vps
```

Después conectás el cliente MCP a:

```txt
http://127.0.0.1:8000/mcp
```

Para uso de equipo, mejor usar una red privada tipo WireGuard o Tailscale.

No expongas el endpoint MCP directo a internet sin autenticación, rate limiting y monitoreo.

## Producción

Antes de `ALLOW_PRODUCTION=true`:

- Confirmá que el certificado fue generado manualmente.
- Confirmá que el certificado está asociado a WSFE.
- Si emitís Factura E, confirmá que el certificado está asociado a WSFEX.
- Confirmá que `AFIP_PUNTO_VENTA` corresponde a tu punto de venta WSFE.
- Si emitís Factura E, confirmá que `AFIP_PUNTO_VENTA_EXPORTACION` corresponde a tu punto de venta WSFEX.
- Confirmá que `AFIP_CUIT` no tiene guiones.
- Corré `config_status`.
- Para WSFEX, corré `parametros_factura_e(catalogo="puntos_venta")`.
- Hacé un preview y leelo completo.

Después de la primera factura real:

- Verificá que exista en ARCA.
- Verificá CAE, fecha, punto de venta e importe.
- Verificá que quedó guardada en PostgreSQL.
- Hacé un backup.

## Afip SDK

Afip SDK simplifica la integración con ARCA, pero para producción recibe tu certificado y private key para autenticar.

Ese certificado no es tu clave fiscal, pero permite operar el web service asociado. Si no querés ese tradeoff, necesitás implementar WSAA local y firmar desde tu infraestructura.

## Backup

Configurá backups periódicos de PostgreSQL. El repo trae:

```bash
./scripts/backup-postgres.sh
```

Probá también restaurar en un entorno aparte. Un backup que nunca restauraste es una promesa, no una garantía.

## SMTP

- Guardá `SMTP_PASS` solo en `.env`.
- Para Gmail usá app password, no tu contraseña normal.
- Preferí `SMTP_PORT=587` si tu VPS bloquea `465`.
- El email al contador solo envía comprobantes ya emitidos; no debe disparar emisión de facturas.
