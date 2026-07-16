# ARCA MCP

Servidor MCP para emitir Factura C y Factura E de exportación de servicios de ARCA/AFIP usando Afip SDK, PostgreSQL local y un flujo seguro de preview antes de emitir.

La idea es simple: en vez de tener un bot de Telegram, WhatsApp o una web cerrada, exponés herramientas MCP que cualquier agente compatible puede usar desde Hermes, Claude Desktop, Cursor, VS Code, Windsurf u otro cliente MCP.

Este proyecto está inspirado en el enfoque de [`Lanuti-Franco/facturador-ARCA`](https://github.com/Lanuti-Franco/facturador-ARCA): separar el core fiscal de la interfaz. Acá la interfaz es MCP.

## Qué Hace

- Emite **Factura C** para monotributistas mediante WSFE.
- Emite **Factura E** de exportación de servicios mediante WSFEX.
- Usa **Afip SDK** para hablar con los web services de ARCA.
- Guarda comprobantes, previews y auditoría en **PostgreSQL local**.
- Corre con **Docker Compose**.
- Expone tools MCP por `streamable-http`.
- Genera PDF con QR obligatorio de ARCA.
- Envía reportes por email al contador con PDFs ya emitidos y CSV opcional.
- Valida CUIT con dígito verificador y acepta DNI.
- Acepta montos en formato argentino o estadounidense: `15.000,50`, `15000,50`, `15,000.50`.
- Tiene alerta de umbral para consumidor final anónimo (`UMBRAL_CF`).
- Tiene un kill switch de producción: `ALLOW_PRODUCTION`.
- Obliga a hacer preview antes de emitir una factura real.

## Qué No Hace Todavía

- No emite Factura A/B para responsables inscriptos.
- No cubre exportación de mercadería con permisos de embarque.
- No emite Nota de Crédito C todavía.
- No tiene firma WSAA local; usa Afip SDK.
- No reemplaza la revisión de tu contador.

## Arquitectura

```txt
Cliente MCP / agente / IDE
        |
        | tunel SSH o red privada
        v
arca-mcp container  ->  Afip SDK  ->  ARCA WSFE / WSFEX
        |
        v
postgres-main container
```

Por defecto el compose publica todo solo en localhost del host:

```txt
MCP:        http://127.0.0.1:8000/mcp
PostgreSQL: 127.0.0.1:5432
```

Eso te permite correrlo en un VPS sin dominio y accederlo por túnel SSH.

## Qué Necesitás

1. Ser monotributista con clave fiscal 3 suficiente para administrar certificados y relaciones.
2. Certificado digital de ARCA creado manualmente.
3. Certificado asociado al web service de Facturación Electrónica / WSFE si vas a emitir Factura C.
4. Certificado asociado a Factura Electrónica de Exportación / WSFEX si vas a emitir Factura E.
5. Un punto de venta Web Service para Factura C, distinto al de Comprobantes en Línea.
6. Un punto de venta de exportación para Factura E si vas a usar WSFEX.
7. Cuenta y `access_token` de Afip SDK.
8. Docker y Docker Compose.

La parte fiscal está explicada paso a paso en [`docs/arca-setup.md`](docs/arca-setup.md).

## Instalación Rápida

```bash
git clone https://github.com/ignaciovargasDEV/arca-mcp.git
cd arca-mcp
cp .env.example .env
mkdir -p certs backups
```

Editá `.env` con tus datos.

Levantá los servicios:

```bash
docker compose up -d --build
```

Verificá que estén vivos:

```bash
docker compose ps
```

Logs del MCP:

```bash
docker compose logs -f arca-mcp
```

## Configuración Para Homologación

Para probar sin emitir comprobantes reales:

```env
POSTGRES_DB=arca_mcp
POSTGRES_USER=arca_mcp_user
POSTGRES_PASSWORD=change-me-long-random-password

AFIP_ACCESS_TOKEN=tu-token-de-afip-sdk
PRODUCTION=false
ALLOW_PRODUCTION=false

TEST_CUIT=20409378472
TEST_PUNTO_VENTA=1

EMISOR_NOMBRE=Tu Nombre
FACTURA_DESCRIPCION=Servicios
CONCEPTO=2
```

En homologación la confirmación requerida para emitir es:

```txt
CONFIRMO EMITIR
```

## Configuración Para Producción

Para comprobantes reales:

```env
PRODUCTION=true
ALLOW_PRODUCTION=false
AFIP_CUIT=tu-cuit-sin-guiones
AFIP_PUNTO_VENTA=tu-punto-de-venta-wsfe
AFIP_PUNTO_VENTA_EXPORTACION=tu-punto-de-venta-wsfex
AFIP_CERT_PATH=/certs/arca.crt
AFIP_KEY_PATH=/certs/arca.key
```

`AFIP_PUNTO_VENTA` y `AFIP_PUNTO_VENTA_EXPORTACION` son configurables. En una instalación pueden ser `3` y `4`, en otra `1` y `2`, o cualquier número habilitado en ARCA. No copies números de otra persona: verificá tus puntos de venta en ARCA y con `config_status` / `parametros_factura_e`.

Montá tus archivos así:

```txt
certs/arca.crt  certificado descargado de ARCA
certs/arca.key  private key generada con OpenSSL
```

No actives `ALLOW_PRODUCTION=true` hasta haber revisado bien el primer preview.

En producción la confirmación exacta para emitir es:

```txt
CONFIRMO EMITIR FACTURA REAL
```

## Flujo Seguro De Emisión

`emitir_factura_c` y `emitir_factura_e` no emiten de una. Primero tenés que pedir un preview.

1. Llamás `preview_factura_c`.
2. Revisás monto, receptor, fecha, modo y advertencias.
3. El MCP devuelve un `confirmation_id` que dura 10 minutos.
4. Llamás `emitir_factura_c` con ese `confirmation_id` y la frase exacta.

Ejemplo conceptual:

```txt
preview_factura_c(monto="15000", documento="20-12345678-6", descripcion="Servicios julio")
```

Después:

```txt
emitir_factura_c(confirmation_id="...", confirmacion="CONFIRMO EMITIR FACTURA REAL")
```

Para exportación de servicios:

```txt
preview_factura_e(monto="100", cliente="Cliente Exterior", domicilio_cliente="Madrid, España", pais_destino=200, cuit_pais_cliente=50000000016, moneda="DOL", cotizacion="1200", descripcion="Servicios profesionales")
```

Después:

```txt
emitir_factura_e(confirmation_id="...", confirmacion="CONFIRMO EMITIR FACTURA REAL")
```

## Tools MCP Disponibles

- `config_status`: revisa DB, token, modo, CUIT, punto de venta y certificados.
- `validar_cuit_dni`: valida CUIT/DNI y devuelve el tipo de documento ARCA.
- `preview_factura_c`: genera preview y `confirmation_id` sin emitir.
- `emitir_factura_c`: emite usando un `confirmation_id` válido.
- `preview_factura_e`: genera preview de Factura E de servicios sin emitir.
- `emitir_factura_e`: emite Factura E usando un `confirmation_id` válido.
- `parametros_factura_e`: consulta catálogos WSFEX.
- `resumen_periodo`: lista comprobantes emitidos entre dos fechas ISO.
- `exportar_csv_periodo`: devuelve un CSV separado por `;`.
- `enviar_reporte_contador`: manda resumen, CSV y PDFs ya emitidos por email.
- `receptores_recientes`: lista receptores identificados ya usados.

Más detalle en [`docs/tools.md`](docs/tools.md).

La guía específica de Factura E está en [`docs/factura-e-exportacion.md`](docs/factura-e-exportacion.md).

## Puntos De Venta

Este proyecto separa los puntos de venta por web service:

- Factura C usa WSFE y `AFIP_PUNTO_VENTA`.
- Factura E de exportación usa WSFEX y `AFIP_PUNTO_VENTA_EXPORTACION`.

Los números no son universales. Cada contribuyente debe crear o identificar sus propios puntos de venta en `Administración de Puntos de Venta y Domicilios`.

Ejemplo ficticio:

```env
AFIP_PUNTO_VENTA=3
AFIP_PUNTO_VENTA_EXPORTACION=4
```

Si tus puntos de venta son otros, poné tus números. Para validar WSFEX:

```txt
parametros_factura_e(catalogo="puntos_venta")
```

## Uso Desde Un VPS Sin Dominio

Si lo corrés en un VPS, no hace falta exponer el puerto a internet. Abrí un túnel SSH desde tu máquina:

```bash
ssh -L 8000:127.0.0.1:8000 usuario@tu-vps
```

Configurá tu cliente MCP con:

```txt
http://127.0.0.1:8000/mcp
```

## Hermes

Si usás Hermes, agregás el MCP en `~/.hermes/config.yaml` y después corrés `/reload-mcp`.

La guía está en [`docs/hermes.md`](docs/hermes.md).

## Ejemplos Con Hermes Scheduler

Hermes puede usar este MCP tanto para acciones manuales como para tareas recurrentes. La recomendación segura es automatizar previews, reportes y recordatorios, pero no dejar emisiones reales sin confirmación humana.

Ejemplo: reporte mensual al contador:

```txt
El primer día de cada mes, usá arca_mcp enviar_reporte_contador para enviar al contador los comprobantes del mes anterior. Usá confirmacion="CONFIRMO ENVIAR EMAIL". No emitas facturas.
```

Ejemplo: preparar una Factura C recurrente sin emitir:

```txt
El día 1 de cada mes, prepará con arca_mcp preview_factura_c una factura por mis servicios mensuales usando los defaults configurados. Mostrame el preview y esperá mi confirmación. No llames emitir_factura_c automáticamente.
```

Ejemplo: preparar una Factura E recurrente sin emitir:

```txt
El día 1 de cada mes, prepará con arca_mcp preview_factura_e la factura de exportación de servicios para mi cliente recurrente usando los defaults del perfil. Mostrame el confirmation_id y esperá mi confirmación exacta. No llames emitir_factura_e automáticamente.
```

Ejemplo: recordatorio de cierre:

```txt
El último día hábil de cada mes, pedime revisar los previews pendientes y recordame enviar el reporte al contador cuando termine de emitir.
```

Si querés automatizar emisión real, entendé que eso puede generar comprobantes fiscales reales sin revisión humana. Este proyecto lo permite técnicamente solo si se pasa la frase exacta, pero no lo recomienda como default operativo.

## Personalización

Podés adaptar el proyecto a tu formato habitual sin tocar código:

- PDFs de referencia privados en `private/reference-pdfs/`.
- Defaults de facturación en `private/billing-profiles.yml`.
- Ejemplo versionado en `config/billing-profiles.example.yml`.

Más detalle en [`docs/personalizacion-facturas.md`](docs/personalizacion-facturas.md).

Hermes puede manejar tareas recurrentes, por ejemplo enviar mensualmente el reporte al contador usando `enviar_reporte_contador`. El MCP no necesita cron propio para eso.

La guía SMTP y contador está en [`docs/smtp-contador.md`](docs/smtp-contador.md).

## Backups

El proyecto trae scripts simples para PostgreSQL:

```bash
./scripts/backup-postgres.sh
./scripts/restore-postgres.sh backups/arca_mcp_YYYYmmddTHHMMSSZ.sql.gz
```

Más detalle en [`docs/deployment.md`](docs/deployment.md).

## Seguridad

- No subas `.env` a git.
- No subas `certs/` a git.
- No compartas tu `arca.key`.
- No expongas `/mcp` a internet sin autenticación, VPN o túnel.
- No actives `ALLOW_PRODUCTION=true` hasta que estés listo para emitir real.
- Revisá siempre el preview antes de confirmar.

Más detalle en [`docs/security.md`](docs/security.md).

## Afip SDK Y Certificados

Este proyecto usa Afip SDK. Eso simplifica mucho la integración con ARCA, pero tenés que saber el tradeoff: para producción, Afip SDK recibe tu certificado y tu private key para autenticar contra ARCA.

Ese certificado no es tu clave fiscal, pero sí permite facturar desde el punto de venta asociado. Si querés evitar terceros por completo, habría que reemplazar Afip SDK por una implementación local de WSAA/WSFE.

## Roadmap Posible

- Nota de Crédito C.
- Regeneración de PDF por número de comprobante.
- Aviso de vencimiento del certificado.
- Límite mensual/anual de monotributo.
- Firma WSAA local sin Afip SDK.
- Soporte para Factura A/B.

## Disclaimer

Esto no es asesoramiento fiscal. Verificá los comprobantes emitidos, los puntos de venta, los umbrales de consumidor final anónimo, las reglas de exportación de servicios y tu categoría de monotributo con tu contador. Usalo bajo tu propia responsabilidad.

Este proyecto se entrega tal cual, para uso personal o como base de integración. Puede emitir comprobantes fiscales reales si lo configurás en producción y confirmás la emisión. Revisá siempre el preview antes de emitir.

Afip SDK es un servicio de terceros: para producción recibe tu certificado y tu private key para autenticar contra ARCA. Ese certificado no es tu clave fiscal, pero sí permite operar los web services asociados. Si querés cero terceros, tenés que reemplazar esa parte por firma WSAA local.

## Licencia

MIT. Usalo, modificalo y compartilo.
