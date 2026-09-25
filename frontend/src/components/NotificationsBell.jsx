import { useState } from "react";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import { markAllNotificationsRead, markNotificationRead } from "../api/client";

export default function NotificationsBell({ notifications }) {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();
  // Backend shape: { unread_count, notifications: [{ id, title, message, is_read, created_at }] }
  const items = notifications?.notifications || [];
  const unreadCount = notifications?.unread_count ?? items.filter((n) => !n.is_read).length;

  const markOne = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAll = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative text-sm text-ink px-3 py-1.5 rounded-sm hover:bg-paper"
        aria-label="Notifications"
      >
        Notifications
        {unreadCount > 0 && (
          <span className="ml-1.5 inline-flex items-center justify-center w-5 h-5 text-[11px] rounded-full bg-signal text-white">
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white border border-hairline shadow-sm z-10">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-hairline">
            <p className="text-sm font-medium">Notifications</p>
            {unreadCount > 0 && (
              <button
                onClick={() => markAll.mutate()}
                className="text-xs text-signal underline underline-offset-2"
              >
                Mark all read
              </button>
            )}
          </div>
          <ul className="max-h-80 overflow-y-auto">
            {items.length === 0 && (
              <li className="px-4 py-6 text-sm text-slate text-center">
                Nothing yet — updates on your documents will show up here.
              </li>
            )}
            {items.map((n) => (
              <li
                key={n.id}
                className={`px-4 py-3 text-sm border-b border-hairline last:border-b-0 ${
                  n.is_read ? "text-slate" : "text-ink"
                }`}
              >
                <p className="font-medium">{n.title}</p>
                <p>{n.message}</p>
                {!n.is_read && (
                  <button
                    onClick={() => markOne.mutate(n.id)}
                    className="text-xs text-signal underline underline-offset-2 mt-1"
                  >
                    Mark read
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
