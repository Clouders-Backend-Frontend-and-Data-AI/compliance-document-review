import { NavLink, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../auth/useAuth";
import { getNotifications } from "../api/client";
import NotificationsBell from "./NotificationsBell";

const ICONS = {
  submissions: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
      <path d="M9 12h6M9 16h6M9 8h6M6 4h9l3 3v13a1 1 0 01-1 1H6a1 1 0 01-1-1V5a1 1 0 011-1z" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  upload: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
      <path d="M12 16V4m0 0L7 9m5-5l5 5M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  queue: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
      <path d="M4 6h16M4 12h16M4 18h7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
};

const ADVISOR_LINKS = [
  { to: "/advisor", label: "My submissions", end: true, icon: ICONS.submissions },
  { to: "/advisor/upload", label: "Submit a document", icon: ICONS.upload },
];

const OFFICER_LINKS = [
  { to: "/officer", label: "Review queue", end: true, icon: ICONS.queue },
];

function initials(nameOrEmail) {
  if (!nameOrEmail) return "?";
  const base = nameOrEmail.includes("@") ? nameOrEmail.split("@")[0] : nameOrEmail;
  const parts = base.trim().split(/\s+/);
  return parts.length > 1
    ? (parts[0][0] + parts[1][0]).toUpperCase()
    : base.slice(0, 2).toUpperCase();
}

export default function AppShell() {
  const { user, logout } = useAuth();
  const links = user.role === "officer" ? OFFICER_LINKS : ADVISOR_LINKS;

  const { data: notifications } = useQuery({
    queryKey: ["notifications"],
    queryFn: getNotifications,
    refetchInterval: 30000,
  });

  return (
    <div className="min-h-screen flex bg-paper">
      <aside className="w-64 shrink-0 border-r border-hairline bg-white flex flex-col shadow-[1px_0_3px_rgba(0,0,0,0.03)]">
        <div className="px-5 py-5 border-b border-hairline">
          <p className="font-serif text-lg leading-tight text-ink">Compliance Review</p>
          <p className="text-xs text-slate mt-0.5 capitalize">{user.role} workspace</p>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 text-sm rounded-sm transition-all duration-150 ${
                  isActive
                    ? "bg-signal text-white shadow-sm"
                    : "text-ink hover:bg-paper hover:translate-x-0.5"
                }`
              }
            >
              {link.icon}
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-hairline flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-signal text-white flex items-center justify-center text-xs font-medium shrink-0">
            {initials(user.name || user.email)}
          </div>
          <div className="min-w-0">
            <p className="text-sm text-ink truncate">{user.name || user.email}</p>
            <button
              onClick={logout}
              className="text-xs text-slate underline underline-offset-2 hover:text-signal transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-hairline bg-white flex items-center justify-end px-6 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
          <NotificationsBell notifications={notifications} />
        </header>
        <main className="flex-1 px-8 py-8 max-w-5xl">
          <Outlet />
        </main>
      </div>
    </div>
  );
}