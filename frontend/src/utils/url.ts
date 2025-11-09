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
    // Server-side: return a default or throw error
    throw new Error("getNormalizedOrigin can only be called on the client side");
  }
  return normalizeOrigin(window.location.origin);
}

