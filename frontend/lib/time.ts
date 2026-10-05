/**
 * Time and Date utilities for SentinelTrap Dashboard.
 *
 * Backend timestamps are generated/stored in UTC without a trailing 'Z'
 * (e.g. "2026-10-05T15:44:27.833349" or "2026-10-05 15:44:27").
 * Per ECMAScript specification, ISO strings without timezone offsets are parsed
 * as local time by Date.parse(), causing UTC timestamps to display incorrectly
 * (e.g., 5.5 hours behind in India/IST).
 *
 * This utility ensures backend UTC timestamps are correctly interpreted as UTC
 * and formatted using the user's browser/system local timezone.
 */

/**
 * Safely parses a backend timestamp into a JavaScript Date object,
 * ensuring naive UTC strings are interpreted as UTC rather than local time.
 */
export function parseUtcDate(value: string | number | Date | null | undefined): Date | null {
  if (!value) return null;
  if (value instanceof Date) return isNaN(value.getTime()) ? null : value;
  if (typeof value === "number") {
    const d = new Date(value);
    return isNaN(d.getTime()) ? null : d;
  }
  let str = String(value).trim();
  if (!str) return null;

  // Standardize space separator to 'T' for ISO-8601 parsing
  if (str.includes(" ") && !str.includes("T")) {
    str = str.replace(" ", "T");
  }

  // If the string lacks a timezone designator (Z or +HH:mm / -HH:mm offset),
  // append 'Z' so Date parses it as UTC instead of local time.
  const hasTimezone = /([zZ]|[+-]\d{2}(?::?\d{2})?)$/.test(str);
  const isoStr = hasTimezone ? str : `${str}Z`;

  const d = new Date(isoStr);
  if (!isNaN(d.getTime())) {
    return d;
  }

  const fallback = new Date(str);
  return isNaN(fallback.getTime()) ? null : fallback;
}

/**
 * Formats a timestamp into a 24-hour HH:mm:ss string in the browser's local timezone.
 * Used by LiveFeed and TerminalReplay.
 */
export function formatClock(iso: string | number | Date | null | undefined): string {
  try {
    const d = parseUtcDate(iso);
    if (!d) return "--:--:--";
    return d.toLocaleTimeString(undefined, {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return "--:--:--";
  }
}

/**
 * Formats a timestamp into a short local time string (e.g. "09:14 PM" or "21:14").
 * Used by SessionsView and SessionSidebar for session started_at.
 */
export function formatLocalTime(
  iso: string | number | Date | null | undefined,
  options?: Intl.DateTimeFormatOptions
): string {
  try {
    const d = parseUtcDate(iso);
    if (!d) return "--:--";
    return d.toLocaleTimeString([], options ?? { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "--:--";
  }
}

/**
 * Formats a timestamp into a full local time string (e.g. "09:14:27 PM").
 * Used by SessionsView event timeline.
 */
export function formatEventTime(iso: string | number | Date | null | undefined): string {
  try {
    const d = parseUtcDate(iso);
    if (!d) return "--:--:--";
    return d.toLocaleTimeString();
  } catch {
    return "--:--:--";
  }
}

/**
 * Formats a timestamp into a full local date and time string.
 * Used by Alerts view.
 */
export function formatLocalDateTime(iso: string | number | Date | null | undefined): string {
  try {
    const d = parseUtcDate(iso);
    if (!d) return "--";
    return d.toLocaleString();
  } catch {
    return "--";
  }
}
