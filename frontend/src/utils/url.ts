/**
 * URL utility functions for handling origin normalization and URL construction
 */

/**
 * Normalizes an origin URL by converting 0.0.0.0 to localhost
 * This ensures consistent redirect URLs regardless of how the app is accessed
 * 
 * @param origin - The origin URL (e.g., "http://0.0.0.0:3000" or "http://localhost:3000")
 * @returns Normalized origin URL with localhost instead of 0.0.0.0
 * 
 * @example
 * normalizeOrigin("http://0.0.0.0:3000") // Returns "http://localhost:3000"
 * normalizeOrigin("http://localhost:3000") // Returns "http://localhost:3000"
 */
export function normalizeOrigin(origin: string): string {
  try {
    const url = new URL(origin);
    // Replace 0.0.0.0 with localhost
    if (url.hostname === "0.0.0.0") {
      url.hostname = "localhost";
    }
    return url.origin;
  } catch {
    // If URL parsing fails, try simple string replacement
    return origin.replace(/0\.0\.0\.0/g, "localhost");
  }
}

/**
 * Gets the normalized origin from the current window location
 * Useful for constructing redirect URLs that work consistently
 *
 * @returns Normalized origin (localhost instead of 0.0.0.0)
 */
export function getNormalizedOrigin(): string {
  if (typeof window === "undefined") {
    // Server-side: use environment variable or default
    return process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
  }
  return normalizeOrigin(window.location.origin);
}

/**
 * Gets the app origin URL, prioritizing environment variable
 * Use this for OAuth redirects to ensure correct URL in all environments
 *
 * @returns App origin URL
 */
export function getAppOrigin(): string {
  // Priority: ENV variable > window location (if available) > default
  if (process.env.NEXT_PUBLIC_SITE_URL) {
    return process.env.NEXT_PUBLIC_SITE_URL;
  }

  if (typeof window !== "undefined") {
    return normalizeOrigin(window.location.origin);
  }

  return "http://localhost:3000";
}

