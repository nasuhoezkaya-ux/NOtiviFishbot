-- FishBot — üye paneli güncellemesi (supabase_kurulum.sql'i zaten çalıştırdıysan SADECE bunu çalıştır)
-- Supabase > SQL Editor > New query > yapıştır > Run. Var olan üyelere dokunmaz.

create or replace function public.fb_admin_list(p_token uuid)
returns json language plpgsql security definer set search_path = public as $$
begin
    perform public.fb__admin(p_token);
    return coalesce((
        select json_agg(json_build_object(
                   'id', m.id, 'username', m.username, 'expires_at', m.expires_at, 'active', m.active,
                   'is_admin', m.is_admin, 'max_clients', m.max_clients, 'hwid_lock', m.hwid_lock, 'hwid', m.hwid,
                   'note', m.note, 'created_at', m.created_at, 'last_login', m.last_login,
                   'sessions', (select count(*) from public.fb_sessions s
                                 where s.member_id = m.id and s.last_seen > now() - interval '15 minutes'),
                   'last_seen', (select max(s.last_seen) from public.fb_sessions s where s.member_id = m.id))
               order by lower(m.username))
          from public.fb_members m), '[]'::json);
end $$;

-- Üyenin açık oturumlarını kapat (botu birkaç dakika içinde durur)
create or replace function public.fb_admin_kick(p_token uuid, p_username text)
returns json language plpgsql security definer set search_path = public as $$
begin
    perform public.fb__admin(p_token);
    delete from public.fb_sessions s using public.fb_members m
     where s.member_id = m.id and lower(m.username) = lower(p_username) and s.token <> p_token;
    return json_build_object('ok', true);
end $$;

revoke all on function public.fb_admin_kick(uuid, text) from public;
grant execute on function public.fb_admin_kick(uuid, text) to anon, authenticated;
