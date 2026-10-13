-- Execute this migration in Supabase SQL Editor before distributing a build
-- with cloud license synchronization enabled.
--
-- The desktop application has only the publishable key. It cannot read or
-- write this table directly; it may only execute the narrow RPC below.

-- An earlier deployment may have created this table with a different column
-- layout. `create table if not exists` would silently keep that table and the
-- foreign keys below would then fail because `license_hash` is absent.
--
-- Do not delete legacy activations: their machine identifiers cannot be
-- converted into the SHA-256 hash of the activation code (the code is not
-- stored in that schema). Rename the old table as an immutable archive and
-- let each authorized installation register its existing activation code on
-- its next synchronization.
do $$
begin
    if to_regclass('public.curvsat_license_activations') is not null
       and not exists (
           select 1
           from information_schema.columns
           where table_schema = 'public'
             and table_name = 'curvsat_license_activations'
             and column_name = 'license_hash'
       ) then
        if to_regclass('public.curvsat_license_activations_legacy_20261011') is not null then
            raise exception
                'A tabela de ativacoes legada ja foi arquivada em public.curvsat_license_activations_legacy_20261011. Verifique-a antes de continuar.';
        end if;

        alter table public.curvsat_license_activations
            rename to curvsat_license_activations_legacy_20261011;
    end if;
end;
$$;

create table if not exists public.curvsat_license_activations (
    license_hash text primary key
        check (license_hash ~ '^[a-f0-9]{64}$'),
    organization text not null check (length(trim(organization)) > 0),
    expires_on date,
    status text not null default 'active'
        check (status in ('active', 'suspended', 'revoked')),
    first_activated_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now()
);

alter table public.curvsat_license_activations enable row level security;

revoke all on table public.curvsat_license_activations from anon, authenticated;

create or replace function public.sync_curvsat_license(
    p_license_hash text,
    p_organization text,
    p_expires_on date
)
returns table (
    status text,
    matched boolean,
    last_seen_at timestamptz
)
language plpgsql
security definer
set search_path = public
as $$
begin
    if p_license_hash !~ '^[a-f0-9]{64}$' then
        raise exception 'invalid license hash';
    end if;

    -- The signed activation is shared by all authorized computers. Its hash
    -- identifies the organization license without identifying any device.
    insert into public.curvsat_license_activations (
        license_hash, organization, expires_on
    )
    values (
        p_license_hash, trim(p_organization), p_expires_on
    )
    on conflict (license_hash) do update
        set last_seen_at = now();

    return query
        select
            activation.status,
            true,
            activation.last_seen_at
        from public.curvsat_license_activations as activation
        where activation.license_hash = p_license_hash;
end;
$$;

revoke all on function public.sync_curvsat_license(text, text, date) from public;
grant execute on function public.sync_curvsat_license(text, text, date) to anon, authenticated;

-- Dados compartilhados da organiza\u00e7\u00e3o. O execut\u00e1vel nunca recebe permiss\u00f5es
-- diretas nas tabelas: ele usa somente a RPC abaixo, limitada ao hash da sua
-- licen\u00e7a ativa.
create table if not exists public.curvsat_system_settings (
    license_hash text primary key references public.curvsat_license_activations(license_hash) on delete cascade,
    values_json jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now()
);

create table if not exists public.curvsat_system_records (
    license_hash text not null references public.curvsat_license_activations(license_hash) on delete cascade,
    pn text not null,
    serial_number text not null default '',
    data_json jsonb,
    curve_json jsonb,
    updated_at timestamptz not null,
    deleted boolean not null default false,
    primary key (license_hash, pn, serial_number)
);
create index if not exists idx_curvsat_system_records_sync
    on public.curvsat_system_records (license_hash, updated_at desc);

-- A instalação inicial podia já ter a tabela de registros sem o marcador de
-- exclusão. Mantenha esta migração reaplicável nesses bancos.
alter table public.curvsat_system_records
    add column if not exists deleted boolean not null default false;

create table if not exists public.curvsat_system_reports (
    license_hash text not null references public.curvsat_license_activations(license_hash) on delete cascade,
    sha256 text not null check (sha256 ~ '^[a-f0-9]{64}$'),
    numero text not null,
    prefixo text not null,
    ano integer not null,
    sequencia integer not null,
    emitido_em text not null,
    pn text not null default '',
    serial_number text not null default '',
    conteudo_html text not null,
    criado_em text not null,
    deleted boolean not null default false,
    updated_at timestamptz not null default now(),
    primary key (license_hash, sha256)
);

alter table public.curvsat_system_reports
    add column if not exists deleted boolean not null default false;
alter table public.curvsat_system_reports
    add column if not exists updated_at timestamptz;
update public.curvsat_system_reports
set updated_at = coalesce(updated_at, criado_em::timestamptz, now());
alter table public.curvsat_system_reports
    alter column updated_at set default now(),
    alter column updated_at set not null;

alter table public.curvsat_system_settings enable row level security;
alter table public.curvsat_system_records enable row level security;
alter table public.curvsat_system_reports enable row level security;
revoke all on table public.curvsat_system_settings, public.curvsat_system_records, public.curvsat_system_reports from anon, authenticated;

create or replace function public.sync_curvsat_system_data(
    p_license_hash text,
    p_settings jsonb,
    p_settings_updated_at timestamptz,
    p_records jsonb,
    p_reports jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_status text;
begin
    if p_license_hash !~ '^[a-f0-9]{64}$' then
        raise exception 'invalid license hash';
    end if;
    select status into v_status
    from public.curvsat_license_activations
    where license_hash = p_license_hash;
    if v_status is distinct from 'active' then
        raise exception 'active license required';
    end if;

    if jsonb_typeof(p_settings) = 'object' and p_settings_updated_at is not null then
        insert into public.curvsat_system_settings (license_hash, values_json, updated_at)
        values (p_license_hash, p_settings, p_settings_updated_at)
        on conflict (license_hash) do update set
            values_json = excluded.values_json,
            updated_at = excluded.updated_at
        where excluded.updated_at >= public.curvsat_system_settings.updated_at;
    end if;

    insert into public.curvsat_system_records
        (license_hash, pn, serial_number, data_json, curve_json, updated_at, deleted)
    select
        p_license_hash,
        trim(item.pn),
        coalesce(item.serial_number, ''),
        item.data,
        item.curve,
        item.updated_at,
        coalesce(item.deleted, false)
    from jsonb_to_recordset(coalesce(p_records, '[]'::jsonb)) as item(
        pn text, serial_number text, data jsonb, curve jsonb,
        updated_at timestamptz, deleted boolean
    )
    where length(trim(item.pn)) > 0 and item.updated_at is not null
    on conflict (license_hash, pn, serial_number) do update set
        data_json = excluded.data_json,
        curve_json = excluded.curve_json,
        updated_at = excluded.updated_at,
        deleted = excluded.deleted
    where excluded.updated_at >= public.curvsat_system_records.updated_at;

    insert into public.curvsat_system_reports
        (license_hash, sha256, numero, prefixo, ano, sequencia, emitido_em, pn, serial_number, conteudo_html, criado_em, deleted, updated_at)
    select
        p_license_hash, item.sha256, coalesce(item.numero, ''), coalesce(item.prefixo, ''), coalesce(item.ano, 0),
        coalesce(item.sequencia, 0), coalesce(item.emitido_em, ''), coalesce(item.pn, ''),
        coalesce(item.serial_number, ''), coalesce(item.conteudo_html, ''), coalesce(item.criado_em, ''),
        coalesce(item.deleted, false), item.updated_at
    from jsonb_to_recordset(coalesce(p_reports, '[]'::jsonb)) as item(
        sha256 text, numero text, prefixo text, ano integer, sequencia integer,
        emitido_em text, pn text, serial_number text, conteudo_html text, criado_em text,
        deleted boolean, updated_at timestamptz
    )
    where item.sha256 ~ '^[a-f0-9]{64}$'
      and item.updated_at is not null
      and (coalesce(item.deleted, false) or (item.numero <> '' and item.prefixo <> '' and item.conteudo_html <> ''))
    on conflict (license_hash, sha256) do update set
        numero = case when excluded.deleted then public.curvsat_system_reports.numero else excluded.numero end,
        prefixo = case when excluded.deleted then public.curvsat_system_reports.prefixo else excluded.prefixo end,
        ano = case when excluded.deleted then public.curvsat_system_reports.ano else excluded.ano end,
        sequencia = case when excluded.deleted then public.curvsat_system_reports.sequencia else excluded.sequencia end,
        emitido_em = case when excluded.deleted then public.curvsat_system_reports.emitido_em else excluded.emitido_em end,
        pn = case when excluded.deleted then public.curvsat_system_reports.pn else excluded.pn end,
        serial_number = case when excluded.deleted then public.curvsat_system_reports.serial_number else excluded.serial_number end,
        conteudo_html = case when excluded.deleted then public.curvsat_system_reports.conteudo_html else excluded.conteudo_html end,
        criado_em = case when excluded.deleted then public.curvsat_system_reports.criado_em else excluded.criado_em end,
        deleted = excluded.deleted,
        updated_at = excluded.updated_at
    where excluded.updated_at >= public.curvsat_system_reports.updated_at;

    return jsonb_build_object(
        'settings', (
            select jsonb_build_object('values', values_json, 'updated_at', updated_at)
            from public.curvsat_system_settings where license_hash = p_license_hash
        ),
        'records', coalesce((
            select jsonb_agg(jsonb_build_object(
                'pn', pn, 'serial_number', serial_number, 'data', data_json,
                'curve', curve_json, 'updated_at', updated_at, 'deleted', deleted
            )) from public.curvsat_system_records where license_hash = p_license_hash
        ), '[]'::jsonb),
        'reports', coalesce((
            select jsonb_agg(jsonb_build_object(
                'numero', numero, 'prefixo', prefixo, 'ano', ano, 'sequencia', sequencia,
                'emitido_em', emitido_em, 'pn', pn, 'serial_number', serial_number,
                'conteudo_html', conteudo_html, 'sha256', sha256, 'criado_em', criado_em,
                'deleted', deleted, 'updated_at', updated_at
            )) from public.curvsat_system_reports where license_hash = p_license_hash
        ), '[]'::jsonb)
    );
end;
$$;

revoke all on function public.sync_curvsat_system_data(text, jsonb, timestamptz, jsonb, jsonb) from public;
grant execute on function public.sync_curvsat_system_data(text, jsonb, timestamptz, jsonb, jsonb) to anon, authenticated;
