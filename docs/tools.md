# MCP Tools

## `config_status`

Checks database, Afip SDK token, production flags, CUIT, point of sale, and certificate readability. It does not return secrets.

## `validar_cuit_dni`

Validates a CUIT or DNI and returns the ARCA document type.

## `preview_factura_c`

Creates a preview and a single-use `confirmation_id`. It does not emit.

Arguments:

- `monto`: required string. Accepts Argentine or US number formats.
- `documento`: optional CUIT or DNI. Omit for Consumidor Final.
- `condicion_iva`: optional ARCA condition ID. Defaults to Consumidor Final or Monotributo.
- `fecha`: optional `dd/mm`, `dd/mm/yyyy`, or `hoy`.
- `descripcion`: optional PDF line description.

## `emitir_factura_c`

Emits a real or homologation Factura C using a valid `confirmation_id`.

Arguments:

- `confirmation_id`: returned by `preview_factura_c`.
- `confirmacion`: exact confirmation phrase.

Production phrase:

```txt
CONFIRMO EMITIR FACTURA REAL
```

Homologation phrase:

```txt
CONFIRMO EMITIR
```

## `resumen_periodo`

Lists emitted invoices between two ISO dates.

## `exportar_csv_periodo`

Returns a semicolon-separated CSV for a date range.

## `receptores_recientes`

Lists recently used identified receivers.
