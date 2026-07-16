# Tools MCP

Estas son las herramientas que expone el servidor.

## `config_status`

Revisa la configuración sin devolver secretos.

Devuelve:

- modo (`production` u homologación)
- CUIT configurado
- punto de venta
- concepto
- estado de PostgreSQL
- si hay token de Afip SDK
- si producción está habilitada
- si el certificado y la key son legibles

Uso típico:

```txt
Usá arca_mcp config_status.
```

## `validar_cuit_dni`

Valida un CUIT o DNI.

Para CUIT valida el dígito verificador.

Ejemplo:

```txt
validar_cuit_dni(documento="20-12345678-6")
```

## `preview_factura_c`

Genera un preview. No emite.

Argumentos:

- `monto`: requerido. Acepta `15000`, `15.000`, `15.000,50`, `15,000.50`.
- `documento`: opcional. CUIT o DNI. Si lo omitís, usa Consumidor Final.
- `condicion_iva`: opcional. Si omitís y hay documento, usa Monotributo por default.
- `fecha`: opcional. Acepta `hoy`, `dd/mm` o `dd/mm/aaaa`.
- `descripcion`: opcional. Sale en el PDF, no se envía como dato fiscal a ARCA.

Devuelve:

- `confirmation_id`
- monto formateado
- receptor
- condición IVA
- advertencias
- frase de confirmación requerida

Ejemplo:

```txt
preview_factura_c(monto="15000", documento="20-12345678-6", descripcion="Servicios julio")
```

## `emitir_factura_c`

Emite Factura C usando un `confirmation_id` generado por `preview_factura_c`.

Argumentos:

- `confirmation_id`: token devuelto por el preview.
- `confirmacion`: frase exacta.

En producción:

```txt
CONFIRMO EMITIR FACTURA REAL
```

En homologación:

```txt
CONFIRMO EMITIR
```

Devuelve:

- tipo de comprobante
- punto de venta
- número
- CAE
- vencimiento del CAE
- URL del PDF

## `resumen_periodo`

Lista comprobantes emitidos entre dos fechas ISO.

Ejemplo:

```txt
resumen_periodo(desde="2026-07-01", hasta="2026-07-31")
```

## `exportar_csv_periodo`

Devuelve un CSV separado por `;` para un período.

Ejemplo:

```txt
exportar_csv_periodo(desde="2026-07-01", hasta="2026-07-31")
```

## `receptores_recientes`

Lista receptores identificados usados recientemente.

Ejemplo:

```txt
receptores_recientes(limit=5)
```

## Notas De Uso

- Si vas a emitir real, siempre pedí preview primero.
- Si el monto supera `UMBRAL_CF` y no pasaste documento, el preview te avisa.
- Si `ALLOW_PRODUCTION=false`, producción queda bloqueada aunque `PRODUCTION=true`.
- Si el `confirmation_id` expiró, generá otro preview.
