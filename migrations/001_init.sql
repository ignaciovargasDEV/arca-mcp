create table if not exists clientes (
  id bigint generated always as identity primary key,
  nombre text not null,
  doc_tipo int not null,
  doc_nro bigint not null default 0,
  condicion_iva_receptor int not null,
  email text,
  notas text,
  created_at timestamptz not null default now(),
  unique (doc_tipo, doc_nro)
);

create table if not exists facturas_emitidas (
  id bigint generated always as identity primary key,
  cliente_id bigint references clientes(id),
  doc_tipo int not null default 99,
  doc_nro bigint not null default 0,
  condicion_iva_receptor int not null default 5,
  pto_vta int not null,
  cbte_tipo int not null,
  cbte_nro int not null,
  concepto int not null,
  imp_total numeric(14,2) not null,
  fch_serv_desde date,
  fch_serv_hasta date,
  cae text not null,
  cae_vto date not null,
  fecha_cbte date not null,
  pdf_url text,
  asociado_cbte_nro int,
  descripcion text,
  created_at timestamptz not null default now(),
  unique (pto_vta, cbte_tipo, cbte_nro)
);

create index if not exists idx_facturas_fecha on facturas_emitidas (fecha_cbte desc);
create index if not exists idx_facturas_created_at on facturas_emitidas (created_at desc);

create table if not exists confirmation_tokens (
  token text primary key,
  action text not null,
  payload jsonb not null,
  expires_at timestamptz not null,
  used_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists mcp_audit_log (
  id bigint generated always as identity primary key,
  tool_name text not null,
  mode text not null,
  request jsonb,
  result jsonb,
  error text,
  created_at timestamptz not null default now()
);
