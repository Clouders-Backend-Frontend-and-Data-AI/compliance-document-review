import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import { getErrorMessage } from "../api/errorMessage";

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
    <div className="min-h-screen flex">
      {/* Intro panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-ink text-white flex-col justify-between px-12 py-12">
        <p className="font-serif text-xl">Compliance Review</p>

        <div>
          <h1 className="font-serif text-4xl leading-tight mb-4">
            Review, revise, and approve —
            <br />
            without the back-and-forth.
          </h1>
          <p className="text-white/70 text-base leading-relaxed mb-8 max-w-md">
            A shared workspace for advisors and compliance officers to submit
            documents, get AI-assisted analysis, and track every decision in
            one place.
          </p>

          <ul className="space-y-3 text-sm text-white/80">
            <li className="flex items-start gap-2.5">
              <span className="text-white/50 mt-0.5">—</span>
              Automatic PII masking before anything reaches the AI reviewer
            </li>
            <li className="flex items-start gap-2.5">
              <span className="text-white/50 mt-0.5">—</span>
              Full audit trail on every submission and revision
            </li>
            <li className="flex items-start gap-2.5">
              <span className="text-white/50 mt-0.5">—</span>
              Clear status tracking from submission to approval
            </li>
          </ul>
        </div>

        <p className="text-xs text-white/40">
          Built for teams who take compliance seriously.
        </p>
      </div>

      {/* Form panel */}
      <div className="w-full lg:w-1/2 flex items-center justify-center px-4 bg-paper">
        <div className="w-full max-w-sm">
          <div className="lg:hidden mb-8">
            <h1 className="font-serif text-2xl text-ink mb-1">Compliance Review</h1>
            <p className="text-sm text-slate">Sign in to your workspace.</p>
          </div>
          <div className="hidden lg:block mb-8">
            <h2 className="font-serif text-2xl text-ink mb-1">Welcome back</h2>
            <p className="text-sm text-slate">Sign in to your workspace.</p>
          </div>

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
                className="w-full border border-hairline rounded-sm px-3 py-2 text-sm bg-white focus:outline-none focus:border-signal"
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
                className="w-full border border-hairline rounded-sm px-3 py-2 text-sm bg-white focus:outline-none focus:border-signal"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <p className="text-sm text-rust bg-rustBg rounded-sm px-3 py-2">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-signal text-white text-sm py-2.5 rounded-sm hover:opacity-90 transition-opacity disabled:opacity-60"
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
    </div>
  );
}