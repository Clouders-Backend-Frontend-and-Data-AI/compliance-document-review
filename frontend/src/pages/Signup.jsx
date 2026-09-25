import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import { getErrorMessage } from "../api/errorMessage";
import AuthLayout from "../components/AuthLayout";
import { ErrorNote, Field, PasswordField, RoleToggle, SubmitButton } from "../components/AuthFields";

export default function Signup() {
  const navigate = useNavigate();
  const signup = useAuth((s) => s.signup);
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "advisor" });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signup(form);
      navigate(form.role === "officer" ? "/officer" : "/advisor");
    } catch (err) {
      setError(getErrorMessage(err, "Couldn't create the account."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      title="Create an account"
      subtitle="Choose your role now. It can't be changed after you sign up."
      linkTo="/login"
      linkLabel="Sign in"
      variant="dawn"
      tagline="From first draft to final approval."
      blurb="Advisors submit and revise. Officers review and decide. Every step is recorded."
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        <RoleToggle value={form.role} onChange={(role) => update("role", role)} />
        <Field
          id="full_name"
          label="Full name"
          required
          autoComplete="name"
          value={form.full_name}
          onChange={(e) => update("full_name", e.target.value)}
        />
        <Field
          id="email"
          label="Email"
          type="email"
          required
          autoComplete="email"
          placeholder="you@firm.com"
          value={form.email}
          onChange={(e) => update("email", e.target.value)}
        />
        <PasswordField
          id="password"
          required
          autoComplete="new-password"
          value={form.password}
          onChange={(e) => update("password", e.target.value)}
        />
        <ErrorNote>{error}</ErrorNote>
        <SubmitButton loading={loading} loadingLabel="Creating account...">
          Create account
        </SubmitButton>
      </form>
    </AuthLayout>
  );
}
