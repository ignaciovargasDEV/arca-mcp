# Personalización De Facturas

La idea es que el proyecto sea reusable: cada persona puede cargar sus PDFs de referencia, defaults de facturación y datos del contador sin modificar código ni subir información privada al repo.

## Archivos Privados

Usá la carpeta `private/`. Está ignorada por git.

Estructura recomendada:

```txt
private/
  billing-profiles.yml
  reference-pdfs/
    factura-c-referencia.pdf
    factura-e-referencia.pdf
  accountant/
    notas.md
```

## Perfiles De Facturación

Copiá el ejemplo:

```bash
cp config/billing-profiles.example.yml private/billing-profiles.yml
```

Después editá `private/billing-profiles.yml` con tus defaults.

El objetivo del perfil es definir:

- qué tool MCP usar para preview
- qué tool MCP usar para emitir
- qué PDF de referencia representa el formato deseado
- qué campos se asumen por defecto
- qué datos solo se piden cuando faltan

Ejemplo conceptual:

```yaml
invoice_profiles:
  factura_e_exportacion_servicios:
    reference_pdf: factura-e-referencia.pdf
    defaults:
      moneda: DOL
      forma_pago: Contado
      descripcion: Servicios profesionales
```

## PDFs De Referencia

Poné tus PDFs reales en:

```txt
private/reference-pdfs/
```

Nombres recomendados:

```txt
factura-c-referencia.pdf
factura-e-referencia.pdf
```

Con esos PDFs se puede ajustar el HTML del comprobante para que el PDF generado por el MCP respete tu formato habitual.

## Regla De Defaults

El comportamiento esperado es:

- Si un campo está en el perfil, se usa como default.
- Si vos especificás otro valor al pedir la factura, tu valor gana.
- Si falta un dato obligatorio, Hermes o el cliente MCP debe preguntarlo antes del preview.
- Siempre se genera preview antes de emitir.
- La emisión real siempre requiere la frase exacta.

## Envío Al Contador

El perfil de contador vive en `accountant_profiles`.

Campos esperados:

- `name`
- `email`
- `hermes_schedule.enabled`
- `hermes_schedule.day_of_month`
- `hermes_schedule.hour_local`
- `monthly_report.attach_pdfs`
- `monthly_report.attach_csv`
- `monthly_report.include_summary`

El envío se hace con la tool MCP `enviar_reporte_contador`. El scheduling lo puede manejar Hermes.

Configuración SMTP en `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email
SMTP_PASS=tu-app-password
SMTP_FROM=tu-email
ACCOUNTANT_EMAIL=contador@example.com
ACCOUNTANT_NAME=Nombre Contador
EMAIL_MAX_ATTACHMENT_MB=15
```

Más detalle en [`docs/smtp-contador.md`](smtp-contador.md).

Uso manual:

```txt
Usa arca_mcp enviar_reporte_contador con desde="2026-07-01", hasta="2026-07-31", confirmacion="CONFIRMO ENVIAR EMAIL"
```

La tool puede:

- incluir resumen en el cuerpo del email
- adjuntar PDFs ya emitidos si tienen `pdf_url`
- adjuntar CSV si pasás `adjuntar_csv=true`
- incluir links a PDFs en el cuerpo

No emite facturas. Solo envía comprobantes ya registrados.

## Scheduling Con Hermes

En vez de un cron del sistema, conviene que Hermes programe una tarea recurrente.

Instrucción sugerida para Hermes:

```txt
El primer día hábil de cada mes, usá arca_mcp enviar_reporte_contador para enviar al contador los comprobantes del mes anterior. Usá confirmacion="CONFIRMO ENVIAR EMAIL". No emitas facturas.
```

## Skill Para Hermes

Una skill o instrucción de Hermes debería decir:

```txt
Usá los perfiles de private/billing-profiles.yml.
Para facturación local usá factura_c_local.
Para exportación de servicios usá factura_e_exportacion_servicios.
Aplicá defaults del perfil salvo que el usuario indique otro valor.
Siempre pedí preview antes de emitir.
Nunca emitas real sin la confirmación exacta requerida por arca_mcp.
```

## Seguridad

- No subas `private/` a git.
- No subas PDFs reales al repo.
- No guardes contraseñas SMTP en YAML; usá `.env`.
- No automatices emisión real desde tareas programadas.
- La tarea del contador solo debe enviar comprobantes ya emitidos.
