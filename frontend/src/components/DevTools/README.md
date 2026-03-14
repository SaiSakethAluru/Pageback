# `components/DevTools/`

This folder contains development-only UI helpers.

## Contents

- `ApiKeySetup.jsx`: stores a dev OpenAI API key in `localStorage` for local development flows.

## Notes

- This component is gated behind `VITE_ENV === 'development'`.
- It should be removed before a public release.
