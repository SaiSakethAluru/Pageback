# `components/Auth/`

This folder contains authentication-related UI.

## Contents

- `LoginPage.jsx`: sign-in screen that starts the backend-owned Google OAuth flow.
- `AuthGuard.jsx`: protects authenticated routes and redirects anonymous users.

## Notes

- `LoginPage.jsx` is the only public-facing auth page in the app.
- `AuthGuard.jsx` wraps private routes such as the library and reader.
