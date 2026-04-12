alter table public.ingestion_requests
  add column if not exists control_status text not null default 'active',
  add column if not exists embedded_chunks integer not null default 0,
  add column if not exists total_chunks integer,
  add column if not exists embedded_tokens integer not null default 0,
  add column if not exists total_tokens integer;

create unique index if not exists book_chunks_book_chapter_chunk_unique
  on public.book_chunks using btree (book_id, chapter_index, chunk_index);
