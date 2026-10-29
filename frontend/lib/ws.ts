/**
 * SentinelTrap Centralized WebSocket URL Resolver
 * Resolves the appropriate WebSocket connection URL across local dev (port 3000 -> 8000),
 * production reverse proxies, and custom environment configuration.
 */
export function getSentinelWsUrl(): string {
  if (process.env.NEXT_PUBLIC_SENTINELTRAP_WS_URL) {
    return process.env.NEXT_PUBLIC_SENTINELTRAP_WS_URL;
  }
  if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    // If running in local dev/preview on port 3000, redirect WebSocket directly to backend port 8000
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      const host = window.location.port === "3000" ? `${window.location.hostname}:8000` : window.location.host;
      return `${proto}//${host}/ws`;
    }
    return `${proto}//${window.location.host}/ws`;
  }
  return "";
}
