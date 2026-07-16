# Hermes Integration

Hermes reads MCP servers from `~/.hermes/config.yaml`.

Add this under `mcp_servers:` when the MCP server runs on the same VPS:

```yaml
mcp_servers:
  arca_mcp:
    url: http://127.0.0.1:8000/mcp
    enabled: true
    timeout: 120
    connect_timeout: 30
```

Reload MCP tools from Hermes:

```txt
/reload-mcp
```

If Hermes asks for confirmation, approve it.

Test with:

```txt
Use arca_mcp config_status.
```

Preview without emitting:

```txt
Use arca_mcp preview_factura_c with monto 100 and descripcion "test MCP".
```

Production emission requires the `confirmation_id` from the preview and the exact phrase:

```txt
CONFIRMO EMITIR FACTURA REAL
```
