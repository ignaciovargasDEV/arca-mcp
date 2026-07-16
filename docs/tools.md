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

## `parametros_factura_e`

Consulta catálogos de WSFEX para configurar Factura E.

Argumentos:

- `catalogo`: opcional. Default `puntos_venta`.

Valores soportados:

- `puntos_venta`
- `tipos_comprobante`
- `tipos_exportacion`
- `idiomas`
- `unidades_medida`
- `paises`
- `cuits_pais`
- `monedas`
- `incoterms`

Ejemplo:

```txt
parametros_factura_e(catalogo="paises")
```

## `preview_factura_e`

Genera un preview de Factura E de exportación de servicios. No emite.

Argumentos:

- `monto`: requerido. Importe en la moneda indicada.
- `cliente`: requerido. Nombre del cliente exterior.
- `domicilio_cliente`: requerido.
- `pais_destino`: opcional si configuraste `EXPORTACION_PAIS_DESTINO`.
- `cuit_pais_cliente`: opcional si configuraste `EXPORTACION_CUIT_PAIS`.
- `id_impositivo`: opcional. Identificador fiscal extranjero.
- `fecha`: opcional. Acepta `hoy`, `dd/mm` o `dd/mm/aaaa`.
- `descripcion`: opcional. Sale como item del servicio.
- `moneda`: opcional. Default `EXPORTACION_MONEDA`.
- `cotizacion`: requerida si la moneda no es `PES`.
- `forma_pago`: opcional. Default `EXPORTACION_FORMA_PAGO`.
- `idioma_cbte`: opcional. Default `EXPORTACION_IDIOMA`.

Devuelve:

- `confirmation_id`
- punto de venta de exportación
- monto, moneda y cotización
- cliente exterior
- advertencias
- frase de confirmación requerida

Ejemplo:

```txt
preview_factura_e(monto="100", cliente="Cliente Exterior", domicilio_cliente="Madrid, España", pais_destino=200, cuit_pais_cliente=50000000016, moneda="DOL", cotizacion="1200", descripcion="Servicios profesionales")
```

## `emitir_factura_e`

Emite Factura E usando un `confirmation_id` generado por `preview_factura_e`.

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

- tipo de comprobante `19`
- punto de venta de exportación
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

## `enviar_reporte_contador`

Envía por email al contador el resumen, CSV y PDFs de comprobantes ya emitidos. No emite facturas.

Requiere SMTP configurado en `.env`.

Ver [`docs/smtp-contador.md`](smtp-contador.md) para Gmail, otros proveedores y Hermes scheduler.

Argumentos:

- `desde`: requerido. Fecha ISO `yyyy-mm-dd`.
- `hasta`: requerido. Fecha ISO `yyyy-mm-dd`.
- `email_contador`: opcional si configuraste `ACCOUNTANT_EMAIL`.
- `nombre_contador`: opcional si configuraste `ACCOUNTANT_NAME`.
- `adjuntar_csv`: default `false`.
- `adjuntar_pdfs`: default `true`.
- `incluir_resumen`: default `true`.
- `confirmacion`: debe ser exactamente `CONFIRMO ENVIAR EMAIL`.

Ejemplo:

```txt
enviar_reporte_contador(desde="2026-07-01", hasta="2026-07-31", adjuntar_pdfs=true, confirmacion="CONFIRMO ENVIAR EMAIL")
```

Para Hermes scheduler, usá una tarea recurrente que llame esta tool para el mes anterior.

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
- Para Factura E, validá catálogos WSFEX antes de emitir real.
