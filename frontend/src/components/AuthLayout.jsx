import { Link } from "react-router-dom";
import AuthScene from "./AuthScene";
import DawnScene from "./DawnScene";
import "./auth-scene.css";

const DEFAULT_TAGLINE = "Every submission reviewed. Every decision on record.";

function ShieldIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
      <path d="M12 3l7 3v5c0 4.5-3 8.5-7 10-4-1.5-7-5.5-7-10V6l7-3z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 12l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// variant: "dusk" (lake and institution, used on sign in) or "dawn" (bridge and city, used on sign up).
// tagline and blurb are the copy shown over the scene.
export default function AuthLayout({
  title,
  subtitle,
  linkTo,
  linkLabel,
  variant = "dusk",
  tagline = DEFAULT_TAGLINE,
  blurb,
  children,
}) {
  const Scene = variant === "dawn" ? DawnScene : AuthScene;

  return (
    <div className="min-h-screen bg-white font-auth text-ink lg:grid lg:grid-cols-2">
      <div className="flex min-h-screen flex-col px-6 py-6 sm:px-10 lg:px-14">
        <div className="auth-rise flex items-center gap-2 text-signal">
          <ShieldIcon />
          <span className="text-lg font-semibold text-ink">Compliance Review</span>
        </div>

        <div className="flex flex-1 items-center justify-center py-10">
          <div className="w-full max-w-[400px]">
            <div className="auth-rise flex items-baseline justify-between gap-4" style={{ "--d": "100ms" }}>
              <h1 className="font-auth text-2xl font-semibold">{title}</h1>
              <Link
                to={linkTo}
                className="text-sm font-medium text-signal underline-offset-2 hover:underline"
              >
                {linkLabel}
              </Link>
            </div>
            {subtitle && (
              <p className="auth-rise mt-2 text-sm text-slate" style={{ "--d": "150ms" }}>
                {subtitle}
              </p>
            )}
            <div className="auth-enter mt-8">{children}</div>
          </div>
        </div>
      </div>

      <div className="sticky top-0 hidden h-screen p-4 lg:block">
        <div className="relative h-full overflow-hidden rounded-3xl bg-ink">
          <Scene className="absolute inset-0 h-full w-full" />
          <div
            className="auth-rise absolute inset-x-0 top-0 mx-auto max-w-sm px-6 pt-14 text-center text-white"
            style={{ "--d": "500ms", textShadow: "0 1px 18px rgba(10,16,32,0.45)" }}
          >
            <p className="text-balance text-3xl font-medium leading-snug">{tagline}</p>
            {blurb && <p className="mt-4 text-balance text-base leading-relaxed text-white/90">{blurb}</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
