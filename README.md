# ARCA MCP

MCP server for issuing Argentine ARCA/AFIP Factura C invoices through Afip SDK, with a local PostgreSQL audit database and a safety-first two-step emission flow.

This project turns a fiscal invoicing backend into MCP tools usable from agents, IDEs, Hermes, Claude Desktop, Cursor, VS Code extensions, or any MCP-compatible client.

## Features

- Factura C emission through ARCA WSFE using Afip SDK.
- Local PostgreSQL storage, no Supabase required.
- Streamable HTTP MCP endpoint.
- Docker Compose deployment.
- Preview-before-emit workflow with single-use confirmation tokens.
- Production kill switch with `ALLOW_PRODUCTION`.
- PDF generation through Afip SDK.
- Audit log for MCP tool calls.
- SSH tunnel friendly; no public domain required.

## Architecture

```txt
MCP client / agent / IDE
        |
        | SSH tunnel or private network
        v
arca-mcp container  ->  Afip SDK  ->  ARCA WSFE
        |
        v
postgres-main container
```

The server exposes MCP tools over `streamable-http` at:

```txt
http://127.0.0.1:8000/mcp
```

Docker Compose binds both MCP and PostgreSQL to localhost by default.

## Quick Start

```bash
git clone https://github.com/ignaciovargasDEV/arca-mcp.git
cd arca-mcp
cp .env.example .env
```

Edit `.env`, then start:

```bash
docker compose up -d --build
```

Check containers:

```bash
docker compose ps
```

## Configuration

Minimum `.env` for homologation/testing:

```env
POSTGRES_DB=arca_mcp
POSTGRES_USER=arca_mcp_user
POSTGRES_PASSWORD=change-me

AFIP_ACCESS_TOKEN=your-afip-sdk-token
PRODUCTION=false
ALLOW_PRODUCTION=false

TEST_CUIT=20409378472
TEST_PUNTO_VENTA=1

EMISOR_NOMBRE=Your Name
FACTURA_DESCRIPCION=Servicios
CONCEPTO=2
```

Production requires:

```env
PRODUCTION=true
ALLOW_PRODUCTION=false
AFIP_CUIT=your-cuit-without-dashes
AFIP_PUNTO_VENTA=your-webservice-pos
AFIP_CERT_PATH=/certs/arca.crt
AFIP_KEY_PATH=/certs/arca.key
```

Keep `ALLOW_PRODUCTION=false` until you are ready to emit real invoices.

## Certificates

Create and mount:

```txt
certs/arca.crt
certs/arca.key
```

These files are ignored by git and must never be committed.

See [docs/arca-setup.md](docs/arca-setup.md) for the ARCA certificate and point-of-sale setup.

## Usage

The safe production flow is:

1. Call `preview_factura_c`.
2. Review amount, receiver, mode, warnings, and date.
3. Call `emitir_factura_c` with the returned `confirmation_id` and exact confirmation phrase.

Production confirmation phrase:

```txt
CONFIRMO EMITIR FACTURA REAL
```

Homologation confirmation phrase:

```txt
CONFIRMO EMITIR
```

Available tools are documented in [docs/tools.md](docs/tools.md).

## SSH Tunnel

For a VPS without a domain:

```bash
ssh -L 8000:127.0.0.1:8000 user@your-vps
```

Configure your MCP client with:

```txt
http://127.0.0.1:8000/mcp
```

## Hermes

Hermes setup is documented in [docs/hermes.md](docs/hermes.md).

## Deployment And Backups

Deployment and PostgreSQL backup commands are documented in [docs/deployment.md](docs/deployment.md).

## Security

Read [docs/security.md](docs/security.md) before enabling production.

Important defaults:

- MCP binds to `127.0.0.1:8000` on the host.
- PostgreSQL binds to `127.0.0.1:5432` on the host.
- Production emission requires `ALLOW_PRODUCTION=true`.
- Emission requires a preview confirmation token.
- Confirmation tokens expire after 10 minutes.

## Disclaimer

This is not tax advice. Verify emitted invoices, fiscal limits, receiver identification requirements, and monotributo rules with your accountant.

## License

MIT
