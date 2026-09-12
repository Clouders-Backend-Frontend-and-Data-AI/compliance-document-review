import { NavLink, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../auth/useAuth";
import { getNotifications } from "../api/client";
import NotificationsBell from "./NotificationsBell";

const ADVISOR_LINKS = [
  { to: "/advisor", label: "My submissions", end: true },
  { to: "/advisor/upload", label: "Submit a document" },
];

const OFFICER_LINKS = [
  { to: "/officer", label: "Review queue", end: true },
];

export default function AppShell() {
  const { user, logout } = useAuth();
  const links = user.role === "officer" ? OFFICER_LINKS : ADVISOR_LINKS;

  const { data: notifications } = useQuery({
    queryKey: ["notifications"],
    queryFn: getNotifications,
    refetchInterval: 30000,
  });

  return (
    <div className="min-h-screen flex">
      <aside className="w-60 shrink-0 border-r border-hairline bg-white flex flex-col">
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
                `block px-3 py-2 text-sm rounded-sm ${
                  isActive
                    ? "bg-signal text-white"
                    : "text-ink hover:bg-paper"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-hairline">
          <p className="text-sm text-ink">{user.name || user.email}</p>
          <button
            onClick={logout}
            className="text-xs text-slate underline underline-offset-2 mt-1"
          >
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-hairline bg-white flex items-center justify-end px-6">
          <NotificationsBell notifications={notifications} />
        </header>
        <main className="flex-1 px-8 py-8 max-w-5xl">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
