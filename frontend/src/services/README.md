# `services/`

This folder contains frontend integration code for external services.

## Contents

- `api.js`: wrapper functions for all Flask backend endpoints.

## Notes

- Keep all backend HTTP calls in `api.js`.
- Keep authentication session handling on the backend instead of introducing client-side auth providers.
