alter table facturas_emitidas
  add column if not exists moneda_id text not null default 'PES',
  add column if not exists moneda_ctz numeric(18,6) not null default 1,
  add column if not exists cliente_nombre text,
  add column if not exists domicilio_cliente text,
  add column if not exists id_impositivo text,
  add column if not exists pais_dst_cmp int,
  add column if not exists tipo_expo int,
  add column if not exists forma_pago text,
  add column if not exists idioma_cbte int,
  add column if not exists wsfex_id bigint;

create index if not exists idx_facturas_cbte_tipo_fecha on facturas_emitidas (cbte_tipo, fecha_cbte desc);
