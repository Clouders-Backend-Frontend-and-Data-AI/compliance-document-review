import { create } from "zustand";
import { login as apiLogin, signup as apiSignup } from "../api/client";

function readStoredUser() {
  try {
    const raw = localStorage.getItem("cdr_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export const useAuth = create((set) => ({
  token: localStorage.getItem("cdr_token") || null,
  user: readStoredUser(),

  login: async (email, password) => {
    const data = await apiLogin(email, password);
    // Backend shape: { access_token, token_type, user: { id, email, full_name, role, created_at } }
    localStorage.setItem("cdr_token", data.access_token);
    localStorage.setItem("cdr_user", JSON.stringify(data.user));
    set({ token: data.access_token, user: data.user });
    return data.user;
  },

  signup: async (payload) => {
    // payload must be { email, full_name, password, role }
    const data = await apiSignup(payload);
    localStorage.setItem("cdr_token", data.access_token);
    localStorage.setItem("cdr_user", JSON.stringify(data.user));
    set({ token: data.access_token, user: data.user });
    return data.user;
  },

  logout: () => {
    localStorage.removeItem("cdr_token");
    localStorage.removeItem("cdr_user");
    set({ token: null, user: null });
  },
}));
