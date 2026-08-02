const ACCESS_TOKEN_KEY = 'saamu_access_token';
const REFRESH_TOKEN_KEY = 'saamu_refresh_token';
const STORAGE_PREFERENCE_KEY = 'saamu_storage_preference';

/**
 * Browser storage used for JWT tokens.
 *
 * - `localStorage` (default, used when "Remember Me" is checked): persists
 *   across browser restarts.
 * - `sessionStorage` (used when "Remember Me" is unchecked): cleared when the
 *   browser tab/session ends.
 *
 * Trade-off: tokens in browser storage are readable by any same-origin script
 * (XSS risk). Mitigations: we never render tokens as raw HTML, never log them,
 * keep the access token short-lived, and treat the refresh token as a session
 * credential that is blacklisted on the backend at logout.
 */
export type TokenStorageKind = 'localStorage' | 'sessionStorage';

function getPreferredStorageKind(): TokenStorageKind {
  try {
    if (window.localStorage.getItem(STORAGE_PREFERENCE_KEY) === 'sessionStorage') {
      return 'sessionStorage';
    }
  } catch {
    // storage unavailable (e.g. privacy mode) — fall back to localStorage
  }
  return 'localStorage';
}

function storageFor(kind: TokenStorageKind): Storage {
  return kind === 'sessionStorage' ? window.sessionStorage : window.localStorage;
}

function tokenStorage(): Storage {
  return storageFor(getPreferredStorageKind());
}

export function getAccessToken(): string | null {
  return tokenStorage().getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return tokenStorage().getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(access: string, refresh: string, remember: boolean): void {
  const kind: TokenStorageKind = remember ? 'localStorage' : 'sessionStorage';
  try {
    window.localStorage.setItem(STORAGE_PREFERENCE_KEY, kind);
  } catch {
    // ignore storage preference failures
  }
  const storage = storageFor(kind);
  storage.setItem(ACCESS_TOKEN_KEY, access);
  storage.setItem(REFRESH_TOKEN_KEY, refresh);
}

/** Persist a freshly refreshed access token into the active token storage. */
export function persistAccessToken(access: string): void {
  tokenStorage().setItem(ACCESS_TOKEN_KEY, access);
}

export function clearTokens(): void {
  for (const storage of [window.localStorage, window.sessionStorage]) {
    storage.removeItem(ACCESS_TOKEN_KEY);
    storage.removeItem(REFRESH_TOKEN_KEY);
  }
  try {
    window.localStorage.removeItem(STORAGE_PREFERENCE_KEY);
  } catch {
    // ignore
  }
}
