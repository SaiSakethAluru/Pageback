create table if not exists public.ai_model_configs (
  id uuid primary key default gen_random_uuid(),
  provider text not null,
  recap_model text not null,
  embedding_model text not null,
  created_at timestamp with time zone not null default timezone('utc'::text, now()),
  constraint ai_model_configs_provider_models_unique unique (provider, recap_model, embedding_model)
);

create table if not exists public.ingestion_requests (
  id uuid primary key,
  book_id uuid references public.books(id) on delete cascade,
  user_id uuid references public.app_users(id) on delete cascade,
  book_title text,
  model_config_id uuid references public.ai_model_configs(id),
  celery_task_id text,
  status text not null,
  progress integer,
  step text,
  error_type text,
  error_message text,
  log_path text,
  created_at timestamp with time zone not null default timezone('utc'::text, now()),
  started_at timestamp with time zone,
  completed_at timestamp with time zone
);

create table if not exists public.ingestion_request_events (
  id uuid primary key default gen_random_uuid(),
  request_id uuid references public.ingestion_requests(id) on delete cascade,
  status text not null,
  progress integer,
  step text,
  message text,
  created_at timestamp with time zone not null default timezone('utc'::text, now())
);

alter table public.books
  add column if not exists ingestion_request_id uuid references public.ingestion_requests(id);

create index if not exists ingestion_requests_book_created_idx
  on public.ingestion_requests using btree (book_id, created_at desc);

create index if not exists ingestion_requests_user_created_idx
  on public.ingestion_requests using btree (user_id, created_at desc);

create index if not exists ingestion_request_events_request_created_idx
  on public.ingestion_request_events using btree (request_id, created_at asc);
