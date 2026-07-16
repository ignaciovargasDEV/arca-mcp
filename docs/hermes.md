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

Después probá un preview sin emitir para Factura C:

```txt
Usá arca_mcp preview_factura_c con monto 100 y descripción "prueba MCP".
```

Si el preview está bien y querés emitir real, usá el `confirmation_id` devuelto y la frase exacta:

```txt
CONFIRMO EMITIR FACTURA REAL
```

Para Factura E, primero validá WSFEX:

```txt
Usá arca_mcp parametros_factura_e con catalogo="puntos_venta".
```

Después pedí preview:

```txt
Usá arca_mcp preview_factura_e con monto="100", cliente="Cliente Exterior", domicilio_cliente="Madrid, España", pais_destino=200, cuit_pais_cliente=50000000016, moneda="DOL", cotizacion="1200", descripcion="Servicios profesionales".
```

## Reporte Al Contador

Hermes puede programar el envío mensual usando la tool `enviar_reporte_contador`. El MCP no necesita cron propio.

Uso manual:

```txt
Usá arca_mcp enviar_reporte_contador con desde="2026-07-01", hasta="2026-07-31", adjuntar_pdfs=true, confirmacion="CONFIRMO ENVIAR EMAIL".
```

Instrucción sugerida para scheduler de Hermes:

```txt
El primer día de cada mes, usá arca_mcp enviar_reporte_contador para enviar al contador los comprobantes del mes anterior. Usá confirmacion="CONFIRMO ENVIAR EMAIL". No emitas facturas.
```

## Tareas Recurrentes De Facturación

Hermes puede schedulear preparación de facturas recurrentes. La forma segura es que la tarea genere previews y te pida confirmación antes de emitir.

Factura C recurrente:

```txt
El día 1 de cada mes, usá arca_mcp preview_factura_c para preparar la factura local de servicios mensuales con los defaults configurados. Mostrame monto, receptor, punto de venta y confirmation_id. No emitas automáticamente.
```

Factura E recurrente:

```txt
El día 1 de cada mes, usá arca_mcp preview_factura_e para preparar la factura de exportación de servicios de mi cliente recurrente con los defaults configurados. Mostrame moneda, cotización, país destino, punto de venta y confirmation_id. No emitas automáticamente.
```

Recordatorio de emisión y cierre:

```txt
El último día hábil de cada mes, recordame revisar las facturas emitidas y, cuando estén todas, usar arca_mcp enviar_reporte_contador para mandarle PDFs al contador.
```

Si decidís automatizar emisión real, la tarea tendría que incluir la frase exacta de emisión. No es el default recomendado porque puede generar comprobantes fiscales reales sin revisión humana.

## Importante

Hermes puede llamar tools, pero el MCP igual mantiene sus propias barreras:

- preview obligatorio
- `confirmation_id` con vencimiento
- confirmación textual exacta
- `ALLOW_PRODUCTION=true` para producción
- confirmación textual exacta para emails al contador
