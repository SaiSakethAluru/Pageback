# Frontend

The frontend is a React + Vite app that handles authentication, library management, reading, and the recap interaction.

## Responsibilities

- authenticate users with Supabase Auth
- show the user's uploaded library
- upload EPUB files through the backend API
- render books in the browser with `epubjs`
- save reading position as the user moves
- request progressively deeper recaps from the backend

## Structure

```text
frontend/
  src/
    components/
      Auth/
      Library/
      Reader/
      DevTools/
    readers/
    services/
  index.html
  package.json
  vite.config.js
```

## Important Modules

- `src/services/supabaseClient.js`: single Supabase client instance
- `src/services/api.js`: backend API wrapper
- `src/components/Library/LibraryPage.jsx`: library screen
- `src/components/Reader/ReaderPage.jsx`: main reading experience
- `src/components/Reader/RecapFAB.jsx`: recap interaction entry point
- `src/readers/EpubReader.jsx`: EPUB rendering wrapper around `epubjs`

## Local Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Environment Variables

- `VITE_API_BASE_URL`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_ENV`

## User Flow

1. User signs in on `/login`.
2. User lands on `/library`.
3. User uploads an EPUB.
4. The app polls until ingestion is complete.
5. User opens `/reader/:bookId`.
6. Position is restored and saved as the user reads.
7. The recap FAB asks the backend for progressively deeper summaries.

## Development Notes

- `ApiKeySetup` is a development-only helper and should not ship publicly.
- `PdfReader` is currently a stub.
- The UI is intentionally thin and API-driven; most business logic lives in the backend.
