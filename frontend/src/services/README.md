# `services/`

This folder contains frontend integration code for external services.

## Contents

- `api.js`: wrapper functions for all Flask backend endpoints.
- `supabaseClient.js`: the single shared Supabase client instance.

## Notes

- Keep all backend HTTP calls in `api.js`.
- Do not initialize extra Supabase clients elsewhere in the app.
