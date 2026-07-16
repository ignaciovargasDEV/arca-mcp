# ARCA Setup

This project emits Factura C through ARCA/AFIP WSFE using Afip SDK. Before production use, your CUIT must have a certificate associated to WSFE and a Web Service point of sale.

## 1. Generate Private Key And CSR

Run this on a trusted machine or directly on your VPS. Keep `arca.key` private.

```bash
openssl genrsa -out arca.key 2048

openssl req -new -key arca.key \
  -subj "/C=AR/O=YOUR_LEGAL_NAME/CN=arca-mcp/serialNumber=CUIT YOUR_CUIT_WITHOUT_DASHES" \
  -out pedido.csr
```

Example subject:

```txt
/C=AR/O=Ignacio Matias Vargas/CN=arca-mcp/serialNumber=CUIT 20123456789
```

## 2. Create Certificate In ARCA

In ARCA, use Administrador de Certificados Digitales:

1. Add an alias using the same `CN` value.
2. Upload `pedido.csr`.
3. Download the generated certificate.
4. Save it as `certs/arca.crt`.

Never upload or share `arca.key`.

## 3. Associate Certificate To WSFE

In Administrador de Relaciones con Clave Fiscal, associate the certificate alias to the Electronic Billing Web Service, usually listed as WSFE or Facturacion Electronica.

## 4. Create A Web Service Point Of Sale

Create a point of sale specifically for Web Services. Do not reuse a Comprobantes en Linea point of sale.

Set that number in `.env`:

```env
AFIP_PUNTO_VENTA=3
```

## 5. Afip SDK Token

Create an account at Afip SDK and set:

```env
AFIP_ACCESS_TOKEN=your-token
```

The Afip SDK production flow receives your certificate and private key to authenticate with ARCA. If you do not accept that tradeoff, this project needs a local WSAA implementation instead.
