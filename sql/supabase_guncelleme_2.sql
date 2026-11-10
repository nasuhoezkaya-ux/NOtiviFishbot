-- NOtivi Fishbot — captcha raporları (üyelerde bilinmeyen captcha çıkınca resmi yöneticiye gelir)
-- Supabase > SQL Editor > New query > yapıştır > Run. Var olan verilere dokunmaz; tekrar çalıştırmak güvenlidir.

create table if not exists public.fb_captcha_reports (
    id          bigint generated always as identity primary key,
    member_id   uuid references public.fb_members(id) on delete set null,
    username    text,
    title       text not null default '',          -- botun okuyabildiği soru (okuyamadıysa boş)
    image       text not null,                     -- captcha penceresinin resmi (JPEG, base64)
    click_x     integer,                           -- üye elle çözdüyse tıkladığı yer (resim koordinatı)
    click_y     integer,
    solved      boolean not null default false,    -- üyenin tıklamasından sonra pencere kapandı mı
    done        boolean not null default false,    -- yönetici çözümü ekledi / işaretledi
    created_at  timestamptz not null default now()
);
create index if not exists fb_captcha_reports_at_idx on public.fb_captcha_reports (created_at desc);
alter table public.fb_captcha_reports enable row level security;
revoke all on public.fb_captcha_reports from anon, authenticated;

-- Üyenin botu gönderir (oturum gerekli; saatte en fazla 30 rapor, resim en fazla ~400 KB)
create or replace function public.fb_captcha_report(p_token uuid, p_title text, p_image text,
                                                    p_click_x integer, p_click_y integer, p_solved boolean)
returns json language plpgsql security definer set search_path = public as $$
declare m public.fb_members;
begin
    select mb.* into m from public.fb_sessions s join public.fb_members mb on mb.id = s.member_id
     where s.token = p_token;
    if not found then
        return json_build_object('ok', false, 'error', 'Oturum bulunamadı.');
    end if;
    if length(coalesce(p_image, '')) < 100 or length(p_image) > 550000 then
        return json_build_object('ok', false, 'error', 'Resim geçersiz.');
    end if;
    if (select count(*) from public.fb_captcha_reports
         where member_id = m.id and created_at > now() - interval '1 hour') >= 30 then
        return json_build_object('ok', false, 'error', 'Çok fazla rapor.');
    end if;
    delete from public.fb_captcha_reports where created_at < now() - interval '30 days';
    insert into public.fb_captcha_reports(member_id, username, title, image, click_x, click_y, solved)
    values (m.id, m.username, left(coalesce(p_title, ''), 200), p_image, p_click_x, p_click_y, coalesce(p_solved, false));
    return json_build_object('ok', true);
end $$;

create or replace function public.fb_admin_captcha_list(p_token uuid, p_limit integer default 60)
returns json language plpgsql security definer set search_path = public as $$
begin
    perform public.fb__admin(p_token);
    return coalesce((select json_agg(x) from (
        select id, username, title, image, click_x, click_y, solved, done, created_at
          from public.fb_captcha_reports order by done, created_at desc limit greatest(1, least(p_limit, 300))
    ) x), '[]'::json);
end $$;

create or replace function public.fb_admin_captcha_done(p_token uuid, p_id bigint, p_delete boolean)
returns json language plpgsql security definer set search_path = public as $$
begin
    perform public.fb__admin(p_token);
    if p_delete then
        delete from public.fb_captcha_reports where id = p_id;
    else
        update public.fb_captcha_reports set done = true where id = p_id;
    end if;
    return json_build_object('ok', true);
end $$;

revoke all on function public.fb_captcha_report(uuid, text, text, integer, integer, boolean),
    public.fb_admin_captcha_list(uuid, integer), public.fb_admin_captcha_done(uuid, bigint, boolean) from public;
grant execute on function public.fb_captcha_report(uuid, text, text, integer, integer, boolean),
    public.fb_admin_captcha_list(uuid, integer), public.fb_admin_captcha_done(uuid, bigint, boolean)
    to anon, authenticated;
