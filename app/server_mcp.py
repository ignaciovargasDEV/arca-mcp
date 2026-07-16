import os

from mcp.server.fastmcp import FastMCP

from . import core

mcp = FastMCP("arca-mcp")


@mcp.tool()
def config_status() -> dict:
    """Verifica configuracion del MCP, PostgreSQL y ARCA sin exponer secretos."""
    return core.status()


@mcp.tool()
def validar_cuit_dni(documento: str) -> dict:
    """Valida un CUIT o DNI y devuelve el codigo ARCA de documento."""
    return core.validar_documento(documento)


@mcp.tool()
def preview_factura_c(monto: str, documento: str | None = None,
                      condicion_iva: int | None = None, fecha: str | None = None,
                      descripcion: str | None = None) -> dict:
    """Prepara una Factura C y devuelve un confirmation_id. No emite."""
    return core.preview_factura_c(monto, documento, condicion_iva, fecha, descripcion)


@mcp.tool()
def emitir_factura_c(confirmation_id: str, confirmacion: str) -> dict:
    """Emite una Factura C usando un confirmation_id generado por preview_factura_c."""
    return core.emitir_factura_c(confirmation_id, confirmacion)


@mcp.tool()
def preview_factura_e(monto: str, cliente: str, domicilio_cliente: str,
                      pais_destino: int | str | None = None,
                      cuit_pais_cliente: int | str | None = None,
                      id_impositivo: str | None = None, fecha: str | None = None,
                      descripcion: str | None = None, moneda: str | None = None,
                      cotizacion: str | None = None, forma_pago: str | None = None,
                      idioma_cbte: int | None = None) -> dict:
    """Prepara una Factura E de exportacion de servicios y devuelve un confirmation_id. No emite."""
    return core.preview_factura_e(
        monto, cliente, domicilio_cliente, pais_destino, cuit_pais_cliente,
        id_impositivo, fecha, descripcion, moneda, cotizacion, forma_pago,
        idioma_cbte,
    )


@mcp.tool()
def emitir_factura_e(confirmation_id: str, confirmacion: str) -> dict:
    """Emite una Factura E usando un confirmation_id generado por preview_factura_e."""
    return core.emitir_factura_e(confirmation_id, confirmacion)


@mcp.tool()
def parametros_factura_e(catalogo: str = "puntos_venta") -> dict:
    """Consulta catalogos WSFEX: puntos_venta, paises, cuits_pais, monedas, idiomas, unidades_medida, tipos_exportacion."""
    return core.parametros_factura_e(catalogo)


@mcp.tool()
def resumen_periodo(desde: str, hasta: str) -> dict:
    """Devuelve comprobantes emitidos entre dos fechas ISO yyyy-mm-dd."""
    return core.resumen_periodo(desde, hasta)


@mcp.tool()
def exportar_csv_periodo(desde: str, hasta: str) -> str:
    """Devuelve CSV de comprobantes entre dos fechas ISO yyyy-mm-dd."""
    return core.exportar_csv_periodo(desde, hasta)


@mcp.tool()
def enviar_reporte_contador(desde: str, hasta: str, email_contador: str | None = None,
                            nombre_contador: str | None = None, adjuntar_csv: bool = False,
                            adjuntar_pdfs: bool = True, incluir_resumen: bool = True,
                            confirmacion: str | None = None) -> dict:
    """Envia por email al contador el resumen, CSV y PDFs de comprobantes ya emitidos. No emite facturas."""
    return core.enviar_reporte_contador(
        desde, hasta, email_contador, nombre_contador, adjuntar_csv,
        adjuntar_pdfs, incluir_resumen, confirmacion,
    )


@mcp.tool()
def receptores_recientes(limit: int = 5) -> list[dict]:
    """Lista receptores identificados usados recientemente."""
    return core.receptores_recientes(limit)


if __name__ == "__main__":
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8000"))
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.run(transport="streamable-http")
