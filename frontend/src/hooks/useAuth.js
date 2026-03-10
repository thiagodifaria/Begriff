import { useEffect, useState } from "react";

import { getCurrentUser, login as apiLogin } from "../services/api";

const TOKEN_STORAGE_KEY = "begriff_token";

export function useAuth() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_STORAGE_KEY) || "");
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(token));
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    getCurrentUser(token)
      .then((response) => {
        setUser(response);
        setError("");
      })
      .catch(() => {
        setToken("");
        setUser(null);
        localStorage.removeItem(TOKEN_STORAGE_KEY);
      })
      .finally(() => setLoading(false));
  }, [token]);

  async function login(email, password) {
    setError("");
    try {
      const response = await apiLogin(email, password);
      localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
      setToken(response.access_token);
      return true;
    } catch (err) {
      setError(err.message || "Falha no login.");
      return false;
    }
  }

  function logout() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken("");
    setUser(null);
  }

  return {
    token,
    user,
    loading,
    error,
    login,
    logout,
    isAuthenticated: Boolean(token && user)
  };
}
