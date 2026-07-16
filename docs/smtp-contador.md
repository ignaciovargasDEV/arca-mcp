# SMTP Y Reporte Al Contador

El MCP puede enviar por email un reporte de comprobantes ya emitidos. No emite facturas desde esta tool.

La tool principal es:

```txt
enviar_reporte_contador
```

## Qué Envía

- Resumen del período en el cuerpo del email.
- Links a PDFs emitidos si existen en la base.
- PDFs adjuntos por default cuando los comprobantes tienen `pdf_url`.
- CSV opcional si pasás `adjuntar_csv=true`.

Si no hay comprobantes en el período, envía el email con warning en la respuesta de la tool.

## Variables SMTP

Configurá estas variables en `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=usuario@example.com
SMTP_PASS=tu-app-password
SMTP_FROM=usuario@example.com

ACCOUNTANT_EMAIL=contador@example.com
ACCOUNTANT_NAME=Nombre Contador
ACCOUNTANT_EMAIL_SUBJECT=Comprobantes emitidos - {desde} a {hasta}
EMAIL_MAX_ATTACHMENT_MB=15
```

`SMTP_FROM` puede ser igual a `SMTP_USER`.

## Gmail

Para Gmail necesitás:

1. Activar verificación en dos pasos en tu cuenta Google.
2. Crear una app password en `https://myaccount.google.com/apppasswords`.
3. Usar esa app password en `SMTP_PASS`.

No uses tu contraseña normal de Google.

Puerto recomendado:

```env
SMTP_PORT=587
```

`587` usa STARTTLS. En algunos VPS el puerto `465` queda bloqueado o falla por IPv6, aunque Gmail también lo soporte.

## Otros Proveedores SMTP

También podés usar cualquier SMTP compatible:

```env
SMTP_HOST=smtp.tu-proveedor.com
SMTP_PORT=587
SMTP_USER=usuario
SMTP_PASS=password-o-api-key
SMTP_FROM=facturacion@tu-dominio.com
```

Si usás un proveedor transaccional, normalmente `SMTP_PASS` es una API key SMTP.

## Uso Manual

Enviar PDFs del mes:

```txt
enviar_reporte_contador(desde="2026-07-01", hasta="2026-07-31", confirmacion="CONFIRMO ENVIAR EMAIL")
```

Enviar PDFs y CSV:

```txt
enviar_reporte_contador(desde="2026-07-01", hasta="2026-07-31", adjuntar_pdfs=true, adjuntar_csv=true, confirmacion="CONFIRMO ENVIAR EMAIL")
```

Enviar solo CSV:

```txt
enviar_reporte_contador(desde="2026-07-01", hasta="2026-07-31", adjuntar_pdfs=false, adjuntar_csv=true, confirmacion="CONFIRMO ENVIAR EMAIL")
```

## Scheduling Con Hermes

No hace falta cron del sistema. Si usás Hermes y soporta tareas recurrentes, dejá que Hermes programe el envío.

Instrucción sugerida:

```txt
El primer día de cada mes, usá arca_mcp enviar_reporte_contador para enviar al contador los comprobantes del mes anterior. Usá confirmacion="CONFIRMO ENVIAR EMAIL". No emitas facturas.
```

El MCP se mantiene simple: recibe el pedido, arma el reporte y manda el email.

## Seguridad

- No subas `.env` a git.
- No guardes `SMTP_PASS` en `billing-profiles.yml`.
- Usá app password o API key SMTP, no contraseña personal.
- No automatices emisión de facturas desde tareas programadas.
- La tarea mensual solo debe enviar comprobantes ya emitidos.

## Troubleshooting

`Network is unreachable`:
Puede ser IPv6 o puerto bloqueado. Probá `SMTP_PORT=587`.

Timeout conectando a Gmail:
El proveedor del VPS puede bloquear `465` o `25`. Usá `587`.

Autenticación fallida:
En Gmail, confirmá que `SMTP_PASS` sea app password y que 2FA esté activo.

No adjunta PDFs:
El reporte solo adjunta PDFs si los comprobantes del período tienen `pdf_url` guardado en la base y si el tamaño total no supera `EMAIL_MAX_ATTACHMENT_MB`.
