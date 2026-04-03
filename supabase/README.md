# Supabase Schema

The checked-in source of truth for database structure lives in [`supabase/migrations/`](/Users/saketh/Projects/Pageback/supabase/migrations).

The generated CLI project config lives in [`supabase/config.toml`](/Users/saketh/Projects/Pageback/supabase/config.toml).

## Current migration layout

- `20260402160000_initial_schema.sql`: baseline schema captured from the existing Supabase project.
- `20260402161000_align_schema_with_app_code.sql`: follow-up fixes to match the current backend expectations.

## Important note

The baseline migration reflects the live schema that existed before we started codifying migrations. The second migration intentionally changes a few things to align the database with the application code:

- adds `public.books.cover_path`
- points `public.reading_positions.user_id` to `public.app_users(id)`
- points `public.llm_usage.user_id` to `public.app_users(id)`

Those FK changes match the app's backend-owned user model in [`backend/app/auth/service.py`](/Users/saketh/Projects/Pageback/backend/app/auth/service.py#L10) and session handling in [`backend/app/auth/session.py`](/Users/saketh/Projects/Pageback/backend/app/auth/session.py#L10).

## Applying migrations

## How The CLI Tracks State

`supabase/config.toml` is not the last known remote schema state.

- The schema source of truth is the SQL files in `supabase/migrations/`.
- The Supabase CLI stores linked-project metadata locally under `supabase/.temp/` and that directory is intentionally gitignored.
- Applied migration history is tracked in the database by Supabase's migration history table, not in `config.toml`.

That means the CLI can tell which migrations are already applied after you link the repo to a hosted project and reconcile migration history.

## Recommended Workflow For This Repo

1. Install or invoke the Supabase CLI.

```bash
npx supabase@latest --version
```

2. Link this repo to your hosted Supabase project.

```bash
npx supabase@latest link --project-ref <your-project-ref>
```

3. Because the hosted project already existed before migrations were checked in, mark the baseline migrations as already applied instead of re-running them.

```bash
npx supabase@latest migration repair 20260402160000 --status applied
npx supabase@latest migration repair 20260402161000 --status applied
```

4. For future schema changes, create a new migration file and apply it through the CLI workflow instead of copy-pasting SQL manually.

```bash
npx supabase@latest migration new <name>
```

5. Apply pending migrations to a linked project.

```bash
npx supabase@latest db push
```

## Important Notes

- `db push` compares your linked project's recorded migration history to the files in `supabase/migrations/` and applies pending ones.
- Since `20260402161000_align_schema_with_app_code.sql` was already run manually on the hosted database, use `migration repair ... --status applied` so the CLI history matches reality.
- The same is true for `20260402160000_initial_schema.sql`: the underlying schema already existed, so it should be marked as applied rather than executed on the live project.

For an existing Supabase project, review the diff first. The alignment migration changes foreign keys, so it should be applied intentionally rather than assumed to be no-op.
