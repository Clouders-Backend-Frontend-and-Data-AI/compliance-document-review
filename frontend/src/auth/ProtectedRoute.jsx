import { Navigate } from "react-router-dom";
import { useAuth } from "./useAuth";

// Wrap a route element with this to require login, and optionally a role.
// Usage: <ProtectedRoute role="advisor"><AdvisorHome /></ProtectedRoute>
export default function ProtectedRoute({ children, role }) {
  const { token, user } = useAuth();

  if (!token || !user) {
    return <Navigate to="/login" replace />;
  }

  if (role && user.role !== role) {
    // Signed in, but the wrong role for this route — send them to their own home.
    return <Navigate to={user.role === "officer" ? "/officer" : "/advisor"} replace />;
  }

  return children;
}
