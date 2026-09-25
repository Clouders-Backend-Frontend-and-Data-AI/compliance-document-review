import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import { getErrorMessage } from "../api/errorMessage";
import AuthLayout from "../components/AuthLayout";
import { ErrorNote, Field, PasswordField, SubmitButton } from "../components/AuthFields";

export default function Login() {
  const navigate = useNavigate();
  const login = useAuth((s) => s.login);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await login(email, password);
      navigate(user.role === "officer" ? "/officer" : "/advisor");
    } catch (err) {
      setError(getErrorMessage(err, "Couldn't sign in. Check your email and password."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title="Sign in" linkTo="/signup" linkLabel="Create account">
      <form onSubmit={handleSubmit} className="space-y-5">
        <Field
          id="email"
          label="Email"
          type="email"
          required
          autoComplete="email"
          placeholder="you@firm.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <PasswordField
          id="password"
          required
          autoComplete="current-password"
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <ErrorNote>{error}</ErrorNote>
        <SubmitButton loading={loading} loadingLabel="Signing in...">
          Sign in
        </SubmitButton>
      </form>
    </AuthLayout>
  );
}
