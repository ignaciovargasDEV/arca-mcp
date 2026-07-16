import base64
import csv
import io
import json
import os
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

import segno
from afip import Afip
from dotenv import load_dotenv

from . import db

load_dotenv()

FACTURA_C = 11
NOTA_CREDITO_C = 13
DOC_TIPO_CF = 99
DOC_NRO_CF = 0
COND_IVA_CF = 5
DOC_TIPO_CUIT = 80
DOC_TIPO_DNI = 96
TZ_AR = ZoneInfo("America/Argentina/Buenos_Aires")

CONDICIONES_IVA = {
    1: "Resp. Inscripto",
    4: "IVA Exento",
    5: "Consumidor Final",
    6: "Monotributo",
    15: "IVA No Alcanzado",
}


def is_production() -> bool:
    return os.environ.get("PRODUCTION", "").strip().lower() in ("1", "true", "si", "sí")


def config() -> dict:
    production = is_production()
    concepto = int(os.environ.get("CONCEPTO", "2"))
    if concepto not in (1, 2, 3):
        raise ValueError("CONCEPTO debe ser 1, 2 o 3")
    if production:
        cuit = int(os.environ["AFIP_CUIT"])
        pto_vta = int(os.environ["AFIP_PUNTO_VENTA"])
        cert_path = os.environ["AFIP_CERT_PATH"]
        key_path = os.environ["AFIP_KEY_PATH"]
    else:
        cuit = int(os.environ.get("TEST_CUIT", "20409378472"))
        pto_vta = int(os.environ.get("TEST_PUNTO_VENTA", "1"))
        cert_path = None
        key_path = None
    return {
        "production": production,
        "allow_production": os.environ.get("ALLOW_PRODUCTION", "").lower() in ("1", "true", "si", "sí"),
        "afip_access_token_configured": bool(os.environ.get("AFIP_ACCESS_TOKEN") or os.environ.get("AFIP_SDK_ACCESS_TOKEN")),
        "cuit": cuit,
        "pto_vta": pto_vta,
        "concepto": concepto,
        "usa_periodo": concepto != 1,
        "cert_path": cert_path,
        "key_path": key_path,
        "emisor_nombre": os.environ.get("EMISOR_NOMBRE") or "-",
        "umbral_cf": _optional_float("UMBRAL_CF"),
        "max_factura_ars": _optional_float("MAX_FACTURA_ARS"),
    }


def status() -> dict:
    cfg = config()
    checks = {
        "database": True,
        "afip_access_token": cfg["afip_access_token_configured"],
        "production_enabled": cfg["production"],
        "allow_production": cfg["allow_production"],
        "cert_file_readable": None,
        "key_file_readable": None,
    }
    if cfg["production"]:
        checks["cert_file_readable"] = bool(cfg["cert_path"] and os.path.isfile(cfg["cert_path"]))
        checks["key_file_readable"] = bool(cfg["key_path"] and os.path.isfile(cfg["key_path"]))
    try:
        with db.connect() as conn:
            conn.execute("select 1").fetchone()
    except Exception:
        checks["database"] = False
    return {
        "mode": "production" if cfg["production"] else "homologacion",
        "cuit": cfg["cuit"],
        "pto_vta": cfg["pto_vta"],
        "concepto": cfg["concepto"],
        "checks": checks,
    }


def parsear_monto(texto: str) -> float:
    t = texto.strip().replace(" ", "").lstrip("$")
    if "," in t and "." in t:
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif re.fullmatch(r"\d{1,3}([.,]\d{3})+", t):
        t = re.sub(r"[.,]", "", t)
    else:
        t = t.replace(",", ".")
    monto = float(round(Decimal(t), 2))
    if monto <= 0:
        raise InvalidOperation
    return monto


def hoy_ar() -> date:
    return datetime.now(TZ_AR).date()


def parsear_fecha(texto: str | None) -> date:
    if not texto:
        return hoy_ar()
    t = texto.strip().lower().replace("-", "/")
    if t == "hoy":
        return hoy_ar()
    partes = t.split("/")
    if len(partes) == 2:
        return date(hoy_ar().year, int(partes[1]), int(partes[0]))
    if len(partes) == 3:
        anio = int(partes[2])
        if anio < 100:
            anio += 2000
        return date(anio, int(partes[1]), int(partes[0]))
    raise ValueError("fecha invalida; usar dd/mm o dd/mm/aaaa")


def validar_fecha(fecha: date) -> None:
    cfg = config()
    dias_atras = 10 if cfg["usa_periodo"] else 5
    hoy = hoy_ar()
    if fecha > hoy:
        raise ValueError("La fecha no puede ser futura")
    if fecha < hoy - timedelta(days=dias_atras):
        raise ValueError(f"Maximo {dias_atras} dias para atras")


def parsear_cuit(texto: str) -> int | None:
    t = re.sub(r"[-.\s]", "", texto.strip())
    if not re.fullmatch(r"\d{11}", t):
        return None
    digitos = [int(c) for c in t]
    pesos = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    resto = sum(d * p for d, p in zip(digitos, pesos)) % 11
    verificador = 0 if resto == 0 else 11 - resto
    if verificador == 10 or verificador != digitos[10]:
        return None
    return int(t)


def parsear_doc(texto: str | None) -> tuple[int, int]:
    if not texto:
        return DOC_TIPO_CF, DOC_NRO_CF
    t = re.sub(r"[-.\s]", "", texto.strip())
    if re.fullmatch(r"\d{11}", t):
        cuit = parsear_cuit(t)
        if cuit is None:
            raise ValueError("CUIT invalido")
        return DOC_TIPO_CUIT, cuit
    if re.fullmatch(r"\d{7,8}", t):
        return DOC_TIPO_DNI, int(t)
    raise ValueError("Documento invalido; usar CUIT o DNI")


def fmt_ars(monto: float) -> str:
    return f"{monto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_doc(doc_tipo: int, nro: int) -> str:
    if doc_tipo == DOC_TIPO_CF:
        return "Consumidor Final"
    if doc_tipo == DOC_TIPO_CUIT:
        s = str(nro)
        return f"CUIT {s[:2]}-{s[2:10]}-{s[10]}"
    return "DNI " + f"{nro:,}".replace(",", ".")


def preview_factura_c(monto: str, documento: str | None = None,
                      condicion_iva: int | None = None, fecha: str | None = None,
                      descripcion: str | None = None) -> dict:
    cfg = config()
    importe = parsear_monto(monto)
    fecha_cbte = parsear_fecha(fecha)
    validar_fecha(fecha_cbte)
    doc_tipo, doc_nro = parsear_doc(documento)
    cond_iva = condicion_iva or (COND_IVA_CF if doc_tipo == DOC_TIPO_CF else 6)
    if cond_iva not in CONDICIONES_IVA:
        raise ValueError("condicion_iva no soportada")
    max_factura = cfg["max_factura_ars"]
    if max_factura is not None and importe > max_factura:
        raise ValueError(f"El monto supera MAX_FACTURA_ARS (${fmt_ars(max_factura)})")

    warnings = []
    if cfg["umbral_cf"] is not None and doc_tipo == DOC_TIPO_CF and importe >= cfg["umbral_cf"]:
        warnings.append("El monto exige identificar al receptor; ARCA podria rechazar consumidor final anonimo")
    if cfg["production"]:
        warnings.append("PRODUCCION: esto emitira un comprobante real si se confirma")

    payload = {
        "monto": importe,
        "doc_tipo": doc_tipo,
        "doc_nro": doc_nro,
        "condicion_iva": cond_iva,
        "fecha": fecha_cbte.isoformat(),
        "descripcion": descripcion,
    }
    confirmation_id = db.create_confirmation("emitir_factura_c", payload)
    result = {
        "confirmation_id": confirmation_id,
        "expires_in_minutes": 10,
        "mode": "production" if cfg["production"] else "homologacion",
        "monto": importe,
        "monto_formateado": fmt_ars(importe),
        "fecha": fecha_cbte.isoformat(),
        "receptor": fmt_doc(doc_tipo, doc_nro),
        "condicion_iva": CONDICIONES_IVA[cond_iva],
        "descripcion": descripcion or os.environ.get("FACTURA_DESCRIPCION", "Servicios"),
        "warnings": warnings,
        "confirmacion_requerida": "CONFIRMO EMITIR FACTURA REAL" if cfg["production"] else "CONFIRMO EMITIR",
    }
    db.audit("preview_factura_c", result["mode"], payload, result)
    return result


def emitir_factura_c(confirmation_id: str, confirmacion: str) -> dict:
    cfg = config()
    expected = "CONFIRMO EMITIR FACTURA REAL" if cfg["production"] else "CONFIRMO EMITIR"
    if confirmacion != expected:
        raise ValueError(f"confirmacion invalida; debe ser exactamente: {expected}")
    if cfg["production"] and not cfg["allow_production"]:
        raise ValueError("PRODUCTION=true pero ALLOW_PRODUCTION no esta habilitado")

    payload = db.consume_confirmation(confirmation_id, "emitir_factura_c")
    fecha_cbte = date.fromisoformat(payload["fecha"])
    validar_fecha(fecha_cbte)
    res = _emitir_factura_afip(
        importe_total=float(payload["monto"]),
        doc_tipo=int(payload["doc_tipo"]),
        doc_nro=int(payload["doc_nro"]),
        cond_iva=int(payload["condicion_iva"]),
        fecha=fecha_cbte,
        cbte_tipo=FACTURA_C,
    )
    fila = _fila_factura(res, payload)
    db.insert_factura(fila)
    ud = {
        "monto": float(payload["monto"]),
        "doc_tipo": int(payload["doc_tipo"]),
        "doc_nro": int(payload["doc_nro"]),
        "cond_iva": int(payload["condicion_iva"]),
        "descripcion": payload.get("descripcion"),
    }
    pdf_url = generar_pdf_desde_res(res, ud)
    db.update_pdf_url(cfg["pto_vta"], FACTURA_C, res["numero"], pdf_url)
    result = {
        "mode": "production" if cfg["production"] else "homologacion",
        "cbte_tipo": FACTURA_C,
        "pto_vta": cfg["pto_vta"],
        "numero": res["numero"],
        "cae": res["CAE"],
        "cae_vto": res["CAEFchVto"],
        "pdf_url": pdf_url,
    }
    db.audit("emitir_factura_c", result["mode"], payload, result)
    return result


def resumen_periodo(desde: str, hasta: str) -> dict:
    rows = db.list_facturas(desde, hasta)
    total = 0.0
    items = []
    for row in rows:
        monto = float(row["imp_total"])
        signo = -1 if row["cbte_tipo"] == NOTA_CREDITO_C else 1
        total += signo * monto
        items.append({
            "tipo": "NC C" if row["cbte_tipo"] == NOTA_CREDITO_C else "Factura C",
            "numero": row["cbte_nro"],
            "fecha": row["fecha_cbte"].isoformat(),
            "monto": signo * monto,
            "receptor": fmt_doc(row["doc_tipo"], row["doc_nro"]),
        })
    return {"desde": desde, "hasta": hasta, "total": round(total, 2), "items": items}


def exportar_csv_periodo(desde: str, hasta: str) -> str:
    rows = db.list_facturas(desde, hasta)
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["tipo", "punto_venta", "numero", "fecha", "doc_tipo", "doc_nro", "importe", "cae", "vto_cae"])
    for row in rows:
        signo = -1 if row["cbte_tipo"] == NOTA_CREDITO_C else 1
        writer.writerow([
            "NC C" if row["cbte_tipo"] == NOTA_CREDITO_C else "Factura C",
            row["pto_vta"], row["cbte_nro"], row["fecha_cbte"].isoformat(),
            row["doc_tipo"], row["doc_nro"], f"{signo * float(row['imp_total']):.2f}".replace(".", ","),
            row["cae"], row["cae_vto"].isoformat(),
        ])
    return buffer.getvalue()


def receptores_recientes(limit: int = 5) -> list[dict]:
    return db.recent_receptores(limit)


def validar_documento(documento: str) -> dict:
    doc_tipo, doc_nro = parsear_doc(documento)
    return {"doc_tipo": doc_tipo, "doc_nro": doc_nro, "descripcion": fmt_doc(doc_tipo, doc_nro)}


def _get_afip() -> Afip:
    cfg = config()
    opciones = {"CUIT": cfg["cuit"], "production": cfg["production"]}
    access_token = os.environ.get("AFIP_ACCESS_TOKEN") or os.environ.get("AFIP_SDK_ACCESS_TOKEN")
    if access_token:
        opciones["access_token"] = access_token
    if cfg["production"]:
        with open(cfg["cert_path"], encoding="utf-8") as cert_file:
            opciones["cert"] = cert_file.read()
        with open(cfg["key_path"], encoding="utf-8") as key_file:
            opciones["key"] = key_file.read()
    return Afip(opciones)


def _emitir_factura_afip(importe_total: float, doc_tipo: int, doc_nro: int,
                         cond_iva: int, fecha: date, cbte_tipo: int,
                         asociado_nro: int | None = None) -> dict:
    cfg = config()
    afip = _get_afip()
    ultimo = afip.ElectronicBilling.getLastVoucher(cfg["pto_vta"], cbte_tipo)
    numero = ultimo + 1
    fecha_int = int(fecha.strftime("%Y%m%d"))
    data = {
        "CantReg": 1,
        "PtoVta": cfg["pto_vta"],
        "CbteTipo": cbte_tipo,
        "Concepto": cfg["concepto"],
        "DocTipo": doc_tipo,
        "DocNro": doc_nro,
        "CbteDesde": numero,
        "CbteHasta": numero,
        "CbteFch": fecha_int,
        "ImpTotal": importe_total,
        "ImpTotConc": 0,
        "ImpNeto": importe_total,
        "ImpOpEx": 0,
        "ImpIVA": 0,
        "ImpTrib": 0,
        "MonId": "PES",
        "MonCotiz": 1,
        "CondicionIVAReceptorId": cond_iva,
    }
    if cfg["usa_periodo"]:
        data["FchServDesde"] = fecha_int
        data["FchServHasta"] = fecha_int
        data["FchVtoPago"] = fecha_int
    if asociado_nro is not None:
        data["CbtesAsoc"] = [{"Tipo": FACTURA_C, "PtoVta": cfg["pto_vta"], "Nro": asociado_nro, "Cuit": str(cfg["cuit"])}]
    res = afip.ElectronicBilling.createVoucher(data)
    res["numero"] = numero
    res["fecha_int"] = fecha_int
    res["serv_desde_int"] = fecha_int if cfg["usa_periodo"] else None
    res["serv_hasta_int"] = fecha_int if cfg["usa_periodo"] else None
    res["cbte_tipo"] = cbte_tipo
    res["asociado_nro"] = asociado_nro
    return res


def _fila_factura(res: dict, payload: dict) -> dict:
    cfg = config()
    return {
        "cliente_id": None,
        "doc_tipo": int(payload["doc_tipo"]),
        "doc_nro": int(payload["doc_nro"]),
        "condicion_iva_receptor": int(payload["condicion_iva"]),
        "pto_vta": cfg["pto_vta"],
        "cbte_tipo": res["cbte_tipo"],
        "cbte_nro": res["numero"],
        "concepto": cfg["concepto"],
        "imp_total": float(payload["monto"]),
        "fch_serv_desde": _fecha_int_a_iso(res["serv_desde_int"]) if res.get("serv_desde_int") else None,
        "fch_serv_hasta": _fecha_int_a_iso(res["serv_hasta_int"]) if res.get("serv_hasta_int") else None,
        "cae": res["CAE"],
        "cae_vto": res["CAEFchVto"],
        "fecha_cbte": _fecha_int_a_iso(res["fecha_int"]),
        "asociado_cbte_nro": res.get("asociado_nro"),
        "descripcion": payload.get("descripcion"),
    }


def generar_pdf_desde_res(res: dict, ud: dict) -> str:
    respuesta = _get_afip().ElectronicBilling.createPDF({
        "html": _html_factura(res, ud),
        "file_name": _nombre_pdf(res),
        "options": {"width": 8, "marginLeft": 0.4, "marginRight": 0.4, "marginTop": 0.4, "marginBottom": 0.4},
    })
    return respuesta["file"]


def _html_factura(res: dict, ud: dict) -> str:
    cfg = config()
    fecha = datetime.strptime(str(res["fecha_int"]), "%Y%m%d").strftime("%d/%m/%Y")
    cae_vto = datetime.strptime(res["CAEFchVto"], "%Y-%m-%d").strftime("%d/%m/%Y")
    qr_png = segno.make(_url_qr_arca(res, ud), error="m").png_data_uri(scale=4)
    descripcion = ud.get("descripcion") or os.environ.get("FACTURA_DESCRIPCION", "Servicios")
    receptor = fmt_doc(ud["doc_tipo"], ud["doc_nro"])
    cond = CONDICIONES_IVA.get(ud.get("cond_iva"), "-")
    total = fmt_ars(float(ud["monto"]))
    return f"""
<style>
body {{ font-family: Helvetica, Arial, sans-serif; font-size: 11px; color: #111; }}
.marco {{ border: 1px solid #111; padding: 16px; }}
.top {{ display: flex; justify-content: space-between; border-bottom: 1px solid #111; padding-bottom: 12px; }}
.letra {{ font-size: 42px; font-weight: bold; text-align: center; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
th {{ background: #eee; text-align: left; padding: 6px; }}
td {{ padding: 6px; border-bottom: 1px solid #ddd; }}
.right {{ text-align: right; }}
.total {{ font-size: 16px; font-weight: bold; margin-top: 20px; text-align: right; }}
.footer {{ display: flex; justify-content: space-between; align-items: end; margin-top: 28px; }}
</style>
<div class="marco">
  <div class="top">
    <div>
      <h2>{cfg['emisor_nombre']}</h2>
      <div><b>CUIT:</b> {cfg['cuit']}</div>
      <div><b>Domicilio:</b> {os.environ.get('EMISOR_DOMICILIO') or '-'}</div>
      <div><b>IVA:</b> Responsable Monotributo</div>
    </div>
    <div class="letra">C<br><small>COD. 011</small></div>
    <div>
      <h2>FACTURA</h2>
      <div><b>PV:</b> {cfg['pto_vta']:05d}</div>
      <div><b>Nro:</b> {res['numero']:08d}</div>
      <div><b>Fecha:</b> {fecha}</div>
    </div>
  </div>
  <p><b>Receptor:</b> {receptor} - {cond}</p>
  <table><tr><th>Descripcion</th><th class="right">Subtotal</th></tr><tr><td>{descripcion}</td><td class="right">$ {total}</td></tr></table>
  <div class="total">Importe Total: $ {total}</div>
  <div class="footer"><img src="{qr_png}" width="110" height="110"><div><b>CAE:</b> {res['CAE']}<br><b>Vto CAE:</b> {cae_vto}</div></div>
</div>
"""


def _url_qr_arca(res: dict, ud: dict) -> str:
    cfg = config()
    datos = {
        "ver": 1,
        "fecha": _fecha_int_a_iso(res["fecha_int"]),
        "cuit": cfg["cuit"],
        "ptoVta": cfg["pto_vta"],
        "tipoCmp": res.get("cbte_tipo", FACTURA_C),
        "nroCmp": res["numero"],
        "importe": round(float(ud["monto"]), 2),
        "moneda": "PES",
        "ctz": 1,
        "tipoDocRec": ud["doc_tipo"],
        "nroDocRec": ud["doc_nro"],
        "tipoCodAut": "E",
        "codAut": int(res["CAE"]),
    }
    payload = base64.b64encode(json.dumps(datos).encode()).decode()
    return f"https://www.afip.gob.ar/fe/qr/?p={payload}"


def _nombre_pdf(res: dict) -> str:
    return f"Factura-C-{config()['pto_vta']:05d}-{res['numero']:08d}"


def _fecha_int_a_iso(fecha_int: int) -> str:
    s = str(fecha_int)
    return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"


def _optional_float(name: str) -> float | None:
    value = os.environ.get(name)
    return float(value) if value else None
