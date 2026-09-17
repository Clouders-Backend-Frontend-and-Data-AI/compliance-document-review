import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import { getErrorMessage } from "../api/errorMessage";

function ShieldIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
      <path
        d="M12 3l7 3v5c0 4.5-3 8.5-7 10-4-1.5-7-5.5-7-10V6l7-3z"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M9 12l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function EyeIcon({ open }) {
  return open ? (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="12" cy="12" r="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ) : (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
      <path d="M3 3l18 18M10.6 10.6a3 3 0 004.24 4.24M9.9 5.1A10.4 10.4 0 0112 5c6.5 0 10 7 10 7a17.3 17.3 0 01-3.2 4.1M6.3 6.3A17.6 17.6 0 002 12s3.5 7 10 7c1.2 0 2.3-.2 3.3-.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
      <path className="opacity-90" d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export default function Login() {
  const navigate = useNavigate();
  const login = useAuth((s) => s.login);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 30);
    return () => clearTimeout(t);
  }, []);

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
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-ink text-white flex-col justify-between px-12 py-12">
        <div
          className="absolute inset-0 opacity-[0.07] pointer-events-none"
          style={{
            backgroundImage:
              "radial-gradient(currentColor 1px, transparent 1px)",
            backgroundSize: "24px 24px",
          }}
        />
        <div
          className="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-signal/30 blur-3xl pointer-events-none"
        />
        <div
          className="absolute -bottom-32 -left-16 w-80 h-80 rounded-full bg-signalDark/40 blur-3xl pointer-events-none"
        />

        <div
          className={`relative flex items-center gap-2 transition-all duration-700 ${
            mounted ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-2"
          }`}
        >
          <ShieldIcon />
          <p className="font-serif text-xl">Compliance Review</p>
        </div>

        <div
          className={`relative transition-all duration-700 delay-100 ${
            mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-3"
          }`}
        >
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

        <p className="relative text-xs text-white/40">
          Built for teams who take compliance seriously.
        </p>
      </div>

      {/* Form panel */}
      <div className="w-full lg:w-1/2 flex items-center justify-center px-4 bg-paper">
        <div
          className={`w-full max-w-sm transition-all duration-700 ${
            mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-3"
          }`}
        >
          <div className="lg:hidden mb-8 flex items-center gap-2">
            <ShieldIcon />
            <div>
              <h1 className="font-serif text-2xl text-ink leading-tight">Compliance Review</h1>
              <p className="text-sm text-slate">Sign in to your workspace.</p>
            </div>
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
                className="w-full border border-hairline rounded-sm px-3 py-2 text-sm bg-white transition-shadow duration-150 focus:outline-none focus:border-signal focus:ring-4 focus:ring-signal/10"
                placeholder="you@firm.com"
              />
            </div>
            <div>
              <label className="block text-sm text-ink mb-1" htmlFor="password">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full border border-hairline rounded-sm px-3 py-2 pr-10 text-sm bg-white transition-shadow duration-150 focus:outline-none focus:border-signal focus:ring-4 focus:ring-signal/10"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate hover:text-signal transition-colors"
                  tabIndex={-1}
                >
                  <EyeIcon open={showPassword} />
                </button>
              </div>
            </div>

            {error && (
              <p className="text-sm text-rust bg-rustBg rounded-sm px-3 py-2 animate-[fadeIn_0.2s_ease-in]">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-signal text-white text-sm py-2.5 rounded-sm hover:opacity-90 active:scale-[0.99] transition-all disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {loading && <Spinner />}
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="text-sm text-slate mt-6">
            New here?{" "}
            <Link to="/signup" className="text-signal underline underline-offset-2 hover:text-signalDark transition-colors">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}