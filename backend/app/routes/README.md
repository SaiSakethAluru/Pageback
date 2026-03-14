# `routes/`

This folder contains the Flask blueprints exposed by the backend API.

## Contents

- `__init__.py`: package marker.
- `books.py`: upload, ingestion-status lookup, and library-list endpoints.
- `positions.py`: save and restore reading positions.
- `recap.py`: recap generation, cache lookup, and recap-level config endpoints.

## Endpoint Groups

- `books.py` handles `/api/v1/books`
- `positions.py` handles `/api/v1/positions`
- `recap.py` handles `/api/v1/recap`
