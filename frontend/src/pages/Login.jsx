import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";

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
      setError(
        err.response?.data?.detail || "Couldn't sign in. Check your email and password."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl mb-1">Compliance Review</h1>
        <p className="text-sm text-slate mb-8">Sign in to your workspace.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-ink mb-1" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-hairline px-3 py-2 text-sm bg-white focus:outline-none focus:border-signal"
              placeholder="you@firm.com"
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
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-hairline px-3 py-2 text-sm bg-white focus:outline-none focus:border-signal"
              placeholder="••••••••"
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
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="text-sm text-slate mt-6">
          New here?{" "}
          <Link to="/signup" className="text-signal underline underline-offset-2">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}
