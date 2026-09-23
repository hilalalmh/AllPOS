const ACCESS_KEY = "pos_access_token";
const REFRESH_KEY = "pos_refresh_token";
const USER_KEY = "pos_user";

// Saat logout, refresh yang masih berjalan tidak boleh menulis token baru
// (hasil rotasi) setelah clearAuth — kalau tidak, sesi "kembali hidup" diam-diam.
let writesLocked = false;

export function lockRefreshTokenWrites(): void {
  writesLocked = true;
}

export function unlockRefreshTokenWrites(): void {
  writesLocked = false;
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function getUser(): unknown | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setTokens(access: string, refresh: string): void {
  if (writesLocked) return;
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function setUser(user: unknown): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isAuthenticated(): boolean {
  return getAccessToken() !== null;
}