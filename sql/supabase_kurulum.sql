-- =====================================================================================================
--  FishBot üyelik sistemi — Supabase kurulumu
--  Supabase > SQL Editor > New query > bu dosyanın TAMAMINI yapıştır > Run.
--  Birden fazla kez çalıştırmak güvenlidir (var olanları bozmaz).
--  En alttaki "İLK YÖNETİCİ" bölümünde kullanıcı adını ve şifreyi değiştirmeyi unutma.
-- =====================================================================================================

create extension if not exists pgcrypto with schema extensions;

-- ---------------------------------------------------------------------------- tablolar
create table if not exists public.fb_members (
    id           uuid primary key default gen_random_uuid(),
    username     text not null,
    pass_hash    text not null,                       -- bcrypt (şifrenin kendisi saklanmaz)
    expires_at   timestamptz,                          -- NULL = süresiz üyelik
    active       boolean not null default true,        -- false = askıya alındı
    is_admin     boolean not null default false,       -- programdaki "Üyeler" sayfasını görür
    max_clients  integer not null default 0,           -- aynı anda kaç client; 0 = sınırsız
    hwid_lock    boolean not null default false,       -- true = sadece ilk giriş yaptığı bilgisayar
    hwid         text,                                 -- son / kilitli bilgisayar kimliği (özet)
    note         text not null default '',
    created_at   timestamptz not null default now(),
    last_login   timestamptz
);
create unique index if not exists fb_members_username_uq on public.fb_members (lower(username));

create table if not exists public.fb_sessions (
    token       uuid primary key default gen_random_uuid(),
    member_id   uuid not null references public.fb_members(id) on delete cascade,
    hwid        text,
    created_at  timestamptz not null default now(),
    last_seen   timestamptz not null default now()
);
create index if not exists fb_sessions_member_idx on public.fb_sessions (member_id);

create table if not exists public.fb_login_log (
    id        bigint generated always as identity primary key,
    username  text,
    ok        boolean not null,
    reason    text,
    hwid      text,
    at        timestamptz not null default now()
);
create index if not exists fb_login_log_user_at_idx on public.fb_login_log (lower(username), at desc);

-- Tablolar dışarıya tamamen kapalı: RLS açık ve hiçbir politika yok. Erişim sadece aşağıdaki fonksiyonlarla.
alter table public.fb_members   enable row level security;
alter table public.fb_sessions  enable row level security;
alter table public.fb_login_log enable row level security;
revoke all on public.fb_members, public.fb_sessions, public.fb_login_log from anon, authenticated;

-- ---------------------------------------------------------------------------- giriş
create or replace function public.fb_login(p_username text, p_password text, p_hwid text)
returns json language plpgsql security definer set search_path = public, extensions as $$
declare
    m        public.fb_members;
    v_token  uuid;
    v_fails  integer;
begin
    select count(*) into v_fails from public.fb_login_log
     where lower(username) = lower(trim(p_username)) and not ok and at > now() - interval '10 minutes';
    if v_fails >= 8 then
        return json_build_object('ok', false, 'error', 'Çok fazla hatalı deneme. 10 dakika sonra tekrar dene.');
    end if;

    select * into m from public.fb_members where lower(username) = lower(trim(p_username));
    if not found or m.pass_hash <> crypt(p_password, m.pass_hash) then
        insert into public.fb_login_log(username, ok, reason, hwid) values (trim(p_username), false, 'sifre', p_hwid);
        return json_build_object('ok', false, 'error', 'Kullanıcı adı veya şifre hatalı.');
    end if;
    if not m.active then
        insert into public.fb_login_log(username, ok, reason, hwid) values (m.username, false, 'askida', p_hwid);
        return json_build_object('ok', false, 'error', 'Hesabınız askıya alınmış.');
    end if;
    if m.expires_at is not null and m.expires_at <= now() then
        insert into public.fb_login_log(username, ok, reason, hwid) values (m.username, false, 'sure', p_hwid);
        return json_build_object('ok', false, 'error', 'Üyeliğinizin süresi dolmuş.');
    end if;
    if m.hwid_lock and m.hwid is not null and m.hwid <> p_hwid then
        insert into public.fb_login_log(username, ok, reason, hwid) values (m.username, false, 'cihaz', p_hwid);
        return json_build_object('ok', false, 'error', 'Bu hesap başka bir bilgisayara kilitli.');
    end if;

    update public.fb_members
       set last_login = now(),
           hwid = case when hwid_lock and hwid is not null then hwid else p_hwid end
     where id = m.id;
    delete from public.fb_sessions where member_id = m.id and last_seen < now() - interval '30 days';
    insert into public.fb_sessions(member_id, hwid) values (m.id, p_hwid) returning token into v_token;
    insert into public.fb_login_log(username, ok, reason, hwid) values (m.username, true, null, p_hwid);

    return json_build_object('ok', true, 'token', v_token, 'username', m.username, 'expires_at', m.expires_at,
                             'is_admin', m.is_admin, 'max_clients', m.max_clients);
end $$;

-- Bot çalışırken birkaç dakikada bir çağırır: süre uzatıldıysa / askıya alındıysa hemen yansır.
create or replace function public.fb_verify(p_token uuid)
returns json language plpgsql security definer set search_path = public, extensions as $$
declare m public.fb_members;
begin
    select mb.* into m from public.fb_sessions s join public.fb_members mb on mb.id = s.member_id
     where s.token = p_token;
    if not found then
        return json_build_object('ok', false, 'error', 'Oturum bulunamadı.');
    end if;
    update public.fb_sessions set last_seen = now() where token = p_token;
    if not m.active then
        return json_build_object('ok', false, 'error', 'Hesabınız askıya alınmış.');
    end if;
    if m.expires_at is not null and m.expires_at <= now() then
        return json_build_object('ok', false, 'error', 'Üyeliğinizin süresi dolmuş.');
    end if;
    return json_build_object('ok', true, 'expires_at', m.expires_at, 'is_admin', m.is_admin,
                             'max_clients', m.max_clients);
end $$;

create or replace function public.fb_logout(p_token uuid)
returns json language sql security definer set search_path = public as $$
    delete from public.fb_sessions where token = p_token;
    select json_build_object('ok', true);
$$;

-- ---------------------------------------------------------------------------- yönetici
-- (iç yardımcı: oturum bir yöneticiye ait değilse hata verir; dışarıdan çağrılamaz)
create or replace function public.fb__admin(p_token uuid)
returns uuid language plpgsql security definer set search_path = public as $$
declare v_id uuid;
begin
    select mb.id into v_id from public.fb_sessions s join public.fb_members mb on mb.id = s.member_id
     where s.token = p_token and mb.is_admin and mb.active
       and (mb.expires_at is null or mb.expires_at > now());
    if v_id is null then
        raise exception 'Bu işlem için yönetici yetkisi gerekli.';
    end if;
    update public.fb_sessions set last_seen = now() where token = p_token;
    return v_id;
end $$;

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

-- p_original NULL = yeni üye (şifre zorunlu); dolu = o adlı üyeyi güncelle (ad değiştirilebilir).
-- p_password NULL/boş ise şifre değişmez. p_expires_at NULL = süresiz.
create or replace function public.fb_admin_save(
    p_token uuid, p_original text, p_username text, p_password text, p_expires_at timestamptz,
    p_active boolean, p_is_admin boolean, p_max_clients integer, p_hwid_lock boolean, p_note text)
returns json language plpgsql security definer set search_path = public, extensions as $$
declare
    v_me  uuid;
    v_id  uuid;
begin
    v_me := public.fb__admin(p_token);
    if coalesce(trim(p_username), '') = '' then
        raise exception 'Kullanıcı adı boş olamaz.';
    end if;
    if p_original is null then
        if coalesce(p_password, '') = '' then
            raise exception 'Yeni üye için şifre gerekli.';
        end if;
        if exists (select 1 from public.fb_members where lower(username) = lower(trim(p_username))) then
            raise exception 'Bu kullanıcı adı zaten var.';
        end if;
        insert into public.fb_members(username, pass_hash, expires_at, active, is_admin, max_clients, hwid_lock, note)
        values (trim(p_username), crypt(p_password, gen_salt('bf')), p_expires_at, coalesce(p_active, true),
                coalesce(p_is_admin, false), coalesce(p_max_clients, 0), coalesce(p_hwid_lock, false),
                coalesce(p_note, ''));
    else
        select id into v_id from public.fb_members where lower(username) = lower(p_original);
        if v_id is null then
            raise exception 'Üye bulunamadı.';
        end if;
        if exists (select 1 from public.fb_members
                    where lower(username) = lower(trim(p_username)) and id <> v_id) then
            raise exception 'Bu kullanıcı adı zaten var.';
        end if;
        if v_id = v_me and (not coalesce(p_is_admin, true) or not coalesce(p_active, true)) then
            raise exception 'Kendi yönetici yetkini ya da hesabını kapatamazsın.';
        end if;
        update public.fb_members set
            username    = trim(p_username),
            pass_hash   = case when coalesce(p_password, '') = '' then pass_hash
                               else crypt(p_password, gen_salt('bf')) end,
            expires_at  = p_expires_at,
            active      = coalesce(p_active, active),
            is_admin    = coalesce(p_is_admin, is_admin),
            max_clients = coalesce(p_max_clients, max_clients),
            hwid_lock   = coalesce(p_hwid_lock, hwid_lock),
            note        = coalesce(p_note, note)
         where id = v_id;
        if not coalesce(p_active, true) then
            delete from public.fb_sessions where member_id = v_id;   -- askıya alınan anında düşer
        end if;
    end if;
    return json_build_object('ok', true);
end $$;

create or replace function public.fb_admin_delete(p_token uuid, p_username text)
returns json language plpgsql security definer set search_path = public as $$
declare v_me uuid;
begin
    v_me := public.fb__admin(p_token);
    if exists (select 1 from public.fb_members where id = v_me and lower(username) = lower(p_username)) then
        raise exception 'Kendi hesabını silemezsin.';
    end if;
    delete from public.fb_members where lower(username) = lower(p_username);
    return json_build_object('ok', true);
end $$;

create or replace function public.fb_admin_reset_hwid(p_token uuid, p_username text)
returns json language plpgsql security definer set search_path = public as $$
begin
    perform public.fb__admin(p_token);
    update public.fb_members set hwid = null where lower(username) = lower(p_username);
    return json_build_object('ok', true);
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

-- Son giriş denemeleri (Üyeler sayfasındaki "Giriş kayıtları")
create or replace function public.fb_admin_log(p_token uuid, p_limit integer default 200)
returns json language plpgsql security definer set search_path = public as $$
begin
    perform public.fb__admin(p_token);
    return coalesce((select json_agg(x) from (
        select username, ok, reason, at from public.fb_login_log order by at desc limit greatest(1, least(p_limit, 1000))
    ) x), '[]'::json);
end $$;

-- ---------------------------------------------------------------------------- yetkiler
revoke all on function public.fb__admin(uuid) from public, anon, authenticated;
revoke all on function public.fb_login(text, text, text), public.fb_verify(uuid), public.fb_logout(uuid),
    public.fb_admin_list(uuid), public.fb_admin_delete(uuid, text), public.fb_admin_reset_hwid(uuid, text),
    public.fb_admin_kick(uuid, text), public.fb_admin_log(uuid, integer),
    public.fb_admin_save(uuid, text, text, text, timestamptz, boolean, boolean, integer, boolean, text)
    from public;
grant execute on function public.fb_login(text, text, text), public.fb_verify(uuid), public.fb_logout(uuid),
    public.fb_admin_list(uuid), public.fb_admin_delete(uuid, text), public.fb_admin_reset_hwid(uuid, text),
    public.fb_admin_kick(uuid, text), public.fb_admin_log(uuid, integer),
    public.fb_admin_save(uuid, text, text, text, timestamptz, boolean, boolean, integer, boolean, text)
    to anon, authenticated;

-- ---------------------------------------------------------------------------- İLK YÖNETİCİ
-- 'admin' ve 'SifreniYaz' kısmını değiştir. Süresiz yönetici oluşturur (zaten varsa dokunmaz).
insert into public.fb_members (username, pass_hash, expires_at, is_admin)
select 'admin', crypt('SifreniYaz', gen_salt('bf')), null, true
where not exists (select 1 from public.fb_members where lower(username) = 'admin');
