import { Navigate, Route, Routes } from "react-router-dom";

import AuthGuard from "./components/Auth/AuthGuard";
import LoginPage from "./components/Auth/LoginPage";
import LibraryPage from "./components/Library/LibraryPage";
import ReaderPage from "./components/Reader/ReaderPage";
import SettingsPage from "./components/Settings/SettingsPage";

export default function App() {
  return (
    <>
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
        <Route
          path="/settings"
          element={
            <AuthGuard>
              <SettingsPage />
            </AuthGuard>
          }
        />
      </Routes>
    </>
  );
}
