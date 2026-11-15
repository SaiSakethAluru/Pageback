alter table public.books
  add column if not exists series_name text,
  add column if not exists series_order numeric;
