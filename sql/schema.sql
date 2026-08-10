create extension if not exists pgcrypto;

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  username text unique not null,
  password_hash text not null,
  created_at timestamptz default now()
);

create table if not exists holdings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  ticker text not null,
  name text,
  market text,
  quantity numeric not null default 0,
  avg_price numeric default 0,
  created_at timestamptz default now()
);

create index if not exists holdings_user_id_idx on holdings(user_id);

-- 이 앱은 자체 로그인(아이디/비밀번호)을 쓰고 Supabase Auth를 쓰지 않으므로
-- RLS는 껴두고 접근 제어는 앱 코드(user_id 필터링)에서 처리합니다.
alter table users enable row level security;
alter table holdings enable row level security;

create policy "allow all via anon key" on users for all using (true) with check (true);
create policy "allow all via anon key" on holdings for all using (true) with check (true);
