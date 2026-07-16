# ARCA MCP

Servidor MCP para emitir Factura C de ARCA/AFIP usando Afip SDK, PostgreSQL local y un flujo seguro de preview antes de emitir.

La idea es simple: en vez de tener un bot de Telegram, WhatsApp o una web cerrada, exponés herramientas MCP que cualquier agente compatible puede usar desde Hermes, Claude Desktop, Cursor, VS Code, Windsurf u otro cliente MCP.

Este proyecto está inspirado en el enfoque de [`Lanuti-Franco/facturador-ARCA`](https://github.com/Lanuti-Franco/facturador-ARCA): separar el core fiscal de la interfaz. Acá la interfaz es MCP.

## Qué Hace

- Emite **Factura C** para monotributistas mediante WSFE.
- Usa **Afip SDK** para hablar con los web services de ARCA.
- Guarda comprobantes, previews y auditoría en **PostgreSQL local**.
- Corre con **Docker Compose**.
- Expone tools MCP por `streamable-http`.
- Genera PDF con QR obligatorio de ARCA.
- Valida CUIT con dígito verificador y acepta DNI.
- Acepta montos en formato argentino o estadounidense: `15.000,50`, `15000,50`, `15,000.50`.
- Tiene alerta de umbral para consumidor final anónimo (`UMBRAL_CF`).
- Tiene un kill switch de producción: `ALLOW_PRODUCTION`.
- Obliga a hacer preview antes de emitir una factura real.

## Qué No Hace Todavía

- No emite Factura A/B para responsables inscriptos.
- No emite Nota de Crédito C todavía.
- No manda emails todavía.
- No tiene firma WSAA local; usa Afip SDK.
- No reemplaza la revisión de tu contador.

## Arquitectura

```txt
Cliente MCP / agente / IDE
        |
        | tunel SSH o red privada
        v
arca-mcp container  ->  Afip SDK  ->  ARCA WSFE
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
3. Certificado asociado al web service de Facturación Electrónica / WSFE.
4. Punto de venta tipo Web Service, distinto al de Comprobantes en Línea.
5. Cuenta y `access_token` de Afip SDK.
6. Docker y Docker Compose.

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
AFIP_PUNTO_VENTA=tu-punto-de-venta-web-service
AFIP_CERT_PATH=/certs/arca.crt
AFIP_KEY_PATH=/certs/arca.key
```

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

`emitir_factura_c` no emite de una. Primero tenés que pedir un preview.

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

## Tools MCP Disponibles

- `config_status`: revisa DB, token, modo, CUIT, punto de venta y certificados.
- `validar_cuit_dni`: valida CUIT/DNI y devuelve el tipo de documento ARCA.
- `preview_factura_c`: genera preview y `confirmation_id` sin emitir.
- `emitir_factura_c`: emite usando un `confirmation_id` válido.
- `resumen_periodo`: lista comprobantes emitidos entre dos fechas ISO.
- `exportar_csv_periodo`: devuelve un CSV separado por `;`.
- `receptores_recientes`: lista receptores identificados ya usados.

Más detalle en [`docs/tools.md`](docs/tools.md).

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
- Envío por email.
- Regeneración de PDF por número de comprobante.
- Aviso de vencimiento del certificado.
- Límite mensual/anual de monotributo.
- Firma WSAA local sin Afip SDK.
- Soporte para Factura A/B.

## Disclaimer

Esto no es asesoramiento fiscal. Verificá comprobantes emitidos, topes, umbrales de consumidor final y categoría de monotributo con tu contador. Usalo bajo tu responsabilidad.

## Licencia

MIT. Usalo, modificalo y compartilo.
