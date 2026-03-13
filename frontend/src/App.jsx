import { Navigate, Route, Routes } from "react-router-dom";

import AuthGuard from "./components/Auth/AuthGuard";
import LoginPage from "./components/Auth/LoginPage";
import ApiKeySetup from "./components/DevTools/ApiKeySetup";
import LibraryPage from "./components/Library/LibraryPage";
import ReaderPage from "./components/Reader/ReaderPage";

export default function App() {
  return (
    <>
      <ApiKeySetup />
      <Routes>
        <Route path="/" element={<Navigate to="/library" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/library"
          element={
            <AuthGuard>
              <LibraryPage />
            </AuthGuard>
          }
        />
        <Route
          path="/reader/:bookId"
          element={
            <AuthGuard>
              <ReaderPage />
            </AuthGuard>
          }
        />
      </Routes>
    </>
  );
}
