# Security Notes

This server can emit real fiscal invoices. Treat it as production infrastructure.

## Defaults

- The Docker Compose file binds MCP and PostgreSQL to `127.0.0.1` only.
- Production emission requires both `PRODUCTION=true` and `ALLOW_PRODUCTION=true`.
- `emitir_factura_c` requires a prior `preview_factura_c` call.
- Confirmation tokens expire after 10 minutes and are single-use.
- The exact confirmation phrase for production is `CONFIRMO EMITIR FACTURA REAL`.
- Tool calls are written to `mcp_audit_log` with secret-like keys redacted.

## Do Not Commit

- `.env`
- `certs/`
- `*.key`
- `*.crt`
- `*.csr`
- database dumps

## Recommended Access Patterns

For a VPS without a domain, use an SSH tunnel:

```bash
ssh -L 8000:127.0.0.1:8000 user@your-vps
```

Then configure your MCP client with:

```txt
http://127.0.0.1:8000/mcp
```

For team usage, put the service behind a private network such as WireGuard or Tailscale. Do not expose the MCP endpoint directly to the public internet without authentication and rate limiting.

## Production Checklist

- Certificate was generated manually and associated to WSFE.
- Point of sale is a Web Service point of sale.
- `.env` uses the correct CUIT and point of sale.
- `ALLOW_PRODUCTION=false` until the first preview was reviewed.
- A small real invoice was tested and verified in ARCA.
- Backups are configured for PostgreSQL.
