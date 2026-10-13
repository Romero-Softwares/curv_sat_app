-- Aplica-se após 20261012_compact_deleted_system_data.sql.
--
-- Mantém marcadores de exclusão por sete dias para que instalações autorizadas
-- recebam a remoção. O conteúdo dos itens excluídos já é limpo pela migração
-- anterior; ao término do prazo, o marcador também é removido definitivamente.

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
        case when coalesce(item.deleted, false) then null else item.data end,
        case when coalesce(item.deleted, false) then null else item.curve end,
        item.updated_at,
        coalesce(item.deleted, false)
    from jsonb_to_recordset(coalesce(p_records, '[]'::jsonb)) as item(
        pn text, serial_number text, data jsonb, curve jsonb,
        updated_at timestamptz, deleted boolean
    )
    where length(trim(item.pn)) > 0 and item.updated_at is not null
    on conflict (license_hash, pn, serial_number) do update set
        data_json = case when excluded.deleted then null else excluded.data_json end,
        curve_json = case when excluded.deleted then null else excluded.curve_json end,
        updated_at = excluded.updated_at,
        deleted = excluded.deleted
    where excluded.updated_at >= public.curvsat_system_records.updated_at;

    insert into public.curvsat_system_reports
        (license_hash, sha256, numero, prefixo, ano, sequencia, emitido_em, pn, serial_number, conteudo_html, criado_em, deleted, updated_at)
    select
        p_license_hash, item.sha256,
        case when coalesce(item.deleted, false) then '' else coalesce(item.numero, '') end,
        case when coalesce(item.deleted, false) then '' else coalesce(item.prefixo, '') end,
        case when coalesce(item.deleted, false) then 0 else coalesce(item.ano, 0) end,
        case when coalesce(item.deleted, false) then 0 else coalesce(item.sequencia, 0) end,
        case when coalesce(item.deleted, false) then '' else coalesce(item.emitido_em, '') end,
        case when coalesce(item.deleted, false) then '' else coalesce(item.pn, '') end,
        case when coalesce(item.deleted, false) then '' else coalesce(item.serial_number, '') end,
        case when coalesce(item.deleted, false) then '' else coalesce(item.conteudo_html, '') end,
        case when coalesce(item.deleted, false) then '' else coalesce(item.criado_em, '') end,
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
        numero = case when excluded.deleted then '' else excluded.numero end,
        prefixo = case when excluded.deleted then '' else excluded.prefixo end,
        ano = case when excluded.deleted then 0 else excluded.ano end,
        sequencia = case when excluded.deleted then 0 else excluded.sequencia end,
        emitido_em = case when excluded.deleted then '' else excluded.emitido_em end,
        pn = case when excluded.deleted then '' else excluded.pn end,
        serial_number = case when excluded.deleted then '' else excluded.serial_number end,
        conteudo_html = case when excluded.deleted then '' else excluded.conteudo_html end,
        criado_em = case when excluded.deleted then '' else excluded.criado_em end,
        deleted = excluded.deleted,
        updated_at = excluded.updated_at
    where excluded.updated_at >= public.curvsat_system_reports.updated_at;

    delete from public.curvsat_system_records
    where license_hash = p_license_hash
      and deleted
      and updated_at <= now() - interval '7 days';

    delete from public.curvsat_system_reports
    where license_hash = p_license_hash
      and deleted
      and updated_at <= now() - interval '7 days';

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
