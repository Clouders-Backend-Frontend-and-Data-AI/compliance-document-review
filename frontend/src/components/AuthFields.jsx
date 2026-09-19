import { useState } from "react";

const inputClass =
  "h-12 w-full rounded-lg border border-gray-300 bg-white px-4 text-[15px] text-ink " +
  "placeholder:text-slate/50 transition-shadow focus:border-signal focus:outline-none " +
  "focus:ring-4 focus:ring-signal/15";

const labelClass = "mb-1.5 block text-sm font-medium text-ink";

export function Field({ id, label, ...inputProps }) {
  return (
    <div>
      <label htmlFor={id} className={labelClass}>
        {label}
      </label>
      <input id={id} className={inputClass} {...inputProps} />
    </div>
  );
}

function EyeIcon({ open }) {
  return open ? (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="12" cy="12" r="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ) : (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
      <path
        d="M3 3l18 18M10.6 10.6a3 3 0 004.24 4.24M9.9 5.1A10.4 10.4 0 0112 5c6.5 0 10 7 10 7a17.3 17.3 0 01-3.2 4.1M6.3 6.3A17.6 17.6 0 002 12s3.5 7 10 7c1.2 0 2.3-.2 3.3-.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function PasswordField({ id, label = "Password", ...inputProps }) {
  const [visible, setVisible] = useState(false);
  return (
    <div>
      <label htmlFor={id} className={labelClass}>
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={visible ? "text" : "password"}
          className={`${inputClass} pr-12`}
          {...inputProps}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Hide password" : "Show password"}
          className="absolute inset-y-0 right-0 flex w-12 items-center justify-center rounded-r-lg text-slate transition-colors hover:text-signal"
        >
          <EyeIcon open={visible} />
        </button>
      </div>
    </div>
  );
}

export function ErrorNote({ children }) {
  if (!children) return null;
  return (
    <p
      role="alert"
      className="rounded-lg bg-rustBg px-4 py-3 text-sm text-rust motion-safe:animate-fade-in"
    >
      {children}
    </p>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
      <path className="opacity-90" d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export function SubmitButton({ loading, loadingLabel, children }) {
  return (
    <button
      type="submit"
      disabled={loading}
      className="flex h-14 w-full items-center justify-center gap-2 rounded-full bg-signal text-base font-medium text-white transition-colors hover:bg-signalDark disabled:cursor-not-allowed disabled:opacity-60"
    >
      {loading && <Spinner />}
      {loading ? loadingLabel : children}
    </button>
  );
}

const ROLES = [
  {
    value: "advisor",
    label: "Advisor",
    hint: "Advisors submit documents and respond to review feedback.",
  },
  {
    value: "officer",
    label: "Officer",
    hint: "Officers review submissions and record the decision.",
  },
];

export function RoleToggle({ value, onChange }) {
  const active = ROLES.find((r) => r.value === value) || ROLES[0];
  return (
    <div>
      <span id="role-label" className={labelClass}>
        Role
      </span>
      <div
        role="radiogroup"
        aria-labelledby="role-label"
        className="grid grid-cols-2 rounded-full bg-gray-100 p-1"
      >
        {ROLES.map((r) => {
          const selected = value === r.value;
          return (
            <button
              key={r.value}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => onChange(r.value)}
              className={`h-10 rounded-full text-sm font-medium transition-colors ${
                selected ? "bg-white text-signal shadow-sm" : "text-slate hover:text-ink"
              }`}
            >
              {r.label}
            </button>
          );
        })}
      </div>
      <p className="mt-2 text-sm text-slate" aria-live="polite">
        {active.hint}
      </p>
    </div>
  );
}
