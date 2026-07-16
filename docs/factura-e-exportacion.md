# Factura E De Exportación De Servicios

El soporte de Factura E está pensado para exportación de servicios y usa WSFEX. No es el mismo web service que Factura C.

## Alcance

- Tipo de comprobante: `19` Factura E.
- Punto de venta: `AFIP_PUNTO_VENTA_EXPORTACION`, configurable por instalación.
- Web service: `wsfex`.
- Tipo de exportación default: `EXPORTACION_TIPO=2`.
- No incluye permisos de embarque ni exportación de mercadería.

## Configuración

Variables principales:

```env
AFIP_PUNTO_VENTA=tu-punto-de-venta-wsfe
AFIP_PUNTO_VENTA_EXPORTACION=tu-punto-de-venta-wsfex

EXPORTACION_TIPO=2
EXPORTACION_MONEDA=DOL
EXPORTACION_PAIS_DESTINO=
EXPORTACION_CUIT_PAIS=
EXPORTACION_IDIOMA=1
EXPORTACION_UMED=7
EXPORTACION_FORMA_PAGO=Contado
```

Antes de emitir real, usá `parametros_factura_e` para confirmar códigos vigentes de país, CUIT país, moneda, idioma, unidad de medida y punto de venta.

Los números de punto de venta no son parte del proyecto. Cada contribuyente debe usar los números habilitados en su propia cuenta ARCA. Si tu WSFEX está en punto de venta `4`, usá `4`; si está en `8`, usá `8`.

## Tools

### `parametros_factura_e`

Consulta catálogos WSFEX.

Catálogos soportados:

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
parametros_factura_e(catalogo="puntos_venta")
```

### `preview_factura_e`

Genera un preview y un `confirmation_id`. No emite.

Argumentos principales:

- `monto`: importe en la moneda indicada.
- `cliente`: nombre del cliente exterior.
- `domicilio_cliente`: domicilio del cliente exterior.
- `pais_destino`: código WSFEX del país destino. Si omitís, usa `EXPORTACION_PAIS_DESTINO`.
- `cuit_pais_cliente`: CUIT país WSFEX. Si omitís, usa `EXPORTACION_CUIT_PAIS`.
- `id_impositivo`: identificador fiscal extranjero, si corresponde.
- `moneda`: default `EXPORTACION_MONEDA`.
- `cotizacion`: requerida si la moneda no es `PES`.
- `descripcion`: detalle del servicio.
- `forma_pago`: default `EXPORTACION_FORMA_PAGO`.

Ejemplo:

```txt
preview_factura_e(monto="100", cliente="Cliente Exterior", domicilio_cliente="Madrid, España", pais_destino=200, cuit_pais_cliente=50000000016, moneda="DOL", cotizacion="1200", descripcion="Servicios profesionales")
```

### `emitir_factura_e`

Emite usando un `confirmation_id` generado por `preview_factura_e`.

En producción la confirmación debe ser exactamente:

```txt
CONFIRMO EMITIR FACTURA REAL
```

## Checklist Antes De Producción

- El certificado está asociado a WSFEX en ARCA.
- El punto de venta de exportación está activo.
- `parametros_factura_e(catalogo="puntos_venta")` devuelve el punto de venta esperado.
- El número devuelto por WSFEX coincide con `AFIP_PUNTO_VENTA_EXPORTACION`.
- `ALLOW_PRODUCTION=true` solo se activa después de revisar el preview.
- Los códigos de país, CUIT país, moneda e idioma fueron validados con catálogos WSFEX.
