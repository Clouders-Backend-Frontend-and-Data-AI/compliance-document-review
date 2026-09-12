import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import { getErrorMessage } from "../api/errorMessage";

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
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl mb-1">Create an account</h1>
        <p className="text-sm text-slate mb-8">
          Choose your role now — it's fixed once you sign up.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-ink mb-1">Role</label>
            <div className="grid grid-cols-2 gap-2">
              {["advisor", "officer"].map((r) => (
                <button
                  type="button"
                  key={r}
                  onClick={() => update("role", r)}
                  className={`border px-3 py-2 text-sm capitalize ${
                    form.role === r
                      ? "border-signal text-signal bg-white"
                      : "border-hairline text-slate"
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm text-ink mb-1" htmlFor="full_name">
              Full name
            </label>
            <input
              id="full_name"
              required
              value={form.full_name}
              onChange={(e) => update("full_name", e.target.value)}
              className="w-full border border-hairline px-3 py-2 text-sm bg-white focus:outline-none focus:border-signal"
            />
          </div>
          <div>
            <label className="block text-sm text-ink mb-1" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={form.email}
              onChange={(e) => update("email", e.target.value)}
              className="w-full border border-hairline px-3 py-2 text-sm bg-white focus:outline-none focus:border-signal"
            />
          </div>
          <div>
            <label className="block text-sm text-ink mb-1" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={form.password}
              onChange={(e) => update("password", e.target.value)}
              className="w-full border border-hairline px-3 py-2 text-sm bg-white focus:outline-none focus:border-signal"
            />
          </div>

          {error && (
            <p className="text-sm text-rust bg-rustBg px-3 py-2">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-signal text-white text-sm py-2.5 disabled:opacity-60"
          >
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="text-sm text-slate mt-6">
          Already have an account?{" "}
          <Link to="/login" className="text-signal underline underline-offset-2">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
