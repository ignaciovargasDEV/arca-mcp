# Setup Fiscal En ARCA

Objetivo: dejar tu CUIT habilitado para emitir por Web Service, con certificado propio, puntos de venta correctos y sin darle tu clave fiscal a ningún tercero.

Esta guía está escrita para monotributistas y para el flujo de este MCP, que usa Afip SDK.

## Antes De Arrancar

- El portal de ARCA cambia seguido. Si un nombre no coincide exacto, buscá el equivalente en pantalla.
- Guardá `arca.key`, `pedido.csr` y `arca.crt` en un lugar seguro.
- La private key (`arca.key`) no se sube a ARCA y no se comparte.
- El orden recomendado es: certificado, asociaciones a web services, puntos de venta.
- No uses automatizaciones que te pidan clave fiscal si no querés delegar ese acceso.

## 1. Clave Fiscal

Para usar estos servicios normalmente necesitás clave fiscal con nivel suficiente, usualmente nivel 3 o superior. Verificá el requisito vigente en ARCA porque puede cambiar.

Servicios que vas a usar:

- `Administración de Certificados Digitales`.
- `Administrador de Relaciones con Clave Fiscal`.
- `Administración de Puntos de Venta y Domicilios`.

## 2. Generar Private Key Y CSR

Podés hacerlo en tu máquina, en WSL, en Git Bash o en el VPS. Linux y macOS suelen traer OpenSSL.

Generá la private key:

```bash
openssl genrsa -out arca.key 2048
```

Generá el CSR:

```bash
openssl req -new -key arca.key \
  -subj "/C=AR/O=TU_NOMBRE_LEGAL/CN=arca-mcp/serialNumber=CUIT TUCUIT_SIN_GUIONES" \
  -out pedido.csr
```

Ejemplo ficticio:

```bash
openssl req -new -key arca.key \
  -subj "/C=AR/O=Juan Perez/CN=arca-mcp/serialNumber=CUIT 20123456789" \
  -out pedido.csr
```

Campos importantes:

- `C=AR`: país.
- `O=TU_NOMBRE_LEGAL`: tu nombre o razón social como figura en ARCA.
- `CN=arca-mcp`: alias para reconocer el certificado. Podés usar otro alias.
- `serialNumber=CUIT TUCUIT`: tiene que decir `CUIT`, espacio, y tu CUIT sin guiones.

Al final tenés:

```txt
arca.key    private key, no se comparte nunca
pedido.csr  archivo que sí subís a ARCA
```

## 3. Crear El Certificado En ARCA

Entrá a `Administración de Certificados Digitales`.

Flujo típico:

1. Agregá un alias.
2. Usá el mismo alias que pusiste en `CN`, por ejemplo `arca-mcp`.
3. Adjuntá `pedido.csr`.
4. Confirmá la creación del alias/certificado.
5. Descargá el certificado que te da ARCA.

Renombralo para este proyecto:

```txt
certs/arca.crt
```

Y guardá la private key como:

```txt
certs/arca.key
```

No subas `arca.key` al portal. ARCA solo necesita el CSR.

## 4. Asociar El Certificado A Los Web Services

El certificado por sí solo no alcanza. Tenés que asociarlo a cada web service que vayas a usar.

Entrá a `Administrador de Relaciones con Clave Fiscal`.

Para Factura C local:

1. Nueva relación.
2. Servicio.
3. ARCA.
4. Web Services.
5. Buscá `Facturación Electrónica` o `WSFE`.
6. Como representante, elegí el certificado/alias que acabás de crear.
7. Confirmá la relación.

Para Factura E de exportación:

1. Repetí el flujo de nueva relación.
2. Buscá `Factura Electrónica de Exportación` o `WSFEX`.
3. Como representante, elegí el mismo certificado/alias.
4. Confirmá la relación.

Si falta una asociación, el certificado existe pero no puede operar ese web service.

## 5. Crear Puntos De Venta

Necesitás puntos de venta específicos para los web services. No reutilices uno de `Comprobantes en Línea`.

Entrá a `Administración de Puntos de Venta y Domicilios`.

Para Factura C / WSFE:

1. Alta de punto de venta.
2. Elegí un número libre.
3. Tipo/sistema: Web Service.
4. Sistema: algo equivalente a `Factura Electrónica - Monotributo - Web Services`.
5. Guardá.

Después poné ese número en `.env`:

```env
AFIP_PUNTO_VENTA=tu-punto-de-venta-wsfe
```

Para Factura E / WSFEX:

1. Alta de punto de venta.
2. Elegí un número libre.
3. Tipo/sistema: exportación / Factura Electrónica de Exportación Web Service, según lo muestre ARCA.
4. Guardá.

Después poné ese número en `.env`:

```env
AFIP_PUNTO_VENTA_EXPORTACION=tu-punto-de-venta-wsfex
```

Ejemplo ficticio:

```env
AFIP_PUNTO_VENTA=3
AFIP_PUNTO_VENTA_EXPORTACION=4
```

No copies esos números salvo que sean los tuyos. Cada CUIT puede tener otra numeración.

Si mezclás puntos de venta de Comprobantes en Línea y Web Service, vas a tener errores de autorización o numeración.

## 6. Crear Token En Afip SDK

Creá una cuenta en Afip SDK y generá un `access_token`.

En `.env`:

```env
AFIP_ACCESS_TOKEN=tu-token
```

Para producción el MCP le pasa a Afip SDK:

```txt
CUIT
production=true
cert
key
access_token
```

## 7. Probar Antes De Emitir Real

Primero levantá el MCP con:

```env
PRODUCTION=false
ALLOW_PRODUCTION=false
```

Después revisá `config_status` desde tu cliente MCP. Para WSFEX, además revisá:

```txt
parametros_factura_e(catalogo="puntos_venta")
```

Cuando pases a producción, dejá inicialmente:

```env
PRODUCTION=true
ALLOW_PRODUCTION=false
```

Hacé un `preview_factura_c`. Si todo está bien, recién ahí activá:

```env
ALLOW_PRODUCTION=true
```

Probá con una factura real chica y verificá el comprobante en ARCA.

## Checklist Final

- `arca.key` guardada y con backup seguro.
- `pedido.csr` generado.
- `arca.crt` descargado desde ARCA.
- Certificado asociado a WSFE si emitís Factura C.
- Certificado asociado a WSFEX si emitís Factura E.
- Punto de venta WSFE creado y configurado.
- Punto de venta WSFEX creado y configurado si emitís Factura E.
- `AFIP_ACCESS_TOKEN` configurado.
- `.env` con CUIT y punto de venta correctos.
- `config_status` OK.
- Preview revisado antes de emitir.

## Problemas Comunes

`cert_file_readable=false` o `key_file_readable=false`:
Revisá rutas y permisos de `certs/arca.crt` y `certs/arca.key`.

ARCA rechaza el comprobante por punto de venta:
Verificá que el punto sea Web Service y que esté asociado correctamente.

Error de autorización WSFE/WSFEX:
Revisá la relación del web service correspondiente en `Administrador de Relaciones con Clave Fiscal`.

El CSR rebota:
Revisá `O=`, `CN=` y `serialNumber=CUIT ...`. El nombre legal tiene que coincidir razonablemente con ARCA.
