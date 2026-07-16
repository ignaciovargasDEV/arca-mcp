# Integración Con Hermes

Hermes puede consumir este MCP igual que cualquier otro servidor MCP HTTP.

## Configuración

Editá `~/.hermes/config.yaml` y agregá esto bajo `mcp_servers:`:

```yaml
mcp_servers:
  arca_mcp:
    url: http://127.0.0.1:8000/mcp
    enabled: true
    timeout: 120
    connect_timeout: 30
```

Si ya tenés otros MCP, no dupliques `mcp_servers:`. Agregá solo el bloque `arca_mcp` al mismo nivel que los otros servidores.

## Recargar Tools

Desde Hermes:

```txt
/reload-mcp
```

Si te pide confirmación, aprobalo.

## Probar Con Hermes

Primero verificá configuración:

```txt
Usá arca_mcp config_status.
```

Después probá un preview sin emitir:

```txt
Usá arca_mcp preview_factura_c con monto 100 y descripción "prueba MCP".
```

Si el preview está bien y querés emitir real, usá el `confirmation_id` devuelto y la frase exacta:

```txt
CONFIRMO EMITIR FACTURA REAL
```

## Importante

Hermes puede llamar tools, pero el MCP igual mantiene sus propias barreras:

- preview obligatorio
- `confirmation_id` con vencimiento
- confirmación textual exacta
- `ALLOW_PRODUCTION=true` para producción
