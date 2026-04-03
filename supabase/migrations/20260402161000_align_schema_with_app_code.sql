alter table public.books
  add column if not exists cover_path text;

alter table public.reading_positions
  drop constraint if exists reading_positions_user_id_fkey;

alter table public.reading_positions
  add constraint reading_positions_user_id_fkey
  foreign key (user_id)
  references public.app_users(id);

alter table public.llm_usage
  drop constraint if exists llm_usage_user_id_fkey;

alter table public.llm_usage
  add constraint llm_usage_user_id_fkey
  foreign key (user_id)
  references public.app_users(id);
