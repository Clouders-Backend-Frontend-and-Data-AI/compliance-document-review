import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./auth/useAuth";
import ProtectedRoute from "./auth/ProtectedRoute";
import AppShell from "./components/AppShell";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import AdvisorHome from "./pages/advisor/AdvisorHome";
import UploadDocument from "./pages/advisor/UploadDocument";
import DocumentDetail from "./pages/advisor/DocumentDetail";
import OfficerQueue from "./pages/officer/OfficerQueue";
import DocumentReview from "./pages/officer/DocumentReview";

export default function App() {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      <Route
        path="/advisor"
        element={
          <ProtectedRoute role="advisor">
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<AdvisorHome />} />
        <Route path="upload" element={<UploadDocument />} />
        <Route path="documents/:id" element={<DocumentDetail />} />
      </Route>

      <Route
        path="/officer"
        element={
          <ProtectedRoute role="officer">
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<OfficerQueue />} />
        <Route path="documents/:id" element={<DocumentReview />} />
      </Route>

      <Route
        path="/"
        element={
          <Navigate to={user ? (user.role === "officer" ? "/officer" : "/advisor") : "/login"} replace />
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
