create extension if not exists pgcrypto;
create extension if not exists vector;

create table if not exists public.app_users (
  id uuid primary key default gen_random_uuid(),
  email text,
  display_name text,
  avatar_url text,
  auth_provider text not null,
  provider_subject text not null,
  created_at timestamp with time zone not null default timezone('utc'::text, now()),
  updated_at timestamp with time zone not null default timezone('utc'::text, now()),
  last_login_at timestamp with time zone
);

create table if not exists public.books (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.app_users(id),
  title text,
  author text,
  storage_path text,
  ingestion_status text default 'pending'::text,
  created_at timestamp with time zone default now(),
  ingestion_progress integer,
  ingestion_step text,
  ingestion_error text
);

create table if not exists public.book_chunks (
  id uuid primary key default gen_random_uuid(),
  book_id uuid references public.books(id),
  chapter_index integer,
  chunk_index integer,
  start_char integer,
  end_char integer,
  token_count integer,
  text text,
  embedding vector(1536)
);

create table if not exists public.llm_usage (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id),
  provider text,
  model text,
  input_tokens integer,
  output_tokens integer,
  cost_usd numeric,
  created_at timestamp with time zone default now()
);

create table if not exists public.reading_positions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id),
  book_id uuid references public.books(id),
  position_cfi text,
  position_char integer,
  updated_at timestamp with time zone default now(),
  constraint reading_positions_user_id_book_id_key unique (user_id, book_id)
);

create table if not exists public.recap_cache (
  cache_key text primary key,
  book_id uuid,
  level integer,
  summary_text text,
  created_at timestamp with time zone default now(),
  expires_at timestamp with time zone
);

create unique index if not exists app_users_provider_subject_unique
  on public.app_users using btree (auth_provider, provider_subject);

create index if not exists app_users_email_idx
  on public.app_users using btree (email);

create index if not exists app_users_provider_idx
  on public.app_users using btree (auth_provider, provider_subject);

create index if not exists book_chunks_book_id_end_char_idx
  on public.book_chunks using btree (book_id, end_char desc);

create index if not exists book_chunks_embedding_idx
  on public.book_chunks using ivfflat (embedding vector_cosine_ops);

create or replace function public.match_chunks(
  query_embedding vector,
  p_book_id uuid,
  max_char_offset integer,
  token_budget integer
)
returns table(
  id uuid,
  text text,
  token_count integer,
  start_char integer,
  end_char integer
)
language sql
as $function$
  select id, text, token_count, start_char, end_char
  from book_chunks
  where book_id = p_book_id
    and end_char <= max_char_offset
  order by embedding <=> query_embedding
  limit 20;
$function$;

insert into storage.buckets (id, name, public)
values ('books', 'books', false)
on conflict (id) do nothing;
