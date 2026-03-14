# `tests/integration/`

This folder contains integration tests that exercise real backend flows.

## Contents

- `__init__.py`: package marker.
- `conftest.py`: shared fixtures for app setup, test client, Supabase client, and cleanup.
- `test_ingestion_pipeline.py`: runs the ingestion pipeline end to end.
- `test_recap_endpoint.py`: verifies recap generation and cache behavior over HTTP.

## Notes

- These tests require `.env.test` with valid credentials.
- They write test data into Supabase and rely on cleanup fixtures.
