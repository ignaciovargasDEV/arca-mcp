import json
import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row


DATABASE_URL = os.environ["DATABASE_URL"]


@contextmanager
def connect():
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        yield conn


def audit(tool_name: str, mode: str, request: dict[str, Any] | None = None,
          result: dict[str, Any] | None = None, error: str | None = None) -> None:
    safe_request = _json_safe(request or {})
    safe_result = _json_safe(result or {})
    with connect() as conn:
        conn.execute(
            """
            insert into mcp_audit_log (tool_name, mode, request, result, error)
            values (%s, %s, %s, %s, %s)
            """,
            (tool_name, mode, json.dumps(safe_request), json.dumps(safe_result), error),
        )


def create_confirmation(action: str, payload: dict[str, Any], ttl_minutes: int = 10) -> str:
    import secrets

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    with connect() as conn:
        conn.execute(
            """
            insert into confirmation_tokens (token, action, payload, expires_at)
            values (%s, %s, %s, %s)
            """,
            (token, action, json.dumps(_json_safe(payload)), expires_at),
        )
    return token


def consume_confirmation(token: str, action: str) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute(
            """
            select token, action, payload, expires_at, used_at
            from confirmation_tokens
            where token = %s
            for update
            """,
            (token,),
        ).fetchone()
        if row is None:
            raise ValueError("confirmation_id invalido")
        if row["action"] != action:
            raise ValueError("confirmation_id no corresponde a esta accion")
        if row["used_at"] is not None:
            raise ValueError("confirmation_id ya fue usado")
        if row["expires_at"] <= datetime.now(timezone.utc):
            raise ValueError("confirmation_id expirado")
        conn.execute(
            "update confirmation_tokens set used_at = now() where token = %s",
            (token,),
        )
        return row["payload"]


def insert_factura(fila: dict[str, Any]) -> None:
    columns = list(fila.keys())
    placeholders = ", ".join(["%s"] * len(columns))
    query = f"insert into facturas_emitidas ({', '.join(columns)}) values ({placeholders})"
    with connect() as conn:
        conn.execute(query, tuple(fila[col] for col in columns))


def update_pdf_url(pto_vta: int, cbte_tipo: int, cbte_nro: int, pdf_url: str) -> None:
    with connect() as conn:
        conn.execute(
            """
            update facturas_emitidas
            set pdf_url = %s
            where pto_vta = %s and cbte_tipo = %s and cbte_nro = %s
            """,
            (pdf_url, pto_vta, cbte_tipo, cbte_nro),
        )


def get_factura(cbte_nro: int, cbte_tipo: int = 11) -> dict[str, Any] | None:
    with connect() as conn:
        return conn.execute(
            """
            select * from facturas_emitidas
            where cbte_tipo = %s and cbte_nro = %s
            order by created_at desc
            limit 1
            """,
            (cbte_tipo, cbte_nro),
        ).fetchone()


def list_facturas(desde: str, hasta: str) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            select * from facturas_emitidas
            where fecha_cbte >= %s and fecha_cbte <= %s
            order by fecha_cbte, cbte_nro
            """,
            (desde, hasta),
        ).fetchall()
        return list(rows)


def recent_receptores(limit: int = 5) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            select doc_tipo, doc_nro, condicion_iva_receptor, count(*) as veces, max(created_at) as ultimo_uso
            from facturas_emitidas
            where doc_tipo <> 99
            group by doc_tipo, doc_nro, condicion_iva_receptor
            order by veces desc, ultimo_uso desc
            limit %s
            """,
            (limit,),
        ).fetchall()
        return list(rows)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items() if not _is_secret_key(k)}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _is_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in ("token", "secret", "password", "cert", "key"))
